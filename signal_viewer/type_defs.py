import datetime
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, TypedDict, Union

import numpy as np
import numpy.typing as npt

from signal_viewer.enum_defs import (
    IncompleteWindowMethod,
    PointSymbols,
    StandardizationMethod,
    SVGColors,
    WFDBPeakDirection,
)

if TYPE_CHECKING:
    from loguru import RecordException, RecordFile, RecordLevel, RecordProcess, RecordThread
    from PySide6 import QtCore, QtGui

    from signal_viewer.sv_data.section import SectionID

type PGColor = Union[str, int, float, tuple[int, int, int], tuple[int, int, int, int], "QtGui.QColor", SVGColors]
type PGPen = Union[PGColor, "QtGui.QPen", PGPenKwargs, None]
type PGBrush = Union[PGColor, "QtGui.QBrush", PGBrushKwargs, None]

type PGPointSymbols = Union[PointSymbols, "QtGui.QPainterPath", str]

type UpdatePeaksAction = Literal["add", "remove"]


class PGPenKwargs(TypedDict, total=False):
    color: PGColor
    width: float
    cosmetic: bool
    dash: Sequence[float] | None
    style: Union["QtCore.Qt.PenStyle", None]
    hsv: tuple[float, float, float, float]


class PGBrushKwargs(TypedDict, total=False):
    color: PGColor


class MetadataDict(TypedDict):
    file_path: str
    sampling_rate: int
    signal_column: str
    info_column: str | None
    column_names: list[str]


class SignalFilterKwargs(TypedDict, total=False):
    lowcut: float | None
    highcut: float | None
    method: str
    order: int
    window_size: int | Literal["default"]
    powerline: int | float


class SignalStandardizeKwargs(TypedDict, total=False):
    method: StandardizationMethod | None
    robust: bool
    window_size: int | None


class PeaksPPGElgendi(TypedDict):
    peakwindow: float
    beatwindow: float
    beatoffset: float
    mindelay: float


class PeaksLocalMaxima(TypedDict):
    search_radius: int
    min_distance: int


class PeaksLocalMinima(TypedDict):
    search_radius: int
    min_distance: int


class PeaksECGXQRS(TypedDict):
    search_radius: int
    peak_dir: WFDBPeakDirection
    min_peak_distance: int


class PeaksECGNeuroKit(TypedDict):
    smoothwindow: float
    avgwindow: float
    gradthreshweight: float
    minlenweight: float
    mindelay: float


class PeaksECGGamboa(TypedDict):
    tol: float


class PeaksECGEmrich(TypedDict):
    window_seconds: float  # seconds
    window_overlap: float  # percentage (0-1)
    accelerated: bool


class PeaksECGPromac(TypedDict):
    threshold: float
    gaussian_sd: int  # milliseconds


type PeakDetectionAlgorithmParameters = Union[
    PeaksPPGElgendi,
    PeaksECGNeuroKit,
    PeaksECGPromac,
    PeaksECGGamboa,
    PeaksECGEmrich,
    PeaksLocalMinima,
    PeaksLocalMaxima,
    PeaksECGXQRS,
]


class SelectedFileMetadataDict(TypedDict):
    file_name: str
    file_format: str
    sampling_rate: int
    name_signal_column: str
    name_info_column: str | None


class ProcessingParametersDict(TypedDict):
    sampling_rate: int
    processing_pipeline: str
    filter_parameters: list[SignalFilterKwargs]
    standardization_parameters: SignalStandardizeKwargs | None
    peak_detection_method: str | None
    peak_detection_method_parameters: PeakDetectionAlgorithmParameters | None
    rate_computation_method: str


class ManualPeakEditsDict(TypedDict):
    added: list[int]
    removed: list[int]


class SectionMetadataDict(TypedDict):
    signal_name: str
    section_id: "SectionID"
    global_bounds: tuple[int, int]
    sampling_rate: int
    processing_parameters: ProcessingParametersDict
    rate_computation_method: str


class SectionSummaryDict(TypedDict):
    name: str
    size: int
    sampling_rate: int
    start_index: int
    end_index: int
    peak_count: int
    processing_parameters: ProcessingParametersDict


class SectionResultDict(TypedDict):
    peak_data: npt.NDArray[np.void]
    rate_data: npt.NDArray[np.void]


class DetailedSectionResultDict(TypedDict):
    metadata: SectionMetadataDict
    section_dataframe: npt.NDArray[np.void]
    manual_peak_edits: ManualPeakEditsDict
    section_result: SectionResultDict
    rate_per_temperature: npt.NDArray[np.void]


class CompleteResultDict(TypedDict):
    metadata: SelectedFileMetadataDict
    global_dataframe: npt.NDArray[np.void]
    section_results: dict["SectionID", DetailedSectionResultDict]


class LogRecordDict(TypedDict):
    elapsed: datetime.timedelta
    exception: "RecordException | None"
    extra: dict[str, Any]
    file: "RecordFile"
    function: str
    level: "RecordLevel"
    line: int | None
    message: str
    module: str
    name: str | None
    process: "RecordProcess"
    thread: "RecordThread"
    time: datetime.datetime


class RollingRateKwargsDict(TypedDict, total=False):
    sec_new_window_every: int
    sec_window_length: int
    incomplete_window_method: IncompleteWindowMethod
