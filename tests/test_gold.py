import pandas as pd
import pytest
from fixtures.sample_data import DRIVERS, LAPS, STINTS

from kordel_racing.gold.metrics import calculate_degradation, create_gold_tables
from kordel_racing.silver.transformations import build_silver


def test_calculate_degradation():
    result = calculate_degradation(pd.Series([1, 2, 3]), pd.Series([90.0, 90.2, 90.4]))
    assert result == pytest.approx(0.2)


def test_creates_gold_tables_and_summary(tmp_path):
    silver = tmp_path / "silver" / "session_1"
    silver.mkdir(parents=True)
    laps = pd.DataFrame(LAPS)
    laps["lap_duration_seconds"] = laps["lap_duration"]
    laps.to_parquet(silver / "laps.parquet", index=False)
    pd.DataFrame(DRIVERS).to_parquet(silver / "drivers.parquet", index=False)
    pd.DataFrame(STINTS).to_parquet(silver / "stints.parquet", index=False)

    tables = create_gold_tables(silver, tmp_path, 1)

    assert {"driver_lap_performance", "driver_session_summary", "tyre_stint_analysis"} <= tables.keys()
    summary = tables["driver_session_summary"].set_index("driver_number")
    assert summary.loc[4, "best_lap"] == 90.0
    assert summary.loc[4, "average_lap"] == 91.0
    assert summary.loc[4, "consistency_std"] == 1.0
    assert (tmp_path / "gold/session_1/driver_session_summary.parquet").exists()


def test_silver_and_gold_pipeline_with_synthetic_data(tmp_path):
    bronze = tmp_path / "bronze"
    bronze.mkdir()
    for name, data in {"drivers": DRIVERS, "laps": LAPS, "stints": STINTS}.items():
        pd.DataFrame(data).to_parquet(bronze / f"{name}.parquet", index=False)

    silver = build_silver(bronze, tmp_path, 1)
    tables = create_gold_tables(silver, tmp_path, 1)

    assert len(tables["driver_lap_performance"]) == 5
    assert len(tables["tyre_stint_analysis"]) == 2
