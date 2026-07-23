"""Pipeline local completo: Bronze, Silver e Gold."""

import logging

from kordel_racing.api.client import OpenF1Client
from kordel_racing.bronze.ingestion import ingest_session
from kordel_racing.gold.metrics import create_gold_tables
from kordel_racing.silver.transformations import build_silver
from kordel_racing.utils.config import load_settings
from kordel_racing.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def run_pipeline(config_path: str = "config/settings.yaml", **overrides: object) -> None:
    configure_logging()
    settings = load_settings(config_path)
    pipeline = settings["pipeline"] | {key: value for key, value in overrides.items() if value is not None}
    api = settings["openf1"]
    client = OpenF1Client(api["base_url"], api["timeout_seconds"])
    bronze = ingest_session(
        client, pipeline["meeting_key"], pipeline["session_key"], pipeline["endpoints"], pipeline["output_dir"]
    )
    silver = build_silver(bronze, pipeline["output_dir"], pipeline["session_key"])
    LOGGER.info("Camada Silver concluída: %s", silver)
    tables = create_gold_tables(silver, pipeline["output_dir"], pipeline["session_key"])
    LOGGER.info("Camada Gold concluída: %s tabelas", len(tables))
    LOGGER.info("Pipeline finalizado com sucesso.")
