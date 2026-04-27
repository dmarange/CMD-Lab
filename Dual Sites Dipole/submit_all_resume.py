#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import shutil
import subprocess
import sys
from pathlib import Path


ADSORBATE_DIRS = ("clean", "no2", "no2r", "no2co2")
RUNNER_TEMPLATE = "run_restart.template"
SLURM_TEMPLATE = "slurm__restart.template"
RUNNER_SCRIPT = "run_restart.py"
SLURM_SCRIPT = "slurm__restart.sh"
ARCHIVE_PREFIX = "resume_old_files"


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Submit restart jobs only for unfinished VASP relaxation directories. "
            "Pass a single root such as 'runs' to scan every metal-pair and "
            "adsorbate subdirectory below it. "
            "A job is considered complete if dft.energy/relaxed.traj exists or "
            "OUTCAR reports that the required accuracy was reached."
        ),
        epilog=(
            "Examples:\n"
            "  python submit_all_resume.py runs\n"
            "  python submit_all_resume.py --runs\n"
            "  python submit_all_resume.py runs --dry-run\n"
            "  python submit_all_resume.py --no2\n"
            "  python submit_all_resume.py runs --adsorbate no2r"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        "--adsorbate",
        choices=ADSORBATE_DIRS,
        help="Only consider leaf job directories with this name, for example no2r.",
    )
    adsorbate_group = parser.add_mutually_exclusive_group()
    adsorbate_group.add_argument(
        "--clean",
        action="store_true",
        help="Shortcut for --adsorbate clean.",
    )
    adsorbate_group.add_argument(
        "--no2",
        action="store_true",
        help="Shortcut for --adsorbate no2.",
    )
    adsorbate_group.add_argument(
        "--no2r",
        action="store_true",
        help="Shortcut for --adsorbate no2r.",
    )
    adsorbate_group.add_argument(
        "--no2co2",
        action="store_true",
        help="Shortcut for --adsorbate no2co2.",
    )
    parser.add_argument(
        "--runs",
        action="store_true",
        help=(
            "Compatibility flag for runs-style trees. This is already the default: "
            "the script recursively scans all metal-pair/adsorbate subdirectories."
        ),
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=script_dir,
        help="Base directory used to resolve relative roots (default: script directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print restart jobs that would be submitted without copying or calling sbatch.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Submit even if output files suggest the job is already complete.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing run_restart.py and slurm__restart.sh files.",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Do not move existing job files into a resume_old_files_* folder first.",
    )
    args = parser.parse_args()
    if args.adsorbate and any(getattr(args, adsorbate) for adsorbate in ADSORBATE_DIRS):
        parser.error("use either --adsorbate or an adsorbate shortcut flag, not both")
    return args


def selected_adsorbate(args: argparse.Namespace) -> str | None:
    for adsorbate in ADSORBATE_DIRS:
        if getattr(args, adsorbate):
            return adsorbate
    return args.adsorbate


def resolve_root(root_arg: str, base_dir: Path) -> Path:
    root_path = Path(root_arg)
    if root_path.is_absolute():
        return root_path
    return (base_dir / root_path).resolve()


def has_text(path: Path, text: str) -> bool:
    if not path.is_file():
        return False
    try:
        with path.open("r", errors="ignore") as handle:
            return any(text in line for line in handle)
    except OSError:
        return False


