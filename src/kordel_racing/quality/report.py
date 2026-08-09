"""Estruturas e persistência dos relatórios de qualidade."""

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class QualityIssue:
    """Resultado de uma regra que encontrou registros afetados."""

    rule: str
    message: str
    affected_rows: int
    sample: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class QualityResult:
    """Resultado completo e serializável da validação de um dataset."""

    dataset: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[QualityIssue] = field(default_factory=list)
    warnings: list[QualityIssue] = field(default_factory=list)
    evaluated_rules: list[str] = field(default_factory=list)
    executed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def to_dict(
        self,
        session_key: int | None = None,
        rule_severities: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("evaluated_rules")
        payload["session_key"] = session_key
        payload["error_count"] = len(self.errors)
        payload["warning_count"] = len(self.warnings)
        issues = {issue.rule: "ERROR" for issue in self.errors}
        issues.update({issue.rule: "WARNING" for issue in self.warnings})
        payload["rule_results"] = [
            {
                "rule": rule,
                "severity": severity,
                "status": issues.get(rule, "PASS" if rule in self.evaluated_rules else "NOT_EVALUATED"),
            }
            for rule, severity in (rule_severities or {}).items()
        ]
        return payload


def save_quality_report(
    result: QualityResult,
    output_dir: str | Path,
    session_key: int,
) -> Path:
    """Salva um relatório JSON mesmo quando a validação falha."""

    target = Path(output_dir) / "quality"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{result.dataset}_quality_{session_key}.json"
    from kordel_racing.quality.contracts import LAPS_RULE_SEVERITIES

    rule_severities = LAPS_RULE_SEVERITIES if result.dataset == "laps" else {}
    path.write_text(
        json.dumps(
            result.to_dict(session_key, rule_severities),
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    return path
