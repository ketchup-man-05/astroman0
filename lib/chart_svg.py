"""North Indian (diamond) whole-sign horary chart as inline SVG. Dark-theme friendly."""
import html

_ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
         "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}

# 12 house regions as polygons in a 400x400 box, North Indian order
# (1st = top diamond, then counter-clockwise).
_REGIONS = [
    [(200, 20), (290, 110), (200, 200), (110, 110)],   # 1 top diamond
    [(20, 20), (110, 110), (200, 20)],                 # 2 upper-left
    [(20, 20), (20, 200), (110, 110)],                 # 3 left-upper
    [(110, 110), (200, 200), (110, 290), (20, 200)],   # 4 left diamond
    [(20, 200), (110, 290), (20, 380)],                # 5 left-lower
    [(20, 380), (200, 380), (110, 290)],               # 6 lower-left
    [(110, 290), (200, 200), (290, 290), (200, 380)],  # 7 bottom diamond
    [(200, 380), (290, 290), (380, 380)],              # 8 lower-right
    [(380, 380), (380, 200), (290, 290)],              # 9 right-lower
    [(290, 290), (200, 200), (290, 110), (380, 200)],  # 10 right diamond
    [(380, 200), (380, 20), (290, 110)],               # 11 right-upper
    [(380, 20), (200, 20), (290, 110)],                # 12 upper-right
]
# where the small sign number sits, and where the planet stack sits, per house
_SIGN_AT = [(200, 52), (88, 52), (52, 88), (52, 200), (52, 312), (88, 348),
            (200, 348), (312, 348), (348, 312), (348, 200), (348, 88), (312, 52)]
_PLANET_AT = [(200, 130), (105, 60), (60, 105), (105, 200), (60, 295), (105, 340),
              (200, 270), (295, 340), (340, 295), (295, 200), (340, 105), (295, 60)]


def north_indian_svg(asc_longitude, planets, size=340):
    """asc_longitude: degrees. planets: {name: longitude}. Returns SVG string."""
    lagna_sign = int(asc_longitude // 30)  # 0 = Aries
    houses = {i: [] for i in range(1, 13)}
    for name, lon in (planets or {}).items():
        try:
            sign = int(float(lon) // 30) % 12
        except (TypeError, ValueError):
            continue
        h = (sign - lagna_sign) % 12 + 1
        houses[h].append(_ABBR.get(name, name[:2]))
    houses[1].append("As")

    gold, ink, dim = "#c9a227", "#f5f0e6", "#8b93a7"
    parts = [f'<svg viewBox="0 0 400 400" width="{size}" height="{size}" '
             f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="North Indian horary chart">']
    parts.append(f'<rect x="20" y="20" width="360" height="360" fill="none" stroke="{gold}" stroke-width="2"/>')
    for (x1, y1), (x2, y2) in [((20, 20), (380, 380)), ((380, 20), (20, 380))]:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{gold}" stroke-width="1.4"/>')
    for i, poly in enumerate(_REGIONS):
        pts = " ".join(f"{x},{y}" for x, y in poly)
        parts.append(f'<polygon points="{pts}" fill="none" stroke="{gold}" stroke-width="1"/>')
        sx, sy = _SIGN_AT[i]
        sign_no = (lagna_sign + i) % 12 + 1
        parts.append(f'<text x="{sx}" y="{sy}" text-anchor="middle" font-size="13" '
                     f'fill="{dim}" font-family="sans-serif">{sign_no}</text>')
        px, py = _PLANET_AT[i]
        names = houses[i + 1]
        # stack planet abbreviations, up to 3 per line
        lines = [" ".join(names[j:j + 3]) for j in range(0, len(names), 3)] or []
        for li, line in enumerate(lines):
            parts.append(f'<text x="{px}" y="{py + li * 17}" text-anchor="middle" font-size="15" '
                         f'fill="{ink}" font-family="sans-serif">{html.escape(line)}</text>')
    parts.append('</svg>')
    return "".join(parts)
