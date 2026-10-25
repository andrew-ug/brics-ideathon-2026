"""Реальная проверка модели дрейфа узла J2 на спутниках OneWeb, выведенных индийской LVM3.
LVM3-M3 (26.03.2023, COSPAR 2023-043) и LVM3-M2 (23.10.2022, COSPAR 2022-138). Данные: история TLE Space-Track
(HF juliensimon/space-track-tle-history, CC BY 4.0). Для каждого спутника по его собственной истории большой полуоси и
наклонения интегрируем вековой дрейф узла от J2 и сравниваем с узлом из TLE. Плюс длительность подъёма орбиты."""
import math, json
import numpy as np, pandas as pd, pyarrow.parquet as pq
from huggingface_hub import hf_hub_download
MU, RE, J2 = 398600.4418, 6378.137, 1.08262668e-3
LAUNCHES = {"LVM3-M2 23.10.2022": "2022-10-22", "LVM3-M3 26.03.2023": "2023-03-26"}
# v5: обозначение запуска включает верхние ступени, а не только OneWeb.
# Обе ступени: Foster et al., §5.2 и рис. 8,
# https://lss.fnal.gov/archive/2024/pub/fermilab-pub-24-0844-ppd.pdf
# 56082 также прямо идентифицирована ISRO:
# https://www.isro.gov.in/LVM3_M3UpperStageRe_entersAtmosphere.html
EXCLUDED_ROCKET_BODIES = {54149, 56082}
EXPECTED_COUNTS = {name: 36 for name in LAUNCHES}
frames = []
for year in (2022, 2023):
    path = hf_hub_download("juliensimon/space-track-tle-history", f"data/tle_{year}.parquet", repo_type="dataset")
    t = pq.read_table(path, columns=["norad_id", "epoch", "inclination", "raan", "eccentricity", "mean_motion", "intl_designator", "altitude_km"])
    df = t.to_pandas()
    print(year, "строк всего", len(df), "пример обозначений", df["intl_designator"].dropna().unique()[:5].tolist())
    # v4: отбор по международному обозначению запуска, а не по наклонению. В v3 фильтр 87,2–88,2° выкидывал точки,
    # где наклонение на подъёме опускалось ниже 87,2°, и это выглядело как «дыры в данных» у 29 спутников
    m = df["intl_designator"].fillna("").str[:5].isin(["22138", "23043"])
    m &= ~df["norad_id"].isin(EXCLUDED_ROCKET_BODIES)
    frames.append(df[m]); print("  строк двух запусков LVM3", int(m.sum()), "наклонение мин/макс", df.loc[m, "inclination"].min(), df.loc[m, "inclination"].max())
    del df, t
d = pd.concat(frames).sort_values(["norad_id", "epoch"]).drop_duplicates(["norad_id", "epoch"])
first = d.groupby("norad_id")["epoch"].min()
pick = {}
for name, day in LAUNCHES.items():
    t0 = pd.Timestamp(day, tz="UTC")
    ids = first[(first >= t0) & (first <= t0 + pd.Timedelta(days=4))].index
    for i in ids:
        pick[i] = name
print("выбрано по дате первого TLE:", len(pick))
d = d[d["norad_id"].isin(pick)].copy()
d["launch"] = d["norad_id"].map(pick)
counts = d.groupby("launch")["norad_id"].nunique().to_dict()
if counts != EXPECTED_COUNTS:
    raise SystemExit(f"ожидалось по 36 OneWeb на запуск, получено {counts}; проверь состав выборки")
