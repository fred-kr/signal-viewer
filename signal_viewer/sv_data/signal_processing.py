# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

"""
Filters and standardization applied to a section's signal, and the ready-made cleaning pipelines.

Thin, typed wrappers around `neurokit2.signal_filter` plus the pipelines of `PreprocessPipeline`. Every pipeline
returns the parameters it used, so the section can record them in its processing history and the user guide can
state them (`enum_defs.PreprocessPipeline` lists the same numbers).
"""

from typing import Literal, NamedTuple, Unpack

import numpy as np
import numpy.typing as npt
import polars as pl

# import neurokit2 as nk
from neurokit2.signal import signal_filter as _nk_signal_filter
from scipy import signal

from signal_viewer.enum_defs import FilterMethod, PreprocessPipeline
from signal_viewer.type_defs import SignalFilterKwargs


class CleaningResult(NamedTuple):
    """Output of a pipeline: the cleaned signal and the filter parameters it used (two sets for the NeuroKit ECG pipeline)."""

    cleaned: npt.NDArray[np.float64]
    parameters: SignalFilterKwargs
    additional_parameters: SignalFilterKwargs | None = None


def signal_filter(
    sig: npt.NDArray[np.float64],
    sampling_rate: int = 1000,
    lowcut: float | None = None,
    highcut: float | None = None,
    method: str = "butterworth",
    order: int = 2,
    window_size: int | Literal["default"] = "default",
    powerline: float = 50,
    show: bool = False,
) -> npt.NDArray[np.float64]:
    """Typed wrapper around `neurokit2.signal.signal_filter` that casts the return value."""
    out = _nk_signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=lowcut,
        highcut=highcut,
        method=method,
        order=order,
        window_size=window_size,  # pyright: ignore[reportArgumentType]
        powerline=powerline,  # pyright: ignore[reportArgumentType]
        show=show,
    )
    return np.asarray(out, dtype=np.float64)


def rolling_standardize(sig: pl.Series, window_size: int) -> pl.Series:
    """Z-score with mean and standard deviation from a moving window of `window_size` samples (`min_samples=0`)."""
    roll_mean = sig.rolling_mean(window_size, min_samples=0)
    roll_std = sig.rolling_std(window_size, min_samples=0)
    return (sig - roll_mean) / roll_std


def calculate_mad(sig: pl.Series, constant: float = 1.4826) -> np.float64:
    """Median absolute deviation scaled by `constant`, which makes it a consistent estimator of the standard deviation."""
    sig_median = sig.median()
    mad = np.median(np.abs(sig - sig_median))
    return np.float64(constant * mad)


def standardize_signal(sig: pl.Series, robust: bool = False, window_size: int | None = None) -> pl.Series:
    """
    Z-score (`robust=False`) or median/MAD score (`robust=True`) of `sig`, optionally in a rolling window.

    NaN and infinite results (constant stretches) are back-filled from the next valid value.

    Raises
    ------
    ValueError
        If `robust` and `window_size` are combined; windowed MAD scaling is not supported.
    """
    if robust and window_size:
        raise ValueError("Windowed MAD scaling is not supported for robust scaling")
    if window_size:
        result = rolling_standardize(sig, window_size)
    elif robust:
        result = (sig - sig.median()) / calculate_mad(sig)
    else:
        result = (sig - sig.mean()) / sig.std(ddof=1)

    return result.fill_nan(None).fill_null(strategy="backward")


def ecg_clean_neurokit(
    sig: npt.NDArray[np.float64], sampling_rate: int, powerline: int = 50
) -> npt.NDArray[np.float64]:
    """neurokit2's ECG cleaning: 0.5 Hz Butterworth high-pass (order 5) then a powerline filter."""
    clean = signal_filter(
        sig=sig,
        sampling_rate=sampling_rate,
        lowcut=0.5,
        method=FilterMethod.Butterworth,
        order=5,
    )
    return signal_filter(clean, sampling_rate=sampling_rate, method=FilterMethod.Powerline, powerline=powerline)


def ppg_clean_elgendi(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """Elgendi PPG cleaning: Butterworth band-pass 0.5 to 8 Hz, order 3. Returns the signal and the parameters used."""
    return signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=0.5,
        highcut=8,
        method=FilterMethod.Butterworth,
        order=3,
    ), {"lowcut": 0.5, "highcut": 8, "method": FilterMethod.Butterworth, "order": 3}


