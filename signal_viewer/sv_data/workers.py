"""
Background workers for the two slow operations: peak detection and the final section result.

Each worker copies what it needs from the `Section` on the calling (GUI) thread, computes on a `QThreadPool` thread
without touching the section, and emits the result through `sig_result`. `DataController` applies the result on the
GUI thread, so a `Section` is only ever read or written from there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import attrs
import numpy as np
import numpy.typing as npt
import polars as pl
from PySide6 import QtCore

from signal_viewer.sv_config import Config
from signal_viewer.sv_data.peak_detection import find_peaks
from signal_viewer.sv_data.section import compute_peak_data, compute_rate_data

if TYPE_CHECKING:
    from signal_viewer.sv_data.section import Section
    from signal_viewer.type_defs import PeakDetectionRequest


class WorkerRunner(Protocol):
    """What `DataController` needs from a thread pool. `QtCore.QThreadPool` satisfies it; tests pass a synchronous one."""

    def start(self, runnable: QtCore.QRunnable, /) -> None: ...


class WorkerSignals(QtCore.QObject):
    """
    Signals of a worker. Created on the GUI thread, so a slot on a GUI-thread `QObject` receives them queued.

    A plain Python callable connected to these runs on the worker thread (it has no thread affinity), so connect
    bound methods of `QObject`s only.
    """

    sig_result = QtCore.Signal(object)  # PeakDetectionResult | SectionResultData
    sig_error = QtCore.Signal(object)  # the raised Exception instance
    sig_finished = QtCore.Signal(object)  # the Worker that finished


class Worker(QtCore.QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = WorkerSignals()

    def compute(self) -> object:
        raise NotImplementedError

    @QtCore.Slot()
    def run(self) -> None:
        try:
            result = self.compute()
        except Exception as e:
            self.signals.sig_error.emit(e)
        else:
            self.signals.sig_result.emit(result)
        finally:
            self.signals.sig_finished.emit(self)


@attrs.frozen
class PeakDetectionResult:
    section: Section
    request: PeakDetectionRequest
    peaks: npt.NDArray[np.intp]


class PeakDetectionWorker(Worker):
    """Runs `find_peaks` on a copy of the section's processed signal."""

    def __init__(self, section: Section, request: PeakDetectionRequest) -> None:
        super().__init__()
        self.section = section
        self.request = request
        # Own copy: the worker must not share memory with a frame the GUI thread may replace meanwhile.
        self._signal = section.processed_signal.to_numpy(allow_copy=True).copy()
        self._sampling_rate = section.sampling_rate

    def compute(self) -> PeakDetectionResult:
        peaks = find_peaks(self._signal, self._sampling_rate, self.request.method, self.request.params)
        return PeakDetectionResult(self.section, self.request, peaks)


@attrs.frozen
class SectionResultData:
    section: Section
    peak_data: pl.DataFrame
    rate_data: pl.DataFrame


class SectionResultWorker(Worker):
    """
    Computes the final peak and rate frames for a section.

    Polars frames are immutable, so holding a reference to the section's frame is a snapshot; later changes on the GUI
    thread replace `section.data` with a new frame and leave this one untouched.
    """

    def __init__(self, section: Section) -> None:
        super().__init__()
        self.section = section
        self._data = section.data
        self._processed_signal_name = section.processed_signal_name
        self._sampling_rate = section.sampling_rate
        self._info_name = section.info_name
        self._rate_params = section.rate_params.copy()
        self._rate_method = Config.editing.rate_computation_method  # read on the GUI thread

    def compute(self) -> SectionResultData:
        peak_df = compute_peak_data(
            self._data,
            self._processed_signal_name,
            self._sampling_rate,
            self._info_name,
            include_global=True,
            include_info=True,
        )
        rate_df = compute_rate_data(
            self._data,
            self._sampling_rate,
            self._info_name,
            self._rate_params,
            self._rate_method,
            full_info=True,
        )
        return SectionResultData(self.section, peak_df, rate_df)
