"""Данные для калькулятора docs/index.html: та же модель strategy_map.best(), посчитанная заранее на сетке.
Старт: СОО 550 км, i = 97,6°, буксир 150 кг + груз 50 кг. Сетка: сдвиг узла −30…+30° через 1°, срок 30…365 сут через 5 сут.
Страница ничего не пересчитывает, она только показывает эти числа, поэтому они совпадают с кодом в work/calc.
Плюс 72 спутника OneWeb из work/kaggle/oneweb_drift/out_v5/oneweb_drift_check.csv.
Запуск: python3 -I work/tools/make_calc_data.py (около минуты), пишет docs/data.js."""
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "calc"))
import strategy_map as sm

H0, INC, M0 = 550, 97.6, 200.0
SHIFTS = [d for d in range(-30, 31) if d != 0]
DEADLINES = list(range(30, 366, 5))

def legs_days(m0, legs):
    """Сутки работы двигателя на каждом участке, как в sm.plan_cost."""
    m, out = m0, []
    for dv in legs:
        mp = m * (1 - math.exp(-dv / sm.VE)); m -= mp
        out.append(mp * sm.VE / sm.T / 86400 / sm.DUTY)
    return out

def plan(dO, dl):
    r = sm.best(M0, H0, INC, dO, dl)
    if r is None:
        return None
    xe, dv, days, text = r
    h_wait, part = re.search(r"высота ожидания (\d+) км, тягой ([\d.]+)°", text).groups()
    h_wait, part = int(h_wait), float(part)
    k = math.pi / 2 * sm.v(H0) * math.sin(math.radians(INC)) * math.pi / 180
    dv_h = abs(sm.v(H0) - sm.v(h_wait))
    t_up, t_part, t_down = legs_days(M0, [dv_h, k * part, dv_h])
    return dict(xe=round(xe, 2), dv=round(dv), days=round(days, 1), h=h_wait, part=part,
                kind=text.split(":")[0], up=round(t_up, 1), turn=round(t_part, 1), down=round(t_down, 1),
                wait=round(max(0.0, days - t_up - t_part - t_down), 1))

def oneweb():
    rows = []
    with open(ROOT / "work/kaggle/oneweb_drift/out_v5/oneweb_drift_check.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(dict(norad=int(r["norad"]), launch=r["launch"].split()[0], days=round(float(r["days"])),
                             obs=round(float(r["raan_obs_total"]), 2), pred=round(float(r["raan_pred_total"]), 2),
                             err=round(float(r["err_max"]), 3)))
    return rows

if __name__ == "__main__":
    grid = {str(dO): [plan(dO, dl) for dl in DEADLINES] for dO in SHIFTS}
    data = dict(start=dict(h=H0, inc=INC, m0=M0, payload=50, xe_tank=round(sm.XE, 1), thrust_mN=sm.T * 1e3,
                           isp=sm.ISP, duty=sm.DUTY, own_rate=round(sm.rate(H0, INC), 3)),
                deadlines=DEADLINES, grid=grid, oneweb=oneweb())
    out = ROOT / "docs" / "data.js"
    out.parent.mkdir(exist_ok=True)
    out.write_text("window.DRIFT = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    g = grid["-15"]
    for dl in (90, 180, 365):
        p = g[DEADLINES.index(dl)]
        print(f"−15° за {dl} сут: {p['xe']} кг, высота ожидания {p['h']} км, {p['days']} сут")
    print(f"спутников OneWeb: {len(data['oneweb'])}, максимум ошибки {max(r['err'] for r in data['oneweb']):.3f}°")
    print(f"записано: {out.relative_to(ROOT)}, {out.stat().st_size // 1024} КБ")
