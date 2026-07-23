"""Limpeza e padronização dos dados brutos."""

import re
from pathlib import Path

import pandas as pd

DATASET_NAMES = {
    "sessions": "sessions",
    "drivers": "drivers",
    "laps": "laps",
    "stints": "stints",
    "pit": "pit_stops",
    "weather": "weather",
    "position": "position",
    "session_result": "race_results",
}


def duration_to_seconds(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if re.fullmatch(r"\d+(\.\d+)?", text):
        return float(text)
    parts = text.split(":")
    try:
        return sum(float(part) * (60**index) for index, part in enumerate(reversed(parts)))
    except ValueError:
        return None


def standardize_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.columns = [
        re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower())).strip("_")
        for column in result.columns
    ]
    for column in result.select_dtypes(include=["object", "str"]):
        result[column] = result[column].map(lambda value: value.strip() if isinstance(value, str) else value)
        if result[column].dropna().map(type).nunique() > 1:
            result[column] = result[column].map(lambda value: str(value) if not pd.isna(value) else None)
        if column == "date" or column.startswith("date_"):
            result[column] = pd.to_datetime(result[column], errors="coerce", utc=True)
    keys = [
        column
        for column in ("session_key", "driver_number", "lap_number", "stint_number", "date")
        if column in result.columns
    ]
    return result.drop_duplicates(subset=keys or None).reset_index(drop=True)


def build_silver(bronze_dir: str | Path, output_dir: str | Path, session_key: int) -> Path:
    source = Path(bronze_dir)
    target = Path(output_dir) / "silver" / f"session_{session_key}"
    target.mkdir(parents=True, exist_ok=True)
    files = list(source.glob("*.parquet")) + list(source.glob("*.json"))
    for file in files:
        if file.name == "metadata.json":
            continue
        raw = pd.read_parquet(file) if file.suffix == ".parquet" else pd.read_json(file)
        frame = standardize_dataframe(raw)
        name = DATASET_NAMES.get(file.stem, file.stem)
        if name == "laps" and "lap_duration" in frame:
            frame["lap_duration_seconds"] = frame["lap_duration"].map(duration_to_seconds)
            for sector in ("duration_sector_1", "duration_sector_2", "duration_sector_3"):
                if sector in frame:
                    frame[sector.replace("duration_", "") + "_seconds"] = frame[sector].map(duration_to_seconds)
        if name == "pit_stops":
            source_column = "lane_duration" if "lane_duration" in frame else "pit_duration"
            if source_column in frame:
                frame["pit_duration_seconds"] = pd.to_numeric(frame[source_column], errors="coerce")
        frame.to_parquet(target / f"{name}.parquet", index=False)
    return target
