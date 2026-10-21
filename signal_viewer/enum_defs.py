"""
Enumerations shared by the data layer and the GUI.

The user-facing ones derive from `DocumentedStrEnum`, so every member carries a short description that the parameter
dock shows as the tooltip of the matching combo box entry (`EnumComboBox.set_enum_class(doc_data=...)`) and that the
user guide repeats in `doc/reference/dock_parameters.html`. Keep the two in step when a member changes.
"""

import enum
from typing import Self

from PySide6 import QtGui


class DocumentedStrEnum(enum.StrEnum):
    """
    `StrEnum` whose members carry their own docstring.

    Declare a member as `NAME = ("value", "description")`. `inspect.getdoc(member)` then returns the description
    instead of the class docstring, which is what `signal_viewer.help_texts.enum_doc` and the combo boxes rely on.
    A member declared with a bare string gets an empty docstring; `tests/test_help_texts.py` fails on those, so every
    member that reaches the GUI is described.
    """

    def __new__(cls, value: str, docstr: str = "") -> Self:
        member = str.__new__(cls, value)
        member._value_ = value
        member.__doc__ = " ".join(docstr.split())
        return member


class RateComputationMethod(DocumentedStrEnum):
    """How the rate is derived from the detected peaks. A setting (Settings > Processing), not a dock input."""

    Instantaneous = (
        "instantaneous",
        """
        One rate value per sample, interpolated from the time between consecutive peaks (neurokit2 `signal_rate`).
        Follows every beat; noisy when single peaks are missed.
        """,
    )
    RollingWindow = (
        "rolling_window",
        """
        Peaks are counted inside a window of fixed length that moves along the section, and the count is scaled to
        beats per minute. Window length, step and the handling of the last, shorter windows are set on the
        'Rate Calculation' tab. Smoother than the instantaneous rate; the default.
        """,
    )


class TextFileSeparator(DocumentedStrEnum):
    """Field separator used when reading `.txt` files (Settings > Data). `.csv` and `.tsv` ignore it."""

    Tab = ("\t", "Tab character. The default.")
    Space = (" ", "Single space.")
    Comma = (",", "Comma, as in a .csv file.")
    Semicolon = (";", "Semicolon, as in a .csv file written by a German-locale Excel.")
    Pipe = ("|", "Vertical bar.")


class InputFileFormat(DocumentedStrEnum):
    """
    File extensions the Open File dialog accepts. `DataController` picks the reader by this extension.

    Text and Excel files need a column per channel; the first row holds the column names. The sampling rate is read
    from a time column when one is found (`file_io.detect_sampling_rate`), otherwise the user enters it.
    """

    CSV = (".csv", "Comma-separated text. The separator is always a comma.")
    TXT = (".txt", "Delimited text. The separator is the 'Text file separator' setting (tab by default).")
    TSV = (".tsv", "Tab-separated text.")
    XLS = (".xls", "Excel 97-2003 workbook. The first sheet is read.")
    XLSX = (".xlsx", "Excel workbook. The first sheet is read.")
    FEATHER = (".feather", "Apache Arrow IPC file (Feather v2).")
    ARROW = (".arrow", "Apache Arrow IPC file.")
    IPC = (".ipc", "Apache Arrow IPC file.")
    EDF = (
        ".edf",
        """
        European Data Format recording, read with mne. Every EDF channel is offered as a column; the sampling rate
        comes from the file header.
        """,
    )


