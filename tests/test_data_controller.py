"""
End-to-end tests for `DataController` on a real CSV file: open, edit metadata, load, section, reload.

`DataController` is a `QObject`, which works without a running `QApplication`. Background work is run through
`SyncRunner`, so results are applied before the call returns; `test_workers_deliver_on_the_gui_thread` covers the real
thread pool.
"""

import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import polars as pl
import pytest
from PySide6 import QtCore

from signal_viewer.constants import COMBO_BOX_NO_SELECTION, INDEX_COL
from signal_viewer.enum_defs import IncompleteWindowMethod, PeakDetectionAlgorithm, PreprocessPipeline, SectionChange
from signal_viewer.sv_data.data_controller import DataController
from signal_viewer.sv_data.section import DEFAULT_RATE_PARAMS
from signal_viewer.type_defs import (
    PeakDetectionRequest,
    PeaksLocalMaxima,
    ProcessingRequest,
    RollingRateKwargs,
)

FS = 100
N = FS * 20


class SyncRunner:
    """Stands in for `QThreadPool`: runs each worker immediately on the calling thread."""

    def start(self, runnable: QtCore.QRunnable, /) -> None:
        runnable.run()


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """20 s at 100 Hz with a float `time` column so the sampling rate can be detected."""
    t = np.arange(N) / FS
    pl.DataFrame(
        {
            "time": t,
            "Alpha Sig": np.sin(2 * np.pi * t),
            "Beta Temp": np.linspace(20.0, 30.0, N),
        }
    ).write_csv(tmp_path / "recording.csv")
    return tmp_path / "recording.csv"


def test_open_file_reads_schema_and_sampling_rate(csv_file: Path) -> None:
    dc = DataController()
    emitted: list[object] = []
    dc.sig_new_metadata.connect(emitted.append)

    dc.open_file(csv_file)

    assert dc.metadata.valid_columns == ["time", "Alpha Sig", "Beta Temp"]
    assert dc.metadata.sampling_rate == FS
    assert not dc.has_data
    assert emitted == [dc.metadata]


