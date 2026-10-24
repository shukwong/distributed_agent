"""Compute two deterministic source reports from explicitly synthetic measurements.

This is a software integration fixture, not an agent or a biological experiment.
No statistical significance or mechanism is inferred from these invented values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


SOURCE = Path(__file__).with_name("synthetic_observations.csv")
HEADINGS = ("Evidence JSONL", "References JSONL", "Biological Findings JSONL", "Literature Comparisons JSONL", "Pathways JSONL", "Cell Type Specificity JSONL")


def generate(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    paths = []
    for target in sorted({row["target"] for row in rows}):
        selected = [row for row in rows if row["target"] == target]
        groups = {group: [float(row["readout"]) for row in selected if row["group"] == group] for group in ("control", "perturbed")}
        controls, perturbed = mean(groups["control"]), mean(groups["perturbed"])
        difference = perturbed - controls
        statistics = f"control_n=3; perturbed_n=3; control_mean={controls:g}; perturbed_mean={perturbed:g}; mean_difference={difference:g}; source_sha256={digest}"
        summary = f"Synthetic fixture {target} has a readout mean difference of {difference:g} units (perturbed minus control)."
        caveat = "Entirely synthetic engineering fixture; no biological samples, significance test, cancer/aging association, or mechanism."
        evidence = [{"evidence_id": "E001", "evidence_slug": "synthetic_mean_difference", "cell_type": None, "genes": None, "statistics": statistics, "description": "Arithmetic computed from the six synthetic CSV rows assigned to this target."}]
        references = [{"ref_id": "R001", "ref_slug": "synthetic_input_fixture", "source": "Included synthetic CSV", "source_type": "other", "citation": "examples/bootstrap/synthetic_observations.csv; invented numbers for software validation only.", "url": "synthetic_observations.csv", "description": "Local source data, not a scientific publication; SHA256=" + digest}]
        findings = [{"finding_id": "F001", "finding_type": "other", "summary": summary, "why_it_matters": "Tests retrieval and target-scoped evidence resolution for changed and unchanged synthetic signals.", "cell_types": None, "genes": None, "comparators": None, "direction": "increased" if difference > 0 else "unchanged", "confidence": "high", "evidence_ids": ["E001"], "ref_ids": ["R001"], "literature_status": "not_assessed_synthetic_fixture", "main_caveats": caveat}]
        report = f"# Synthetic engineering report: {target}\n\n{caveat}\n\n## Key Biological Findings\n\n[F001] {summary} [E001] [R001] This required upstream section name does not imply biological evidence.\n\n## Direct Dataset Observations\n\n[E001] {statistics}\n\n## Literature Context\n\nNo literature claims; [R001] is the included synthetic source file.\n\n## Integrated Interpretation\n\nOnly deterministic arithmetic is evaluated.\n\n## Caveats\n\n{caveat}\n\n## References\n\n[R001] synthetic_observations.csv; SHA256={digest}\n\n## Missed-Finding Audit\n\nAll six rows for this target are included. No mechanisms or statistical significance are evaluated.\n\n## Structured Appendix\n\n"
        for heading, ledger in zip(HEADINGS, (evidence, references, findings, [], [], [])):
            report += f"### {heading}\n\n```jsonl\n" + "".join(json.dumps(row, sort_keys=True) + "\n" for row in ledger) + "```\n\n"
        path = output_dir / f"{target}.md"
        if path.exists():
            raise FileExistsError(f"refusing to replace {path}")
        path.write_text(report, encoding="utf-8")
        paths.append(path)
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    for path in generate(args.output_dir):
        print(path)
