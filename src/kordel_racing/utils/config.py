"""Leitura e validação da configuração."""

from pathlib import Path

import yaml


def load_settings(path: str | Path = "config/settings.yaml") -> dict:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuração não encontrada: {config_path}")
    with config_path.open(encoding="utf-8") as file:
        settings = yaml.safe_load(file)
    if not settings or "openf1" not in settings or "pipeline" not in settings:
        raise ValueError("Configuração deve conter as seções openf1 e pipeline")
    return settings