class FilterMethod(DocumentedStrEnum):
    """
    Filters of `neurokit2.signal_filter`, selectable as a custom preprocessing step.

    Which inputs a method uses is decided in `ParameterInputs._on_filter_method_changed`; the descriptions below
    name the same inputs so the dock and the user guide agree.
    """

    Butterworth = (
        "butterworth",
        """
        Butterworth IIR filter applied forward and backward (zero phase, second-order sections). Uses lower cutoff,
        upper cutoff and order. The usual choice for a custom band-pass.
        """,
    )
    ButterworthLegacy = (
        "butterworth_ba",
        """
        Butterworth filter in transfer-function (b, a) form, forward and backward. Numerically less stable than the
        default form at high orders; kept to reproduce older results. Uses lower cutoff, upper cutoff and order.
        """,
    )
    ButterworthZI = (
        "butterworth_zi",
        """
        Butterworth filter applied in one direction with matched initial conditions (`lfilter_zi`). Introduces a
        phase delay but no edge artefacts; the ECG pipelines of Pan-Tompkins, Hamilton and Elgendi use it. Uses
        lower cutoff, upper cutoff and order.
        """,
    )
    SavGol = (
        "savgol",
        """
        Savitzky-Golay smoothing: a polynomial of the given order is fitted inside a moving window. Uses order
        (polynomial degree) and window size (samples).
        """,
    )
    FIR = (
        "fir",
        """
        Finite impulse response band-pass filter, forward and backward (zero phase). Uses lower cutoff, upper cutoff
        and window size (number of taps). The minimum window size stands for neurokit2's default, about a third of
        a second of samples.
        """,
    )
    Bessel = (
        "bessel",
        """
        Bessel IIR filter, forward and backward. Its group delay is nearly constant, so peak shapes are distorted
        less than by a Butterworth filter of the same order. Uses lower cutoff, upper cutoff and order.
        """,
    )
    Powerline = (
        "powerline",
        """
        Removes mains interference by averaging over one period of the powerline frequency (50 Hz in Europe, 60 Hz in
        North America). Uses the powerline input only.
        """,
    )


class PreprocessPipeline(DocumentedStrEnum):
    """
    Ready-made cleaning pipelines, implemented in `sv_data.signal_processing.apply_cleaning_pipeline`.

    Selecting a pipeline disables the custom filter and standardization inputs. The descriptions state the filters a
    pipeline applies, so a user can reproduce it with the custom inputs.
    """

    PPG_Elgendi = (
        "ppg_elgendi",
        """
        PPG: Butterworth band-pass 0.5 to 8 Hz, order 3 (Elgendi et al. 2013). The default; pair it with the
        'PPG_Elgendi' peak detector.
        """,
    )
    ECG_Emrich_2023 = (
        "vg",
        """
        ECG: Butterworth high-pass 4 Hz, order 2. The preprocessing of the visibility-graph R-peak detector
        (Emrich et al. 2023); pair it with the 'ECG_Emrich_2023' detector.
        """,
    )
    ECG_NeuroKit = (
        "ecg_neurokit2",
        """
        ECG: Butterworth high-pass 0.5 Hz, order 5, followed by a 50 Hz powerline filter. neurokit2's default ECG
        cleaning.
        """,
    )
    ECG_BioSPPy = (
        "biosppy",
        """
        ECG: FIR band-pass 0.67 to 45 Hz with 1.5 times the sampling rate as number of taps, then the mean is
        removed (BioSPPy).
        """,
    )
    ECG_PanTompkins_1985 = (
        "pantompkins1985",
        "ECG: Butterworth band-pass 5 to 15 Hz, order 1, one direction (Pan & Tompkins 1985).",
    )
    ECG_Hamilton_2002 = (
        "hamilton2002",
        "ECG: Butterworth band-pass 8 to 16 Hz, order 1, one direction (Hamilton 2002).",
    )
    ECG_Elgendi_2010 = (
        "elgendi2010",
        "ECG: Butterworth band-pass 8 to 20 Hz, order 2, one direction (Elgendi et al. 2010).",
    )
    ECG_EngzeeMod_2012 = (
        "engzeemod2012",
        """
        ECG: Butterworth band-stop 48 to 52 Hz, order 4, one direction, i.e. only the 50 Hz mains band is removed
        (Engelse & Zeelenberg 1979, modified by Lourenço et al. 2012).
        """,
    )


class StandardizationMethod(DocumentedStrEnum):
    """Rescaling applied to the filtered signal (`sv_data.signal_processing.standardize_signal`)."""

    ZScore = (
        "std",
        """
        Z-score: subtract the mean and divide by the standard deviation. With 'Use rolling window' both are taken
        from a moving window, which removes slow baseline drift.
        """,
    )
    ZScoreRobust = (
        "mad",
        """
        Robust z-score: subtract the median and divide by the median absolute deviation (scaled by 1.4826). Outliers
        and artefacts influence the scaling far less. No rolling window.
        """,
    )


