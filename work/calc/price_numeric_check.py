"""Независимая численная проверка чисел слайда 2 («цена срочности»: сдвиг плоскости −15° с СОО 550 км, буксир 200 кг).
strategy_map.py выбрал для 90, 180 и 365 суток чистый дрейф: спираль вверх до высоты ожидания, ожидание, спираль вниз.
Здесь тот же план летит прямым интегрированием (RK4, шаг 30 с): центральное поле + J2, тяга 55 мН вдоль или против
скорости только на свету (цилиндрическая тень, Солнце в плоскости экватора, вращается 0,9856°/сут, в начале лежит
в плоскости орбиты — худший случай по тени), сопротивление атмосферы по той же таблице плотности, расход массы.
Опорная плоскость клиента — второй спутник, который всё время остаётся на 550 км без тяги, так что формула дрейфа
в проверке не используется. Высота — средняя большая полуось за последний виток.
Отдельно: сколько градусов можно набрать за 60 суток в пределе «весь срок вверх, затем весь вниз».
Запуск: python3 -I work/calc/price_numeric_check.py (около 3 минут, только стандартная библиотека)."""
import math
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategy_map import rho, best            # таблица плотности и выбор плана — из проверяемой модели

MU, RE, J2, G0 = 398600.4418e9, 6378137.0, 1.08262668e-3, 9.80665
T, ISP, CDA, M0 = 0.055, 1500.0, 2.2, 200.0
W_SUN = 2 * math.pi / (365.2422 * 86400)
DT = 30.0

def acc(s, m, t, thrust):
    x, y, z, vx, vy, vz = s
    r2 = x*x + y*y + z*z; r = math.sqrt(r2); k = -MU / (r2 * r)
    f = 1.5 * J2 * MU * RE**2 / r**5; zz = 5 * z*z / r2
    ax = k*x + f*x*(zz - 1); ay = k*y + f*y*(zz - 1); az = k*z + f*z*(zz - 3)
    v = math.sqrt(vx*vx + vy*vy + vz*vz)
    d = 0.5 * rho((r - RE) / 1e3) * v * v * CDA / m          # сопротивление, м/с²
    ax -= d*vx/v; ay -= d*vy/v; az -= d*vz/v
    lit = True
    if thrust:
        cx, cy = math.cos(W_SUN*t), math.sin(W_SUN*t)          # направление на Солнце в плоскости экватора
        p = x*cx + y*cy
        lit = not (p < 0 and r2 - p*p < RE*RE)
        if lit:
            a_t = thrust * T / m
            ax += a_t*vx/v; ay += a_t*vy/v; az += a_t*vz/v
    return (vx, vy, vz, ax, ay, az), lit

def step(s, m, t, thrust):
    k1, lit = acc(s, m, t, thrust)
    k2, _ = acc(tuple(a + DT/2*b for a, b in zip(s, k1)), m, t + DT/2, thrust)
    k3, _ = acc(tuple(a + DT/2*b for a, b in zip(s, k2)), m, t + DT/2, thrust)
    k4, _ = acc(tuple(a + DT*b for a, b in zip(s, k3)), m, t + DT, thrust)
    return tuple(a + DT/6*(b + 2*c + 2*d + e) for a, b, c, d, e in zip(s, k1, k2, k3, k4)), lit

def elems(s):
    x, y, z, vx, vy, vz = s
    hx, hy = y*vz - z*vy, z*vx - x*vz
    r = math.sqrt(x*x + y*y + z*z); v2 = vx*vx + vy*vy + vz*vz
    return 1.0 / (2.0/r - v2/MU), math.degrees(math.atan2(hx, -hy))

def start(h_km):
    r0 = RE + h_km*1e3; v0 = math.sqrt(MU / r0); i = math.radians(97.6)
    return (r0, 0.0, 0.0, 0.0, v0*math.cos(i), v0*math.sin(i))

def fly(h_wait, target, t_up=None, t_max=400):
    """План «вверх — ждать — вниз». Если t_up задан: вверх ровно t_up суток, затем сразу вниз (предел по времени)."""
    s, ref, m, t = start(550), start(550), M0, 0.0
    phase, burn, burn_lit, d_out = "up", 0.0, 0.0, None
    win = deque(maxlen=int(6000 / DT))                         # окно чуть больше витка для средней полуоси
    unwrap, prev, sa, su = 0.0, None, 0.0, 0.0
    while t < t_max * 86400:
        thrust = {"up": 1, "coast": 0, "down": -1}[phase]
        s, lit = step(s, m, t, thrust)
        ref, _ = step(ref, M0, t, 0)
        t += DT
        if thrust:
            burn += DT
            if lit:
                burn_lit += DT; m -= T / (ISP * G0) * DT
        a, om = elems(s); _, om_ref = elems(ref)
        dd = om - om_ref
        if prev is not None:
            unwrap += (dd - prev + 180) % 360 - 180
        else:
            unwrap = dd
        prev = dd
        if len(win) == win.maxlen:
            old = win[0]; sa -= old[0]; su -= old[1]
        win.append((a, unwrap)); sa += a; su += unwrap
        if len(win) < win.maxlen:
            continue
        a_m = sa / len(win) - RE; d_m = su / len(win)
        if phase == "up" and ((t_up is None and a_m >= h_wait*1e3) or (t_up is not None and t >= t_up*86400)):
            phase, d_out = ("coast" if t_up is None else "down"), d_m
        elif phase == "coast" and d_m <= target - d_out:          # на спуске наберём примерно столько же, сколько на подъёме
            phase = "down"
        elif phase == "down" and a_m <= 550e3:
            return dict(days=t/86400, xe=M0 - m, dOmega=d_m, duty=burn_lit/burn if burn else 0, h_top=None)
    return dict(days=t/86400, xe=M0 - m, dOmega=d_m, duty=burn_lit/burn if burn else 0, unfinished=phase)

if __name__ == "__main__":
    print("Сдвиг −15° с СОО 550 км, буксир 200 кг. Модель strategy_map против прямого интегрирования.")
    for dl in (90, 180, 365):
        xe_m, dv_m, days_m, plan = best(M0, 550, 97.6, -15, dl)
        h_wait = int(plan.split("высота ожидания ")[1].split(" км")[0])
        r = fly(h_wait, -15.0)
        print(f"  срок {dl:3d} сут | {plan} | модель: {days_m:6.1f} сут, Xe {xe_m:4.2f} кг | "
              f"численно: {r['days']:6.1f} сут, Xe {r['xe']:4.2f} кг, сдвиг {r['dOmega']:+6.2f}°, доля света {r['duty']:.2f} | "
              f"расхождение: сутки {100*(r['days']/days_m-1):+.1f} %, ксенон {100*(r['xe']/xe_m-1):+.1f} %")
    r = fly(None, -999, t_up=30, t_max=60.5)
    print(f"  предел за 60 сут (30 сут вверх, 30 вниз, тяга всё время на свету): сдвиг {r['dOmega']:+.2f}° из нужных −15°, "
          f"Xe {r['xe']:.2f} кг, не закончено: {r.get('unfinished')}")
