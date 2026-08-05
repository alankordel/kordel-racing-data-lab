import numpy as np
import pandas as pd
import pytest

from kordel_racing.quality.validators import validate_laps


def valid_laps() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"session_key": 1, "driver_number": 4, "lap_number": 1, "lap_duration": 90.1},
            {"session_key": 1, "driver_number": 4, "lap_number": 2, "lap_duration": 89.8},
        ]
    )


def rules(result, severity: str = "errors") -> set[str]:
    return {issue.rule for issue in getattr(result, severity)}


def test_valid_dataframe_passes():
    result = validate_laps(valid_laps())
    assert result.status == "PASS"
    assert result.valid_rows == 2
    assert result.invalid_rows == 0


def test_missing_required_column_is_error():
    result = validate_laps(valid_laps().drop(columns="lap_number"))
    assert "required_columns" in rules(result)
    assert result.invalid_rows == 2


def test_null_logical_key_is_error():
    frame = valid_laps()
    frame.loc[0, "driver_number"] = np.nan
    result = validate_laps(frame)
    assert "driver_number_not_null" in rules(result)


def test_zero_lap_number_is_error():
    frame = valid_laps()
    frame.loc[0, "lap_number"] = 0
    assert "lap_number_positive" in rules(validate_laps(frame))


@pytest.mark.parametrize("duration", [-1.0, np.inf])
def test_invalid_duration_is_error(duration):
    frame = valid_laps()
    frame.loc[0, "lap_duration"] = duration
    assert "lap_duration_positive_finite" in rules(validate_laps(frame))


def test_null_duration_is_allowed_with_warning():
    frame = valid_laps()
    frame.loc[0, "lap_duration"] = np.nan
    result = validate_laps(frame)
    assert result.status == "WARNING"
    assert "lap_duration_nullable" in rules(result, "warnings")
    assert not result.errors


def test_invalid_type_is_error():
    frame = valid_laps().astype({"driver_number": "object"})
    frame.loc[0, "driver_number"] = "quatro"
    assert "driver_number_numeric" in rules(validate_laps(frame))


def test_duplicate_logical_key_is_error_and_reports_sample():
    frame = pd.concat([valid_laps(), valid_laps().iloc[[0]]], ignore_index=True)
    result = validate_laps(frame)
    duplicate = next(issue for issue in result.errors if issue.rule == "logical_key_unique")
    assert duplicate.affected_rows == 1
    assert duplicate.sample


def test_empty_dataframe_is_warning():
    result = validate_laps(pd.DataFrame())
    assert result.status == "WARNING"
    assert "dataset_not_empty" in rules(result, "warnings")


def test_extra_column_is_accepted():
    frame = valid_laps().assign(speed_trap=310)
    assert validate_laps(frame).status == "PASS"


def test_non_dataframe_is_rejected():
    with pytest.raises(TypeError, match="pandas.DataFrame"):
        validate_laps([])