def ecg_clean_biosppy(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """BioSPPy ECG cleaning: FIR band-pass 0.67 to 45 Hz with 1.5 x sampling rate taps (made odd), mean removed."""
    order = int(1.5 * sampling_rate)
    if order % 2 == 0:
        order += 1

    frequency = [0.67, 45]

    frequency = 2 * np.array(frequency) / sampling_rate  # Normalize frequency to Nyquist Frequency

    a = np.array([1])
    b = signal.firwin(numtaps=order, cutoff=frequency, pass_zero=False)

    filtered = signal.filtfilt(b, a, sig)

    filtered -= np.mean(filtered)

    return filtered, {"lowcut": 0.67, "highcut": 45, "method": FilterMethod.FIR, "order": order}


def ecg_clean_pantompkins(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """Pan & Tompkins (1985): Butterworth band-pass 5 to 15 Hz, order 1, one direction."""
    return signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=5,
        highcut=15,
        method=FilterMethod.ButterworthZI,
        order=1,
    ), {"lowcut": 5, "highcut": 15, "method": FilterMethod.ButterworthZI, "order": 1}


def ecg_clean_hamilton(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """Hamilton (2002): Butterworth band-pass 8 to 16 Hz, order 1, one direction."""
    return signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=8,
        highcut=16,
        method=FilterMethod.ButterworthZI,
        order=1,
    ), {"lowcut": 8, "highcut": 16, "method": FilterMethod.ButterworthZI, "order": 1}


def ecg_clean_elgendi(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """Elgendi et al. (2010): Butterworth band-pass 8 to 20 Hz, order 2, one direction."""
    return signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=8,
        highcut=20,
        method=FilterMethod.ButterworthZI,
        order=2,
    ), {"lowcut": 8, "highcut": 20, "method": FilterMethod.ButterworthZI, "order": 2}


def ecg_clean_engzee(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """Engelse & Zeelenberg / Lourenço: Butterworth band-stop 48 to 52 Hz, order 4, one direction (lowcut above highcut)."""
    return signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=52,
        highcut=48,
        method=FilterMethod.ButterworthZI,
        order=4,
    ), {"lowcut": 52, "highcut": 48, "method": FilterMethod.ButterworthZI, "order": 4}


def ecg_clean_vgraph(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """Emrich et al. (2023) preprocessing: Butterworth high-pass 4 Hz, order 2."""
    return signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=4,
        method=FilterMethod.Butterworth,
        order=2,
    ), {"lowcut": 4, "method": FilterMethod.Butterworth, "order": 2}


def filter_signal(
    sig: npt.NDArray[np.float64],
    sampling_rate: int,
    **kwargs: Unpack[SignalFilterKwargs],
) -> tuple[npt.NDArray[np.float64], SignalFilterKwargs]:
    """
    Applies a custom filter with the dock's parameters and returns the signal together with the parameters as used.

    A cutoff of 0 means "no cutoff on that side" and is turned into `None` before neurokit2 sees it.
    """
    highcut = kwargs.get("highcut")
    lowcut = kwargs.get("lowcut")
    if highcut == 0:
        kwargs["highcut"] = None
    if lowcut == 0:
        kwargs["lowcut"] = None
    out = signal_filter(sig, sampling_rate=sampling_rate, **kwargs)

    return out, kwargs


def apply_cleaning_pipeline(
    sig: npt.NDArray[np.float64], sampling_rate: int, pipeline: PreprocessPipeline
) -> CleaningResult:
    """Runs the `pipeline` on `sig` and reports the filter parameters it used, for the processing history."""
    additional_params: SignalFilterKwargs | None = None
    if pipeline == PreprocessPipeline.PPG_Elgendi:
        cleaned, params = ppg_clean_elgendi(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECG_NeuroKit:
        cleaned = ecg_clean_neurokit(sig, sampling_rate)
        params: SignalFilterKwargs = {
            "lowcut": 0.5,
            "method": str(FilterMethod.Butterworth),
            "order": 5,
        }
        additional_params = {
            "method": str(FilterMethod.Powerline),
            "powerline": 50,
        }
    elif pipeline == PreprocessPipeline.ECG_BioSPPy:
        cleaned, params = ecg_clean_biosppy(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECG_PanTompkins_1985:
        cleaned, params = ecg_clean_pantompkins(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECG_Hamilton_2002:
        cleaned, params = ecg_clean_hamilton(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECG_Elgendi_2010:
        cleaned, params = ecg_clean_elgendi(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECG_EngzeeMod_2012:
        cleaned, params = ecg_clean_engzee(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECG_Emrich_2023:
        cleaned, params = ecg_clean_vgraph(sig, sampling_rate)

    return CleaningResult(cleaned, params, additional_params)
