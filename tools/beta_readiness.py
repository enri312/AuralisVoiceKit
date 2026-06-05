"""Beta readiness checklist for AuralisVoiceKit.

The report is intentionally conservative: the project can be ready for real
pilots while still blocked for a public beta until real-world evidence exists.
The default Markdown target is BETA_CHECKLIST.md. Use --evidence with pilot
JSON artifacts to close blockers without copying private content into Markdown.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


BETA_MIN_WORD_ACCURACY = 0.75


def build_beta_readiness_report(
    root: str | Path = ".",
    evidence_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Build a deterministic report with beta blockers and known issues."""

    workspace = Path(root).resolve()
    gate = _load_stability_gate(workspace).build_report(workspace)
    findings = _read_text(workspace / "PILOT_FINDINGS.md")
    evidence_reports = _load_evidence_reports(workspace, evidence_paths or [])
    checks = [
        _gate_check(gate),
        _evidence_or_terms_check(
            name="windows_wasapi_capture",
            title="Windows WASAPI capture pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_windows_wasapi_capture_evidence,
            required_terms=(
                "Windows WASAPI captura real a 48000 Hz",
                "Piloto manual: `passed=true`",
                "Check `capture-test:wasapi`: `ok`",
            ),
            next_action="Keep the passing Windows WASAPI pilot documented with sample rate and no stored audio.",
        ),
        _evidence_or_terms_check(
            name="real_transcription_quality",
            title="Real transcription quality pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_real_transcription_quality_evidence,
            required_terms=(
                "Real transcription requested: True",
                "Quality gate passed: `true`",
            ),
            next_action=(
                "Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, "
                "--expected-text or --expected-text-file, and a meaningful --min-word-accuracy."
            ),
        ),
        _evidence_or_terms_check(
            name="system_output_audible",
            title="Audible system output pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_system_output_audible_evidence,
            required_terms=(
                "Real audio requested: True",
                "Operator confirmation status: confirmed",
            ),
            next_action=(
                "Run tools/output_pilot.py --speak --operator-present --confirm-audible "
                "with a human operator and record only sanitized findings."
            ),
        ),
        _evidence_or_terms_check(
            name="ubuntu_linux_capture",
            title="Ubuntu/Linux capture pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_ubuntu_linux_capture_evidence,
            required_terms=(
                "Sistema: Ubuntu/Linux",
                "Piloto manual: `passed=true`",
            ),
            next_action="Run the manual capture pilot on Ubuntu/Linux with real hardware and sanitized artifacts.",
        ),
        _evidence_or_terms_check(
            name="macos_capture",
            title="macOS capture pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_macos_capture_evidence,
            required_terms=(
                "Sistema: macOS",
                "Piloto manual: `passed=true`",
            ),
            next_action="Run the manual capture pilot on macOS with real hardware and sanitized artifacts.",
        ),
    ]
    blockers = [check for check in checks if check["blocker"] and not check["ok"]]
    known_issues = _known_issues(findings)
    ready_for_beta = not blockers

    return {
        "project": "AuralisVoiceKit",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "version": gate["version"],
        "status": "beta-ready" if ready_for_beta else "pilot",
        "ready_for_beta": ready_for_beta,
        "gate": {
            "stage": gate["stage"],
            "ready_for_real_world_pilots": gate["ready_for_real_world_pilots"],
            "ready_for_stable_release": gate["ready_for_stable_release"],
            "stable_blockers": gate["stable_blockers"],
        },
        "checks": checks,
        "blockers": [check["name"] for check in blockers],
        "evidence": {
            "files": [_safe_evidence_source(report["_evidence_path"]) for report in evidence_reports],
            "count": len(evidence_reports),
        },
        "known_issues": known_issues,
        "next_actions": [check["next_action"] for check in checks if not check["ok"]],
        "notes": (
            "Beta requires documented real-world evidence. Dry-runs prove safety paths, "
            "but they do not replace real transcription, audible output or cross-platform capture pilots."
        ),
    }


