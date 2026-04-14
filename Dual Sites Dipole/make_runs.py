#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ADSORBATE_DIRS = ("clean", "no2", "no2r", "no2co2")
TEMPLATE_MAP = {
    "run.template": "run.py",
    "slurm.template": "slurm.sh",
}


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Create a runs/ directory with one metal-pair directory per shared pair, "
            "and adsorbate subdirectories containing initial.traj, run.py, and slurm.sh."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=script_dir,
        help=(
            "Directory containing trajectories/ plus run.template and slurm.template "
            "(default: script directory)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=script_dir / "runs",
        help="Directory to create for the generated run tree (default: %(default)s).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing destination files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without creating files.",
    )
    return parser.parse_args()


def extract_pair_name(traj_path: Path) -> str:
    parts = traj_path.stem.split("-")
    if len(parts) < 3:
        raise ValueError(f"Cannot extract metal pair from {traj_path.name}")
    return f"{parts[0]}-{parts[1]}"


def load_adsorbate_map(directory: Path) -> dict[str, Path]:
    pair_to_file: dict[str, Path] = {}
    for traj_path in sorted(directory.glob("*.traj")):
        pair_name = extract_pair_name(traj_path)
        if pair_name in pair_to_file:
            raise ValueError(
                f"Duplicate pair '{pair_name}' in {directory}: "
                f"{pair_to_file[pair_name].name}, {traj_path.name}"
            )
        pair_to_file[pair_name] = traj_path
    return pair_to_file


def ensure_sources(root: Path) -> None:
    trajectories_dir = root / "trajectories"
    missing_paths = [
        trajectories_dir / name
        for name in ADSORBATE_DIRS
        if not (trajectories_dir / name).is_dir()
    ]
    missing_paths.extend(
        root / src_name for src_name in TEMPLATE_MAP if not (root / src_name).is_file()
    )
    if missing_paths:
        formatted = "\n".join(f"  {path}" for path in missing_paths)
        raise FileNotFoundError(f"Missing required inputs:\n{formatted}")


def copy_file(src: Path, dst: Path, overwrite: bool, dry_run: bool) -> None:
    if dst.exists() and not overwrite:
        print(f"skip: {dst}")
        return
    if dry_run:
        print(f"copy: {src} -> {dst}")
        return
    shutil.copy2(src, dst)
    print(f"copy: {src.name} -> {dst}")


def maybe_mkdir(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"mkdir: {path}")
        return
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    trajectories_dir = root / "trajectories"
    output_dir = args.output_dir.resolve()

    try:
        ensure_sources(root)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        adsorbate_maps = {
            adsorbate: load_adsorbate_map(trajectories_dir / adsorbate)
            for adsorbate in ADSORBATE_DIRS
        }
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    common_pairs = set.intersection(*(set(mapping) for mapping in adsorbate_maps.values()))
    if not common_pairs:
        print("Error: no common metal pairs found across all adsorbate folders.", file=sys.stderr)
        return 1

    print(f"Found {len(common_pairs)} common metal pairs.")
    for adsorbate, mapping in adsorbate_maps.items():
        extras = sorted(set(mapping) - common_pairs)
        if extras:
            print(f"Note: ignoring {len(extras)} extra pair(s) in {adsorbate}: {', '.join(extras)}")

    maybe_mkdir(output_dir, args.dry_run)

    for pair_name in sorted(common_pairs):
        pair_dir = output_dir / pair_name.lower()
        maybe_mkdir(pair_dir, args.dry_run)

        for adsorbate in ADSORBATE_DIRS:
            job_dir = pair_dir / adsorbate
            maybe_mkdir(job_dir, args.dry_run)

            copy_file(
                adsorbate_maps[adsorbate][pair_name],
                job_dir / "initial.traj",
                args.overwrite,
                args.dry_run,
            )

            for src_name, dst_name in TEMPLATE_MAP.items():
                copy_file(
                    root / src_name,
                    job_dir / dst_name,
                    args.overwrite,
                    args.dry_run,
                )

    print(f"Done. Prepared {len(common_pairs)} metal-pair directories in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
