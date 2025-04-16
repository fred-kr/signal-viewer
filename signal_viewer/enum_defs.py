import enum

from PySide6 import QtGui


class RateComputationMethod(enum.StrEnum):
    """
    Method with which the rate is calculated after peak detection.
    """

    Instantaneous = "instantaneous"
    RollingWindow = "rolling_window"


class TextFileSeparator(enum.StrEnum):
    """
    Separator to use when reading text files.
    """

    Tab = "\t"
    Space = " "
    Comma = ","
    Semicolon = ";"
    Pipe = "|"


class InputFileFormat(enum.StrEnum):
    """
    Supported file formats.
    """

    CSV = ".csv"
    TXT = ".txt"
    TSV = ".tsv"
    XLS = ".xls"
    XLSX = ".xlsx"
    FEATHER = ".feather"
    EDF = ".edf"


class FilterMethod(enum.StrEnum):
    """
    Available signal filtering methods.
    """

    Butterworth = "butterworth"
    ButterworthLegacy = "butterworth_ba"
    ButterworthZI = "butterworth_zi"
    SavGol = "savgol"
    FIR = "fir"
    Bessel = "bessel"
    Powerline = "powerline"


class PreprocessPipeline(enum.StrEnum):
    """
    Processing pipelines available in the `neurokit2` package.
    """

    PPG_Elgendi = "ppg_elgendi"
    ECG_NeuroKit = "ecg_neurokit2"
    ECG_BioSPPy = "biosppy"
    ECG_PanTompkins_1985 = "pantompkins1985"
    ECG_Hamilton_2002 = "hamilton2002"
    ECG_Elgendi_2010 = "elgendi2010"
    ECG_EngzeeMod_2012 = "engzeemod2012"
    ECG_Emrich_2023 = "vg"


class StandardizationMethod(enum.StrEnum):
    ZScore = "std"
    ZScoreRobust = "mad"


class PeakDetectionAlgorithm(enum.StrEnum):
    """
    Available peak detection algorithms.
    """

    # PPG methods
    PPG_Elgendi = "ppg_elgendi"
    """
    Implementation of Elgendi M, Norton I, Brearley M, Abbott D, Schuurmans D (2013) Systolic Peak Detection in
    Acceleration Photoplethysmograms Measured from Emergency Responders in Tropical Conditions. PLoS ONE 8(10): e76585.
    doi:10.1371/journal.pone.0076585.
    """
    # ECG methods
    ECG_Emrich_2023 = "emrich2023"
    """
    FastNVG Algorithm by Emrich et al. (2023) based on the visibility graph detector of Koka et al. (2022). Provides
    fast and sample-accurate R-peak detection. The algorithm transforms the ecg into a graph representation and extracts
    exact R-peak positions using graph metrics.
    """
    ECG_NeuroKit = "neurokit"
    """
    QRS complexes are detected based on the steepness of the absolute gradient of the ECG signal. Subsequently, R-peaks
    are detected as local maxima in the QRS complexes. The method is unpublished, but see: (i)
    https://github.com/neuropsychology/NeuroKit/issues/476 for discussion of this algorithm; and (ii)
    https://doi.org/10.21105/joss.02621 for the original validation of this algorithm.
    """
    ECG_Gamboa_2008 = "gamboa2008"
    """Algorithm by Gamboa (2008)."""
    ECG_Promac = "promac"
    """
    ProMAC combines the result of several R-peak detectors in a probabilistic way. For a given peak detector, the binary
    signal representing the peak locations is convolved with a Gaussian distribution, resulting in a probabilistic
    representation of each peak location. This procedure is repeated for all selected methods and the resulting signals
    are accumulated. Finally, a threshold is used to accept or reject the peak locations. See this discussion for more
    information on the origins of the method: https://github.com/neuropsychology/NeuroKit/issues/222
    """
    ECG_XQRS = "wfdb_xqrs"
    # below methods dont have any adjustable parameters
    ECG_PanTompkins_1985 = "pantompkins"
    """Algorithm by Pan & Tompkins (1985)."""
    ECG_Hamilton_2002 = "hamilton2002"
    """Algorithm by Hamilton (2002)."""
    ECG_Martinez_2004 = "martinez2004"
    """Algorithm by Martinez et al. (2004)."""
    ECG_Christov_2004 = "christov2004"
    """Algorithm by Christov (2004)."""
    ECG_Nabian_2018 = "nabian2018"
    """Algorithm by Nabian et al. (2018) based on the Pan-Tompkins algorithm."""
    ECG_EngzeeMod_2012 = "engzee2012"
    """Original algorithm by Engelse & Zeelenberg (1979) modified by Lourenço et al. (2012)."""
    ECG_Manikandan_2012 = "manikandan2012"
    """Algorithm by Manikandan & Soman (2012) based on the Shannon energy envelope (SEE)."""
    ECG_Elgendi_2010 = "elgendi2010"
    """Algorithm by Elgendi et al. (2010)."""
    ECG_Kalidas_2017 = "kalidas2017"
    """Algorithm by Kalidas et al. (2017)."""
    ECG_Rodrigues_2021 = "rodrigues2021"
    """Adaptation of the work by Sadhukhan & Mitra (2012) and Gutiérrez-Rivas et al. (2015) by Rodrigues et al. (2021)."""
    # Other methods
    LocalMaxima = "local_maxima"
    LocalMinima = "local_minima"


class WFDBPeakDirection(enum.StrEnum):
    Up = "up"
    Down = "down"
    Both = "both"
    Compare = "compare"


class PointSymbols(enum.StrEnum):
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
        return QtGui.QColor(self.value)


class LogLevel(enum.IntEnum):
    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class IncompleteWindowMethod(enum.StrEnum):
    Drop = "drop"
    Approximate = "approximate"
    RepeatLast = "repeat_last"
