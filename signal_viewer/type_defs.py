import datetime
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, NotRequired, TypedDict, Union

import numpy as np
import numpy.typing as npt

from signal_viewer.enum_defs import (
    FilterMethod,
    IncompleteWindowMethod,
    PointSymbols,
    StandardizationMethod,
    SVGColors,
    TextFileSeparator,
    WFDBPeakDirection,
)

if TYPE_CHECKING:
    import mne
    from loguru import RecordException, RecordFile, RecordLevel, RecordProcess, RecordThread
    from PySide6 import QtCore, QtGui

    from signal_viewer.sv_logic.section import SectionID

type PGColor = Union[str, int, float, tuple[int, int, int], tuple[int, int, int, int], "QtGui.QColor", SVGColors]


class PGPenKwargs(TypedDict, total=False):
    color: PGColor
    width: float
    cosmetic: bool
    dash: Sequence[float] | None
    style: Union["QtCore.Qt.PenStyle", None]
    hsv: tuple[float, float, float, float]


class PGBrushKwargs(TypedDict, total=False):
    color: PGColor


PGPen = Union[PGColor, "QtGui.QPen", PGPenKwargs, None]
PGBrush = Union[PGColor, "QtGui.QBrush", PGBrushKwargs, None]

PGPointSymbols = Union[PointSymbols, "QtGui.QPainterPath", str]

UpdatePeaksAction = Literal["add", "remove"]


class FindPeaksKwargs(TypedDict, total=False):
    min_peak_distance: int
    n_std: float


class MetadataDict(TypedDict):
    file_path: str
    sampling_rate: int
    signal_column: str
    info_column: str | None
    column_names: list[str]


class ReadFileKwargs(TypedDict, total=False):
    columns: list[str]
    index_col: str | int | None
    try_parse_dates: bool
    separator: "TextFileSeparator"
    use_pyarrow: bool
    has_header: bool


class SignalFilterParameters(TypedDict, total=False):
    lowcut: float | None
    highcut: float | None
    method: str
    order: int
    window_size: int | Literal["default"]
    powerline: int | float


class StandardizationParameters(TypedDict, total=False):
    method: StandardizationMethod | None
    robust: bool
    window_size: int | None


class SpotDict(TypedDict):
    pos: "tuple[float, float] | QtCore.QPointF"
    size: float
    pen: PGPen
    brush: PGBrush
    symbol: PGPointSymbols


class SpotItemSetDataKwargs(TypedDict, total=False):
    spots: list[SpotDict]
    x: npt.NDArray[np.float64 | np.intp | np.uintp] | Iterable[float | int]
    y: npt.NDArray[np.float64 | np.intp | np.uintp] | Iterable[float | int]
    pos: npt.NDArray[np.float64 | np.intp] | list[tuple[float, float]]
    pxMode: bool
    symbol: PGPointSymbols
    pen: PGPen
    brush: PGBrush
    size: float
    data: npt.NDArray[np.void]
    hoverable: bool
    tip: str | None
    hoverSymbol: PGPointSymbols
    hoverSize: float
    hoverPen: PGPen
    hoverBrush: PGBrush
    useCache: bool
    antialias: bool
    compositionMode: "QtGui.QPainter.CompositionMode | None"
    name: str | None


class PGConfigOptions(TypedDict):
    useOpenGL: bool
    leftButtonPan: bool
    foreground: PGColor
    background: PGColor
    antialias: bool
    editorCommand: str | None
    exitCleanup: bool
    enableExperimental: bool
    crashWarning: bool
    mouseRateLimit: int
    imageAxisOrder: Literal["row-major", "col-major"]
    useCupy: bool
    useNumba: bool
    segmentedLineMode: Literal["auto", "on", "off"]


class PlotDataItemKwargs(TypedDict, total=False):
    x: npt.NDArray[np.float64 | np.intp | np.uintp]
    y: npt.NDArray[np.float64 | np.intp | np.uintp]
    connect: Literal["all", "pairs", "finite", "auto"] | npt.NDArray[np.int32]
    pen: PGPen | None
    shadowPen: PGPen | None
    fillLevel: float | None
    fillOutline: bool
    fillBrush: PGBrush | None
    stepMode: Literal["center", "left", "right"] | None
    symbol: PGPointSymbols | list[PGPointSymbols] | None
    symbolPen: Union[PGPen, list["QtGui.QPen"], None]
    symbolBrush: Union[PGBrush, list["QtGui.QBrush"], None]
    symbolSize: float | list[float]
    pxMode: bool
    useCache: bool
    antialias: bool
    downsample: int
    downsampleMethod: Literal["subsample", "mean", "peak"]
    autoDownsample: bool
    clipToView: bool
    dynamicRangeLimit: float | None
    dynamicRangeHyst: float
    skipFiniteCheck: bool
    name: str
    clickable: bool


class PlotCurveItemKwargs(TypedDict, total=False):
    x: npt.ArrayLike | None
    y: npt.ArrayLike | None
    pen: PGPen | None
    shadowPen: PGPen | None
    fillLevel: float | None
    fillOutline: bool
    brush: PGBrush | None
    antialias: bool
    stepMode: Literal["", "center", "left", "right"] | None
    connect: Literal["all", "pairs", "finite"] | npt.NDArray[np.bool]
    compositionMode: "QtGui.QPainter.CompositionMode"
    skipFiniteCheck: bool


