"""Карта выбора стратегии для буксира СКАУТ: когда выгоден дрейф плоскости от J2, когда прямой манёвр, когда никак.
Задача: перевести груз с орбиты попутного запуска (h0, i) в плоскость, сдвинутую по узлу на dO, к сроку deadline.
Стратегии: прямой поворот узла тягой (Эдельбаум), дрейф на высоте h0+dh с возвратом, гибрид (часть дрейфом, остаток тягой).
Учтены тень (тяга только на свету), расход массы, сопротивление на низкой орбите ожидания (компенсируется тягой).
Не учтены: фазирование внутри плоскости, оптимальное совмещение подъёма и поворота, сезонность тени. Это модель первого порядка.
Запуск: python3 work/calc/strategy_map.py > work/calc/strategy_map.out"""
import math
MU, RE, J2, G0 = 398600.4418, 6378.137, 1.08262668e-3, 9.80665
T, ISP, IMP, DUTY = 0.055, 1500.0, 380e3, 0.62      # сайт А-РОКЕТС, DUTY — допущение
VE = ISP * G0
XE = IMP / VE                                       # 25.8 кг ксенона на весь суммарный импульс
CDA = 2.2 * 1.0                                     # Cd·A, м² (допущение: 1 м² поперечного сечения)
H_MIN = 350                                         # ниже орбиту ожидания не опускаем
RHO = [(300, 1.9e-11), (350, 7.0e-12), (400, 2.8e-12), (450, 1.2e-12), (500, 5.2e-13),
       (600, 1.1e-13), (700, 3.0e-14), (800, 9.0e-15), (1000, 1.5e-15), (1500, 1e-16)]  # кг/м³, средняя солнечная активность

def v(h): return math.sqrt(MU / (RE + h)) * 1e3
def rate(h, i):                                     # град/сут
    a = RE + h; n = math.sqrt(MU / a**3)
    return -1.5 * n * J2 * (RE / a)**2 * math.cos(math.radians(i)) * 86400 * 180 / math.pi
def rho(h):
    for (h1, r1), (h2, r2) in zip(RHO, RHO[1:]):
        if h1 <= h <= h2:
            return r1 * (r2 / r1) ** ((h - h1) / (h2 - h1))
    return RHO[-1][1]
def plan_cost(m0, legs):
    """legs: список Δv (м/с) по порядку. Возвращает (Δv сумма, кг Xe, сутки работы двигателя)."""
    m, days = m0, 0.0
    for dv in legs:
        mp = m * (1 - math.exp(-dv / VE)); m -= mp
        days += mp * VE / T / 86400 / DUTY
    return sum(legs), m0 - m, days

def best(m0, h0, i, dO, deadline):
    """Минимум ксенона при сроке. Возвращает (xe, dv, сутки, описание) или None."""
    k = math.pi / 2 * v(h0) * math.sin(math.radians(i)) * math.pi / 180   # м/с на градус узла
    out = None
    for dh in range(-(h0 - H_MIN), 1001, 10):
        dr = rate(h0 + dh, i) - rate(h0, i)
        dv_h = abs(v(h0) - v(h0 + dh))
        for step in range(0, 81):                    # доля узла, которую берём тягой: 0..100 %
            part = abs(dO) * step / 80
            rest = abs(dO) - part
            if rest > 1e-9 and (dh == 0 or dr * math.copysign(1, dO) <= 0):
                continue                             # дрейф не в ту сторону
            _, _, t_tr = plan_cost(m0, [dv_h, k * part, dv_h])
            if dh == 0:
                wait = 0.0
            else:                                    # на спиралях высота меняется, считаем половину дрейфа
                wait = max(0.0, rest / abs(dr) - t_tr / 2)
            total = t_tr + wait
            if total > deadline:
                continue
            drag = 0.5 * rho(h0 + dh) * v(h0 + dh)**2 * CDA / m0 * wait * 86400   # м/с на компенсацию
            dv, xe, _ = plan_cost(m0, [dv_h, k * part, drag, dv_h])
            if xe > XE:
                continue
            if out is None or xe < out[0]:
                kind = "прямо" if dh == 0 else ("дрейф" if part == 0 else "гибрид")
                out = (xe, dv, total, f"{kind}: высота ожидания {h0 + dh} км, тягой {part:.1f}° из {abs(dO):.0f}°")
    return out

if __name__ == "__main__":
    m0 = 150 + 50
    print(f"Буксир 150 кг + груз 50 кг = {m0} кг, ксенона на борту {XE:.1f} кг, тяга {T*1e3:.0f} мН, Isp {ISP:.0f} с, доля тяги на свету {DUTY}")
    for h0, i, name in ((550, 97.6, "СОО 550 км (типичный попутный запуск)"),
                        (500, 97.4, "СОО 500 км (высота как у иранских Kowsar и Hodhod, «Союз» 5.11.2024, наклонение СОО — допущение)"),
                        (550, 53.0, "550 км, 53° (наклонение группировок)")):
        print(f"\n== {name}: собственный дрейф узла {rate(h0, i):+.3f} °/сут")
        print("  сдвиг узла | срок 30 сут | 60 сут | 90 сут | 180 сут | 365 сут   (кг ксенона, «—» = невыполнимо)")
        for dO in (-30, -15, -5, +5, +15, +30):
            cells = []
            for dl in (30, 60, 90, 180, 365):
                r = best(m0, h0, i, dO, dl)
                cells.append(f"{r[0]:5.1f}" if r else "    —")
            print(f"  {dO:+4d}°      | " + " | ".join(cells))
        for dO, dl in ((-15, 180), (+15, 180), (-15, 60)):
            r = best(m0, h0, i, dO, dl)
            print(f"  пример {dO:+d}° за {dl} сут: " + (f"{r[3]}, Δv {r[1]:.0f} м/с, Xe {r[0]:.1f} кг, {r[2]:.0f} сут" if r else "невыполнимо"))
