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
