"""
Reading and writing files: sampling rate detection for tabular files, EDF reading through mne, and the Excel export.

Tabular files are otherwise read by polars directly in `DataController._read_frame`.
"""

import datetime
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import mne.io
import polars as pl
import polars.selectors as cs
import xlsxwriter
from loguru import logger

from signal_viewer.constants import COMBO_BOX_NO_SELECTION

if TYPE_CHECKING:
    from signal_viewer.sv_data.section import Section

INTEGER_DTYPES = frozenset(
    [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Int128, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]
)


def _infer_time_column(lf: pl.LazyFrame, contains: Sequence[str] | None = None) -> list[str]:
    if contains is None:
        contains = ("time", "ts")
    return (
        lf.select(cs.contains(*contains) | cs.datetime() | cs.duration() | (cs.integer() & ~cs.contains("index")))
        .collect_schema()
        .names()
    )


def _infer_time_unit(
    time_col_dtype: pl.DataType, interpret_integers_as: Literal["ms", "us", "ns"]
) -> Literal["s", "ms", "us", "ns", "datetime"]:
    if time_col_dtype.is_float():
        return "s"
    if time_col_dtype.is_integer():
        return interpret_integers_as
    if time_col_dtype.base_type().is_(pl.Datetime):
        return "datetime"
    if time_col_dtype.is_(pl.Duration("ns")):
        return "ns"
    if time_col_dtype.is_(pl.Duration("ms")):
        return "ms"
    if time_col_dtype.is_(pl.Duration("us")):
        return "us"
    raise ValueError(f"Could not infer valid time unit from time column with dtype: '{time_col_dtype}'.")


def _get_target_for_time_unit(
    time_unit: Literal["s", "ms", "us", "ns", "datetime"],
    time_col_dtype: pl.DataType,
    start_val: datetime.datetime | None = None,
) -> int | float | datetime.datetime:
    if time_unit == "s" and time_col_dtype.is_float():
        return 1.0
    if time_unit == "ms" and time_col_dtype in (INTEGER_DTYPES | {pl.Duration("ms")}):
        return 1_000
    if time_unit == "us" and time_col_dtype in (INTEGER_DTYPES | {pl.Duration("us")}):
        return 1_000_000
    if time_unit == "ns" and time_col_dtype in (INTEGER_DTYPES | {pl.Duration("ns")}):
        return 1_000_000_000
    if time_unit == "datetime" and time_col_dtype.base_type().is_(pl.Datetime) and start_val is not None:
        return start_val + datetime.timedelta(seconds=1)
    raise ValueError(f"Time unit '{time_unit}' does not match the data type of the time column: '{time_col_dtype}'.")


def detect_sampling_rate(
    lf: pl.LazyFrame,
    time_column: str | int = "auto",
    time_unit: Literal["auto", "s", "ms", "us", "ns", "datetime"] = "auto",
    interpret_integers_as: Literal["ms", "us", "ns"] = "us",
    first_column_is_time: bool = False,
) -> int:
    """
    Tries to detect the sampling rate value from a `polars.LazyFrame` containing physiological signal data.

    Parameters
    ----------
    lf : pl.LazyFrame
        The polars LazyFrame containing the data.
    time_column : str | int, optional
        The name or index of the column containing the time information. If set to `"auto"`
        (default), an attempt is made to find a suitable time column automatically. See ``Notes`` for more information.
    time_unit : {"auto", "s", "ms", "us", "ns", "datetime"}, optional
        The unit of the time column. If set to `"auto"` (default), the function will try to infer
        the correct unit automatically. Float columns are interpreted as seconds with decimal places.
    interpret_integers_as : {"ms", "us", "ns"}, optional
        The unit to interpret integer values as. Default is microseconds (`"us"`).

    Returns
    -------
    int
        The sampling rate. Calculated as the number of rows in the first second of the data.

    Notes
    -----
    Possible columns when `time_column` is set to `"auto"`:
    - Columns with a name containing the substring `"time"` or `"ts"`.
    - Columns containing datetime or duration data.
    - Integer columns excluding those whose name contains the substring `"index"`.

    """
    if isinstance(time_column, int):
        try:
            time_column = lf.columns[time_column]
        except IndexError:
            time_column = "auto"

    if time_column == "auto":
        possible_columns = _infer_time_column(lf)
        if not possible_columns:
            raise ValueError("Could not find a column containing time information.")
        if len(possible_columns) == 1 or first_column_is_time:
            time_column = possible_columns[0]
        else:
            raise ValueError(
                f"Detected multiple columns that could be interpreted as time data: [{', '.join([f"'{col}'" for col in possible_columns])}]. Please specify the time column manually."
            )

    time_col_dtype = lf.collect_schema()[time_column]

    if time_unit == "auto":
        time_unit = _infer_time_unit(time_col_dtype, interpret_integers_as)

    start_val = lf.select(time_column).first().collect().item(0, time_column)

    target = _get_target_for_time_unit(time_unit, time_col_dtype, start_val)

    closed = "left" if start_val == 0 or time_unit in {"ms", "us", "ns", "datetime"} else "both"
    return lf.filter(pl.col(time_column).is_between(start_val, target, closed)).collect().height


