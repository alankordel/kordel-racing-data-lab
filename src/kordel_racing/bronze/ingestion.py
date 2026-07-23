"""Persistência fiel das respostas da OpenF1."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from kordel_racing.api.client import OpenF1Client

LOGGER = logging.getLogger(__name__)


def ingest_session(
    client: OpenF1Client,
    meeting_key: int,
    session_key: int,
    endpoints: list[str],
    output_dir: str | Path,
) -> Path:
    LOGGER.info("Iniciando ingestão...")
    LOGGER.info("Sessão selecionada: %s", session_key)
    target = Path(output_dir) / "bronze" / f"meeting_{meeting_key}" / f"session_{session_key}"
    target.mkdir(parents=True, exist_ok=True)
    metadata = {
        "meeting_key": meeting_key,
        "session_key": session_key,
        "extracted_at_utc": datetime.now(UTC).isoformat(),
        "datasets": [],
    }
    for endpoint in endpoints:
        params = {"session_key": session_key}
        item = {"endpoint": endpoint, "params": params, "status": "success"}
        try:
            payload = client.get(endpoint, params)
            path = target / f"{endpoint}.parquet"
            try:
                pd.DataFrame(payload).to_parquet(path, index=False)
            except (TypeError, ValueError, OverflowError):
                path = target / f"{endpoint}.json"
                path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                LOGGER.warning(
                    "Dataset %s incompatível com Parquet; salvo em JSON.",
                    endpoint,
                )
            item.update(records=len(payload), file=path.name)
            LOGGER.info("Arquivo Bronze salvo: %s", path)
        except Exception as exc:
            item.update(status="error", records=0, file=None, error=str(exc))
            LOGGER.error("Falha ao ingerir %s: %s", endpoint, exc)
        metadata["datasets"].append(item)
    (target / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    if not any(item["status"] == "success" for item in metadata["datasets"]):
        raise RuntimeError("Nenhum endpoint pôde ser ingerido")
    return target
