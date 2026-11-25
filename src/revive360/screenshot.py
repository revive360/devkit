"""Xenos 32-bit 8in32 ARGB captures, adapted from Pedro's xenos_untile.py.

Tiled addressing follows Xenia texture_address (BSD-3-Clause; see
licenses/Xenia-BSD-3-Clause.txt). No Microsoft SDK code is used.
"""


def address(x, y, width):
    width = (width + 31) & ~31
    macro = ((y >> 5) * (width >> 5)) << 9
    micro = (y & 6) << 4
    base = macro + ((micro & ~15) << 1) + (micro & 15) + ((y & 8) << 5) + ((y & 1) << 4)
    macro = (x >> 5) << 9
    micro = (x & 7) << 2
    offset = base + macro + ((micro & ~15) << 1) + (micro & 15)
    return ((offset & ~511) << 3) + ((offset & 448) << 2) + (offset & 63) + ((y & 16) << 7) + (((((y & 8) >> 2) + (x >> 3)) & 3) << 6)


def decode(raw, info, width=None, height=None):
    from PIL import Image
    if (info.get('format', 0) & ~0x100) != 0x18280086:
        raise ValueError('Unsupported capture format; raw and JSON have been preserved')
    width = info['width'] if width is None else width
    height = info['height'] if height is None else height
    if width <= 0 or height <= 0 or width * height > 4096 * 4096:
        raise ValueError('Invalid capture dimensions')
    tiled = bool(info.get('format', 0) & 0x100)
    rgb = bytearray(width * height * 3)
    pitch = info.get('pitch', width * 4)
    for y in range(height):
        for x in range(width):
            offset = address(x, y, width) if tiled else y * pitch + x * 4
            if offset + 4 > len(raw):
                raise ValueError('Capture is partial or dimensions are wrong; raw/JSON preserved. See docs/xbdm.md')
            # Reversing 8in32 gives ARGB; directly select the RGB bytes.
            index = (y * width + x) * 3
            rgb[index:index + 3] = bytes((raw[offset + 2], raw[offset + 1], raw[offset]))
    return Image.frombytes('RGB', (width, height), bytes(rgb))