class PlotDataItemOpts(TypedDict):
    connect: Literal["all", "pairs", "finite", "auto"] | npt.NDArray[np.int32]
    skipFiniteCheck: bool
    fftMode: bool
    logMode: list[bool]
    derivativeMode: bool
    phasemapMode: bool
    alphaHint: float
    alphaMode: bool
    pen: PGPen | None
    shadowPen: PGPen | None
    fillLevel: float | None
    fillOutline: bool
    fillBrush: PGBrush | None
    stepMode: Literal["center", "left", "right"] | None
    symbol: PGPointSymbols | list[PGPointSymbols] | None
    symbolPen: Union[PGPen, list["QtGui.QPen"], None]
    symbolBrush: Union[PGBrush, list["QtGui.QBrush"], None]
    symbolSize: float | list[float]
    pxMode: bool
    antialias: bool
    pointMode: Any | None
    useCache: bool
    downsample: int
    autoDownsample: bool
    downsampleMethod: Literal["subsample", "mean", "peak"]
    autoDownsampleFactor: float
    clipToView: bool
    dynamicRangeLimit: float | None
    dynamicRangeHyst: float
    data: Any | None  # Not used?
    name: NotRequired[str]


class NKSignalFilterParams(TypedDict, total=False):
    lowcut: float | None
    highcut: float | None
    method: FilterMethod
    order: int
    window_size: int | Literal["default"]
    powerline: int | float


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


# NK2PeakMethodParams = Union[PeaksECGNeuroKit, PeaksECGGamboa, PeaksECGPromac, PeaksECGEmrich]


# class PeaksECGNeuroKit2(TypedDict):
#     method: NK2ECGPeakDetectionMethod
#     params: Union[NK2PeakMethodParams, None]


class PeaksECGPanTompkins(TypedDict):
    correct_artifacts: bool


PeakDetectionMethodParameters = Union[
    PeaksPPGElgendi,
    PeaksECGNeuroKit,
    PeaksECGPromac,
    PeaksECGGamboa,
    PeaksECGEmrich,
    PeaksECGPanTompkins,
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
    # measured_date: t.NotRequired[str | datetime.datetime | None]
    # subject_id: t.NotRequired[str | None]
    # oxygen_condition: t.NotRequired[str | None]


class MutableMetadataAttributes(TypedDict, total=False):
    measured_date: str | datetime.datetime | None
    subject_id: str | None
    oxygen_condition: str | None


class ProcessingParametersDict(TypedDict):
    sampling_rate: int
    processing_pipeline: str
    filter_parameters: list[SignalFilterParameters]
    standardization_parameters: StandardizationParameters | None
    peak_detection_method: str | None
    peak_detection_method_parameters: PeakDetectionMethodParameters | None
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


class CompactSectionResultDict(TypedDict):
    peaks_global_index: npt.NDArray[np.int32]
    peaks_section_index: npt.NDArray[np.int32]
    seconds_since_global_start: npt.NDArray[np.float64]
    seconds_since_section_start: npt.NDArray[np.float64]
    peak_intervals: npt.NDArray[np.int32]
    rate_data: npt.NDArray[np.void]
    info_values: NotRequired[npt.NDArray[np.float64]]


class SectionResultDict(TypedDict):
    peak_data: npt.NDArray[np.void]
    rate_data: npt.NDArray[np.void]


class DetailedSectionResultDict(TypedDict):
    metadata: SectionMetadataDict
    section_dataframe: npt.NDArray[np.void]
    manual_peak_edits: ManualPeakEditsDict
    section_result: SectionResultDict
    rate_per_temperature: npt.NDArray[np.void]


class ExportInfoDict(TypedDict):
    out_path: Path
    subject_id: str | None
    measured_date: str | None
    oxygen_condition: str | None


##### Types for EDF files read with MNE-Python #####
class EDFSubjectInfoDict(TypedDict, total=False):
    id: int
    his_id: str
    last_name: str
    first_name: str
    middle_name: str
    birthday: tuple[int]
    sex: Literal[0, 1, 2]  # 0 = unknown, 1 = male, 2 = female
    hand: Literal[1, 2, 3]  # 1 = right, 2 = left, 3 = ambidextrous
    weight: float  # in kg
    height: float  # in m


class EDFChannelDict(TypedDict, total=False):
    cal: float
    logno: int
    scanno: int
    range: float
    unit_mul: int
    ch_name: str
    unit: int
    coord_frame: int
    coil_type: int
    kind: int
    loc: npt.NDArray[np.float64]  # shape (12,)


class EDFInfoDict(TypedDict, total=False):
    highpass: float
    lowpass: float
    meas_date: datetime.datetime
    subject_info: dict[str, str]
    bads: list[str]
    chs: list[EDFChannelDict]
    custom_ref_applied: int
    sfreq: float
    dev_head_t: "mne.transforms.Transform"
    ch_names: list[str]
    nchan: int


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
