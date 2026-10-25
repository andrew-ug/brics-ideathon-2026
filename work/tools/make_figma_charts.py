"""Графики в SVG для слайдов в Фигме, в стиле макета: белый фон, Inter, коралловый #f8604a, серые плашки #f6f7f8.
SVG вставляется в Фигму как вектор (перетащить файл). Один цвет на график, подписи прямо у данных, без легенд.
Числа: цена срочности из docs/data.js (та же модель strategy_map.best), ошибки OneWeb из out_v5/oneweb_drift_check.csv.
Запуск: python3 -I work/tools/make_figma_charts.py, пишет out/team/figma/*.svg."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "team" / "figma"
INK, INK2, MUTED, GRID, CORAL, PALE = "#111111", "#4a4f57", "#9097a1", "#eceef1", "#f8604a", "#fde3de"
F = 'font-family="Inter, -apple-system, Helvetica Neue, Arial, sans-serif"'
fmt = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")

def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {F}>\n' + "\n".join(body) + "\n</svg>\n"

def price():
    """Цена срочности: столбцы по срокам, «не нашли» — пустая плашка того же размера."""
    data = json.loads((ROOT / "docs/data.js").read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
    g, dls = data["grid"]["-15"], data["deadlines"]
    bars = [(d, g[dls.index(d)]["xe"] if g[dls.index(d)] else None) for d in (30, 60, 90, 180, 365)]
    W, H, T, B = 720, 400, 40, 52
    ph, top, bw, gap = H - T - B, 7.5, 104, 30
    x0 = (W - (len(bars) * bw + (len(bars) - 1) * gap)) / 2
    y = lambda v: T + ph - v / top * ph
    s = []
    for k, (d, v) in enumerate(bars):
        x = x0 + k * (bw + gap)
        if v is None:
            s.append(f'<rect x="{x:.1f}" y="{y(1.1):.1f}" width="{bw}" height="{y(0)-y(1.1):.1f}" rx="10" fill="#f6f7f8"/>')
            s.append(f'<text x="{x+bw/2:.1f}" y="{y(0.55)+5:.1f}" font-size="15" fill="{MUTED}" text-anchor="middle">не нашли</text>')
        else:
            s.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{bw}" height="{y(0)-y(v):.1f}" rx="10" fill="{CORAL if d == 90 else PALE if d == 365 else "#fbb3a5"}"/>')
            s.append(f'<text x="{x+bw/2:.1f}" y="{y(v)-14:.1f}" font-size="26" font-weight="700" fill="{INK}" text-anchor="middle" letter-spacing="-0.5">{fmt(v)} кг</text>')
        s.append(f'<text x="{x+bw/2:.1f}" y="{H-B+30:.1f}" font-size="17" font-weight="500" fill="{INK2}" text-anchor="middle">{d} суток</text>')
    s.append(f'<line x1="{x0-12:.1f}" x2="{W-x0+12:.1f}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="{GRID}" stroke-width="2"/>')
    return svg(W, H, s)

def oneweb():
    """72 спутника по возрастанию ошибки, порог 0,3°. Широкий формат под плашку на слайде."""
    rows = sorted(csv.DictReader(open(ROOT / "work/kaggle/oneweb_drift/out_v5/oneweb_drift_check.csv", encoding="utf-8")),
                  key=lambda r: float(r["err_max"]))
    W, H, L, R, T, B = 880, 260, 46, 16, 24, 34
    pw, ph, top = W - L - R, H - T - B, 0.33
    x = lambda i: L + 10 + i * (pw - 20) / (len(rows) - 1)
    y = lambda v: T + ph - v / top * ph
    s = []
    for t in (0, 0.1, 0.2, 0.3):
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{GRID}" stroke-width="1.5"{" stroke-dasharray=\"6 6\"" if t == 0.3 else ""}/>')
        s.append(f'<text x="{L-10}" y="{y(t)+5:.1f}" font-size="14" fill="{MUTED}" text-anchor="end">{fmt(t)}°</text>')
    s.append(f'<text x="{W-R}" y="{y(0.3)-10:.1f}" font-size="14" font-weight="600" fill="{INK}" text-anchor="end">порог 0,3° — ни один спутник не выше</text>')
    for i, r in enumerate(rows):
        s.append(f'<circle cx="{x(i):.1f}" cy="{y(float(r["err_max"])):.1f}" r="5.5" fill="{CORAL}"/>')
    s.append(f'<text x="{L+10}" y="{H-8}" font-size="14" fill="{MUTED}">каждая точка — один из 72 спутников OneWeb, по возрастанию ошибки</text>')
    return svg(W, H, s)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "price_of_urgency.svg").write_text(price(), encoding="utf-8")
    (OUT / "oneweb_errors.svg").write_text(oneweb(), encoding="utf-8")
    print("готово:", ", ".join(p.name for p in sorted(OUT.glob("*.svg"))))