def write_beta_readiness_report(report: dict[str, Any], output: str | Path) -> None:
    """Write JSON or Markdown depending on the output extension."""

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        output_path.write_text(format_markdown(report), encoding="utf-8")


def format_markdown(report: dict[str, Any]) -> str:
    """Format a report as a public-safe Markdown checklist."""

    lines = [
        "# Checklist de beta",
        "",
        "Este documento se genera con `tools\\beta_readiness.py`. No debe incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Estado: `{report['status']}`",
        f"- Listo para beta: `{str(report['ready_for_beta']).lower()}`",
        f"- Gate de pilotos reales: `{str(report['gate']['ready_for_real_world_pilots']).lower()}`",
        f"- Evidencias JSON: `{report['evidence']['count']}`",
        "",
        "## Bloqueadores para beta",
        "",
    ]
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- Ninguno.")

    lines.extend(
        [
            "",
            "## Checklist",
            "",
        ]
    )
    for check in report["checks"]:
        marker = "x" if check["ok"] else " "
        blocker_label = "blocker" if check["blocker"] else "informativo"
        lines.append(f"- [{marker}] `{check['name']}` ({blocker_label}) - {check['title']}")
        if not check["ok"]:
            lines.append(f"  - Accion: {check['next_action']}")
            if check["missing_terms"]:
                terms = ", ".join(_format_missing_term(term) for term in check["missing_terms"])
                lines.append(f"  - Evidencia faltante: {terms}")
        if check["evidence_sources"]:
            sources = ", ".join(f"`{source}`" for source in check["evidence_sources"])
            lines.append(f"  - Evidencia JSON: {sources}")

    lines.extend(
        [
            "",
            "## Bugs conocidos",
            "",
        ]
    )
    if report["known_issues"]:
        for issue in report["known_issues"]:
            lines.append(f"- `{issue['id']}`: {issue['status']} - {issue['summary']}")
    else:
        lines.append("- No hay bugs criticos documentados; los blockers actuales son pilotos pendientes.")

    lines.extend(
        [
            "",
            "## Siguientes acciones",
            "",
        ]
    )
    for action in report["next_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the AuralisVoiceKit beta readiness checklist.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output", help="write report to .md or .json, for example BETA_CHECKLIST.md")
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="pilot JSON evidence file or directory; can be passed more than once",
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="exit with code 1 when beta blockers remain",
    )
    args = parser.parse_args(argv)

    report = build_beta_readiness_report(args.root, evidence_paths=args.evidence)
    if args.output:
        write_beta_readiness_report(report, args.output)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.output:
        print(format_markdown(report))

    if args.fail_on_blockers and not report["ready_for_beta"]:
        return 1
    return 0


