"""Тот же предел «30 суток вверх, 30 вниз», что в price_numeric_check.py, для двух положений Солнца:
полдень-полночь (тень на каждом витке) и рассвет-закат (буксир почти всё время на свету).
Запуск: python3 -I work/calc/dawn_dusk_60.py (около минуты)."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import price_numeric_check as m

for name, sun0 in (("полдень-полночь", 0.0), ("рассвет-закат", math.pi / 2)):
    m.SUN0 = sun0
    r = m.fly(None, -999, t_up=30, t_max=60.5)
    print(f"{name}: за 60 сут сдвиг {r['dOmega']:+.2f}° (нужно −15°), доля света {r['duty']:.2f}, Xe {r['xe']:.2f} кг")
