"""Command-line interface for crosswall."""

import argparse
import sys
from pathlib import Path

from crosswall import __version__
from crosswall.generator import (
    OLED_SAFE_MAX_LUMINANCE,
    STYLES,
    default_shift_px,
    generate,
    luminance_ratio,
    oled_safe,
    shift_offsets,
)
from crosswall.presets import PRESETS, list_presets

DEFAULT_OUT = Path("output")
PANELS = ("oled", "led")
STYLE_NAMES = tuple(STYLES)


def _positive_int(value):
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _resolve_resolution(args):
    if args.preset:
        for presets in PRESETS.values():
            for name, width, height in presets:
                if name == args.preset:
                    return width, height
        raise SystemExit(f"error: unknown preset '{args.preset}' (see --list-presets)")
    if args.all:
        return None
    return args.width, args.height


def _check_style(args, style):
    color = STYLES[style]
    ratio = luminance_ratio(color)
    if args.panel == "oled" and not oled_safe(color) and not args.force:
        raise SystemExit(
            f"error: style '{style}' has {ratio:.1%} luminance, above the "
            f"OLED-safe limit of {OLED_SAFE_MAX_LUMINANCE:.1%}; a static bright element on "
            "a 24/7 OLED will burn in. Use --force if you accept the risk."
        )
    return ratio


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="crosswall",
        description="Generate burn-in-safe Christian cross wallpapers for OLED and LCD screens.",
    )
    parser.add_argument("--version", action="version", version=f"crosswall {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="generate one or more wallpapers")
    generate_parser.add_argument("--width", type=_positive_int, default=1920)
    generate_parser.add_argument("--height", type=_positive_int, default=1080)
    generate_parser.add_argument("--preset", help="use a named resolution preset")
    generate_parser.add_argument(
        "--all", action="store_true", help="generate every preset resolution"
    )
    generate_parser.add_argument(
        "--panel",
        choices=PANELS,
        default="oled",
        help="panel type; oled enables burn-in safeguards (default: oled)",
    )
    generate_parser.add_argument(
        "--style",
        choices=STYLE_NAMES,
        default="safe",
        help="cross color style (default: safe)",
    )
    generate_parser.add_argument(
        "--shift",
        type=_positive_int,
        default=1,
        help="generate N variants with the cross nudged a few pixels for slideshow "
        "rotation (default: 1)",
    )
    generate_parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="output directory (default: ./output)",
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="allow styles above the OLED-safe luminance limit",
    )

    subparsers.add_parser("list-presets", help="list all resolution presets")
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if args.command == "list-presets":
        header = f"{'device':<8} {'name':<12} {'width':>6} {'height':>6}"
        print(header)
        print("-" * len(header))
        for device, name, width, height in list_presets():
            print(f"{device:<8} {name:<12} {width:>6} {height:>6}")
        return 0

    width, height = _resolve_resolution(args)
    style = args.style
    color = STYLES[style]
    ratio = _check_style(args, style)

    if args.panel == "led":
        print(
            f"note: LCD panels do not suffer permanent burn-in; style '{style}' "
            f"({ratio:.1%} luminance) is safe on this panel."
        )
    else:
        print(
            f"cross luminance: {ratio:.1%} "
            f"({'OLED-safe' if oled_safe(color) else 'above OLED-safe limit'})"
        )

    targets = [(name, w, h) for _, name, w, h in list_presets()] if args.all else []
    if not args.all:
        targets.append((f"{width}x{height}", width, height))

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    shift_px = default_shift_px(width, height)
    written = []

    for name, w, h in targets:
        base = f"crosswall_{w}x{h}_{args.panel}_{style}"
        for variant, (dx, dy) in enumerate(shift_offsets(args.shift, shift_px)):
            image = generate(w, h, color, shift_dx=dx, shift_dy=dy)
            suffix = f"_shift{variant}" if args.shift > 1 else ""
            path = out_dir / f"{base}{suffix}.png"
            image.save(path, "PNG")
            written.append(path)

    print(f"wrote {len(written)} wallpaper(s) to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
