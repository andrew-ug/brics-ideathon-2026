"""Сборка слайдов ДРЕЙФ: исходник + графики → HTML → PDF и скриншоты слайдов.
Графики: python3 -I work/tools/make_charts.py (пишет out/slides/charts/*.svg).
Запуск: python3 -I work/tools/build_deck.py [--pdf]
PDF рисует headless Chrome.
Скриншоты кладутся рядом с профилем Chrome в $DECK_SHOTS (по умолчанию ./deck_shots)."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / "out/slides"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

src = (S / "drift_portfolio_v4.src.html").read_text(encoding="utf-8")
html = src.replace("{{PRICE}}", (S / "charts/price_of_urgency.svg").read_text(encoding="utf-8")) \
          .replace("{{ONEWEB}}", (S / "charts/oneweb_model_vs_fact.svg").read_text(encoding="utf-8"))
assert "{{" not in html, "осталась неподставленная метка"
out = S / "drift_portfolio_v4.html"
out.write_text(html, encoding="utf-8")
print("html", len(html), "знаков, незаполненных полей:", html.count('class="fill"'))

if "--pdf" in sys.argv:
    shots = Path(os.environ.get("DECK_SHOTS", "deck_shots")).resolve()
    shots.mkdir(parents=True, exist_ok=True)
    base = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={shots}/chrome-prof"]
    subprocess.run(base + ["--no-pdf-header-footer", f"--print-to-pdf={S}/drift_portfolio_v4.pdf", out.as_uri()],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    # по слайду на скриншот: оставляем шапку со стилями и один <section>
    head = html[:html.find("<!-- 1.")]
    parts = html.split('<section class="slide">')[1:]
    for k, p in enumerate(parts, 1):
        f = shots / f"s{k}.html"
        f.write_text(head + '<section class="slide">' + p.split("</section>")[0] + "</section></body></html>", encoding="utf-8")
        subprocess.run(base + ["--window-size=1280,720", f"--screenshot={shots}/s{k}.png", f.as_uri()],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("pdf", (S / "drift_portfolio_v4.pdf").stat().st_size, "байт, скриншоты в", shots)
