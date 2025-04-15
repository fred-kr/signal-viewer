"""
Various functions for detecting peaks in (bio)signal data.

Most of the functions are adapted from the NeuroKit2 package, with improved type annotations and where necessary
modified to fit the needs of this application.
"""
# Since neurokit2 isn't typed all that well, we disable the following checks to appease the type checker:

# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from collections.abc import Callable
from typing import Literal, cast

import neurokit2 as nk
import numpy as np
import numpy.typing as npt
import wfdb.processing as wp
from scipy import ndimage

import signal_viewer.type_defs as _t
from signal_viewer.enum_defs import PeakDetectionAlgorithm, WFDBPeakDirection


def _find_peaks_local_max(sig: npt.NDArray[np.float64], search_radius: int) -> npt.NDArray[np.intp]:
    if len(sig) == 0 or np.min(sig) == np.max(sig):
        return np.array([], dtype=np.intp)

    max_vals = ndimage.maximum_filter1d(sig, size=2 * search_radius + 1, mode="constant")
    return np.flatnonzero(sig == max_vals)


def _find_peaks_local_min(sig: npt.NDArray[np.float64], search_radius: int) -> npt.NDArray[np.intp]:
    if len(sig) == 0 or np.min(sig) == np.max(sig):
        return np.array([], dtype=np.intp)

    min_vals = ndimage.minimum_filter1d(sig, size=2 * search_radius + 1, mode="constant")
    return np.flatnonzero(sig == min_vals)


def find_extrema(
    sig: npt.NDArray[np.float64], search_radius: int, direction: Literal["up", "down"], min_peak_distance: int
) -> npt.NDArray[np.intp]:
    if direction == "up":
        peaks = _find_peaks_local_max(sig, search_radius)
    else:
        peaks = _find_peaks_local_min(sig, search_radius)

    peak_diffs = np.diff(peaks)
    close_peaks = np.where(peak_diffs < min_peak_distance)[0]
    while len(close_peaks) > 0:
        for i in close_peaks:
            peaks[i] = (peaks[i] + peaks[i + 1]) // 2
        peaks = np.delete(peaks, close_peaks + 1)
        peak_diffs = np.diff(peaks)
        close_peaks = np.where(peak_diffs < min_peak_distance)[0]

    return peaks


# XQRS related functions
def _shift_peaks(
    sig: npt.NDArray[np.float64], peaks: npt.NDArray[np.intp], radius: int, dir_is_up: bool
) -> npt.NDArray[np.intp]:
    start_indices = np.maximum(peaks - radius, 0)
    end_indices = np.minimum(peaks + radius, sig.size)

    shifted_peaks = np.zeros_like(peaks)

    for i, (start, end) in enumerate(zip(start_indices, end_indices, strict=False)):
        local_sig = sig[start:end]
        if dir_is_up:
            shifted_peaks[i] = np.subtract(np.argmax(local_sig), radius)
        else:
            shifted_peaks[i] = np.subtract(np.argmin(local_sig), radius)

    peaks += shifted_peaks
    return peaks


def _adjust_peak_positions(
    sig: npt.NDArray[np.float64],
    peaks: npt.NDArray[np.intp],
    radius: int,
    direction: WFDBPeakDirection,
) -> npt.NDArray[np.intp]:
    if direction == WFDBPeakDirection.Up:
        return _shift_peaks(sig, peaks, radius, dir_is_up=True)
    elif direction == WFDBPeakDirection.Down:
        return _shift_peaks(sig, peaks, radius, dir_is_up=False)
    elif direction == WFDBPeakDirection.Both:
        return _shift_peaks(np.abs(sig), peaks, radius, dir_is_up=True)
    elif direction == WFDBPeakDirection.Compare:
        shifted_up = _shift_peaks(sig, peaks, radius, dir_is_up=True)
        shifted_down = _shift_peaks(sig, peaks, radius, dir_is_up=False)

        up_dist = np.mean(np.abs(sig[shifted_up]))
        down_dist = np.mean(np.abs(sig[shifted_down]))

        return shifted_up if np.greater_equal(up_dist, down_dist) else shifted_down


def _get_comparison_func(find_peak_func: Callable[..., np.intp]) -> Callable[..., np.bool_]:
    if find_peak_func == np.argmax:
        return np.less_equal
    elif find_peak_func == np.argmin:
        return np.greater_equal
    else:
        raise ValueError("find_peak_func must be np.argmax or np.argmin")


def _remove_outliers(
    sig: npt.NDArray[np.float64],
    qrs_locations: npt.NDArray[np.intp],
    n_std: float,
    find_peak_func: Callable[..., np.intp],
) -> npt.NDArray[np.intp]:
    comparison_ops: dict[Callable[..., np.intp], tuple[Callable[..., np.bool_], int]] = {
        np.argmax: (np.less_equal, -1),
        np.argmin: (np.greater_equal, 1),
    }

    if find_peak_func not in comparison_ops:
        raise ValueError("find_peak_func must be np.argmax or np.argmin")

    comparison_func, direction = comparison_ops[find_peak_func]
    outliers_mask = np.zeros_like(qrs_locations, dtype=np.bool_)

    for i, peak in enumerate(qrs_locations):
        start_ind = max(0, i - 2)
        end_ind = min(len(qrs_locations), i + 3)

        surrounding_peaks = qrs_locations[start_ind:end_ind]
        surrounding_values = sig[surrounding_peaks]
        local_mean = np.mean(surrounding_values)
        local_std = np.std(surrounding_values)
        threshold = local_mean + direction * n_std * local_std

        if comparison_func(sig[peak], threshold):
            outliers_mask[i] = True

    qrs_locations = qrs_locations[~outliers_mask]
    return qrs_locations