def _load_stability_gate(workspace: Path):
    path = workspace / "tools" / "stability_gate.py"
    spec = importlib.util.spec_from_file_location("auralis_stability_gate_for_beta", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load stability gate from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _gate_check(gate: dict[str, Any]) -> dict[str, Any]:
    ok = bool(gate["ready_for_real_world_pilots"])
    return {
        "name": "stability_gate_pilot",
        "title": "Stability gate allows real-world pilots",
        "ok": ok,
        "blocker": True,
        "missing_terms": [] if ok else ["ready_for_real_world_pilots"],
        "evidence_sources": [],
        "next_action": "Run tools/stability_gate.py --min-stage pilot and fix any missing checks.",
    }


def _terms_check(
    *,
    name: str,
    title: str,
    blocker: bool,
    content: str,
    required_terms: tuple[str, ...],
    next_action: str,
) -> dict[str, Any]:
    missing_terms = [term for term in required_terms if term not in content]
    return {
        "name": name,
        "title": title,
        "ok": not missing_terms,
        "blocker": blocker,
        "missing_terms": missing_terms,
        "evidence_sources": [],
        "next_action": next_action,
    }


def _evidence_or_terms_check(
    *,
    name: str,
    title: str,
    blocker: bool,
    content: str,
    evidence_reports: list[dict[str, Any]],
    evidence_predicate,
    required_terms: tuple[str, ...],
    next_action: str,
) -> dict[str, Any]:
    evidence_sources = [
        _safe_evidence_source(report["_evidence_path"]) for report in evidence_reports if evidence_predicate(report)
    ]
    if evidence_sources:
        return {
            "name": name,
            "title": title,
            "ok": True,
            "blocker": blocker,
            "missing_terms": [],
            "evidence_sources": evidence_sources,
            "next_action": next_action,
        }
    return _terms_check(
        name=name,
        title=title,
        blocker=blocker,
        content=content,
        required_terms=required_terms,
        next_action=next_action,
    )


def _load_evidence_reports(workspace: Path, evidence_paths: list[str | Path]) -> list[dict[str, Any]]:
    reports = []
    for evidence_path in evidence_paths:
        path = Path(evidence_path)
        if not path.is_absolute():
            path = workspace / path
        for report_path in _expand_evidence_path(path):
            try:
                payload = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid evidence JSON: {report_path.name}") from exc
            if isinstance(payload, dict):
                payload = dict(payload)
                payload["_evidence_path"] = str(report_path)
                reports.append(payload)
    return reports


def _expand_evidence_path(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(item for item in path.rglob("*.json") if _looks_like_pilot_report(item))
    if not path.exists():
        raise ValueError(f"Evidence path was not found: {path.name}")
    return [path]


def _looks_like_pilot_report(path: Path) -> bool:
    return path.name in {
        "manual-pilot-report.json",
        "output-pilot-report.json",
        "transcription-pilot-report.json",
    }


def _is_windows_wasapi_capture_evidence(report: dict[str, Any]) -> bool:
    return (
        report.get("system") == "Windows"
        and report.get("capture_backend") == "wasapi"
        and report.get("hardware_capture_tested") is True
        and report.get("passed") is True
    )


def _is_ubuntu_linux_capture_evidence(report: dict[str, Any]) -> bool:
    system = str(report.get("system", "")).lower()
    return (
        system in {"linux", "ubuntu/linux", "ubuntu"}
        and report.get("hardware_capture_tested") is True
        and report.get("passed") is True
    )


def _is_macos_capture_evidence(report: dict[str, Any]) -> bool:
    system = str(report.get("system", "")).lower()
    return (
        system in {"darwin", "macos", "mac"}
        and report.get("hardware_capture_tested") is True
        and report.get("passed") is True
    )


def _is_system_output_audible_evidence(report: dict[str, Any]) -> bool:
    return (
        report.get("backend") == "system"
        and report.get("real_audio_requested") is True
        and report.get("operator_confirmation_status") == "confirmed"
        and report.get("passed") is True
    )


def _is_real_transcription_quality_evidence(report: dict[str, Any]) -> bool:
    quality = report.get("quality", {})
    return (
        report.get("real_transcription_requested") is True
        and report.get("audio_confirmed_non_sensitive") is True
        and report.get("passed") is True
        and isinstance(quality, dict)
        and quality.get("enabled") is True
        and quality.get("passed") is True
        and float(quality.get("min_word_accuracy") or 0.0) >= BETA_MIN_WORD_ACCURACY
    )


def _safe_evidence_source(path: str) -> str:
    evidence_path = Path(path)
    parts = evidence_path.parts
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return evidence_path.name


def _known_issues(findings: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if "windows_audio:sample_rate" in findings and "reintento con `--sample-rate 48000` paso correctamente" in findings:
        issues.append(
            {
                "id": "windows-wasapi-sample-rate",
                "status": "resolved",
                "summary": "Initial WASAPI invalid sample rate was fixed by exposing --sample-rate and passing at 48000 Hz.",
            }
        )
    return issues


def _format_missing_term(term: str) -> str:
    if "`" in term:
        return term
    return f"`{term}`"


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
