import datetime
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import mne.io
import polars as pl
import polars.selectors as cs
from loguru import logger

from signal_viewer.constants import COMBO_BOX_NO_SELECTION
from signal_viewer.type_defs import CompleteResultDict

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


def read_annotation_file(
    file_path: Path,
    sampling_rate: int,
    separator: str = "\t",
    time_column: str = "time_seconds",
    comment_column: str = "comment_text",
) -> list[dict[str, Any]]:
    return (
        pl.read_csv(file_path, separator=separator)
        .select(
            (pl.col(time_column) * sampling_rate).cast(pl.UInt32).alias("index"),
            pl.col(time_column),
            pl.col(comment_column),
        )
        .to_dicts()
    )


@logger.catch
def write_hdf5(file_path: Path, data: CompleteResultDict) -> None:
    raise NotImplementedError("Needs to be updated to work with new result structure.")
    # fp = file_path.resolve().as_posix()
    # with tb.open_file(fp, "w", title=f"Results_{file_path.stem}") as h5f:
    #     # Root level metadata
    #     for k, v in data["metadata"].items():
    #         h5f.set_node_attr(h5f.root, k, v)

    #     h5f.create_table(
    #         h5f.root, name="combined_data", title="Combined Section Dataframe", obj=data["global_dataframe"]
    #     )

    #     section_results = h5f.create_group(h5f.root, "section_results", "Results by Section")

    #     for section_id, section_data in data["section_results"].items():
    #         section_group = h5f.create_group(section_results, section_id, f"Results for {section_id.pretty_name()}")

    #         h5f.create_table(
    #             section_group, name="peak_result", obj=section_data["section_result"]["peak_data"], title="Peak Results"
    #         )
    #         h5f.create_table(
    #             section_group, name="rate_result", obj=section_data["section_result"]["rate_data"], title="Rate Results"
    #         )

    #         # Section dataframe
    #         h5f.create_table(
    #             section_group,
    #             name="data",
    #             obj=section_data["section_dataframe"],
    #             title="Section Dataframe",
    #         )

    #         # Processing info
    #         processing_group = h5f.create_group(section_group, "processing_info", "Data Processing Information")
    #         h5f.set_node_attr(processing_group, "sampling_rate", section_data["metadata"]["sampling_rate"])
    #         h5f.set_node_attr(
    #             processing_group,
    #             "processing_pipeline",
    #             section_data["metadata"]["processing_parameters"]["processing_pipeline"],
    #         )

    #         # Filters
    #         filters_group = h5f.create_group(processing_group, "filters", "Applied Filters")
    #         for i, filter_params in enumerate(
    #             section_data["metadata"]["processing_parameters"]["filter_parameters"], 1
    #         ):
    #             filter_group = h5f.create_group(filters_group, f"filter_{i}", f"Filter {i} Parameters")
    #             for param, value in filter_params.items():
    #                 h5f.set_node_attr(filter_group, param, value)

    #         # Standardization
    #         std_group = h5f.create_group(processing_group, "standardization", "Data Standardization")
    #         if std_params := section_data["metadata"]["processing_parameters"].get("standardization_parameters", {}):
    #             for param, value in std_params.items():
    #                 h5f.set_node_attr(std_group, param, value)

    #         # Peak detection
    #         peak_detect_group = h5f.create_group(processing_group, "peak_detection", "Peak Detection Method")
    #         peak_method = section_data["metadata"]["processing_parameters"]["peak_detection_method"] or "None"
    #         peak_params = section_data["metadata"]["processing_parameters"]["peak_detection_method_parameters"] or {}
    #         if peak_method == PeakDetectionMethod.ECGNeuroKit2:
    #             peak_method = f"{peak_method} ({peak_params.get('method', 'None')})"
    #             peak_params = peak_params.get("params") or {}
    #         h5f.set_node_attr(peak_detect_group, "method", peak_method)
    #         if peak_params:
    #             for param, value in peak_params.items():
    #                 h5f.set_node_attr(peak_detect_group, param, value)

    #         # Rate computation
    #         rate_group = h5f.create_group(processing_group, "rate_computation", "Rate Computation Method")
    #         rate_method = section_data["metadata"]["processing_parameters"]["rate_computation_method"]
    #         h5f.set_node_attr(rate_group, "method", rate_method)


