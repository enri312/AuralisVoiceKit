"""Release batch guard for alpha tags."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable, Sequence


DEFAULT_THRESHOLD = 5

GitRunner = Callable[[Path, Sequence[str]], str]


def run_git(root: Path, args: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _parse_oneline(output: str) -> list[dict[str, str]]:
    commits: list[dict[str, str]] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if " " in stripped:
            commit_hash, subject = stripped.split(" ", 1)
        else:
            commit_hash, subject = stripped, ""
        commits.append({"hash": commit_hash, "subject": subject})
    return commits


def _latest_tag(root: Path, runner: GitRunner) -> str | None:
    try:
        return runner(root, ("describe", "--tags", "--abbrev=0")) or None
    except subprocess.CalledProcessError:
        return None


def build_release_batch_status(
    root: Path,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    runner: GitRunner = run_git,
) -> dict[str, object]:
    if threshold < 1:
        raise ValueError("threshold must be >= 1")

    latest_tag = _latest_tag(root, runner)
    if latest_tag:
        log_args = ("log", f"{latest_tag}..HEAD", "--oneline")
        compare_command = f"git log {latest_tag}..HEAD --oneline"
    else:
        log_args = ("log", "--oneline")
        compare_command = "git log --oneline"

    commits = _parse_oneline(runner(root, log_args))
    commit_count = len(commits)
    remaining = max(threshold - commit_count, 0)
    ready = commit_count >= threshold

    return {
        "project": "AuralisVoiceKit",
        "latest_tag": latest_tag,
        "threshold": threshold,
        "commit_count": commit_count,
        "remaining": remaining,
        "ready_for_tag": ready,
        "should_create_release": ready,
        "compare_command": compare_command,
        "policy": {
            "tag_every_publishable_commits": threshold,
            "allows_explicit_user_override": True,
            "creates_github_release_each_improvement": False,
        },
        "next_action_es": (
            "Ya corresponde preparar tag y GitHub Release."
            if ready
            else f"No crear tag todavia; faltan {remaining} mejora(s) publicable(s)."
        ),
        "next_action_en": (
            "Prepare the tag and GitHub Release."
            if ready
            else f"Do not tag yet; {remaining} publishable improvement(s) remaining."
        ),
        "commits": commits,
    }


def _format_text(report: dict[str, object]) -> str:
    latest_tag = report["latest_tag"] or "none"
    lines = [
        "AuralisVoiceKit release batch status",
        f"Latest tag: {latest_tag}",
        f"Commits since latest tag: {report['commit_count']}/{report['threshold']}",
        f"Ready for tag: {str(report['ready_for_tag']).lower()}",
        f"Compare command: {report['compare_command']}",
        f"Next action: {report['next_action_es']}",
    ]
    commits = report.get("commits", [])
    if commits:
        lines.append("Commits:")
        for commit in commits:
            lines.append(f"  - {commit['hash']} {commit['subject']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--fail-if-not-ready",
        action="store_true",
        help="Return exit code 1 when fewer than threshold commits are pending.",
    )
    args = parser.parse_args(argv)

    report = build_release_batch_status(args.root, threshold=args.threshold)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_text(report))

    if args.fail_if_not_ready and not report["ready_for_tag"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
