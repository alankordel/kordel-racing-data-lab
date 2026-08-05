"""Validadores simples para as tabelas Silver."""

from collections.abc import Iterable
from numbers import Number
from typing import Any

import numpy as np
import pandas as pd

from kordel_racing.quality.contracts import LAPS_CONTRACT, DataContract
from kordel_racing.quality.report import QualityIssue, QualityResult

SAMPLE_SIZE = 5


class DataQualityError(RuntimeError):
    """Indica que erros críticos impedem a criação da camada Gold."""

    def __init__(self, message: str, result: QualityResult, report_path: str | None = None) -> None:
        super().__init__(message)
        self.result = result
        self.report_path = report_path


def _sample(frame: pd.DataFrame, mask: pd.Series | None = None) -> list[dict[str, Any]]:
    selected = frame.loc[mask] if mask is not None else frame
    sample = selected.head(SAMPLE_SIZE).astype(object)
    return sample.where(pd.notna(sample), None).to_dict(orient="records")


def _issue(rule: str, message: str, frame: pd.DataFrame, mask: pd.Series) -> QualityIssue:
    return QualityIssue(rule, message, int(mask.sum()), _sample(frame, mask))


def _numeric_mask(series: pd.Series) -> pd.Series:
    return series.map(
        lambda value: (
            not isinstance(value, Number) or isinstance(value, (bool, np.bool_)) if not pd.isna(value) else False
        )
    )


def _invalid_row_indexes(issues: Iterable[tuple[QualityIssue, pd.Series]]) -> set[Any]:
    indexes: set[Any] = set()
    for _, mask in issues:
        indexes.update(mask.index[mask])
    return indexes


def validate_laps(frame: pd.DataFrame, contract: DataContract = LAPS_CONTRACT) -> QualityResult:
    """Valida estrutura, tipos, domínio, nulos e unicidade de ``laps``."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("A validação de laps requer um pandas.DataFrame.")

    total_rows = len(frame)
    if frame.empty:
        warning = QualityIssue("dataset_not_empty", "O dataset laps está vazio.", 0, [])
        return QualityResult(contract.dataset, "WARNING", 0, 0, 0, warnings=[warning])

    errors_with_masks: list[tuple[QualityIssue, pd.Series]] = []
    warnings: list[QualityIssue] = []
    missing = [column for column in contract.required_columns if column not in frame.columns]
    if missing:
        mask = pd.Series(True, index=frame.index)
        issue = QualityIssue(
            "required_columns",
            f"Colunas obrigatórias ausentes: {', '.join(missing)}.",
            total_rows,
            _sample(frame),
        )
        errors_with_masks.append((issue, mask))

    available_keys = [column for column in contract.non_nullable_columns if column in frame.columns]
    for column in available_keys:
        mask = frame[column].isna()
        if mask.any():
            errors_with_masks.append(
                (_issue(f"{column}_not_null", f"{column} não pode conter valores nulos.", frame, mask), mask)
            )

    for column in contract.numeric_columns:
        if column not in frame.columns:
            continue
        mask = _numeric_mask(frame[column])
        if mask.any():
            errors_with_masks.append(
                (_issue(f"{column}_numeric", f"{column} deve ser numérico quando preenchido.", frame, mask), mask)
            )

    for column in ("session_key", "driver_number", "lap_number"):
        if column not in frame.columns:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        mask = numeric.notna() & (numeric <= 0)
        if mask.any():
            errors_with_masks.append(
                (_issue(f"{column}_positive", f"{column} deve ser maior que zero.", frame, mask), mask)
            )

    if "lap_duration" in frame.columns:
        duration = pd.to_numeric(frame["lap_duration"], errors="coerce")
        null_mask = frame["lap_duration"].isna()
        if null_mask.any():
            warnings.append(
                _issue(
                    "lap_duration_nullable",
                    "lap_duration nula é aceita para voltas incompletas ou sem cronometragem.",
                    frame,
                    null_mask,
                )
            )
        invalid_duration = duration.notna() & ((duration <= 0) | ~np.isfinite(duration))
        if invalid_duration.any():
            errors_with_masks.append(
                (
                    _issue(
                        "lap_duration_positive_finite",
                        "lap_duration deve ser positiva e finita quando preenchida.",
                        frame,
                        invalid_duration,
                    ),
                    invalid_duration,
                )
            )

    if all(column in frame.columns for column in contract.logical_key):
        duplicate_mask = frame.duplicated(subset=list(contract.logical_key), keep=False)
        if duplicate_mask.any():
            duplicate_count = int(frame.duplicated(subset=list(contract.logical_key), keep="first").sum())
            issue = QualityIssue(
                "logical_key_unique",
                "A chave session_key + driver_number + lap_number deve ser única.",
                duplicate_count,
                _sample(frame, duplicate_mask),
            )
            errors_with_masks.append((issue, duplicate_mask))

    errors = [issue for issue, _ in errors_with_masks]
    invalid_rows = len(_invalid_row_indexes(errors_with_masks))
    status = "ERROR" if errors else "WARNING" if warnings else "PASS"
    return QualityResult(
        dataset=contract.dataset,
        status=status,
        total_rows=total_rows,
        valid_rows=total_rows - invalid_rows,
        invalid_rows=invalid_rows,
        errors=errors,
        warnings=warnings,
    )