class PeakDetectionAlgorithm(DocumentedStrEnum):
    """
    Peak detection algorithms, dispatched in `sv_data.peak_detection.find_peaks`.

    The two local-extrema methods work on any signal; 'PPG_Elgendi' is for photoplethysmograms; the rest are ECG
    R-peak detectors from neurokit2 (and XQRS from the WFDB package). Methods without a parameter page in the dock
    run with their published defaults.
    """

    LocalMaxima = (
        "local_maxima",
        """
        Local maxima: a sample is a peak when it is the highest value within the search radius on either side.
        Peaks closer than the radius are merged. Signal-agnostic; works on any periodic signal whose peaks point up.
        """,
    )
    LocalMinima = (
        "local_minima",
        """
        Local minima: a sample is a peak when it is the lowest value within the search radius on either side. The
        counterpart of 'LocalMaxima' for signals whose peaks point down.
        """,
    )
    PPG_Elgendi = (
        "ppg_elgendi",
        """
        Systolic peak detector for photoplethysmograms. Two moving averages over the squared signal mark the beats,
        and the highest point of each is the peak. Elgendi M, Norton I, Brearley M, Abbott D, Schuurmans D (2013),
        PLoS ONE 8(10): e76585, doi:10.1371/journal.pone.0076585.
        """,
    )
    ECG_Emrich_2023 = (
        "emrich2023",
        """
        FastNVG: the ECG is turned into a visibility graph and R-peaks are read from the graph's degree
        (Emrich et al. 2023, after Koka et al. 2022). Fast and sample-accurate; the 'Accelerated' option builds the
        graph from local maxima only.
        """,
    )
    ECG_NeuroKit = (
        "neurokit",
        """
        QRS complexes are found where the smoothed absolute gradient exceeds a moving threshold; the R-peak is the
        maximum inside each complex. neurokit2's default ECG detector; unpublished, validated in
        doi:10.21105/joss.02621.
        """,
    )
    ECG_Gamboa_2008 = (
        "gamboa2008",
        "R-peak detector of Gamboa (2008): a histogram-based amplitude threshold followed by a gradient search.",
    )
    ECG_Promac = (
        "promac",
        """
        ProMAC: several R-peak detectors run in turn, each result is smeared with a Gaussian and the curves are
        summed; locations above a threshold of that sum are peaks. Robust but slow (runs every detector). See
        github.com/neuropsychology/NeuroKit/issues/222.
        """,
    )
    ECG_XQRS = (
        "wfdb_xqrs",
        """
        XQRS detector of the WFDB package (physionet.org), followed by a correction step that moves each location to
        the real extreme within a radius and removes peaks that are too close together or far from their neighbours'
        amplitude.
        """,
    )
    ECG_PanTompkins_1985 = ("pantompkins", "Classic R-peak detector of Pan & Tompkins (1985). No parameters.")
    ECG_Hamilton_2002 = ("hamilton2002", "R-peak detector of Hamilton (2002). No parameters.")
    ECG_Martinez_2004 = ("martinez2004", "Wavelet-based QRS detector of Martinez et al. (2004). No parameters.")
    ECG_Christov_2004 = ("christov2004", "Adaptive-threshold QRS detector of Christov (2004). No parameters.")
    ECG_Nabian_2018 = ("nabian2018", "Pan-Tompkins variant of Nabian et al. (2018). No parameters.")
    ECG_EngzeeMod_2012 = (
        "engzee2012",
        "Detector of Engelse & Zeelenberg (1979) as modified by Lourenço et al. (2012). No parameters.",
    )
    ECG_Manikandan_2012 = (
        "manikandan2012",
        "Shannon energy envelope detector of Manikandan & Soman (2012). No parameters.",
    )
    ECG_Elgendi_2010 = ("elgendi2010", "Two-moving-average QRS detector of Elgendi et al. (2010). No parameters.")
    ECG_Kalidas_2017 = (
        "kalidas2017",
        "Stationary wavelet transform detector of Kalidas & Tamil (2017). No parameters.",
    )
    ECG_Rodrigues_2021 = (
        "rodrigues2021",
        """
        Low-complexity detector of Rodrigues et al. (2021), adapted from Sadhukhan & Mitra (2012) and
        Gutiérrez-Rivas et al. (2015). No parameters.
        """,
    )


class WFDBPeakDirection(DocumentedStrEnum):
    """
    Where the XQRS correction step moves each detected QRS location, within the search radius
    (`sv_data.peak_detection._adjust_peak_positions`).
    """

    Up = ("up", "To the highest sample within the radius. For R-peaks that point up (the usual case).")
    Down = ("down", "To the lowest sample within the radius. For inverted leads whose R-peaks point down.")
    Both = ("both", "To the sample with the largest absolute value within the radius, whatever its sign.")
    Compare = (
        "compare",
        """
        Tries 'Up' and 'Down' and keeps the one whose peaks have the larger mean absolute amplitude. Use when the
        polarity of the recording is unknown.
        """,
    )


