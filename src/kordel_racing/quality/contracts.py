"""Contratos declarativos dos datasets validados."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DataContract:
    """Regras estruturais mínimas de um dataset."""

    dataset: str
    required_columns: tuple[str, ...]
    non_nullable_columns: tuple[str, ...]
    numeric_columns: tuple[str, ...]
    logical_key: tuple[str, ...]


LAPS_CONTRACT = DataContract(
    dataset="laps",
    required_columns=("session_key", "driver_number", "lap_number", "lap_duration"),
    non_nullable_columns=("session_key", "driver_number", "lap_number"),
    numeric_columns=("session_key", "driver_number", "lap_number", "lap_duration"),
    logical_key=("session_key", "driver_number", "lap_number"),
)

LAPS_RULE_SEVERITIES = {
    "dataset_not_empty": "WARNING",
    "required_columns": "ERROR",
    "session_key_not_null": "ERROR",
    "driver_number_not_null": "ERROR",
    "lap_number_not_null": "ERROR",
    "session_key_numeric": "ERROR",
    "driver_number_numeric": "ERROR",
    "lap_number_numeric": "ERROR",
    "lap_duration_numeric": "ERROR",
    "session_key_positive": "ERROR",
    "driver_number_positive": "ERROR",
    "lap_number_positive": "ERROR",
    "lap_duration_nullable": "WARNING",
    "lap_duration_positive_finite": "ERROR",
    "logical_key_unique": "ERROR",
}
