"""Два графика для слайдов ДРЕЙФ (статичный PDF, поэтому без наведения, числа продублированы в подписях).
1) цена срочности: ксенон на сдвиг узла −15° с СОО 550 км по сроку (work/calc/strategy_map.out)
2) разнос плоскостей OneWeb: модель против факта (work/kaggle/oneweb_drift/out_v4/oneweb_drift_check.csv)
Цвета — слоты 1 и 2 эталонной палитры dataviz (#2a78d6, #eb6834), проверены validate_palette.js.
Запуск: python3 -I work/tools/make_charts.py → out/slides/charts/*.svg"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/slides/charts"
OUT.mkdir(parents=True, exist_ok=True)
INK, MUTED, GRID, S1, S2, NA = "#14171c", "#5b6370", "#e3e5e8", "#2a78d6", "#eb6834", "#9aa3ad"
FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'

def price_chart():
    days = [30, 60, 90, 180, 365]
    xe = [None, None, 6.7, 2.8, 1.3]
    W, H, L, R, T, B = 520, 300, 46, 16, 18, 52
    ymax = 8
    pw, ph = W - L - R, H - T - B
    y = lambda v: T + ph * (1 - v / ymax)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {FONT}>']
    for t in (0, 2, 4, 6, 8):
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<text x="{L-8}" y="{y(t)+4:.1f}" font-size="12" fill="{MUTED}" text-anchor="end">{t}</text>')
    s.append(f'<text x="{L-34}" y="{T+ph/2:.1f}" font-size="12" fill="{MUTED}" transform="rotate(-90 {L-34} {T+ph/2:.1f})" text-anchor="middle">ксенон, кг</text>')
    slot = pw / len(days)
    bw = 24
    for k, (d, v) in enumerate(zip(days, xe)):
        cx = L + slot * (k + 0.5)
        if v is None:
            s.append(f'<text x="{cx:.1f}" y="{y(0)-10:.1f}" font-size="18" fill="{NA}" text-anchor="middle">×</text>')
            s.append(f'<text x="{cx:.1f}" y="{y(0)-30:.1f}" font-size="12" fill="{MUTED}" text-anchor="middle">невыполнимо</text>')
        else:
            top, base, r = y(v), y(0), 4
            s.append(f'<path d="M{cx-bw/2:.1f},{base:.1f} V{top+r:.1f} Q{cx-bw/2:.1f},{top:.1f} {cx-bw/2+r:.1f},{top:.1f} H{cx+bw/2-r:.1f} Q{cx+bw/2:.1f},{top:.1f} {cx+bw/2:.1f},{top+r:.1f} V{base:.1f} Z" fill="{S1}"/>')
            s.append(f'<text x="{cx:.1f}" y="{top-8:.1f}" font-size="14" font-weight="700" fill="{INK}" text-anchor="middle">{str(v).replace(".", ",")} кг</text>')
        s.append(f'<text x="{cx:.1f}" y="{H-B+20:.1f}" font-size="13" fill="{INK}" text-anchor="middle">{d}</text>')
    s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="{MUTED}" stroke-width="1"/>')
    s.append(f'<text x="{L+pw/2:.1f}" y="{H-8}" font-size="12" fill="{MUTED}" text-anchor="middle">срок доставки, суток</text>')
    s.append("</svg>")
    (OUT / "price_of_urgency.svg").write_text("\n".join(s), encoding="utf-8")

def oneweb_chart():
    rows = list(csv.DictReader(open(ROOT / "work/kaggle/oneweb_drift/out_v4/oneweb_drift_check.csv", encoding="utf-8")))
    rows = [r for r in rows if float(r["max_gap"]) < 10]
    series = {}
    for r in rows:
        series.setdefault(r["launch"], []).append((float(r["raan_pred_total"]), float(r["raan_obs_total"])))
    pts = {}
    for name, v in series.items():
        mp = sum(p for p, _ in v) / len(v); mo = sum(o for _, o in v) / len(v)
        pts[name] = [(p - mp, o - mo) for p, o in v]
    allv = [c for v in pts.values() for xy in v for c in xy]
    lim = max(abs(min(allv)), abs(max(allv))) * 1.1
    W, H, L, R, T, B = 420, 330, 52, 16, 40, 48
    pw, ph = W - L - R, H - T - B
    X = lambda v: L + pw * (v + lim) / (2 * lim)
    Y = lambda v: T + ph * (1 - (v + lim) / (2 * lim))
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {FONT}>']
    step = 10 if lim > 15 else 5
    t = -int(lim // step) * step
    while t <= lim:
        s.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T}" y2="{T+ph}" stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<text x="{X(t):.1f}" y="{T+ph+16:.1f}" font-size="11" fill="{MUTED}" text-anchor="middle">{t:+d}°</text>')
        s.append(f'<text x="{L-6}" y="{Y(t)+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{t:+d}°</text>')
        t += step
    s.append(f'<line x1="{X(-lim):.1f}" y1="{Y(-lim):.1f}" x2="{X(lim):.1f}" y2="{Y(lim):.1f}" stroke="{MUTED}" stroke-width="1"/>')
    s.append(f'<text x="{X(lim*0.55):.1f}" y="{Y(lim*0.55)-8:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">модель = факт</text>')
    lx = L
    for (name, v), col in zip(sorted(pts.items()), (S1, S2)):
        for p, o in v:
            s.append(f'<circle cx="{X(p):.1f}" cy="{Y(o):.1f}" r="4.5" fill="{col}" stroke="#ffffff" stroke-width="2"/>')
        label = f'запуск {name.split()[1]} · {len(v)} спутн.'
        s.append(f'<circle cx="{lx+6}" cy="{T-20}" r="5" fill="{col}"/>')
        s.append(f'<text x="{lx+16}" y="{T-16}" font-size="12" fill="{INK}">{label}</text>')
        lx += 190
    s.append(f'<text x="{L+pw/2:.1f}" y="{H-6}" font-size="12" fill="{MUTED}" text-anchor="middle">сдвиг плоскости по модели, относительно среднего запуска</text>')
    s.append(f'<text x="14" y="{T+ph/2:.1f}" font-size="12" fill="{MUTED}" transform="rotate(-90 14 {T+ph/2:.1f})" text-anchor="middle">по данным TLE</text>')
    s.append("</svg>")
    (OUT / "oneweb_model_vs_fact.svg").write_text("\n".join(s), encoding="utf-8")
    return {k: len(v) for k, v in pts.items()}, lim

price_chart()
print(oneweb_chart())