class PointSymbols(enum.StrEnum):
    """Marker symbols of `pyqtgraph.ScatterPlotItem`, by their pyqtgraph name."""

    Circle = "o"
    Square = "s"
    Diamond = "d"
    Plus = "+"
    TriangleDown = "t"
    TriangleUp = "t1"
    TriangleRight = "t2"
    TriangleLeft = "t3"
    Pentagon = "p"
    Hexagon = "h"
    Star = "star"
    Cross = "x"
    ArrowUp = "arrow_up"
    ArrowRight = "arrow_right"
    ArrowDown = "arrow_down"
    ArrowLeft = "arrow_left"
    Crosshair = "crosshair"


class MouseButtons(enum.StrEnum):
    """Mouse button / modifier combinations the editing view box tells apart (`graphic_items.EditingViewBox`)."""

    LeftButton = "left"
    MiddleButton = "middle"
    RightButton = "right"
    LeftButtonWithControl = "left+control"
    RightButtonWithControl = "right+control"
    MiddleButtonWithControl = "middle+control"
    Unknown = "unknown"


class SVGColors(enum.StrEnum):
    """
    SVG color names understood by QtGui.QColor
    """

    AliceBlue = "#f0f8ff"
    AntiqueWhite = "#faebd7"
    Aqua = "#00ffff"
    Aquamarine = "#7fffd4"
    Azure = "#f0ffff"
    Beige = "#f5f5dc"
    Bisque = "#ffe4c4"
    Black = "#000000"
    BlanchedAlmond = "#ffebcd"
    Blue = "#0000ff"
    BlueViolet = "#8a2be2"
    Brown = "#a52a2a"
    BurlyWood = "#deb887"
    CadetBlue = "#5f9ea0"
    Chartreuse = "#7fff00"
    Chocolate = "#d2691e"
    Coral = "#ff7f50"
    CornflowerBlue = "#6495ed"
    Cornsilk = "#fff8dc"
    Crimson = "#dc143c"
    Cyan = "#00ffff"
    DarkBlue = "#00008b"
    DarkCyan = "#008b8b"
    DarkGoldenRod = "#b8860b"
    DarkGray = "#a9a9a9"
    DarkGreen = "#006400"
    DarkGrey = "#a9a9a9"
    DarkKhaki = "#bdb76b"
    DarkMagenta = "#8b008b"
    DarkOliveGreen = "#556b2f"
    DarkOrange = "#ff8c00"
    DarkOrchid = "#9932cc"
    DarkRed = "#8b0000"
    DarkSalmon = "#e9967a"
    DarkSeaGreen = "#8fbc8f"
    DarkSlateBlue = "#483d8b"
    DarkSlateGray = "#2f4f4f"
    DarkSlateGrey = "#2f4f4f"
    DarkTurquoise = "#00ced1"
    DarkViolet = "#9400d3"
    DeepPink = "#ff1493"
    DeepSkyBlue = "#00bfff"
    DimGray = "#696969"
    DimGrey = "#696969"
    DodgerBlue = "#1e90ff"
    FireBrick = "#b22222"
    FloralWhite = "#fffaf0"
    ForestGreen = "#228b22"
    Fuchsia = "#ff00ff"
    Gainsboro = "#dcdcdc"
    GhostWhite = "#f8f8ff"
    Gold = "#ffd700"
    GoldenRod = "#daa520"
    Gray = "#808080"
    Green = "#008000"
    GreenYellow = "#adff2f"
    Grey = "#808080"
    HoneyDew = "#f0fff0"
    HotPink = "#ff69b4"
    IndianRed = "#cd5c5c"
    Indigo = "#4b0082"
    Ivory = "#fffff0"
    Khaki = "#f0e68c"
    Lavender = "#e6e6fa"
    LavenderBlush = "#fff0f5"
    LawnGreen = "#7cfc00"
    LemonChiffon = "#fffacd"
    LightBlue = "#add8e6"
    LightCoral = "#f08080"
    LightCyan = "#e0ffff"
    LightGoldenRodYellow = "#fafad2"
    LightGray = "#d3d3d3"
    LightGreen = "#90ee90"
    LightGrey = "#d3d3d3"
    LightPink = "#ffb6c1"
    LightSalmon = "#ffa07a"
    LightSeaGreen = "#20b2aa"
    LightSkyBlue = "#87cefa"
    LightSlateGray = "#778899"
    LightSlateGrey = "#778899"
    LightSteelBlue = "#b0c4de"
    LightYellow = "#ffffe0"
    Lime = "#00ff00"
    LimeGreen = "#32cd32"
    Linen = "#faf0e6"
    Magenta = "#ff00ff"
    Maroon = "#800000"
    MediumAquaMarine = "#66cdaa"
    MediumBlue = "#0000cd"
    MediumOrchid = "#ba55d3"
    MediumPurple = "#9370db"
    MediumSeaGreen = "#3cb371"
    MediumSlateBlue = "#7b68ee"
    MediumSpringGreen = "#00fa9a"
    MediumTurquoise = "#48d1cc"
    MediumVioletRed = "#c71585"
    MidnightBlue = "#191970"
    MintCream = "#f5fffa"
    MistyRose = "#ffe4e1"
    Moccasin = "#ffe4b5"
    NavajoWhite = "#ffdead"
    Navy = "#000080"
    OldLace = "#fdf5e6"
    Olive = "#808000"
    OliveDrab = "#6b8e23"
    Orange = "#ffa500"
    OrangeRed = "#ff4500"
    Orchid = "#da70d6"
    PaleGoldenRod = "#eee8aa"
    PaleGreen = "#98fb98"
    PaleTurquoise = "#afeeee"
    PaleVioletRed = "#db7093"
    PapayaWhip = "#ffefd5"
    PeachPuff = "#ffdab9"
    Peru = "#cd853f"
    Pink = "#ffc0cb"
    Plum = "#dda0dd"
    PowderBlue = "#b0e0e6"
    Purple = "#800080"
    Red = "#ff0000"
    RosyBrown = "#bc8f8f"
    RoyalBlue = "#4169e1"
    SaddleBrown = "#8b4513"
    Salmon = "#fa8072"
    SandyBrown = "#f4a460"
    SeaGreen = "#2e8b57"
    SeaShell = "#fff5ee"
    Sienna = "#a0522d"
    Silver = "#c0c0c0"
    SkyBlue = "#87ceeb"
    SlateBlue = "#6a5acd"
    SlateGray = "#708090"
    SlateGrey = "#708090"
    Snow = "#fffafa"
    SpringGreen = "#00ff7f"
    SteelBlue = "#4682b4"
    Tan = "#d2b48c"
    Teal = "#008080"
    Thistle = "#d8bfd8"
    Tomato = "#ff6347"
    Turquoise = "#40e0d0"
    Violet = "#ee82ee"
    Wheat = "#f5deb3"
    White = "#ffffff"
    WhiteSmoke = "#f5f5f5"
    Yellow = "#ffff00"
    YellowGreen = "#9acd32"

    def qcolor(self) -> QtGui.QColor:
        """The color as a `QColor`."""
        return QtGui.QColor(self.value)


