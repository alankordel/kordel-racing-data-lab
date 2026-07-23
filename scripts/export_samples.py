"""Exporta uma sessão processada para formatos simples e versionáveis."""

import argparse
import shutil
from pathlib import Path

import pandas as pd


def export_samples(data_dir: Path, meeting_key: int, session_key: int) -> Path:
    bronze_dir = data_dir / "bronze" / f"meeting_{meeting_key}" / f"session_{session_key}"
    gold_dir = data_dir / "gold" / f"session_{session_key}"
    target = data_dir / "samples" / f"session_{session_key}"
    json_dir = target / "json"
    csv_dir = target / "csv"
    json_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    if not bronze_dir.exists() or not gold_dir.exists():
        raise FileNotFoundError("Execute o pipeline antes de exportar as amostras.")

    for parquet_file in sorted(bronze_dir.glob("*.parquet")):
        frame = pd.read_parquet(parquet_file)
        frame.to_json(
            json_dir / f"{parquet_file.stem}.json",
            orient="records",
            date_format="iso",
            force_ascii=False,
            indent=2,
        )

    for json_file in sorted(bronze_dir.glob("*.json")):
        shutil.copyfile(json_file, json_dir / json_file.name)

    for parquet_file in sorted(gold_dir.glob("*.parquet")):
        pd.read_parquet(parquet_file).to_csv(
            csv_dir / f"{parquet_file.stem}.csv",
            index=False,
            encoding="utf-8",
        )

    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--meeting-key", type=int, default=1276)
    parser.add_argument("--session-key", type=int, default=9839)
    args = parser.parse_args()
    target = export_samples(args.data_dir, args.meeting_key, args.session_key)
    print(f"Amostras exportadas para: {target}")


if __name__ == "__main__":
    main()
