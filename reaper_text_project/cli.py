from __future__ import annotations

import argparse
from pathlib import Path

from .generator import GeneratorConfig, generate_project


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate REAPER .rpp from folder structure")
    p.add_argument("source_root", type=Path, help="Root folder with audio files")
    p.add_argument("output_file", type=Path, help="Output .rpp file")
    p.add_argument("--min-db", type=float, default=-3.0)
    p.add_argument("--max-db", type=float, default=3.0)
    p.add_argument("--spacing", type=float, default=3.0, help="Silence between items in seconds")
    p.add_argument("--no-fx", action="store_true", help="Disable FX chain")
    p.add_argument("--no-ds", action="store_true")
    p.add_argument("--no-comp", action="store_true")
    p.add_argument("--no-eq", action="store_true")
    p.add_argument("--no-multiband", action="store_true")
    p.add_argument("--no-limiter", action="store_true")
    p.add_argument("--script", type=Path, help="CSV/XLSX/TXT with desired item order")
    p.add_argument("--sample-rate", type=int, choices=[44100, 48000, 96000], default=48000)
    p.add_argument("--enable-pre-fx-envelope", action="store_true", help="Enable track pre-FX volume envelope")
    p.add_argument("--pre-fx-range-db", type=float, default=0.0, help="Total dB range for pre-FX envelope")
    return p


def main() -> None:
    args = build_parser().parse_args()
    cfg = GeneratorConfig(
        source_root=args.source_root,
        output_file=args.output_file,
        min_db=args.min_db,
        max_db=args.max_db,
        spacing_seconds=args.spacing,
        sample_rate=args.sample_rate,
        enable_pre_fx_volume_envelope=args.enable_pre_fx_envelope,
        pre_fx_volume_envelope_range_db=max(0.0, args.pre_fx_range_db),
        use_fx_chain=not args.no_fx,
        include_ds=not args.no_ds,
        include_comp=not args.no_comp,
        include_eq=not args.no_eq,
        include_multiband=not args.no_multiband,
        include_limiter=not args.no_limiter,
        include_script_order=args.script is not None,
        script_path=args.script,
    )
    generate_project(cfg)
    print(f"RPP generated: {cfg.output_file}")


if __name__ == "__main__":
    main()