def _handle_close_peaks(
    sig: npt.NDArray[np.float64],
    qrs_locations: npt.NDArray[np.intp],
    n_std: float,
    find_peak_func: Callable[..., np.intp],
    min_peak_distance: int,
) -> npt.NDArray[np.intp]:
    qrs_diffs = np.diff(qrs_locations)
    close_indices = np.where(qrs_diffs <= min_peak_distance)[0]

    if not close_indices.size:
        return qrs_locations

    comparison_func = _get_comparison_func(find_peak_func)
    to_remove = [
        i if comparison_func(sig[qrs_locations[i]], sig[qrs_locations[i + 1]]) else i + 1 for i in close_indices
    ]

    qrs_locations = np.delete(qrs_locations, to_remove)
    return _remove_outliers(sig, qrs_locations, n_std, find_peak_func)


def _sanitize_qrs_locations(
    sig: npt.NDArray[np.float64],
    qrs_locations: npt.NDArray[np.intp],
    min_peak_distance: int,
    n_std: float = 4.0,
) -> npt.NDArray[np.intp]:
    find_peak_func = np.argmax if np.mean(sig) < np.mean(sig[qrs_locations]) else np.argmin

    peak_indices = _handle_close_peaks(sig, qrs_locations, n_std, find_peak_func, min_peak_distance)
    sorted_peak_indices = np.argsort(peak_indices)

    return peak_indices[
        sorted_peak_indices[(peak_indices[sorted_peak_indices] > 0) & (peak_indices[sorted_peak_indices] < len(sig))]
    ]


def _find_peaks_xqrs(
    sig: npt.NDArray[np.float64],
    sampling_rate: int,
    radius: int,
    min_peak_distance: int,
    peak_dir: WFDBPeakDirection = WFDBPeakDirection.Up,
) -> npt.NDArray[np.intp]:
    xqrs_out = wp.XQRS(sig, sampling_rate)
    xqrs_out.detect(verbose=False, learn=True)
    peak_indices = _adjust_peak_positions(
        sig, peaks=np.array(xqrs_out.qrs_inds, dtype=np.intp), radius=radius, direction=peak_dir
    )

    return _sanitize_qrs_locations(sig, peak_indices, min_peak_distance)


def find_peaks(
    sig: npt.NDArray[np.float64],
    sampling_rate: int,
    method: PeakDetectionAlgorithm,
    method_parameters: _t.PeakDetectionMethodParameters | None,
) -> npt.NDArray[np.intp]:
    if method == PeakDetectionAlgorithm.LocalMaxima:
        method_parameters = cast(_t.PeaksLocalMaxima, method_parameters)
        return find_extrema(
            sig,
            search_radius=method_parameters["search_radius"],
            direction="up",
            min_peak_distance=method_parameters["min_distance"],
        )
    elif method == PeakDetectionAlgorithm.LocalMinima:
        method_parameters = cast(_t.PeaksLocalMinima, method_parameters)
        return find_extrema(
            sig,
            search_radius=method_parameters["search_radius"],
            direction="down",
            min_peak_distance=method_parameters["min_distance"],
        )
    elif method == PeakDetectionAlgorithm.PPGElgendi:
        method_parameters = cast(_t.PeaksPPGElgendi, method_parameters)
        peak_dict = nk.ppg_findpeaks(
            sig, sampling_rate=sampling_rate, method="elgendi", show=False, **method_parameters
        )
        return np.asarray(peak_dict["PPG_Peaks"], dtype=np.intp)
    elif method == PeakDetectionAlgorithm.ECGXQRS:
        method_parameters = cast(_t.PeaksECGXQRS, method_parameters)
        return _find_peaks_xqrs(
            sig,
            sampling_rate,
            radius=method_parameters["search_radius"],
            min_peak_distance=method_parameters["min_peak_distance"],
            peak_dir=WFDBPeakDirection(method_parameters["peak_dir"]),
        )
    elif method == PeakDetectionAlgorithm.ECGNeuroKit:
        method_parameters = cast(_t.PeaksECGNeuroKit, method_parameters)
        return nk.ecg_findpeaks(
            ecg_cleaned=sig,
            sampling_rate=sampling_rate,
            method=method,
            show=False,
            **method_parameters,
        )["ECG_R_Peaks"]
    elif method == PeakDetectionAlgorithm.ECGEmrich2023:
        method_parameters = cast(_t.PeaksECGEmrich, method_parameters)
        return nk.ecg_findpeaks(
            ecg_cleaned=sig,
            sampling_rate=sampling_rate,
            method=method,
            show=False,
            **method_parameters,
        )["ECG_R_Peaks"]
    elif method == PeakDetectionAlgorithm.ECGGamboa2008:
        method_parameters = cast(_t.PeaksECGGamboa, method_parameters)
        return nk.ecg_findpeaks(
            ecg_cleaned=sig,
            sampling_rate=sampling_rate,
            method=method,
            show=False,
            **method_parameters,
        )["ECG_R_Peaks"]
    elif method == PeakDetectionAlgorithm.ECGPromac:
        method_parameters = cast(_t.PeaksECGPromac, method_parameters)
        return nk.ecg_findpeaks(
            ecg_cleaned=sig,
            sampling_rate=sampling_rate,
            method=method,
            show=False,
            **method_parameters,
        )["ECG_R_Peaks"]
    else:
        return nk.ecg_findpeaks(
            ecg_cleaned=sig,
            sampling_rate=sampling_rate,
            method=method,
            show=False,
        )["ECG_R_Peaks"]