# def _read_edf(filename: str) -> tuple[dict[str, Any], pl.DataFrame]:
#     with open(filename, "rb") as f:
#         header_bytes = f.read(256)
#         version = header_bytes[:8].decode().strip()
#         patient_id = header_bytes[8:88].decode().strip()
#         recording_id = header_bytes[88:168].decode().strip()
#         start_date = header_bytes[168:176].decode().strip()
#         start_time = header_bytes[176:184].decode().strip()
#         header_bytes[184:192]
#         num_data_records = int(header_bytes[236:244].decode().strip())
#         record_duration = float(header_bytes[244:252].decode().strip())
#         n_signals = int(header_bytes[252:256].decode().strip())

#         labels = [f.read(16).decode().strip() for _ in range(n_signals)]
#         transducers = [f.read(80).decode().strip() for _ in range(n_signals)]
#         phys_dims = [f.read(8).decode().strip() for _ in range(n_signals)]
#         phys_mins = [float(f.read(8).decode().strip()) for _ in range(n_signals)]
#         phys_maxs = [float(f.read(8).decode().strip()) for _ in range(n_signals)]
#         dig_mins = [int(f.read(8).decode().strip()) for _ in range(n_signals)]
#         dig_maxs = [int(f.read(8).decode().strip()) for _ in range(n_signals)]
#         prefilters = [f.read(80).decode().strip() for _ in range(n_signals)]
#         samples_per_record = [int(f.read(8).decode().strip()) for _ in range(n_signals)]
#         _ = f.read(32 * n_signals)  # reserved

#         header = {
#             "version": version,
#             "patient_id": patient_id,
#             "recording_id": recording_id,
#             "start_date": start_date,
#             "start_time": start_time,
#             "num_data_records": num_data_records,
#             "record_duration": record_duration,
#             "n_signals": n_signals,
#             "labels": labels,
#             "transducers": transducers,
#             "physical_dimensions": phys_dims,
#             "physical_min": phys_mins,
#             "physical_max": phys_maxs,
#             "digital_min": dig_mins,
#             "digital_max": dig_maxs,
#             "prefiltering": prefilters,
#             "samples_per_record": samples_per_record,
#         }

#         total_samples = sum(samples_per_record) * num_data_records
#         all_data = []

#         scaling = [(phys_maxs[i] - phys_mins[i]) / (dig_maxs[i] - dig_mins[i]) for i in range(n_signals)]
#         offsets = [phys_mins[i] - dig_mins[i] * scaling[i] for i in range(n_signals)]

#         for _ in range(num_data_records):
#             for i in range(n_signals):
#                 n_samp = samples_per_record[i]
#                 raw = f.read(2 * n_samp)
#                 fmt = "<" + "h" * n_samp
#                 vals = struct.unpack(fmt, raw)
#                 phys = [v * scaling[i] + offsets[i] for v in vals]
#                 all_data.append((labels[i], phys))

#         # reorganize into columns
#         cols = {}
#         for label, phys in all_data:
#             cols.setdefault(label, []).extend(phys)

#         df = pl.DataFrame(cols)
#         sample_rate = sum(samples_per_record) / record_duration
#         times = [i / sample_rate for i in range(df.height)]
#         df = df.with_columns(pl.Series("time", times))

#         return header, df


# def _read_edf_header(fname: Path, exclude: Sequence[str] = (), infer_types: bool = True, include: Sequence[str] | None = None, exclude_after_unique: bool = False):
#     edf_info = {}

#     with open(fname, "rb") as f:
#         f.read(8)  # version of this data format
#         f.read(80)  # patient identification
#         f.read(80)  # recording identification

#         start_date = f.read(8).decode("latin-1")  # start date `dd.mm.yy`
#         day, month, year = (int(x) for x in start_date.split("."))
#         year = year + 2000 if year < 85 else year + 1900
#         meas_date = datetime.datetime(year, month, day)

#         start_time = f.read(8).decode("latin-1")  # start time `hh.mm.ss`
#         hour, minute, second = (int(x) for x in start_time.split("."))
#         meas_date.replace(hour=hour, minute=minute, second=second, tzinfo=datetime.timezone.utc)

#         f.read(8)  # number of bytes in header record
#         f.read(44)  # reserved
