# Since neurokit2 isn't typed all that well, we disable the following checks to appease the type checker

# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from typing import NamedTuple, Unpack

import neurokit2 as nk
import numpy as np
import numpy.typing as npt
import polars as pl
from scipy import signal

import signal_viewer.type_defs as _t
from signal_viewer.enum_defs import FilterMethod, PreprocessPipeline


class CleaningResult(NamedTuple):
    cleaned: npt.NDArray[np.float64]
    parameters: _t.SignalFilterKwargs
    additional_parameters: _t.SignalFilterKwargs | None = None


def rolling_standardize(sig: pl.Series, window_size: int) -> pl.Series:
    roll_mean = sig.rolling_mean(window_size, min_samples=0)
    roll_std = sig.rolling_std(window_size, min_samples=0)
    return (sig - roll_mean) / roll_std


def calculate_mad(sig: pl.Series, constant: float = 1.4826) -> np.float64:
    sig_median = sig.median()
    mad = np.median(np.abs(sig - sig_median))
    return np.float64(constant * mad)


def standardize_signal(sig: pl.Series, robust: bool = False, window_size: int | None = None) -> pl.Series:
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
    clean = nk.signal_filter(
        signal=sig,
        sampling_rate=sampling_rate,
        lowcut=0.5,
        method=FilterMethod.Butterworth,
        order=5,
    )
    return nk.signal_filter(clean, sampling_rate=sampling_rate, method=FilterMethod.Powerline, powerline=powerline)


def ppg_clean_elgendi(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
    return nk.signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=0.5,
        highcut=8,
        method=FilterMethod.Butterworth,
        order=3,
    ), {"lowcut": 0.5, "highcut": 8, "method": FilterMethod.Butterworth, "order": 3}


def ecg_clean_biosppy(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
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
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
    return nk.signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=5,
        highcut=15,
        method=FilterMethod.ButterworthZI,
        order=1,
    ), {"lowcut": 5, "highcut": 15, "method": FilterMethod.ButterworthZI, "order": 1}


def ecg_clean_hamilton(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
    return nk.signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=8,
        highcut=16,
        method=FilterMethod.ButterworthZI,
        order=1,
    ), {"lowcut": 8, "highcut": 16, "method": FilterMethod.ButterworthZI, "order": 1}


def ecg_clean_elgendi(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
    return nk.signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=8,
        highcut=20,
        method=FilterMethod.ButterworthZI,
        order=2,
    ), {"lowcut": 8, "highcut": 20, "method": FilterMethod.ButterworthZI, "order": 2}


def ecg_clean_engzee(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
    return nk.signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=52,
        highcut=48,
        method=FilterMethod.ButterworthZI,
        order=4,
    ), {"lowcut": 52, "highcut": 48, "method": FilterMethod.ButterworthZI, "order": 4}


def ecg_clean_vgraph(
    sig: npt.NDArray[np.float64], sampling_rate: int
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
    return nk.signal_filter(
        sig,
        sampling_rate=sampling_rate,
        lowcut=4,
        method=FilterMethod.Butterworth,
        order=2,
    ), {"lowcut": 4, "method": FilterMethod.Butterworth, "order": 2}


def filter_signal(
    sig: npt.NDArray[np.float64],
    sampling_rate: int,
    **kwargs: Unpack[_t.SignalFilterKwargs],
) -> tuple[npt.NDArray[np.float64], _t.SignalFilterKwargs]:
    highcut = kwargs.get("highcut")
    lowcut = kwargs.get("lowcut")
    if highcut == 0:
        kwargs["highcut"] = None
    if lowcut == 0:
        kwargs["lowcut"] = None
    out = nk.signal_filter(sig, sampling_rate=sampling_rate, **kwargs)  # type: ignore

    return np.asarray(out, dtype=np.float64), kwargs


def apply_cleaning_pipeline(
    sig: npt.NDArray[np.float64], sampling_rate: int, pipeline: PreprocessPipeline
) -> CleaningResult:
    additional_params: _t.SignalFilterKwargs | None = None
    if pipeline == PreprocessPipeline.PPGElgendi:
        cleaned, params = ppg_clean_elgendi(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECGNeuroKit2:
        cleaned = ecg_clean_neurokit(sig, sampling_rate)
        params: _t.SignalFilterKwargs = {
            "lowcut": 0.5,
            "method": str(FilterMethod.Butterworth),
            "order": 5,
        }
        additional_params = {
            "method": str(FilterMethod.Powerline),
            "powerline": 50,
        }
    elif pipeline == PreprocessPipeline.ECGBioSPPy:
        cleaned, params = ecg_clean_biosppy(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECGPanTompkins1985:
        cleaned, params = ecg_clean_pantompkins(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECGHamilton2002:
        cleaned, params = ecg_clean_hamilton(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECGElgendi2010:
        cleaned, params = ecg_clean_elgendi(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECGEngzeeMod2012:
        cleaned, params = ecg_clean_engzee(sig, sampling_rate)
    elif pipeline == PreprocessPipeline.ECGVisibilityGraph:
        cleaned, params = ecg_clean_vgraph(sig, sampling_rate)

    return CleaningResult(cleaned, params, additional_params)
