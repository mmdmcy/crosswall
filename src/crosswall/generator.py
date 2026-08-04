"""Cross geometry and burn-in-aware color math."""

from math import ceil, cos, pi, sin

from PIL import Image, ImageDraw

OLED_SAFE_MAX_LUMINANCE = 0.05

STYLES = {
    "safe": (0x17, 0x17, 0x17),
    "classic": (0x2E, 0x2E, 0x2E),
    "bright": (0xFF, 0xFF, 0xFF),
    "night": (0x44, 0x2E, 0x10),
    "amber": (0xB3, 0x78, 0x1E),
}


def _srgb_to_linear(channel):
    value = channel / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def luminance_ratio(color):
    red, green, blue = color
    return (
        0.2126 * _srgb_to_linear(red)
        + 0.7152 * _srgb_to_linear(green)
        + 0.0722 * _srgb_to_linear(blue)
    )


def oled_safe(color):
    return luminance_ratio(color) <= OLED_SAFE_MAX_LUMINANCE


def _supersample_factor(width, height):
    min_dimension = min(width, height)
    return max(2, min(6, ceil(2048 / min_dimension)))


def generate(
    width,
    height,
    cross_color,
    shift_dx=0,
    shift_dy=0,
    size_fraction=0.60,
    thickness_fraction=0.09,
    horizontal_fraction=0.70,
    crossbar_position=0.42,
    corner_fraction=0.30,
):
    factor = _supersample_factor(width, height)
    big_width, big_height = width * factor, height * factor
    image = Image.new("RGB", (big_width, big_height), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    min_dimension = min(width, height)
    center_x = width / 2 + shift_dx
    center_y = height / 2 + shift_dy
    beam_height = size_fraction * min_dimension
    thickness = thickness_fraction * min_dimension
    horizontal_length = horizontal_fraction * beam_height
    radius = corner_fraction * thickness

    vertical_left = (center_x - thickness / 2) * factor
    vertical_right = (center_x + thickness / 2) * factor
    vertical_top = (center_y - beam_height / 2) * factor
    vertical_bottom = (center_y + beam_height / 2) * factor

    horizontal_center_y = center_y - beam_height / 2 + crossbar_position * beam_height
    horizontal_left = (center_x - horizontal_length / 2) * factor
    horizontal_right = (center_x + horizontal_length / 2) * factor
    horizontal_top = (horizontal_center_y - thickness / 2) * factor
    horizontal_bottom = (horizontal_center_y + thickness / 2) * factor

    draw.rounded_rectangle(
        (vertical_left, vertical_top, vertical_right, vertical_bottom),
        radius=radius * factor,
        fill=cross_color,
    )
    draw.rounded_rectangle(
        (horizontal_left, horizontal_top, horizontal_right, horizontal_bottom),
        radius=radius * factor,
        fill=cross_color,
    )

    return image.resize((width, height), Image.LANCZOS)


def shift_offsets(count, shift_px):
    offsets = [(0, 0)]
    for index in range(1, count):
        angle = (index - 1) / max(1, count - 1) * 2 * pi
        offsets.append((round(cos(angle) * shift_px), round(sin(angle) * shift_px)))
    return offsets


def default_shift_px(width, height):
    return max(2, round(min(width, height) * 0.0008))