print("обозначения выбранных:", sorted(d["intl_designator"].dropna().str[:8].unique().tolist())[:12])
n = d["mean_motion"].values * 2 * math.pi / 86400
d["a_km"] = (MU / n**2) ** (1 / 3)
d["h_km"] = d["a_km"] - RE
print(d.groupby("launch")["norad_id"].nunique())
rows = []
for nid, g in d.groupby("norad_id"):
    n_all = len(g)
    g = g[(g["eccentricity"] < 0.01)].copy()
    if len(g) < 30:
        continue
    g = g[(g["h_km"] > 200) & (g["h_km"] < 1400)]
    n_drop = n_all - len(g)
    tt = (g["epoch"] - g["epoch"].iloc[0]).dt.total_seconds().values / 86400
    a = g["a_km"].values; inc = np.radians(g["inclination"].values)
    nn = np.sqrt(MU / a**3)
    rate = -1.5 * nn * J2 * (RE / a) ** 2 * np.cos(inc) * 86400 * 180 / math.pi   # град/сут
    pred = np.concatenate([[0], np.cumsum(0.5 * (rate[1:] + rate[:-1]) * np.diff(tt))])
    obs = np.degrees(np.unwrap(np.radians(g["raan"].values))) - g["raan"].values[0]
    err = obs - pred
    h = g["h_km"].values
    i_end = np.argmax(h > 1190) if (h > 1190).any() else None
    i_start = np.argmax(h > h[:5].min() + 20)
    rows.append(dict(norad=int(nid), launch=g["launch"].iloc[0], n_tle=len(g), days=float(tt[-1]), h0=float(np.median(h[:5])),
                     h_end=float(np.median(h[-5:])), inc=float(np.degrees(inc).mean()), raan_obs_total=float(obs[-1]),
                     raan_pred_total=float(pred[-1]), err_end=float(err[-1]), err_max=float(np.abs(err).max()),
                     raise_days=float(tt[i_end] - tt[i_start]) if i_end else None, wait_low_days=float(tt[i_start]),
                     n_drop=int(n_drop), max_gap=float(np.diff(tt).max()), inc_change=float(np.degrees(inc[-1]-inc[0])),
                     t_err_jump=float(tt[np.argmax(np.abs(np.diff(err)))+1]) if len(err) > 1 else None,
                     err_jump=float(np.abs(np.diff(err)).max()) if len(err) > 1 else None))
    if nid in (54128, 54129, 56046, 56049):
        pd.DataFrame(dict(t=tt, h=h, inc=np.degrees(inc), raan_obs=obs, raan_pred=pred, ecc=g["eccentricity"].values)).to_csv(f"series_{nid}.csv", index=False)
r = pd.DataFrame(rows)
if r.empty:
    raise SystemExit("нет спутников, проверь отбор")
if r.groupby("launch")["norad"].nunique().to_dict() != EXPECTED_COUNTS:
    raise SystemExit("после фильтрации не осталось 72 OneWeb; не публикуй неполную выборку как полную")
r.to_csv("oneweb_drift_check.csv", index=False)
print("\nСпутников с достаточной историей:", len(r))
for L, g in r.groupby("launch"):
    print(f"\n== {L}: {len(g)} спутников, наклонение {g.inc.mean():.2f}°, начальная высота медиана {g.h0.median():.0f} км, конечная {g.h_end.median():.0f} км")
    print(f"  окно наблюдения медиана {g.days.median():.0f} сут")
    print(f"  наблюдаемый уход узла за окно: медиана {g.raan_obs_total.median():.1f}°, разброс между спутниками {g.raan_obs_total.min():.1f}..{g.raan_obs_total.max():.1f}°")
    print(f"  ошибка модели J2 в конце окна: медиана |ошибки| {g.err_end.abs().median():.2f}°, 90-й процентиль {g.err_end.abs().quantile(0.9):.2f}°, макс по траектории медиана {g.err_max.median():.2f}°")
    rel = (g.raan_obs_total - g.raan_obs_total.mean()) ; relp = (g.raan_pred_total - g.raan_pred_total.mean())
    print(f"  разнос плоскостей внутри запуска: наблюдаемый размах {rel.max()-rel.min():.1f}°, предсказанный {relp.max()-relp.min():.1f}°, корреляция {np.corrcoef(rel, relp)[0,1]:.4f}")
    rd = g.raise_days.dropna()
    if len(rd):
        print(f"  подъём до 1190 км: {len(rd)} спутников, медиана {rd.median():.0f} сут (10–90 %: {rd.quantile(0.1):.0f}–{rd.quantile(0.9):.0f}), ожидание на низкой орбите медиана {g.wait_low_days.median():.0f} сут")
print("\nдиагностика выбросов (|ошибка| > 3°) против остальных:")
r["bad"] = r.err_end.abs() > 3
print(r.groupby(["launch", "bad"])[["n_drop", "max_gap", "inc_change", "err_jump", "t_err_jump", "h0", "h_end"]].median().round(3).to_string())
# плотность объектов по высоте: последний TLE каждого объекта за 2026 год, круговые орбиты
path = hf_hub_download("juliensimon/space-track-tle-history", "data/tle_2026.parquet", repo_type="dataset")
z = pq.read_table(path, columns=["norad_id", "epoch", "eccentricity", "mean_motion", "inclination"]).to_pandas()
z = z.sort_values("epoch").groupby("norad_id").tail(1)
z = z[z.eccentricity < 0.02]
z["h"] = (MU / (z.mean_motion * 2 * math.pi / 86400) ** 2) ** (1 / 3) - RE
bins = np.arange(300, 1450, 50)
cnt, _ = np.histogram(z.h, bins)
print("\nобъектов на почти круговых орбитах по высоте (последний TLE 2026):")
for b, c in zip(bins[:-1], cnt):
    print(f"  {b:4d}–{b+50:4d} км: {c}")
json.dump({"n": len(r)}, open("done.json", "w"))
