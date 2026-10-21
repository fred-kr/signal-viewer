"""
`DataController`: owns the open file, its channels and sections, and is the only object that mutates a `Section`.

See the class docstring for the signal contract that the GUI relies on.
"""

import functools
from pathlib import Path
from typing import Any

import attrs
import mne.io
import numpy as np
import numpy.typing as npt
import polars as pl
from loguru import logger
from PySide6 import QtCore

from signal_viewer.constants import INDEX_COL
from signal_viewer.enum_defs import InputFileFormat, SectionChange, TextFileSeparator
from signal_viewer.sv_config import Config
from signal_viewer.sv_data.data_models import DataFrameModel, FileMetadata, SectionListModel
from signal_viewer.sv_data.file_io import detect_sampling_rate, read_edf
from signal_viewer.sv_data.section import DEFAULT_RATE_PARAMS, Section
from signal_viewer.sv_data.workers import (
    PeakDetectionResult,
    PeakDetectionWorker,
    SectionResultData,
    SectionResultWorker,
    Worker,
    WorkerRunner,
)
from signal_viewer.type_defs import PeakDetectionRequest, ProcessingRequest, RollingRateKwargs, UpdatePeaksAction

# Rows polars inspects to infer the dtype of each text-file column. The default (100) turns a numeric column into
# `String` when one of the first rows holds a stray non-numeric value, which would hide it from the channel list.
_CSV_INFER_SCHEMA_LENGTH = 10_000


@attrs.define(eq=False)
class Channel:
    """
    One signal column of the loaded file together with everything the user did on it.

    Created the first time the channel is activated (see `DataController.set_active_channel`); the frame is read
    from the file at that moment and kept until the file is closed.
    """

    file_column: str
    """Column name as it appears in the file and in the channel dropdown."""
    name: str
    """Cleaned column name, the `signal_name` of every section of this channel."""
    base_section: Section
    sections: SectionListModel
    active_section: Section


