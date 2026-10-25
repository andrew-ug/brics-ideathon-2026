"""Первая независимая сверка слоя 1: прямое интегрирование подъёма 550→1000 км с тягой 55 мН вдоль скорости.
Модель: центральное поле + J2, цилиндрическая тень (Солнце в плоскости экватора по +X, наклонение 97.6°,
узел 0° → бета-угол ≈0, худший случай по тени), тяга только на свету, расход массы по Isp. RK4, шаг 20 с.
Сравнение: Эдельбаум Δv = |v1 − v2| и время по ракетному уравнению. Только стандартная библиотека."""
import math
MU, RE, J2, G0 = 398600.4418e9, 6378137.0, 1.08262668e-3, 9.80665
T, ISP = 0.055, 1500.0
def acc(s, m, shadow):
    x, y, z, vx, vy, vz = s
    r2 = x*x + y*y + z*z; r = math.sqrt(r2); k = -MU / (r2 * r)
    f = 1.5 * J2 * MU * RE**2 / r**5; zz = 5 * z*z / r2
    ax = k*x + f*x*(zz - 1); ay = k*y + f*y*(zz - 1); az = k*z + f*z*(zz - 3)
    lit = not (shadow and x < 0 and y*y + z*z < RE*RE)
    if lit:
        v = math.sqrt(vx*vx + vy*vy + vz*vz); a_t = T / m
        ax += a_t*vx/v; ay += a_t*vy/v; az += a_t*vz/v
    return (vx, vy, vz, ax, ay, az), lit
def run(m0, shadow, h0=550e3, h1=1000e3, dt=20.0):
    r0 = RE + h0; v0 = math.sqrt(MU / r0); i = math.radians(97.6)
    s = (r0, 0.0, 0.0, 0.0, v0*math.cos(i), v0*math.sin(i)); m = m0; t = 0.0; lit_t = 0.0
    while True:
        k1, lit = acc(s, m, shadow)
        s2 = tuple(a + dt/2*b for a, b in zip(s, k1)); k2, _ = acc(s2, m, shadow)
        s3 = tuple(a + dt/2*b for a, b in zip(s, k2)); k3, _ = acc(s3, m, shadow)
        s4 = tuple(a + dt*b for a, b in zip(s, k3)); k4, _ = acc(s4, m, shadow)
        s = tuple(a + dt/6*(b + 2*c + 2*d + e) for a, b, c, d, e in zip(s, k1, k2, k3, k4))
        if lit: m -= T / (ISP * G0) * dt; lit_t += dt
        t += dt
        r = math.sqrt(s[0]**2 + s[1]**2 + s[2]**2); v2 = s[3]**2 + s[4]**2 + s[5]**2
        a = 1.0 / (2.0/r - v2/MU)
        if a - RE >= h1: return t/86400, m0 - m, lit_t/t
for m0 in (150.0, 200.0):
    dv = math.sqrt(MU/(RE+550e3)) - math.sqrt(MU/(RE+1000e3))
    mp = m0 * (1 - math.exp(-dv/(ISP*G0))); t_an = mp*ISP*G0/T/86400
    d_n, xe_n, _ = run(m0, False)
    d_s, xe_s, duty = run(m0, True)
    print(f"m0={m0:.0f} кг | Эдельбаум: {t_an:.1f} сут, Xe {mp:.2f} кг | численно без тени: {d_n:.1f} сут, Xe {xe_n:.2f} кг "
          f"(расхождение {100*(d_n/t_an-1):+.1f} %) | с тенью: {d_s:.1f} сут, доля света {duty:.2f}, Xe {xe_s:.2f} кг | "
          f"Эдельбаум/доля: {t_an/duty:.1f} сут ({100*(d_s/(t_an/duty)-1):+.1f} %), при доле 0.62: {t_an/0.62:.1f} сут")
