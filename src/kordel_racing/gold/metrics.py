"""Métricas analíticas explicáveis."""

from pathlib import Path

import numpy as np
import pandas as pd


def calculate_degradation(lap_numbers: pd.Series, lap_times: pd.Series) -> float | None:
    valid = pd.DataFrame({"lap": lap_numbers, "time": lap_times}).dropna()
    if len(valid) < 2:
        return None
    return float(np.polyfit(valid["lap"], valid["time"], 1)[0])


def create_gold_tables(silver_dir: str | Path, output_dir: str | Path, session_key: int) -> dict[str, pd.DataFrame]:
    source = Path(silver_dir)

    def read(name: str) -> pd.DataFrame:
        path = source / f"{name}.parquet"
        return pd.read_parquet(path) if path.exists() else pd.DataFrame()

    laps, drivers, stints, pits = read("laps"), read("drivers"), read("stints"), read("pit_stops")
    results, positions = read("race_results"), read("position")

    performance = laps.copy()
    if not performance.empty and not drivers.empty:
        driver_cols = [c for c in ("session_key", "driver_number", "full_name", "team_name") if c in drivers]
        performance = performance.merge(
            drivers[driver_cols].drop_duplicates(), on=["session_key", "driver_number"], how="left"
        )
        performance = performance.rename(columns={"full_name": "driver_name"})
    if not performance.empty:
        performance["is_valid_lap"] = performance["lap_duration_seconds"].notna()
        keep = [
            c
            for c in (
                "session_key",
                "driver_number",
                "driver_name",
                "team_name",
                "lap_number",
                "lap_duration_seconds",
                "compound",
                "tyre_age",
                "is_valid_lap",
            )
            if c in performance
        ]
        performance = performance[keep]

    grouped = performance[performance.get("is_valid_lap", pd.Series(False, index=performance.index))].groupby(
        ["session_key", "driver_number"], dropna=False
    )
    summary = (
        grouped.agg(
            driver_name=("driver_name", "first"),
            team_name=("team_name", "first"),
            total_laps=("lap_number", "count"),
            best_lap=("lap_duration_seconds", "min"),
            average_lap=("lap_duration_seconds", "mean"),
            median_lap=("lap_duration_seconds", "median"),
            consistency_std=("lap_duration_seconds", "std"),
        ).reset_index()
        if not performance.empty
        else pd.DataFrame()
    )
    if not summary.empty:
        if not pits.empty:
            pit_stats = (
                pits.groupby(["session_key", "driver_number"])
                .agg(
                    total_pit_stops=("lap_number", "count"),
                    average_pit_duration=("pit_duration_seconds", "mean"),
                )
                .reset_index()
            )
            summary = summary.merge(pit_stats, on=["session_key", "driver_number"], how="left")
        if not results.empty and "position" in results:
            summary = summary.merge(
                results[["session_key", "driver_number", "position"]].rename(columns={"position": "final_position"}),
                on=["session_key", "driver_number"],
                how="left",
            )
        elif not positions.empty:
            final = positions.sort_values("date").groupby(["session_key", "driver_number"]).tail(1)
            summary = summary.merge(
                final[["session_key", "driver_number", "position"]].rename(columns={"position": "final_position"}),
                on=["session_key", "driver_number"],
                how="left",
            )
        if not stints.empty and "compound" in stints:
            compounds = (
                stints.groupby(["session_key", "driver_number"])["compound"]
                .agg(lambda values: ", ".join(sorted(set(values.dropna().astype(str)))))
                .rename("tyre_compounds_used")
                .reset_index()
            )
            summary = summary.merge(compounds, on=["session_key", "driver_number"], how="left")

    stint_rows = []
    if not stints.empty and not performance.empty:
        for _, stint in stints.iterrows():
            subset = performance[
                (performance["driver_number"] == stint["driver_number"])
                & performance["lap_number"].between(stint["lap_start"], stint["lap_end"])
                & performance["is_valid_lap"]
            ]
            stint_rows.append(
                {
                    "session_key": session_key,
                    "driver_number": stint["driver_number"],
                    "driver_name": subset["driver_name"].iloc[0] if not subset.empty else None,
                    "compound": stint.get("compound"),
                    "stint_number": stint.get("stint_number"),
                    "stint_length": stint["lap_end"] - stint["lap_start"] + 1,
                    "average_lap_time": subset["lap_duration_seconds"].mean(),
                    "best_lap_time": subset["lap_duration_seconds"].min(),
                    "degradation_per_lap": calculate_degradation(subset["lap_number"], subset["lap_duration_seconds"]),
                    "starting_lap": stint["lap_start"],
                    "ending_lap": stint["lap_end"],
                }
            )
    tyre_analysis = pd.DataFrame(stint_rows)
    target = Path(output_dir) / "gold" / f"session_{session_key}"
    target.mkdir(parents=True, exist_ok=True)
    tables = {
        "driver_lap_performance": performance,
        "driver_session_summary": summary,
        "tyre_stint_analysis": tyre_analysis,
    }
    if not pits.empty:
        pit_analysis = (
            pits.merge(
                drivers[
                    [c for c in ("session_key", "driver_number", "full_name", "team_name") if c in drivers]
                ].drop_duplicates(),
                on=["session_key", "driver_number"],
                how="left",
            )
            if not drivers.empty
            else pits
        )
        tables["pit_stop_analysis"] = pit_analysis.rename(columns={"full_name": "driver_name"})
    for name, frame in tables.items():
        frame.to_parquet(target / f"{name}.parquet", index=False)
    return tables
