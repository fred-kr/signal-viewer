"""
Typed dictionaries and request objects passed between the GUI, `DataController` and the data layer.

The `Peaks*` dictionaries are the keyword arguments of one peak detection method each; `ParameterInputs` builds
them from the dock and `peak_detection.find_peaks` unpacks them. Units are stated in each class docstring because a
`TypedDict` body may hold annotations only.
"""

import datetime
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, TypedDict

import attrs
import numpy as np
import numpy.typing as npt

from signal_viewer.enum_defs import (
    IncompleteWindowMethod,
    PeakDetectionAlgorithm,
    PointSymbols,
    PreprocessPipeline,
    StandardizationMethod,
    SVGColors,
    WFDBPeakDirection,
)

if TYPE_CHECKING:
    from loguru import RecordException, RecordFile, RecordLevel, RecordProcess, RecordThread
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen

    from signal_viewer.sv_data.section import SectionID

type PGColor = str | int | float | tuple[int, int, int] | tuple[int, int, int, int] | QColor | SVGColors
"""Anything `pyqtgraph.mkColor` accepts."""
type PGPen = PGColor | QPen | PGPenKwargs | None
"""Anything `pyqtgraph.mkPen` accepts."""
type PGBrush = PGColor | QBrush | PGBrushKwargs | None
"""Anything `pyqtgraph.mkBrush` accepts."""

type PGPointSymbols = PointSymbols | QPainterPath | str
"""Scatter symbol: a `PointSymbols` name, a custom path, or a pyqtgraph symbol string."""

type UpdatePeaksAction = Literal["add", "remove"]
"""What a manual peak edit does at the given indices (`Section.update_peaks`)."""


class PGPenKwargs(TypedDict, total=False):
    """Keyword arguments of `pyqtgraph.mkPen`."""

    color: PGColor
    width: float
    cosmetic: bool
    dash: Sequence[float] | None
    style: Qt.PenStyle | None
    hsv: tuple[float, float, float, float]


class PGBrushKwargs(TypedDict, total=False):
    """Keyword arguments of `pyqtgraph.mkBrush`."""

    color: PGColor


class MetadataDict(TypedDict):
    """`FileMetadata.to_dict()`: the file path, sampling rate (Hz) and the chosen signal / info column names."""

    file_path: str
    sampling_rate: int
    signal_column: str
    info_column: str | None
    column_names: list[str]


class SignalFilterKwargs(TypedDict, total=False):
    """
    Keyword arguments of `signal_processing.filter_signal` (a typed `neurokit2.signal_filter`).

    `lowcut` / `highcut` in Hz (`None` or 0 = no cutoff on that side); `order` is the filter order or the
    Savitzky-Golay polynomial degree; `window_size` in samples, `"default"` lets neurokit2 choose; `powerline` in Hz.
    """

    lowcut: float | None
    highcut: float | None
    method: str
    order: int
    window_size: int | Literal["default"]
    powerline: int | float


class SignalStandardizeKwargs(TypedDict, total=False):
    """
    Keyword arguments of `Section.standardize_signal`. `window_size` in samples (`None` = whole section); `robust`
    selects the median/MAD variant, which cannot be combined with a window.
    """

    method: StandardizationMethod | None
    robust: bool
    window_size: int | None


class PeaksPPGElgendi(TypedDict):
    """`PeakDetectionAlgorithm.PPG_Elgendi`: windows and delay in seconds, `beatoffset` a fraction."""

    peakwindow: float
    beatwindow: float
    beatoffset: float
    mindelay: float


class PeaksLocalMaxima(TypedDict):
    """`PeakDetectionAlgorithm.LocalMaxima`: both in samples. The dock sets `min_distance = search_radius`."""

    search_radius: int
    min_distance: int


class PeaksLocalMinima(TypedDict):
    """`PeakDetectionAlgorithm.LocalMinima`: both in samples. The dock sets `min_distance = search_radius`."""

    search_radius: int
    min_distance: int


class PeaksECGXQRS(TypedDict):
    """`PeakDetectionAlgorithm.ECG_XQRS`: radius and distance in samples, `peak_dir` the correction direction."""

    search_radius: int
    peak_dir: WFDBPeakDirection
    min_peak_distance: int


class PeaksECGNeuroKit(TypedDict):
    """`PeakDetectionAlgorithm.ECG_NeuroKit`: windows and delay in seconds, the two weights are factors."""

    smoothwindow: float
    avgwindow: float
    gradthreshweight: float
    minlenweight: float
    mindelay: float


