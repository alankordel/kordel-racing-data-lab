import json
from unittest.mock import Mock

import pandas as pd
import pytest

from kordel_racing.pipelines import full_pipeline
from kordel_racing.quality.report import save_quality_report
from kordel_racing.quality.validators import DataQualityError, validate_laps


def test_saves_quality_report_as_json(tmp_path):
    result = validate_laps(
        pd.DataFrame([{"session_key": 1, "driver_number": 4, "lap_number": 1, "lap_duration": None}])
    )
    path = save_quality_report(result, tmp_path, 1)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.name == "laps_quality_1.json"
    assert payload["dataset"] == "laps"
    assert payload["session_key"] == 1
    assert payload["warning_count"] == 1
    assert payload["status"] == "WARNING"


def configure_pipeline_mocks(monkeypatch, tmp_path, laps: pd.DataFrame | None):
    silver = tmp_path / "silver" / "session_1"
    silver.mkdir(parents=True)
    if laps is not None:
        laps.to_parquet(silver / "laps.parquet", index=False)

    monkeypatch.setattr(
        full_pipeline,
        "load_settings",
        lambda _: {
            "openf1": {"base_url": "https://example.test", "timeout_seconds": 1},
            "pipeline": {
                "meeting_key": 1,
                "session_key": 1,
                "output_dir": tmp_path,
                "endpoints": ["laps"],
            },
        },
    )
    monkeypatch.setattr(full_pipeline, "OpenF1Client", Mock())
    monkeypatch.setattr(full_pipeline, "ingest_session", Mock(return_value=tmp_path / "bronze"))
    monkeypatch.setattr(full_pipeline, "build_silver", Mock(return_value=silver))
    gold = Mock(return_value={})
    monkeypatch.setattr(full_pipeline, "create_gold_tables", gold)
    return gold


def test_pipeline_stops_before_gold_on_critical_error(monkeypatch, tmp_path):
    invalid = pd.DataFrame([{"session_key": 1, "driver_number": 4, "lap_number": 0, "lap_duration": 90.0}])
    gold = configure_pipeline_mocks(monkeypatch, tmp_path, invalid)

    with pytest.raises(DataQualityError, match=r"erro\(s\) crítico\(s\)") as error:
        full_pipeline.run_pipeline("settings.yaml")

    assert not gold.called
    assert (tmp_path / "quality/laps_quality_1.json").exists()
    assert error.value.report_path


def test_pipeline_continues_when_only_warnings_exist(monkeypatch, tmp_path):
    warning_only = pd.DataFrame([{"session_key": 1, "driver_number": 4, "lap_number": 1, "lap_duration": None}])
    gold = configure_pipeline_mocks(monkeypatch, tmp_path, warning_only)

    full_pipeline.run_pipeline("settings.yaml")

    gold.assert_called_once()
    report = json.loads((tmp_path / "quality/laps_quality_1.json").read_text(encoding="utf-8"))
    assert report["status"] == "WARNING"