class LogLevel(enum.IntEnum):
    """Loguru severity levels as integers, so a record's level can be compared against a threshold."""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class IncompleteWindowMethod(DocumentedStrEnum):
    """
    What `sv_data.section.compute_rate_rolling` does with windows at the end of a section that hold fewer samples
    than the window length.
    """

    Drop = ("drop", "Leave the short windows out. The rate ends one window length before the section does.")
    Approximate = (
        "approximate",
        """
        Scale the peak count of a short window up to the full window length before converting it to beats per
        minute. The rate covers the whole section; the last values rest on fewer beats.
        """,
    )
    RepeatLast = ("repeat_last", "Give every short window the rate of the last complete window.")


class SectionChange(enum.Flag):
    """
    Which parts of a `Section` a `DataController` mutation touched.

    Carried by `DataController.sig_section_changed` so that subscribers (plot, tables, action states) refresh only
    what changed. `ALL` is what an activation sends: every view redraws from the newly active section.
    """

    SIGNAL = enum.auto()  # processed signal column (filter, pipeline, standardization, reset)
    PEAKS = enum.auto()  # `is_peak` column
    RATE = enum.auto()  # `rate_data` frame
    LOCK = enum.auto()  # `is_locked`
    RESULT = enum.auto()  # `peak_data` / `rate_data` result frames (after locking)
    ALL = SIGNAL | PEAKS | RATE | LOCK | RESULT
