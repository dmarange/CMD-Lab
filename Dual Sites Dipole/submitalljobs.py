#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


JOB_PATTERNS = [
    {
        "label": "bader",
        "script": "bader_slurm.sh",
        "runner": "bader_single_point.py",
        "done_markers": ("relaxed_pbe.e", "OUTCAR", "CHGCAR", "AECCAR0", "AECCAR2"),
    },
    {
        "label": "cohp",
        "script": "cohp_slurm.sh",
        "runner": "lobster_single_point.py",
        "done_markers": ("relaxed_pbe.e", "OUTCAR", "WAVECAR"),
    },
    {
        "label": "vaspGeoRelax",
        "script": "slurm.sh",
        "runner": "run.py",
        "done_markers": ("final.e", "OUTCAR", "CONTCAR"),
    },
    {
        "label": "legacy",
        "script": "bash.slurm",
        "runner": "job.py",
        "done_markers": ("final.e", "OUTCAR"),
    },
]
ADSORBATE_DIRS = ("clean", "no2", "no2r", "no2co2")

def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Recursively submit Slurm jobs found under one or more roots. "
            "By default, scan ./runs next to this script. "
            "Use adsorbate flags such as --no2 to submit one chunk at a time."
        )
    )
    parser.add_argument(
        "roots",
        nargs="*",
        default=["runs"],
        help=(
            "Root directories to scan, relative to this script or as absolute paths "
            "(default: ./runs)."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Submit even if output files suggest the job may already have run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the jobs that would be submitted without calling sbatch.",
    )
    parser.add_argument(
        "--job-type",
        choices=["all", "bader", "cohp", "vaspGeoRelax", "legacy"],
        default="all",
        help="Restrict submission to one job type.",
    )
    adsorbate_group = parser.add_mutually_exclusive_group()
    adsorbate_group.add_argument(
        "--clean",
        action="store_true",
        help="Submit only jobs in clean subdirectories under runs.",
    )
    adsorbate_group.add_argument(
        "--no2",
        action="store_true",
        help="Submit only jobs in no2 subdirectories under runs.",
    )
    adsorbate_group.add_argument(
        "--no2r",
        action="store_true",
        help="Submit only jobs in no2r subdirectories under runs.",
    )
    adsorbate_group.add_argument(
        "--no2co2",
        action="store_true",
        help="Submit only jobs in no2co2 subdirectories under runs.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=script_dir,
        help="Base directory used to resolve relative roots (default: script directory).",
    )
    return parser.parse_args()


def resolve_root(root_arg: str, base_dir: Path) -> Path:
    root_path = Path(root_arg)
    if root_path.is_absolute():
        return root_path
    return (base_dir / root_path).resolve()


def should_skip(job_dir: Path, done_markers: tuple[str, ...], force: bool) -> bool:
    if force:
        return False
    return all((job_dir / marker).exists() for marker in done_markers)


def get_selected_adsorbates(args: argparse.Namespace) -> set[str] | None:
    for adsorbate in ADSORBATE_DIRS:
        if getattr(args, adsorbate):
            return {adsorbate}
    return None


def iter_job_dirs(root_dir: Path):
    yield root_dir
    yield from sorted(path for path in root_dir.rglob("*") if path.is_dir())


def submit_job(job_dir: Path, slurm_script: str, dry_run: bool) -> bool:
    print(f"Submitting job in {job_dir} with {slurm_script}")
    if dry_run:
        return True

    try:
        subprocess.run(["sbatch", slurm_script], cwd=job_dir, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Failed to submit in {job_dir}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    args = parse_args()
    base_dir = args.base_dir.resolve()
    selected_adsorbates = get_selected_adsorbates(args)

    selected_patterns = [
        pattern for pattern in JOB_PATTERNS
        if args.job_type in ("all", pattern["label"])
    ]

    submitted = 0
    skipped = 0
    failed = 0

    for root_arg in args.roots:
        root_dir = resolve_root(root_arg, base_dir)
        if not root_dir.is_dir():
            print(f"Skipping missing root: {root_dir}", file=sys.stderr)
            continue

        for job_dir in iter_job_dirs(root_dir):
            if selected_adsorbates is not None and job_dir.name not in selected_adsorbates:
                continue

            filenames = {child.name for child in job_dir.iterdir() if child.is_file()}

            for pattern in selected_patterns:
                slurm_script = pattern["script"]
                runner = pattern["runner"]

                if slurm_script not in filenames or runner not in filenames:
                    continue

                if should_skip(job_dir, pattern["done_markers"], args.force):
                    print(f"Skipping existing {pattern['label']} job in {job_dir}")
                    skipped += 1
                    break

                if submit_job(job_dir, slurm_script, args.dry_run):
                    submitted += 1
                else:
                    failed += 1
                break

    print(
        f"\nSummary: submitted={submitted}, skipped={skipped}, failed={failed}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
