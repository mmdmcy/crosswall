import subprocess
import sys

import pytest
from PIL import Image

from crosswall.generator import (
    OLED_SAFE_MAX_LUMINANCE,
    STYLES,
    generate,
    luminance_ratio,
    oled_safe,
    shift_offsets,
)
from crosswall.presets import PRESETS, list_presets

SIZES = [(64, 48), (320, 180), (256, 256)]


def cross_bounds(image):
    pixels = image.load()
    width, height = image.size
    xs, ys = [], []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] != (0, 0, 0):
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


@pytest.mark.parametrize("width,height", SIZES)
def test_background_is_pure_black(width, height):
    image = generate(width, height, STYLES["safe"])
    corners = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    assert [image.getpixel(corner) for corner in corners] == [(0, 0, 0)] * 4


@pytest.mark.parametrize("width,height", SIZES)
def test_cross_is_centered(width, height):
    image = generate(width, height, STYLES["safe"])
    bounds = cross_bounds(image)
    assert bounds is not None
    left, top, right, bottom = bounds
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    assert abs(cx - width / 2) <= max(2, width * 0.02)
    assert abs(cy - height / 2) <= max(2, height * 0.02)


def test_cross_is_proportional():
    width, height = 1000, 600
    image = generate(width, height, STYLES["safe"])
    left, top, right, bottom = cross_bounds(image)
    assert right - left > width * 0.2
    assert bottom - top > height * 0.5


@pytest.mark.parametrize("style", STYLES)
def test_style_luminances(style):
    ratio = luminance_ratio(STYLES[style])
    assert 0.0 <= ratio <= 1.0
    if style == "safe":
        assert ratio < OLED_SAFE_MAX_LUMINANCE
    if style == "bright":
        assert ratio > OLED_SAFE_MAX_LUMINANCE


def test_oled_safe():
    assert oled_safe(STYLES["safe"])
    assert oled_safe(STYLES["classic"])
    assert oled_safe(STYLES["night"])
    assert not oled_safe(STYLES["bright"])
    assert not oled_safe(STYLES["amber"])


def test_night_style_is_warm_and_dim():
    red, green, blue = STYLES["night"]
    assert red > green > blue
    assert blue < 0.4 * green
    assert oled_safe(STYLES["night"])


def test_amber_style_is_warm_but_visible():
    red, green, blue = STYLES["amber"]
    assert red > green > blue
    assert luminance_ratio(STYLES["amber"]) > OLED_SAFE_MAX_LUMINANCE


def test_shift_offsets_vary_center():
    offsets = shift_offsets(5, 3)
    assert offsets[0] == (0, 0)
    assert len({offset for offset in offsets}) == 5
    image_a = generate(320, 180, STYLES["safe"], shift_dx=offsets[0][0], shift_dy=offsets[0][1])
    image_b = generate(320, 180, STYLES["safe"], shift_dx=offsets[1][0], shift_dy=offsets[1][1])
    bounds_a = cross_bounds(image_a)
    bounds_b = cross_bounds(image_b)
    assert (bounds_a[0] + bounds_a[2]) != (bounds_b[0] + bounds_b[2])


def test_presets_are_unique():
    pairs = [(device, name) for device, name, _, _ in list_presets()]
    assert len(pairs) == len(set(pairs))
    assert all(width > 0 and height > 0 for _, _, width, height in list_presets())
    assert any(name == "1920x1080" for name, _, _ in PRESETS["laptop"])
    assert any(name == "3840x2160" for name, _, _ in PRESETS["desktop"])


def test_cli_generates_file(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crosswall",
            "generate",
            "--width",
            "320",
            "--height",
            "180",
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    files = list(out.glob("*.png"))
    assert len(files) == 1
    with Image.open(files[0]) as image:
        assert image.size == (320, 180)
        assert image.format == "PNG"


def test_cli_rejects_bright_on_oled(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crosswall",
            "generate",
            "--style",
            "bright",
            "--out",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "OLED-safe" in result.stderr


def test_cli_bright_allowed_on_led(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crosswall",
            "generate",
            "--panel",
            "led",
            "--style",
            "bright",
            "--width",
            "320",
            "--height",
            "180",
            "--out",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert len(list(tmp_path.glob("*.png"))) == 1


def test_cli_force_overrides_guard(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crosswall",
            "generate",
            "--style",
            "bright",
            "--force",
            "--width",
            "320",
            "--height",
            "180",
            "--out",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_cli_shift_variants(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crosswall",
            "generate",
            "--shift",
            "4",
            "--width",
            "320",
            "--height",
            "180",
            "--out",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert len(list(tmp_path.glob("*.png"))) == 4


def test_cli_list_presets():
    result = subprocess.run(
        [sys.executable, "-m", "crosswall", "list-presets"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "3840x2160" in result.stdout


def test_cli_unknown_preset_fails(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "crosswall", "generate", "--preset", "nope", "--out", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