class PeaksECGGamboa(TypedDict):
    """`PeakDetectionAlgorithm.ECG_Gamboa_2008`: `tol` is a fraction of the amplitude range."""

    tol: float


class PeaksECGEmrich(TypedDict):
    """`PeakDetectionAlgorithm.ECG_Emrich_2023`: `window_seconds` in seconds, `window_overlap` a fraction 0-1."""

    window_seconds: float
    window_overlap: float
    accelerated: bool


class PeaksECGPromac(TypedDict):
    """`PeakDetectionAlgorithm.ECG_Promac`: `threshold` a fraction 0-1, `gaussian_sd` in milliseconds."""

    threshold: float
    gaussian_sd: int


type PeakDetectionAlgorithmParameters = (
    PeaksPPGElgendi
    | PeaksECGNeuroKit
    | PeaksECGPromac
    | PeaksECGGamboa
    | PeaksECGEmrich
    | PeaksLocalMinima
    | PeaksLocalMaxima
    | PeaksECGXQRS
)
"""Parameters of whichever method a `PeakDetectionRequest` names; `None` for methods without parameters."""


class ProcessingParametersDict(TypedDict):
    """`ProcessingParameters.to_dict()`: everything that was done to the signal of a section, for the summary."""

    sampling_rate: int
    processing_pipeline: str
    filter_parameters: list[SignalFilterKwargs]
    standardization_parameters: SignalStandardizeKwargs | None
    peak_detection_method: str | None
    peak_detection_method_parameters: PeakDetectionAlgorithmParameters | None
    rate_computation_method: str


class ManualPeakEditsDict(TypedDict):
    """Section indices of peaks the user added and removed by hand (`ManualPeakEdits.to_dict()`)."""

    added: list[int]
    removed: list[int]


class SectionMetadataDict(TypedDict):
    """`SectionMetadata.to_dict()`. `global_bounds` are the first and last file row of the section."""

    signal_name: str
    section_id: SectionID
    global_bounds: tuple[int, int]
    sampling_rate: int
    processing_parameters: ProcessingParametersDict
    rate_computation_method: str


class SectionSummaryDict(TypedDict):
    """What the "Show Section Summary" dialog displays (`Section.get_summary()`)."""

    name: str
    size: int
    sampling_rate: int
    start_index: int
    end_index: int
    peak_count: int
    processing_parameters: ProcessingParametersDict


class SectionResultDict(TypedDict):
    """`SectionResult.to_dict()`: the peak and rate frames as structured numpy arrays."""

    peak_data: npt.NDArray[np.void]
    rate_data: npt.NDArray[np.void]


class DetailedSectionResultDict(TypedDict):
    """`DetailedSectionResult.to_dict()`: metadata, the full section frame, manual edits and the result frames."""

    metadata: SectionMetadataDict
    section_dataframe: npt.NDArray[np.void]
    manual_peak_edits: ManualPeakEditsDict
    section_result: SectionResultDict
    rate_per_temperature: npt.NDArray[np.void]


class LogRecordDict(TypedDict):
    """The `record` dictionary loguru attaches to every message (see `LoggingWindow.append_html`)."""

    elapsed: datetime.timedelta
    exception: RecordException | None
    extra: dict[str, Any]
    file: RecordFile
    function: str
    level: RecordLevel
    line: int | None
    message: str
    module: str
    name: str | None
    process: RecordProcess
    thread: RecordThread
    time: datetime.datetime


class RollingRateKwargs(TypedDict, total=False):
    """
    The rate tab inputs, as keyword arguments of `section.compute_rate_rolling`. Both durations in seconds:
    `sec_new_window_every` is the step between windows, `sec_window_length` the length of each window.
    """

    sec_new_window_every: int
    sec_window_length: int
    incomplete_window_method: IncompleteWindowMethod


@attrs.frozen
class ProcessingRequest:
    """
    What the "Apply to Signal" button asks for, as one object.

    A `pipeline` takes precedence over `filter` and `standardize`, mirroring the parameter dock, which disables the
    custom inputs while a pipeline is selected. All three `None` means "reset the signal".
    """

    pipeline: PreprocessPipeline | None = None
    filter: SignalFilterKwargs | None = None
    standardize: SignalStandardizeKwargs | None = None


@attrs.frozen
class PeakDetectionRequest:
    """What the "Run detection" button asks for."""

    method: PeakDetectionAlgorithm
    params: PeakDetectionAlgorithmParameters | None = None
