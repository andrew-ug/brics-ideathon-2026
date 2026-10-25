"""Два графика в SVG для слайдов в Фигме: SVG вставляется в Фигму как вектор (перетащить файл или вставить код).
Шрифт Inter (есть в Фигме), цвета — слоты 1 и 2 палитры dataviz (#2a78d6, #eb6834), проверены validate_palette.js.
Числа: цена срочности из docs/data.js (та же модель strategy_map.best), ошибки OneWeb из out_v5/oneweb_drift_check.csv.
Запуск: python3 -I work/tools/make_figma_charts.py, пишет out/team/figma/*.svg."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "team" / "figma"
INK, MUTED, GRID, S1, S2, NA = "#14171c", "#6a7280", "#e4e2de", "#2a78d6", "#eb6834", "#a3a9b2"
F = 'font-family="Inter, Helvetica Neue, Arial, sans-serif"'

def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {F}>\n' + "\n".join(body) + "\n</svg>\n"

def price():
    data = json.loads((ROOT / "docs/data.js").read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
    g, dls = data["grid"]["-15"], data["deadlines"]
    bars = [(d, g[dls.index(d)]["xe"] if g[dls.index(d)] else None) for d in (30, 60, 90, 180, 365)]
    W, H, L, R, T, B = 640, 380, 56, 16, 30, 56
    pw, ph, top = W - L - R, H - T - B, 8.0
    y = lambda v: T + ph - v / top * ph
    s = [f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    for t in (0, 2, 4, 6, 8):
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<text x="{L-10}" y="{y(t)+4:.1f}" font-size="13" fill="{MUTED}" text-anchor="end">{t}</text>')
    s.append(f'<text x="{L-10}" y="{T-12}" font-size="13" fill="{MUTED}" text-anchor="end">кг</text>')
    bw, step = 64, pw / len(bars)
    for k, (d, v) in enumerate(bars):
        cx = L + step * (k + 0.5)
        if v is None:
            s.append(f'<text x="{cx:.1f}" y="{y(0)-14:.1f}" font-size="13" fill="{MUTED}" text-anchor="middle">не нашли</text>')
            s.append(f'<line x1="{cx-bw/2:.1f}" x2="{cx+bw/2:.1f}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="{NA}" stroke-width="3" stroke-dasharray="4 4"/>')
        else:
            top_y, r = y(v), 6
            s.append(f'<path d="M{cx-bw/2:.1f},{y(0):.1f} V{top_y+r:.1f} Q{cx-bw/2:.1f},{top_y:.1f} {cx-bw/2+r:.1f},{top_y:.1f} H{cx+bw/2-r:.1f} Q{cx+bw/2:.1f},{top_y:.1f} {cx+bw/2:.1f},{top_y+r:.1f} V{y(0):.1f} Z" fill="{S2}"/>')
            s.append(f'<text x="{cx:.1f}" y="{top_y-10:.1f}" font-size="18" font-weight="700" fill="{INK}" text-anchor="middle">{str(round(v, 1)).replace(".", ",")} кг</text>')
        s.append(f'<text x="{cx:.1f}" y="{H-B+24:.1f}" font-size="15" font-weight="600" fill="{INK}" text-anchor="middle">{d} сут</text>')
    s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="{INK}" stroke-width="1"/>')
    s.append(f'<text x="{L+pw/2:.1f}" y="{H-8}" font-size="13" fill="{MUTED}" text-anchor="middle">срок клиента · сдвиг плоскости −15° с орбиты 550 км · на борту 25,8 кг ксенона</text>')
    return svg(W, H, s)

def oneweb():
    rows = list(csv.DictReader(open(ROOT / "work/kaggle/oneweb_drift/out_v5/oneweb_drift_check.csv", encoding="utf-8")))
    rows.sort(key=lambda r: float(r["err_max"]))
    W, H, L, R, T, B = 640, 380, 56, 16, 56, 50
    pw, ph, top = W - L - R, H - T - B, 0.35
    x = lambda i: L + 8 + i * (pw - 16) / (len(rows) - 1)
    y = lambda v: T + ph - v / top * ph
    s = [f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    for t in (0, 0.1, 0.2, 0.3):
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<text x="{L-10}" y="{y(t)+4:.1f}" font-size="13" fill="{MUTED}" text-anchor="end">{str(t).replace(".", ",")}°</text>')
    s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(0.3):.1f}" y2="{y(0.3):.1f}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="6 5"/>')
    s.append(f'<text x="{L+8}" y="{y(0.3)-8:.1f}" font-size="13" font-weight="600" fill="{INK}">0,3°: ни один из 72 спутников не выше</text>')
    for i, r in enumerate(rows):
        col = S1 if r["launch"].startswith("LVM3-M2") else S2
        s.append(f'<circle cx="{x(i):.1f}" cy="{y(float(r["err_max"])):.1f}" r="5" fill="{col}" stroke="#ffffff" stroke-width="2"/>')
    for k, (col, label) in enumerate(((S1, "LVM3-M2, 23.10.2022, 36 спутников"), (S2, "LVM3-M3, 26.03.2023, 36 спутников"))):
        lx = L + k * 290
        s.append(f'<circle cx="{lx+6}" cy="{T-34}" r="6" fill="{col}"/>')
        s.append(f'<text x="{lx+18}" y="{T-29}" font-size="13" fill="{INK}">{label}</text>')
    s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="{INK}" stroke-width="1"/>')
    s.append(f'<text x="{L+pw/2:.1f}" y="{H-14}" font-size="13" fill="{MUTED}" text-anchor="middle">72 спутника OneWeb по возрастанию ошибки · плоскости ушли на 64–123° за 9–14 месяцев</text>')
    return svg(W, H, s)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "price_of_urgency.svg").write_text(price(), encoding="utf-8")
    (OUT / "oneweb_errors.svg").write_text(oneweb(), encoding="utf-8")
    print("готово:", ", ".join(p.name for p in sorted(OUT.glob("*.svg"))))