def test_load_data_keeps_metadata_and_uses_cleaned_names(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")

    dc.load_data()

    assert dc.has_data
    assert dc.base_df.columns == [INDEX_COL, "alpha_sig", "beta_temp"]
    assert dc.base_df.height == N
    # The metadata still describes the file; only the data frame carries cleaned names.
    assert dc.metadata.signal_column == "Alpha Sig"
    assert dc.metadata.info_column == "Beta Temp"

    base = dc.get_base_section()
    assert dc.sections.rowCount() == 1
    assert dc.active_section is base
    assert base.signal_name == "alpha_sig"
    assert base.info_name == "beta_temp"
    assert base.sampling_rate == FS
    assert base.is_locked


def test_load_data_without_info_column(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col=COMBO_BOX_NO_SELECTION)

    dc.load_data()

    assert dc.base_df.columns == [INDEX_COL, "alpha_sig"]
    assert dc.get_base_section().info_name is None


def test_create_section_and_reload(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")
    dc.load_data()

    dc.create_section(100, 299)
    assert dc.sections.rowCount() == 2
    section = dc.sections.editable_sections[0]
    assert section.global_bounds == (100, 299)
    assert section.data.height == 200
    assert section.signal_name == "alpha_sig"
    assert not section.is_locked

    # Loading again discards sections but keeps the user's metadata choices.
    dc.load_data()
    assert dc.sections.rowCount() == 1
    assert dc.sections.editable_sections == []
    assert dc.metadata.signal_column == "Alpha Sig"
    assert dc.active_section is dc.get_base_section()


def test_rate_params_reach_existing_and_new_sections(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")
    dc.load_data()
    dc.create_section(100, 299)
    assert all(s.rate_params == DEFAULT_RATE_PARAMS for s in dc.sections.all_sections)

    params: RollingRateKwargs = {
        "sec_new_window_every": 5,
        "sec_window_length": 30,
        "incomplete_window_method": IncompleteWindowMethod.Approximate,
    }
    dc.set_rate_params(params)
    assert dc.rate_params == params
    assert all(s.rate_params == params for s in dc.sections.all_sections)

    dc.create_section(300, 499)
    assert dc.sections.editable_sections[-1].rate_params == params


# --- Facade: every mutation goes through the controller and emits one `sig_section_changed` ---------------------------


def _loaded_with_section(csv_file: Path) -> tuple[DataController, list[tuple[object, SectionChange]]]:
    """A controller with one 20 s editable section active, and a recorder for `sig_section_changed`."""
    dc = DataController(thread_pool=SyncRunner())
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")
    dc.load_data()
    dc.create_section(0, N - 1)
    dc.set_active_section(dc.sections.index(1))

    emitted: list[tuple[object, SectionChange]] = []
    dc.sig_section_changed.connect(lambda section, flags: emitted.append((section, flags)))
    return dc, emitted


def sine_peaks() -> np.ndarray:
    """Maxima of the fixture's 1 Hz sine: one per second."""
    return np.arange(25, N, FS)


def test_active_section_signal_carries_the_section(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")
    activated: list[object] = []
    dc.sig_active_section_changed.connect(activated.append)

    dc.load_data()
    dc.create_section(0, 199)
    dc.set_active_section(dc.sections.index(1))

    assert activated == [dc.get_base_section(), dc.sections.editable_sections[0]]
    assert dc.active_section_model.df.height == 200


def test_apply_processing_emits_signal_peaks_and_rate(csv_file: Path) -> None:
    dc, emitted = _loaded_with_section(csv_file)
    section = dc.active_section

    dc.apply_processing(ProcessingRequest(pipeline=PreprocessPipeline.PPG_Elgendi))
    assert emitted == [(section, SectionChange.SIGNAL | SectionChange.PEAKS | SectionChange.RATE)]
    assert section.is_processed

    dc.reset_signal()
    assert emitted[-1] == (section, SectionChange.SIGNAL | SectionChange.PEAKS | SectionChange.RATE)
    assert not section.is_processed
    assert section.processed_signal.equals(section.raw_signal)


def test_peak_edits_emit_peaks_and_rate(csv_file: Path) -> None:
    dc, emitted = _loaded_with_section(csv_file)
    section = dc.active_section
    request = PeakDetectionRequest(
        PeakDetectionAlgorithm.LocalMaxima, PeaksLocalMaxima(search_radius=40, min_distance=40)
    )

    dc.detect_peaks(request)
    assert section.peaks_local.to_list() == sine_peaks().tolist()
    assert emitted[-1] == (section, SectionChange.PEAKS | SectionChange.RATE)

    dc.update_peaks("remove", np.array([25]))
    assert section.peaks_local.to_list() == sine_peaks().tolist()[1:]
    assert section.manual_peak_edits.removed == [25]
    assert emitted[-1] == (section, SectionChange.PEAKS | SectionChange.RATE)

    dc.clear_peaks()
    assert section.peaks_local.is_empty()
    assert section.rate_data.is_empty()
    assert emitted[-1] == (section, SectionChange.PEAKS | SectionChange.RATE)

    dc.detect_peaks_in_range(1000, 1500, request)
    assert section.peaks_local.to_list() == [1025, 1125, 1225, 1325, 1425]
    assert emitted[-1] == (section, SectionChange.PEAKS | SectionChange.RATE)
    assert len(emitted) == 4, "exactly one emission per mutation"


def test_lock_and_unlock(csv_file: Path) -> None:
    dc, emitted = _loaded_with_section(csv_file)
    section = dc.active_section
    tasks: list[str] = []
    dc.sig_task_started.connect(tasks.append)
    dc.sig_task_finished.connect(lambda: tasks.append("finished"))
    failures: list[Exception] = []
    dc.sig_task_failed.connect(failures.append)

    dc.lock_active()
    assert len(failures) == 1 and isinstance(failures[0], RuntimeError) and "at least 3" in str(failures[0])
    assert emitted == [], "a failed lock changes nothing"
    assert not section.is_locked
    assert tasks == ["Creating section result...", "finished"], "the busy indicator is released on failure too"

    dc.update_peaks("add", sine_peaks())
    dc.lock_active()
    assert section.is_locked
    assert not section.peak_data.is_empty()
    assert "global_index" in section.peak_data.columns and "beta_temp" in section.peak_data.columns
    assert "beta_temp_mean" in section.rate_data.columns, "the locked rate carries the full info statistics"
    assert emitted[-1] == (section, SectionChange.LOCK | SectionChange.RESULT)
    assert len(failures) == 1

    # A locked section is not touched by a late detection result or another lock.
    emitted.clear()
    dc.detect_peaks(
        PeakDetectionRequest(PeakDetectionAlgorithm.LocalMaxima, PeaksLocalMaxima(search_radius=40, min_distance=40))
    )
    dc.lock_active()
    assert emitted == []

    dc.unlock_active()
    assert not section.is_locked
    assert emitted[-1] == (section, SectionChange.LOCK)


def test_set_rate_params_recomputes_only_when_peaks_exist(csv_file: Path) -> None:
    dc, emitted = _loaded_with_section(csv_file)
    section = dc.active_section
    params: RollingRateKwargs = {
        "sec_new_window_every": 2,
        "sec_window_length": 10,
        "incomplete_window_method": IncompleteWindowMethod.Drop,
    }

    dc.set_rate_params(params)
    assert emitted == [], "no peaks, so there is no rate to recompute"

    dc.update_peaks("add", sine_peaks())
    emitted.clear()
    dc.set_rate_params(DEFAULT_RATE_PARAMS)
    assert emitted == [(section, SectionChange.RATE)]
    assert section.rate_data.is_empty(), "60 s windows never complete in a 20 s section"

    emitted.clear()
    dc.set_rate_params(params)
    assert emitted == [(section, SectionChange.RATE)]
    # 10 s windows every 2 s in 20 s: starts 0, 2, ..., 10 are complete, each holding 10 peaks.
    assert section.rate_data.get_column("rate_bpm").to_list() == pytest.approx([60.0] * 6)


def test_workers_deliver_on_the_gui_thread(csv_file: Path, qapp: QtCore.QCoreApplication) -> None:
    """With the real thread pool, results are applied on the controller's thread, not the worker's."""
    dc = DataController()  # global QThreadPool
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")
    dc.load_data()
    dc.create_section(0, N - 1)
    dc.set_active_section(dc.sections.index(1))
    section = dc.active_section

    seen: list[tuple[int, SectionChange]] = []
    dc.sig_section_changed.connect(lambda s, f: seen.append((threading.get_ident(), f)))
    finished: list[bool] = []
    dc.sig_task_finished.connect(lambda: finished.append(True))

    dc.detect_peaks(
        PeakDetectionRequest(PeakDetectionAlgorithm.LocalMaxima, PeaksLocalMaxima(search_radius=40, min_distance=40))
    )
    _wait_until(qapp, lambda: len(finished) == 1)
    assert section.peaks_local.to_list() == sine_peaks().tolist()
    assert seen == [(threading.get_ident(), SectionChange.PEAKS | SectionChange.RATE)]

    dc.lock_active()
    _wait_until(qapp, lambda: len(finished) == 2)
    assert section.is_locked
    assert seen[-1] == (threading.get_ident(), SectionChange.LOCK | SectionChange.RESULT)


def _wait_until(qapp: QtCore.QCoreApplication, condition: Callable[[], bool], timeout_s: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_s
    while not condition():
        if time.monotonic() > deadline:
            raise TimeoutError("background task did not finish in time")
        qapp.processEvents()
        time.sleep(0.01)
