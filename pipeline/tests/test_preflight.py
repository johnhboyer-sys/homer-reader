import subprocess
import sys
from pathlib import Path

import yaml

from homer_pipeline.preflight import WorkManifest, _validate_manifest_schema


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "pipeline" / "tests" / "fixtures" / "preflight"
MANIFESTS = ROOT / "manifests"


def _load_manifest(name: str) -> dict:
    return yaml.safe_load((MANIFESTS / name).read_text(encoding="utf-8"))


def _schema_problems(data: dict, name: str = "Euthyphro.yaml") -> list[str]:
    manifest = WorkManifest(work_id=data["work"]["id"], path=MANIFESTS / name, data=data)
    problems: list = []
    _validate_manifest_schema(manifest, problems)
    return [message for _work, _file, message in problems]


def _run_preflight(name: str) -> subprocess.CompletedProcess[str]:
    fixture = FIXTURES / name
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "homer_pipeline.preflight",
            str(fixture / "data"),
            str(fixture / "manifests"),
        ],
        cwd=ROOT / "pipeline",
        text=True,
        capture_output=True,
        check=False,
    )


def test_preflight_valid_fixture_passes():
    result = _run_preflight("valid")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "preflight ok:" in result.stdout


def test_preflight_broken_fixture_reports_bekker_order_and_dangling_reference():
    result = _run_preflight("broken")

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Greek Bekker lines are out of order" in output
    assert "chapter '1' has dangling Bekker anchor 1094a5" in output


def test_preflight_schema_accepts_real_homer_manifests():
    # Verse-line manifests: no bekker_range/chapters/section_spine; books bounded
    # by book.line refs; expected_line_gaps use {book, after, next}.
    assert _schema_problems(_load_manifest("Iliad.yaml"), "Iliad.yaml") == []
    assert _schema_problems(_load_manifest("Odyssey.yaml"), "Odyssey.yaml") == []


def test_preflight_schema_rejects_bad_verse_ref():
    data = _load_manifest("Iliad.yaml")
    data["books"][0]["start"] = "1a1"  # Bekker-shaped, not book.line
    problems = _schema_problems(data, "Iliad.yaml")
    assert any("books[0].start must be a verse book.line ref" in p for p in problems)