def nonempty_file(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def is_completed(job_dir: Path) -> bool:
    if nonempty_file(job_dir / "dft.energy") and nonempty_file(job_dir / "relaxed.traj"):
        return True
    return has_text(job_dir / "OUTCAR", "reached required accuracy")


def is_resumable(job_dir: Path) -> bool:
    return nonempty_file(job_dir / "CONTCAR")


def looks_like_job_dir(path: Path) -> bool:
    job_inputs = ("initial.traj", "POSCAR", "CONTCAR", "run.py", "slurm.sh")
    return any((path / name).exists() for name in job_inputs)


def next_archive_dir(job_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = job_dir / f"{ARCHIVE_PREFIX}_{timestamp}"
    suffix = 1
    while archive_dir.exists():
        archive_dir = job_dir / f"{ARCHIVE_PREFIX}_{timestamp}_{suffix}"
        suffix += 1
    return archive_dir


def archive_old_files(job_dir: Path, dry_run: bool) -> bool:
    children = [
        child for child in job_dir.iterdir()
        if not child.name.startswith(f"{ARCHIVE_PREFIX}_")
    ]
    if not children:
        return True

    archive_dir = next_archive_dir(job_dir)
    print(f"Moving old files in {job_dir} -> {archive_dir.name}")
    if dry_run:
        for child in children:
            print(f"Would move {child.name} -> {archive_dir.name}/{child.name}")
        print(f"Would restore CONTCAR -> {job_dir / 'CONTCAR'}")
        return True

    try:
        archive_dir.mkdir()
        for child in children:
            shutil.move(str(child), str(archive_dir / child.name))
        shutil.copy2(archive_dir / "CONTCAR", job_dir / "CONTCAR")
    except OSError as exc:
        print(f"Failed to archive old files in {job_dir}: {exc}", file=sys.stderr)
        return False
    return True


def iter_job_dirs(root_dir: Path, adsorbate: str | None):
    candidates = [root_dir]
    candidates.extend(sorted(path for path in root_dir.rglob("*") if path.is_dir()))
    for path in candidates:
        if adsorbate is not None and path.name != adsorbate:
            continue
        if looks_like_job_dir(path):
            yield path


def copy_restart_files(
    template_dir: Path,
    job_dir: Path,
    overwrite: bool,
    dry_run: bool,
) -> bool:
    copies = (
        (template_dir / RUNNER_TEMPLATE, job_dir / RUNNER_SCRIPT),
        (template_dir / SLURM_TEMPLATE, job_dir / SLURM_SCRIPT),
    )
    for src, dst in copies:
        if not src.is_file():
            print(f"Missing template: {src}", file=sys.stderr)
            return False
        if dst.exists() and not overwrite:
            continue
        if dry_run:
            print(f"Would copy {src.name} -> {dst}")
            continue
        shutil.copy2(src, dst)
    return True


def submit_job(job_dir: Path, dry_run: bool) -> bool:
    print(f"Submitting restart in {job_dir} with {SLURM_SCRIPT}")
    if dry_run:
        return True
    try:
        subprocess.run(["sbatch", SLURM_SCRIPT], cwd=job_dir, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Failed to submit restart in {job_dir}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    args = parse_args()
    base_dir = args.base_dir.resolve()
    adsorbate = selected_adsorbate(args)

    submitted = 0
    skipped_complete = 0
    skipped_not_resumable = 0
    archived = 0
    failed = 0

    for root_arg in args.roots:
        root_dir = resolve_root(root_arg, base_dir)
        if not root_dir.is_dir():
            print(f"Skipping missing root: {root_dir}", file=sys.stderr)
            continue

        for job_dir in iter_job_dirs(root_dir, adsorbate):
            if not args.force and is_completed(job_dir):
                print(f"Skipping complete job in {job_dir}")
                skipped_complete += 1
                continue

            if not is_resumable(job_dir):
                print(f"Skipping non-resumable job without non-empty CONTCAR in {job_dir}")
                skipped_not_resumable += 1
                continue

            if not args.no_archive:
                if not archive_old_files(job_dir, args.dry_run):
                    failed += 1
                    continue
                archived += 1

            if not copy_restart_files(base_dir, job_dir, args.overwrite, args.dry_run):
                failed += 1
                continue

            if submit_job(job_dir, args.dry_run):
                submitted += 1
            else:
                failed += 1

    print(
        "\nSummary: "
        f"submitted={submitted}, "
        f"skipped_complete={skipped_complete}, "
        f"skipped_not_resumable={skipped_not_resumable}, "
        f"archived={archived}, "
        f"failed={failed}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