class DataController(QtCore.QObject):
    """
    Owns the loaded file, its metadata, and every `Section` of every channel.

    A channel is one numeric column of the file. Each channel keeps its own base section and `SectionListModel`
    (`Channel`); `sections`, `active_section` and the other section accessors refer to the active channel.
    Switching channels keeps the sections of the previous one in memory.

    It is the only object that calls mutating methods on a `Section`. Every mutation of the active section ends in
    exactly one `sig_section_changed(section, flags)` emission, where `flags` is a `SectionChange` naming what
    changed, so views refresh only the parts named.

    Peak detection and the section result run on `thread_pool` (see `sv_data.workers`). The workers only compute; the
    result comes back to this object's thread and is applied here, so sections are never touched from two threads.
    `sig_task_started` / `sig_task_finished` bracket every background run for a busy indicator.
    """

    sig_user_input_required = QtCore.Signal(set)
    sig_new_metadata = QtCore.Signal(object)  # FileMetadata
    sig_new_data = QtCore.Signal()
    sig_channel_changed = QtCore.Signal(object)  # the now-active Channel
    sig_active_section_changed = QtCore.Signal(object)  # the now-active Section
    sig_section_changed = QtCore.Signal(object, object)  # (Section, SectionChange)
    sig_task_started = QtCore.Signal(str)  # description of the background task
    sig_task_finished = QtCore.Signal()
    sig_task_failed = QtCore.Signal(object)  # the raised Exception instance

    def __init__(self, parent: QtCore.QObject | None = None, thread_pool: WorkerRunner | None = None) -> None:
        super().__init__(parent)
        self.has_data = False
        self._thread_pool: WorkerRunner = thread_pool or QtCore.QThreadPool.globalInstance()
        # Keeps running workers (and their signal objects) alive until `sig_finished` arrives.
        self._running_workers: set[Worker] = set()

        self._metadata: FileMetadata | None = None

        self._channels: dict[str, Channel] = {}
        self._active_channel: Channel | None = None
        # What `sections` returns while no channel is active, so views bound early see an empty list.
        self._no_sections = SectionListModel(parent=self)

        self.active_section_model = DataFrameModel(self)
        self.result_model_peaks = DataFrameModel(self)
        self.result_model_rate = DataFrameModel(self)

        # Rolling-rate parameters shared by every section. The GUI pushes changes here via `set_rate_params`.
        self._rate_params: RollingRateKwargs = DEFAULT_RATE_PARAMS.copy()

        try:
            self._txt_separator = Config.data.text_file_separator
        except Exception:
            self._txt_separator = TextFileSeparator.Tab
        self._reader_funcs = {
            ".csv": functools.partial(
                pl.scan_csv, separator=TextFileSeparator.Comma, infer_schema_length=_CSV_INFER_SCHEMA_LENGTH
            ),
            ".txt": functools.partial(
                pl.scan_csv, separator=self._txt_separator, infer_schema_length=_CSV_INFER_SCHEMA_LENGTH
            ),
            ".tsv": functools.partial(
                pl.scan_csv, separator=TextFileSeparator.Tab, infer_schema_length=_CSV_INFER_SCHEMA_LENGTH
            ),
            ".feather": pl.scan_ipc,
            ".arrow": pl.scan_ipc,
            ".ipc": pl.scan_ipc,
        }

    # --- Channels ----------------------------------------------------------------------------------------------------

    @property
    def channels(self) -> list[str]:
        """File column names that can be edited as a channel (the numeric columns), in file order."""
        return self._metadata.numeric_columns if self._metadata is not None else []

    @property
    def active_channel(self) -> str | None:
        """File column name of the active channel, `None` before data is loaded."""
        return self._active_channel.file_column if self._active_channel is not None else None

    @property
    def loaded_channels(self) -> list[str]:
        """Channels whose data has been read from the file, in `channels` order."""
        return [c for c in self.channels if c in self._channels]

    def _require_channel(self) -> Channel:
        if self._active_channel is None:
            raise ValueError("No data available. Select a valid file to load, and try again.")
        return self._active_channel

    @QtCore.Slot(str)
    def set_active_channel(self, file_column: str) -> None:
        """
        Makes `file_column` the channel being edited.

        The channel is read from the file the first time it is activated. Sections of the previously active channel
        stay in memory. Emits `sig_channel_changed` and then `sig_active_section_changed` for the channel's active
        section; unknown names and the already active channel are ignored.
        """
        if not self.has_data or file_column not in self.channels:
            logger.warning(f"Cannot switch to channel '{file_column}': not a numeric column of the loaded file.")
            return
        if self._active_channel is not None and self._active_channel.file_column == file_column:
            return
        self._activate(self._get_or_create_channel(file_column))

    def _get_or_create_channel(self, file_column: str) -> Channel:
        channel = self._channels.get(file_column)
        if channel is not None:
            return channel

        metadata = self.metadata
        info_file_column = metadata.info_column_or_none
        if info_file_column == file_column:
            # A column cannot be signal and info at the same time; the channel simply has no info column.
            info_file_column = None

        df = self._read_frame(file_column, info_file_column)
        name = metadata.name_map.get(file_column, file_column)
        info_name = None if info_file_column is None else metadata.name_map.get(info_file_column, info_file_column)

        # The base section owns the only copy of this channel's data; `base_df` and every other section are views.
        base = Section(
            df,
            signal_name=name,
            sampling_rate=metadata.sampling_rate,
            info_column=info_name,
            rate_params=self._rate_params,
        )
        base.set_locked(True)
        model = SectionListModel(parent=self)
        model.add_section(base)

        channel = Channel(file_column=file_column, name=name, base_section=base, sections=model, active_section=base)
        self._channels[file_column] = channel
        logger.info(f"Loaded channel '{file_column}' from {metadata.file_name}")
        return channel

    def _activate(self, channel: Channel) -> None:
        self._active_channel = channel
        if self.metadata.signal_column != channel.file_column:
            self.metadata.signal_column = channel.file_column
            Config.internal.last_signal_column = channel.file_column
            self.sig_new_metadata.emit(self.metadata)
        self.active_section_model.set_df(channel.active_section.data)
        self.sig_channel_changed.emit(channel)
        self.sig_active_section_changed.emit(channel.active_section)

    def _reset_channels(self) -> None:
        """Drops every channel, section and result so `load_data` can be called again on the same file."""
        for channel in self._channels.values():
            channel.sections.clear()
        self._channels.clear()
        self._active_channel = None
        self.active_section_model.set_df(pl.DataFrame())
        self.result_model_peaks.set_df(pl.DataFrame())
        self.result_model_rate.set_df(pl.DataFrame())
        self.has_data = False

    def _all_sections(self) -> list[Section]:
        return [s for channel in self._channels.values() for s in channel.sections.all_sections]

    def _model_of(self, section: Section) -> SectionListModel | None:
        """The list model holding `section`, whichever channel it belongs to."""
        for channel in self._channels.values():
            if channel.sections.index_of(section).isValid():
                return channel.sections
        return None

    def channel_sections(self) -> dict[str, list[Section]]:
        """The user-created sections per channel, for every loaded channel that has at least one."""
        result: dict[str, list[Section]] = {}
        for file_column in self.loaded_channels:
            editable = self._channels[file_column].sections.editable_sections
            if editable:
                result[file_column] = editable
        return result

    # --- Active channel accessors ------------------------------------------------------------------------------------

    @property
    def base_df(self) -> pl.DataFrame:
        """
        The loaded columns (`index`, signal, info) of the whole file for the active channel.

        A column selection on the base section's frame, so no second copy of the data exists.
        """
        base = self.get_base_section()
        columns = [INDEX_COL, base.signal_name] + ([base.info_name] if base.info_name is not None else [])
        return base.data.select(columns)

    @property
    def sections(self) -> SectionListModel:
        """The active channel's sections; an empty model while no data is loaded."""
        return self._active_channel.sections if self._active_channel is not None else self._no_sections

    @property
    def metadata(self) -> FileMetadata:
        """
        Metadata of the open file.

        Raises
        ------
        ValueError
            When no file is open.
        """
        if self._metadata is None:
            raise ValueError("No data available.")
        return self._metadata

    @property
    def rate_params(self) -> RollingRateKwargs:
        """The rolling-rate parameters every section is created with."""
        return self._rate_params

    @QtCore.Slot(dict)
    def set_rate_params(self, params: RollingRateKwargs) -> None:
        """
        Applies new rolling-rate parameters to every existing section of every channel and to sections created later.

        The active section's rate is recomputed right away when it has peaks and is not locked; other sections
        recompute lazily on their next `update_rate_data` call.
        """
        self._rate_params = params.copy()
        for section in self._all_sections():
            section.set_rate_params(self._rate_params)

        if not self.has_data:
            return
        section = self.active_section
        if section.is_locked or section.peaks_local.is_empty():
            return
        section.update_rate_data()
        self.sig_section_changed.emit(section, SectionChange.RATE)

    def get_base_section(self) -> Section:
        """The base section of the active channel (the whole file)."""
        return self._require_channel().base_section

    @property
    def active_section(self) -> Section:
        """The section being edited. Raises `ValueError` when no file is loaded."""
        return self._require_channel().active_section

    @QtCore.Slot(QtCore.QModelIndex)
    def set_active_section(self, model_index: QtCore.QModelIndex) -> None:
        """Makes the section at `model_index` of the active channel's list model active and emits `sig_active_section_changed`."""
        section = self.sections.data(model_index, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(section, Section):
            self._require_channel().active_section = section
            self.active_section_model.set_df(section.data)
            self.sig_active_section_changed.emit(section)

    @property
    def base_section_index(self) -> QtCore.QModelIndex:
        """Model index of the base section (always row 0)."""
        return self.sections.index(0)

    # --- File handling -----------------------------------------------------------------------------------------------

    def update_metadata(
        self,
        sampling_rate: int | None = None,
        signal_col: str | None = None,
        info_col: str | None = None,
    ) -> None:
        """Changes one or more of sampling rate, signal column and info column of the open file and re-emits `sig_new_metadata`."""
        if self._metadata is None:
            return

        if sampling_rate is not None:
            self.metadata.sampling_rate = sampling_rate
        if signal_col is not None:
            self.metadata.signal_column = signal_col
        if info_col is not None:
            self.metadata.info_column = info_col

        self.sig_new_metadata.emit(self.metadata)

    @QtCore.Slot(str)
    def open_file(self, file_path: Path | str) -> None:
        """
        Reads the metadata of `file_path` (column names, dtypes, sampling rate when detectable) without loading data.

        Emits `sig_new_metadata` so the widgets fill, then `sig_user_input_required` when a required field (sampling
        rate, signal column) is still missing. Unsupported formats and missing files are logged as errors.
        """
        file_path = Path(file_path)
        if not file_path.is_file():
            logger.error(
                f"Path: {file_path} \n\nNo file exists at the specified path. Please check the path and try again."
            )

        path_suffix = file_path.suffix.lower()
        if path_suffix not in InputFileFormat:
            logger.error(f"Unsupported file format: {path_suffix}. Allowed formats: {', '.join(InputFileFormat)}")

        other_info: dict[str, Any] = {}
        schema: dict[str, pl.DataType]

        if path_suffix == ".edf":
            edf_info = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
            sampling_rate = int(edf_info.info["sfreq"])
            column_names: list[str] = edf_info.ch_names
            schema = {c: pl.Float64() for c in column_names}
            other_info = dict(edf_info.info)
        elif path_suffix in {".feather", ".arrow", ".ipc", ".csv", ".txt", ".tsv"}:
            lf = self._reader_funcs[path_suffix](file_path)
            schema = dict(lf.collect_schema())
            column_names = list(schema)
            try:
                sampling_rate = detect_sampling_rate(lf)
            except Exception:
                sampling_rate = 0
        elif path_suffix in {".xls", ".xlsx"}:
            lf = pl.read_excel(file_path).lazy()
            schema = dict(lf.collect_schema())
            column_names = list(schema)
            try:
                sampling_rate = detect_sampling_rate(lf)
            except Exception:
                sampling_rate = 0
        elif path_suffix == ".hdf5":
            raise NotImplementedError("Reading HDF5 files is not yet supported.")
        else:
            raise ValueError(f"Unsupported file format: {path_suffix}. Please select a valid file format.")

        # `FileMetadata.__init__` pre-selects the columns and sampling rate remembered in `Config.internal`.
        metadata = FileMetadata(file_path, column_names, sampling_rate, schema=schema)
        metadata.other_info = other_info
        self._metadata = metadata
        if not metadata.numeric_columns:
            logger.error(f"'{metadata.file_name}' has no numeric column, so there is no signal to load.")

        # Widgets are filled first, so the dialog opened by the second signal already shows the current values.
        self.sig_new_metadata.emit(self.metadata)
        if self.metadata.required_fields:
            self.sig_user_input_required.emit(set(self.metadata.required_fields))

    def _read_frame(self, signal_col: str, info_col: str | None) -> pl.DataFrame:
        """
        Reads `signal_col` (and `info_col`) from the file described by `metadata`, with a row index column.

        Column names are the file's names on input and the cleaned names (`metadata.name_map`) on output.
        """
        suffix = self.metadata.file_format
        file_path = self.metadata.file_path
        separator = Config.data.text_file_separator

        columns = [signal_col] + ([info_col] if info_col is not None else [])
        if INDEX_COL in columns:
            raise ValueError(f"Column name '{INDEX_COL}' is reserved for internal use and cannot be loaded.")

        if suffix == ".csv":
            df = pl.read_csv(file_path, columns=columns, row_index_name=INDEX_COL)
        elif suffix == ".txt":
            df = pl.read_csv(file_path, columns=columns, separator=separator, row_index_name=INDEX_COL)
        elif suffix == ".tsv":
            df = pl.read_csv(file_path, columns=columns, separator=TextFileSeparator.Tab, row_index_name=INDEX_COL)
        elif suffix == ".feather":
            df = pl.read_ipc(file_path, columns=columns, row_index_name=INDEX_COL)
        elif suffix == ".edf":
            df = read_edf(Path(file_path), signal_col, info_col)
        elif suffix == ".hdf5":
            raise NotImplementedError("Reading HDF5 files is not yet supported.")
        elif suffix in {".xls", ".xlsx"}:
            df = pl.read_excel(file_path, columns=columns)
        else:
            raise NotImplementedError(f"Unsupported file format: {suffix}.")

        return df.rename(self.metadata.name_map, strict=False)

    def load_data(self) -> None:
        """
        Reads the channel selected in `metadata` from the file and makes it the active channel.

        Other channels are read when they are first activated (`set_active_channel`). Safe to call repeatedly: an
        earlier load of the same file is discarded first. The metadata itself is not modified, so the user's column
        and sampling-rate choices survive a reload.
        """
        if self._metadata is None:
            return
        if self.metadata.required_fields:
            logger.error(f"Cannot load data. {self.metadata.missing_fields_text()}")
            return

        # The only place the "last used" values are persisted. They hold the raw file column names so they can be
        # matched against the next file's columns.
        Config.internal.last_signal_column = self.metadata.signal_column
        Config.internal.last_info_column = self.metadata.info_column
        Config.internal.last_sampling_rate = self.metadata.sampling_rate

        self._reset_channels()
        # Reading happens before `has_data` flips, so a failed read leaves the controller empty.
        channel = self._get_or_create_channel(self.metadata.signal_column)
        self.has_data = True
        self.sig_new_data.emit()  # listeners fill the channel list here; the sections follow in `_activate`
        self._activate(channel)

    # --- Sections ----------------------------------------------------------------------------------------------------

    def create_section(self, start: int, stop: int) -> None:
        """Creates a section covering the global indices `[start, stop]` and appends it to the active channel."""
        if self._active_channel is None:
            return
        base = self._active_channel.base_section
        start, stop = int(start), int(stop)
        # `index` is the row number, so the row offset equals the index value; a slice is a zero-copy view.
        data = self.base_df.slice(start, stop - start + 1)
        section = Section(
            data,
            base.signal_name,
            sampling_rate=base.sampling_rate,
            info_column=base.info_name,
            rate_params=self._rate_params,
        )
        self._active_channel.sections.add_section(section)

    def delete_section(self, idx: QtCore.QModelIndex) -> None:
        """Removes the section at `idx` from the active channel and makes the base section active."""
        self.sections.remove_section(idx)
        self.set_active_section(self.base_section_index)

    # --- Active-section mutations ------------------------------------------------------------------------------------
    # Each method below is the single entry point for one kind of change. It mutates the active section and emits
    # `sig_section_changed` once with the flags describing what changed. `detect_peaks` and `lock_active` compute on
    # the thread pool and apply the result in `_on_peaks_detected` / `_on_section_result`.

    @QtCore.Slot(object)
    def apply_processing(self, request: ProcessingRequest) -> None:
        """Resets the active section's signal and peaks, then applies `request`."""
        section = self.active_section
        section.apply_processing(request)
        self.sig_section_changed.emit(section, SectionChange.SIGNAL | SectionChange.PEAKS | SectionChange.RATE)

    @QtCore.Slot()
    def reset_signal(self) -> None:
        """Restores the raw signal and discards peaks and processing parameters."""
        self.apply_processing(ProcessingRequest())

    @QtCore.Slot()
    def clear_peaks(self) -> None:
        """Removes every peak of the active section and clears its result frames."""
        section = self.active_section
        section.reset_peaks()
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    def detect_peaks(self, request: PeakDetectionRequest) -> None:
        """
        Starts peak detection on the active section's processed signal in the background.

        The existing peaks are replaced when the result arrives (`_on_peaks_detected`).
        """
        section = self.active_section
        if section.is_locked:
            logger.warning("The active section is locked. Unlock it before detecting peaks.")
            return
        self._start_worker(PeakDetectionWorker(section, request), "Detection running...")

    @QtCore.Slot(object)
    def _on_peaks_detected(self, result: PeakDetectionResult) -> None:
        section = result.section
        if section.is_locked:
            logger.warning(f"{section.section_id.pretty_name()} was locked while detection ran; result discarded.")
            return
        section.set_detected_peaks(result.peaks, result.request.method, result.request.params)
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    def detect_peaks_in_range(self, start: int, stop: int, request: PeakDetectionRequest) -> None:
        """Runs peak detection on section indices `[start, stop]` and adds the result to the existing peaks."""
        section = self.active_section
        section.detect_peaks_in_range(start, stop, request.method, request.params)
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    @QtCore.Slot(str, object)
    def update_peaks(self, action: UpdatePeaksAction, indices: npt.NDArray[np.intp]) -> None:
        """Adds or removes single peaks at section indices `indices` (manual edits from the plot)."""
        section = self.active_section
        section.update_peaks(action, indices)
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    def lock_active(self) -> None:
        """
        Computes the final peak and rate result for the active section in the background, then locks it.

        A section with fewer than three peaks cannot be locked; the worker's `RuntimeError` arrives through
        `sig_task_failed` and nothing changes.
        """
        section = self.active_section
        if section.is_locked:
            return
        self._start_worker(SectionResultWorker(section), "Creating section result...")

    @QtCore.Slot(object)
    def _on_section_result(self, result: SectionResultData) -> None:
        section = result.section
        section.apply_lock_result(result.peak_data, result.rate_data)
        self._notify_list_model(section)  # lock icon in the list view
        self.sig_section_changed.emit(section, SectionChange.LOCK | SectionChange.RESULT)

    @QtCore.Slot()
    def unlock_active(self) -> None:
        """Unlocks the active section so it can be edited again; its result frames stay until the next change."""
        section = self.active_section
        section.set_locked(False)
        self._notify_list_model(section)
        self.sig_section_changed.emit(section, SectionChange.LOCK)

    def _notify_list_model(self, section: Section) -> None:
        """Tells the list model owning `section` that its display data changed; the channel may not be active."""
        model = self._model_of(section)
        if model is not None:
            model.notify_section_changed(section)

    # --- Settings ----------------------------------------------------------------------------------------------------

    def recompute_rate_all(self) -> None:
        """
        Recomputes the rate of every unlocked section (of every channel) that has peaks, after the rate computation
        method changed.

        Locked sections keep the result they were locked with; unlock and lock again to recompute those.
        """
        if not self.has_data:
            return
        for channel in self._channels.values():
            for section in channel.sections.editable_sections:
                if section.is_locked or section.peaks_local.is_empty():
                    continue
                section.update_rate_data(force=True)
                if section is self.active_section:
                    self.sig_section_changed.emit(section, SectionChange.RATE)

    def refresh_table_models(self) -> None:
        """Re-applies the display settings (float precision) by resetting each table model with its current frame."""
        for model in (self.active_section_model, self.result_model_peaks, self.result_model_rate):
            model.set_df(model.df)

    # --- Background workers ------------------------------------------------------------------------------------------

    def _start_worker(self, worker: Worker, description: str) -> None:
        """Wires `worker` to the result slots below and hands it to the thread pool."""
        if isinstance(worker, PeakDetectionWorker):
            worker.signals.sig_result.connect(self._on_peaks_detected)
        elif isinstance(worker, SectionResultWorker):
            worker.signals.sig_result.connect(self._on_section_result)
        worker.signals.sig_error.connect(self._on_worker_error)
        worker.signals.sig_finished.connect(self._on_worker_finished)

        self._running_workers.add(worker)
        self.sig_task_started.emit(description)
        self._thread_pool.start(worker)

    @QtCore.Slot(object)
    def _on_worker_error(self, exc: Exception) -> None:
        self.sig_task_failed.emit(exc)

    @QtCore.Slot(object)
    def _on_worker_finished(self, worker: Worker) -> None:
        self._running_workers.discard(worker)
        self.sig_task_finished.emit()
