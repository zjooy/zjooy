import html
import math
from PIL import Image

SRC = r"C:\Users\zjoy_\Downloads\84483488.png"
OUT_SVG = r"C:\Users\zjoy_\Desktop\Machine Learning\zjooy\assets\ascii-card.svg"

# density ramp, dark -> light (foreground only; background renders as blank space)
RAMP = "@%#*+=-:. "

COLS = 80
CHAR_W = 7.4
CHAR_H = 13
FONT_SIZE = 12
ASCII_COLOR = "#C77DFF"
BG_COLOR = "#0d0221"
PANEL_TITLE_COLOR = "#E0AAFF"
PANEL_TEXT_COLOR = "#EDE3F5"
PANEL_DIM_COLOR = "#B58FD1"

BG_DISTANCE_THRESHOLD = 40


def dominant_color(rgba_img):
    """Most common quantized RGB among opaque pixels -- the flat backdrop
    color, since it covers far more area than any single skin/hair tone."""
    buckets = {}
    for r, g, b, a in rgba_img.getdata():
        if a < 128:
            continue
        key = (r // 8, g // 8, b // 8)
        buckets[key] = buckets.get(key, 0) + 1
    best = max(buckets, key=buckets.get)
    return best[0] * 8 + 4, best[1] * 8 + 4, best[2] * 8 + 4


def image_to_ascii(path, cols):
    rgba = Image.open(path).convert("RGBA")
    w, h = rgba.size
    bg_r, bg_g, bg_b = dominant_color(rgba)
    img = Image.new("RGB", rgba.size, (bg_r, bg_g, bg_b))
    img.paste(rgba, mask=rgba.split()[3])

    aspect = h / w
    cell_aspect = CHAR_W / CHAR_H
    rows = max(1, int(cols * aspect * cell_aspect))
    small = img.resize((cols, rows), Image.LANCZOS)
    pixels = list(small.getdata())

    def dist(p):
        return math.sqrt((p[0] - bg_r) ** 2 + (p[1] - bg_g) ** 2 + (p[2] - bg_b) ** 2)

    def luminance(p):
        return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

    fg_lums = [luminance(p) for p in pixels if dist(p) > BG_DISTANCE_THRESHOLD]
    lum_min = min(fg_lums) if fg_lums else 0
    lum_max = max(fg_lums) if fg_lums else 255
    lum_range = max(1.0, lum_max - lum_min)

    ramp_len = len(RAMP) - 1
    lines = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            p = pixels[r * cols + c]
            if dist(p) <= BG_DISTANCE_THRESHOLD:
                row_chars.append(" ")
                continue
            v = (luminance(p) - lum_min) / lum_range
            v = min(1.0, max(0.0, v))
            idx = int(v * ramp_len)
            row_chars.append(RAMP[idx])
        lines.append("".join(row_chars))
    return lines


def build_svg(lines, ascii_color=ASCII_COLOR, bg_color=BG_COLOR,
              title_color=PANEL_TITLE_COLOR, text_color=PANEL_TEXT_COLOR,
              dim_color=PANEL_DIM_COLOR):
    art_w = COLS * CHAR_W
    art_h = len(lines) * CHAR_H
    pad = 24
    panel_w = 300
    width = pad * 3 + art_w + panel_w
    height = max(art_h, 260) + pad * 2

    art_x = pad
    art_y = pad + FONT_SIZE
    panel_x = pad * 2 + art_w

    svg_lines = []
    svg_lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">'
    )
    svg_lines.append(
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="18" fill="{bg_color}"/>'
    )
    svg_lines.append(
        f'<text x="{art_x}" y="{art_y:.0f}" xml:space="preserve" '
        f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" fill="{ascii_color}">'
    )
    for i, line in enumerate(lines):
        y = art_y + i * CHAR_H
        svg_lines.append(f'<tspan x="{art_x}" y="{y:.0f}">{html.escape(line)}</tspan>')
    svg_lines.append("</text>")

    # divider
    div_x = panel_x - pad
    svg_lines.append(
        f'<line x1="{div_x:.0f}" y1="{pad}" x2="{div_x:.0f}" y2="{height - pad:.0f}" '
        f'stroke="{dim_color}" stroke-opacity="0.35"/>'
    )

    ty = pad + 28
    svg_lines.append(
        f'<text x="{panel_x:.0f}" y="{ty}" font-family="Segoe UI, Verdana, sans-serif" '
        f'font-size="24" font-weight="700" fill="{title_color}">Joyce Pereira</text>'
    )
    ty += 26
    svg_lines.append(
        f'<text x="{panel_x:.0f}" y="{ty}" font-family="Segoe UI, Verdana, sans-serif" '
        f'font-size="15" fill="{text_color}">Engenheira de Software @ Itau</text>'
    )
    ty += 40

    rows = [
        ("Localizacao", "Sao Paulo, SP"),
        ("Repositorios publicos", "32"),
        ("Contribuicoes (ultimo ano)", "245"),
        ("Total de commits", "139"),
        ("Contribuiu para", "10 projetos"),
        ("No GitHub ha", "5 anos"),
    ]
    for label, value in rows:
        svg_lines.append(
            f'<text x="{panel_x:.0f}" y="{ty}" font-family="Segoe UI, Verdana, sans-serif" '
            f'font-size="12.5" fill="{dim_color}">{html.escape(label)}</text>'
        )
        ty += 18
        svg_lines.append(
            f'<text x="{panel_x:.0f}" y="{ty}" font-family="Segoe UI, Verdana, sans-serif" '
            f'font-size="15" font-weight="600" fill="{text_color}">{html.escape(value)}</text>'
        )
        ty += 26

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


if __name__ == "__main__":
    import os
    lines = image_to_ascii(SRC, COLS)

    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    # white/gray ASCII art (higher contrast) over the theme's dark purple background
    svg = build_svg(
        lines,
        ascii_color="#F2F2F2",
        bg_color=BG_COLOR,
        title_color="#FFFFFF",
        text_color="#EDE3F5",
        dim_color=PANEL_DIM_COLOR,
    )
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_SVG} ({len(lines)} rows x {COLS} cols)")