def read_edf(
    file_path: Path,
    data_channel: str,
    info_channel: str | None = None,
    *,
    start: int = 0,
    stop: int | None = None,
    filter_all_zeros: bool = True,
) -> pl.DataFrame:
    """
    Reads `data_channel` (and `info_channel`) of an EDF file into a frame with a row index column.

    EDF recordings are padded with zeros to whole data records, so with `filter_all_zeros` the trailing all-zero rows
    are dropped (rows where either channel is zero when an info channel is given).

    Parameters
    ----------
    start, stop : int
        Sample range to read, as in `mne.io.Raw.get_data`.
    """
    if info_channel is None:
        info_channel = COMBO_BOX_NO_SELECTION
    raw_edf = mne.io.read_raw_edf(file_path, include=[data_channel, info_channel])
    channel_names: list[str] = raw_edf.ch_names  # type: ignore
    data = raw_edf.get_data(start=start, stop=stop).squeeze()  # type: ignore
    out = pl.from_numpy(data, channel_names)  # type: ignore
    if info_channel != COMBO_BOX_NO_SELECTION:
        out = out.select(pl.col(data_channel), pl.col(info_channel))
        if filter_all_zeros:
            out = out.filter((pl.col(data_channel) != 0) & (pl.col(info_channel) != 0))
    else:
        out = out.select(pl.col(data_channel))
        if filter_all_zeros:
            # Find the last row with a non-zero value in the column
            try:
                last_non_zero = out.with_row_index().filter(pl.col(data_channel) != 0).get_column("index").item(-1)
                logger.info(
                    f"Found section of continuous zeros from row {last_non_zero + 1} to the end of the column, removing."
                )
                out = out.head(last_non_zero + 1)
            except IndexError:
                logger.info("No section of continuous zeros found, keeping all rows.")
            # Then remove that many rows from the end of the column

    return out.with_row_index(offset=start)


def _prepend_literal(df: pl.DataFrame, name: str, value: str | int, dtype: pl.DataType) -> pl.DataFrame:
    """A copy of `df` with a constant column `name` in front. The section frames themselves are left untouched."""
    if df.height == 0:
        # A literal broadcasts to one row on an empty frame, which would invent a result row.
        return pl.DataFrame(schema={name: dtype, **df.schema})
    return df.select(pl.lit(value).cast(dtype).alias(name), pl.all())


def write_xlsx(
    sections_by_channel: Mapping[str, Sequence[Section]], path: Path | str, group_var: str | None = None
) -> None:
    """
    Writes the results of every channel's sections to one workbook with the sheets `r_data`, `Detected Peaks`,
    `Rate Data` and `Global Bounds`.

    Every sheet starts with a `channel` column (the key of `sections_by_channel`, i.e. the file's column name).
    The `section_id` column in the first three sheets is the 1-based position of the section within its channel.
    The window step of `r_data` is each section's own `rate_params`. Sections without a result (not locked)
    contribute no rows; their missing columns are filled with nulls so one unlocked section does not break the export.

    Raises
    ------
    ValueError
        If no channel has a section.
    """
    if not any(sections_by_channel.values()):
        raise ValueError("Nothing to export: no sections were given.")

    peak_frames: list[pl.DataFrame] = []
    rate_frames: list[pl.DataFrame] = []
    bounds_frames: list[pl.DataFrame] = []
    r_data_frames: list[pl.DataFrame] = []
    for channel, sections in sections_by_channel.items():
        for i, s in enumerate(sections, start=1):
            numbered_peaks = _prepend_literal(s.peak_data, "section_id", i, pl.Int32())
            numbered_rate = _prepend_literal(s.rate_data, "section_id", i, pl.Int32())
            peak_frames.append(_prepend_literal(numbered_peaks, "channel", channel, pl.String()))
            rate_frames.append(_prepend_literal(numbered_rate, "channel", channel, pl.String()))
            bounds_frames.append(_prepend_literal(s.global_bounds_df, "channel", channel, pl.String()))
            r_data_frames.append(
                _prepend_literal(s.get_simple_result(group_var=group_var), "channel", channel, pl.String())
            )

    with xlsxwriter.Workbook(path) as wb:
        pl.concat(r_data_frames, how="diagonal_relaxed").write_excel(workbook=wb, worksheet="r_data")
        pl.concat(peak_frames, how="diagonal_relaxed").write_excel(workbook=wb, worksheet="Detected Peaks")
        pl.concat(rate_frames, how="diagonal_relaxed").write_excel(workbook=wb, worksheet="Rate Data")
        pl.concat(bounds_frames, how="diagonal_relaxed").write_excel(workbook=wb, worksheet="Global Bounds")


def per_channel_xlsx_paths(
    sections_by_channel: Mapping[str, Sequence[Section]], directory: Path | str, stem: str
) -> dict[str, Path]:
    """
    The workbook path per channel that `write_xlsx_per_channel` writes: `Result_{Signal}_{stem}.xlsx`, where
    `Signal` is the channel's cleaned column name (the sections' `signal_name`), which is safe in a file name.
    """
    directory = Path(directory)
    return {
        channel: directory / f"Result_{sections[0].signal_name.title()}_{stem}.xlsx"
        for channel, sections in sections_by_channel.items()
        if sections
    }


def write_xlsx_per_channel(
    sections_by_channel: Mapping[str, Sequence[Section]],
    directory: Path | str,
    stem: str,
    group_var: str | None = None,
) -> list[Path]:
    """
    Writes one workbook per channel (see `write_xlsx` for the sheets) into `directory` and returns the paths.

    Raises
    ------
    ValueError
        If no channel has a section.
    """
    paths = per_channel_xlsx_paths(sections_by_channel, directory, stem)
    if not paths:
        raise ValueError("Nothing to export: no sections were given.")
    for channel, path in paths.items():
        write_xlsx({channel: sections_by_channel[channel]}, path, group_var)
    return list(paths.values())
