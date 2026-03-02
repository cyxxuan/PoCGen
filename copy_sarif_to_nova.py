#!/usr/bin/env python3
"""
Copy SARIF results from output/secbench/<vuln-id>/ to
~/project/nova/workspace/secbench/<vuln-type>/<package_version>/pocgen_result/
"""

import csv
import re
import shutil
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
SOURCE_ROOT = Path("output/secbench")          # relative to CWD (PoCGen/)
STATS_DIR   = Path.home() / "project/nova/stats/secbench"
TARGET_ROOT = Path.home() / "project/nova/workspace/secbench"

# Map CSV filename stem → workspace subfolder name
CSV_TO_VTYPE = {
    "command-injection":  "command_injection",
    "code-injection":     "code_injection",
    "path-traversal":     "path_traversal",
    "prototype-pollution":"prototype_pollution",
    "redos":              "redos",
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def normalize_id(folder_name: str) -> str:
    """Convert folder name to the ID format used in CSV files.

    npm_angular-http-server_20180426  →  npm:angular-http-server:20180426
    GHSA-g7h8-p22m-2rvx              →  GHSA-G7H8-P22M-2RVX
    SNYK-JS-101-1292345              →  SNYK-JS-101-1292345  (unchanged)
    """
    if folder_name.startswith("npm_"):
        # Last segment is always an 8-digit date
        m = re.match(r"^npm_(.+)_(\d{8})$", folder_name)
        if m:
            return f"npm:{m.group(1)}:{m.group(2)}"
    # GHSA IDs in CSVs are uppercase
    if folder_name.upper().startswith("GHSA"):
        return folder_name.upper()
    return folder_name  # SNYK IDs are already correct


def build_lookup() -> dict:
    """Return {normalized_id: (vuln_type_folder, package_version_folder)}."""
    lookup = {}
    for csv_file in STATS_DIR.glob("*.csv"):
        stem = csv_file.stem               # e.g. "command-injection"
        vtype = CSV_TO_VTYPE.get(stem)
        if vtype is None:
            print(f"[WARN] Unknown CSV '{csv_file.name}', skipping")
            continue
        with csv_file.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_id  = row.get("ID", "").strip()
                package = row.get("package", "").strip()
                if raw_id and package:
                    lookup[raw_id.upper()] = (vtype, package)
    return lookup


# ── Main ─────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False):
    if not SOURCE_ROOT.exists():
        print(f"[ERROR] Source directory not found: {SOURCE_ROOT.resolve()}")
        sys.exit(1)

    lookup = build_lookup()
    print(f"[INFO] Loaded {len(lookup)} entries from stats CSVs")

    copied = skipped = errors = 0

    for src_dir in sorted(SOURCE_ROOT.iterdir()):
        if not src_dir.is_dir():
            continue

        folder_name = src_dir.name
        norm_id     = normalize_id(folder_name)
        entry       = lookup.get(norm_id.upper())

        if entry is None:
            print(f"[SKIP] No CSV entry for '{folder_name}' (normalized: {norm_id})")
            skipped += 1
            continue

        vtype, pkg_ver = entry
        target_base = TARGET_ROOT / vtype / pkg_ver

        if not target_base.exists():
            print(f"[SKIP] Target folder not found: {target_base}")
            skipped += 1
            continue

        sarif_files = list(src_dir.glob("*.sarif"))
        if not sarif_files:
            print(f"[SKIP] No .sarif files in {src_dir}")
            skipped += 1
            continue

        dest_dir = target_base / "pocgen_result"
        if not dry_run:
            dest_dir.mkdir(exist_ok=True)

        for sarif in sarif_files:
            dest_file = dest_dir / sarif.name
            if dry_run:
                print(f"[DRY]  {sarif}  →  {dest_file}")
            else:
                shutil.copy2(sarif, dest_file)
                print(f"[COPY] {sarif.name}  →  {dest_file}")
            copied += 1

    print(f"\n[DONE] copied={copied}  skipped={skipped}  errors={errors}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv or "-n" in sys.argv
    if dry:
        print("[MODE] Dry run — no files will be written\n")
    main(dry_run=dry)
