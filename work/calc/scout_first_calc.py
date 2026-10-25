"""Первый расчёт для портфолио: манёвры буксира СКАУТ 1 (данные сайта a-rockets.com).
Модели: Эдельбаум (непрерывная малая тяга, круговые орбиты), дрейф узла от J2.
Неизвестно: масса самого буксира. Берём вилку 100 и 150 кг с ксеноном, это допущение."""
import math
MU, RE, J2, G0 = 398600.4418, 6378.137, 1.08262668e-3, 9.80665
T, ISP, IMP = 0.055, 1500.0, 380e3          # Н, с, Н·с (сайт)
XE = IMP / (ISP * G0)                        # кг ксенона на весь суммарный импульс
DUTY = 0.62                                  # доля витка на солнце (допущение: тяга только на свету)
def v(h): return math.sqrt(MU / (RE + h)) * 1e3          # м/с
def raan_rate(h, i):                                       # град/сут
    a = RE + h; n = math.sqrt(MU / a**3)
    return -1.5 * n * J2 * (RE / a)**2 * math.cos(math.radians(i)) * 86400 * 180 / math.pi
def burn(m0, dv):                                          # кг ксенона, сутки работы с учётом тени
    mp = m0 * (1 - math.exp(-dv / (ISP * G0)))
    return mp, mp * ISP * G0 / T / 86400 / DUTY
print(f"Ксенон на весь суммарный импульс: {XE:.1f} кг, чистое время работы {IMP/T/86400:.0f} сут")
for mtug in (100, 150):
    m0 = mtug + 50
    dvmax = ISP * G0 * math.log(m0 / (m0 - XE))
    print(f"\n== буксир {mtug} кг + ПН 50 кг: запас Δv {dvmax:.0f} м/с, ускорение {T/m0*1e3:.3f} мм/с²")
    for h1, h2 in ((550, 1000), (550, 1500), (400, 2000)):
        dv = abs(v(h1) - v(h2)); mp, d = burn(m0, dv)
        print(f"  высота {h1}→{h2} км: Δv {dv:.0f} м/с, Xe {mp:.1f} кг, {d:.0f} сут")
    for di in (1, 5):
        dv = math.pi / 2 * v(550) * math.radians(di); mp, d = burn(m0, dv)
        print(f"  наклонение ±{di}° на 550 км: Δv {dv:.0f} м/с, Xe {mp:.1f} кг, {d:.0f} сут")
    i_sso = 97.6; dO = 15.0
    dv = math.pi / 2 * v(550) * math.sin(math.radians(i_sso)) * math.radians(dO); mp, d = burn(m0, dv)
    print(f"  разнос плоскостей ΔΩ={dO}° напрямую: Δv {dv:.0f} м/с, Xe {mp:.1f} кг ({'не хватает' if dv > dvmax else 'хватает'}), {d:.0f} сут")
    for dh in (-100, +100, +200, +300):
        # знак важен: выше цели плоскость отстаёт (дрейф < 0), ниже цели обгоняет (> 0). Исправлено 25.10 по атаке W2.
        drift = raan_rate(550 + dh, i_sso) - raan_rate(550, i_sso)
        dv2 = 2 * abs(v(550) - v(550 + dh)); mp, d = burn(m0, dv2)
        print(f"  дрейф J2 на {dh:+d} км: {drift:+.4f} °/сут → {dO:.0f}° за {dO/abs(drift):.0f} сут ({'−' if drift < 0 else '+'}{dO:.0f}°), Δv {dv2:.0f} м/с, Xe {mp:.1f} кг, манёвры {d:.0f} сут")

# Проверка порядка величины на реальном перелёте: OneWeb, ~450→1200 км «approximately 100 days» (доклад оператора, AdvancedSSA 2022),
# тяга 15–17 мН (Yoon et al. 2023). Масса ~150 кг и доля тяги 0,5–0,62 — допущения.
for duty in (0.5, 0.62):
    dv = abs(v(450) - v(1200)); a = 0.016 / 150
    print(f"\nOneWeb 450→1200 км: Δv {dv:.0f} м/с, модель {dv / a / 86400 / duty:.0f} сут при доле тяги {duty} (факт оператора ≈100 сут)")
