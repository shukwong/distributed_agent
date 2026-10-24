"""Strict validation for the public six-ledger report contract.

This validates structure and internal grounding, not biological truth.
"""
from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator


class BuildError(RuntimeError):
    """A report could not be generated or validated."""


LEDGER_HEADINGS = {
    "evidence": "Evidence JSONL",
    "references": "References JSONL",
    "biological_findings": "Biological Findings JSONL",
    "literature_comparisons": "Literature Comparisons JSONL",
    "pathways": "Pathways JSONL",
    "cell_type_specificity": "Cell Type Specificity JSONL",
}
SCHEMA_RESOURCE = "schemas/structured_appendix.schema.json"


def appendix_schema() -> dict[str, Any]:
    return json.loads(files(__package__).joinpath(SCHEMA_RESOURCE).read_text())


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant {value}")


def parse_structured_appendix(report: str) -> dict[str, list[dict[str, Any]]]:
    """Read exactly six ordered JSONL blocks, then validate all internal links."""
    marker = re.compile(r"(?m)^#{1,6}[ \t]+Structured Appendix[ \t]*$")
    markers = list(marker.finditer(report))
    if len(markers) != 1:
        raise BuildError("expected exactly one Structured Appendix Markdown heading")
    prose = report[:markers[0].start()]
    for title in ("Key Biological Findings", "Missed-Finding Audit"):
        if not re.search(r"(?m)^#{1,6}[ \t]+" + re.escape(title) + r"[ \t]*$", prose):
            raise BuildError(f"missing narrative section: {title}")
    appendix_text = report[markers[0].end():]
    pattern = re.compile(
        r"(?m)^(?:#{1,6}[ \t]+)?([^\n]+?)[ \t]*\n[ \t]*\n?"
        r"```jsonl[ \t]*\n(.*?)^```[ \t]*$",
        re.DOTALL,
    )
    blocks = list(pattern.finditer(appendix_text))
    expected = list(LEDGER_HEADINGS.values())
    actual = [match.group(1).strip() for match in blocks]
    if actual != expected or len(re.findall(r"(?m)^```[^\n]*$", appendix_text)) != 12:
        raise BuildError(f"expected six ordered JSONL headings {expected}; found {actual}")
    appendix = {}
    for (key, title), match in zip(LEDGER_HEADINGS.items(), blocks):
        rows = []
        for number, line in enumerate(match.group(2).splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line, object_pairs_hook=_unique_object,
                                       parse_constant=_invalid_constant))
            except (ValueError, TypeError) as exc:
                raise BuildError(f"{title} line {number}: {exc}") from exc
        appendix[key] = rows
    validate_appendix(appendix)
    known = set()
    for key, field in (("evidence", "evidence_id"), ("references", "ref_id"),
                       ("biological_findings", "finding_id"),
                       ("literature_comparisons", "comparison_id")):
        known.update(row[field] for row in appendix[key])
    # Models commonly group citations, e.g. [E001, E002]. Validate every
    # numbered ID inside a bracket while leaving ordinary Markdown labels alone.
    cited = {
        citation
        for group in re.findall(r"\[([^\[\]\n]+)\]", prose)
        for citation in re.findall(r"(?<![A-Za-z0-9_])(?:LC|F|E|R)\d+(?![A-Za-z0-9_])", group)
    }
    if cited - known:
        raise BuildError(f"unresolved narrative citations: {sorted(cited - known)}")
    return appendix


def validate_appendix(appendix: dict[str, Any]) -> None:
    """Reject malformed rows, duplicate IDs, dangling links, and expanded views."""
    errors = sorted(Draft202012Validator(appendix_schema()).iter_errors(appendix),
                    key=lambda error: str(list(error.path)))
    if errors:
        detail = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:10])
        raise BuildError(f"appendix schema validation failed: {detail}")
    indices = {}
    for key, field in (("evidence", "evidence_id"), ("references", "ref_id"),
                       ("biological_findings", "finding_id"),
                       ("literature_comparisons", "comparison_id")):
        indices[key] = {row[field]: row for row in appendix[key]}
        if len(indices[key]) != len(appendix[key]):
            raise BuildError(f"duplicate {field} in {key}")

    def check_links(row: dict, field: str, pool: dict, context: str) -> None:
        missing = set(row.get(field, [])) - set(pool)
        if missing:
            raise BuildError(f"{context}: unresolved {field}: {sorted(missing)}")

    for key, rows in appendix.items():
        for i, row in enumerate(rows):
            context = f"{key}[{i}]"
            check_links(row, "evidence_ids", indices["evidence"], context)
            check_links(row, "ref_ids", indices["references"], context)
            check_links(row, "finding_ids", indices["biological_findings"], context)
            if "finding_id" in row and key == "literature_comparisons":
                check_links({"finding_ids": [row["finding_id"]]}, "finding_ids",
                            indices["biological_findings"], context)
    literature_statuses = {
        "supports_known_mechanism", "extends_known_mechanism", "refines_cell_type_context",
        "contradicts_expected_relationship", "opposes_reported_direction", "literature_ambiguous",
    }
    for row in appendix["biological_findings"]:
        if row["literature_status"] in literature_statuses and not row["ref_ids"]:
            raise BuildError(f"{row['finding_id']}: literature-based finding requires ref_ids")
    # Literature comparisons may attach additional globally validated sources;
    # only pathway/cell-type views must be subsets of the cited findings.
    for key in ("pathways", "cell_type_specificity"):
        for row in appendix[key]:
            finding_ids = row.get("finding_ids", [row.get("finding_id")])
            findings = [indices["biological_findings"][item] for item in finding_ids]
            for field in ("evidence_ids", "ref_ids", "genes"):
                if field not in row:
                    continue
                allowed = {value for finding in findings for value in (finding.get(field) or [])}
                extras = set(row[field] or []) - allowed
                if extras:
                    raise BuildError(f"{key}: {field} adds items absent from cited findings: {sorted(extras)}")
            contexts = {value for finding in findings for value in (finding["cell_types"] or [])}
            cells = row.get("cell_type")
            cells = [cells] if isinstance(cells, str) else (cells or [])
            if set(cells) - contexts:
                raise BuildError(f"{key}: cell_type absent from cited findings")
