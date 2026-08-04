"""Resolution presets for common laptop and desktop screens."""

PRESETS = {
    "laptop": [
        ("1366x768", 1366, 768),
        ("1536x864", 1536, 864),
        ("1920x1080", 1920, 1080),
        ("1920x1200", 1920, 1200),
        ("2240x1400", 2240, 1400),
        ("2560x1440", 2560, 1440),
        ("2560x1600", 2560, 1600),
        ("2880x1800", 2880, 1800),
        ("3024x1964", 3024, 1964),
        ("3456x2234", 3456, 2234),
    ],
    "desktop": [
        ("1920x1080", 1920, 1080),
        ("2560x1440", 2560, 1440),
        ("3440x1440", 3440, 1440),
        ("3840x2160", 3840, 2160),
        ("5120x1440", 5120, 1440),
        ("7680x2160", 7680, 2160),
    ],
}


def list_presets():
    rows = []
    for device, presets in PRESETS.items():
        for name, width, height in presets:
            rows.append((device, name, width, height))
    return rows
