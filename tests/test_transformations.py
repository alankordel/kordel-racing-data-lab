import pandas as pd

from kordel_racing.silver.transformations import duration_to_seconds, standardize_dataframe


def test_duration_to_seconds():
    assert duration_to_seconds("1:30.500") == 90.5
    assert duration_to_seconds(89.2) == 89.2
    assert duration_to_seconds("inválido") is None


def test_standardizes_columns_strings_dates_and_duplicates():
    frame = pd.DataFrame(
        [
            {"Driver Number": 4, "Session Key": 1, "Date": "2025-01-01", "Name": "  Piloto  "},
            {"Driver Number": 4, "Session Key": 1, "Date": "2025-01-01", "Name": "  Piloto  "},
        ]
    )
    result = standardize_dataframe(frame)
    assert list(result.columns) == ["driver_number", "session_key", "date", "name"]
    assert len(result) == 1
    assert result.loc[0, "name"] == "Piloto"
    assert str(result["date"].dtype).startswith("datetime64[")
    assert str(result["date"].dtype).endswith(", UTC]")
