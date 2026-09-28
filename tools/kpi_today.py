#!/usr/bin/env python3
"""
KPI One-Pager — "Bugün · anlık" bölümünü günceller.

  python3 tools/kpi_today.py kpi/index.html <PAROLA> today.json

today.json (iptaller hariç; [ciro, sipariş, satılan adet]):
  {
    "asof": "28 Eylül 2026, 00:00–19:25",
    "total": [284018.66, 171, 185],        # Pixa dashboardSales, tüm mağazalar
    "Hepsiburada": [35121.46, 20, 23],
    "Trendyol2": [1079.5, 1, 2],
    "Idefix": [0, 0, 0]
  }

Trendyol = toplam − diğer üç mağaza. Betik sayfayı çözer, <!--TODAY--> ile
<!--/TODAY--> arasındaki bölümü yeniden yazar ve aynı parolayla şifreler.
Veri ya da parola repoya yazılmaz.
"""
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rebuild  # noqa: E402

STORES = ["Trendyol", "Hepsiburada", "Trendyol2", "Idefix"]
COLORS = {"Trendyol": "#ffa06b", "Hepsiburada": "#ff8f9c", "Trendyol2": "#f2c46b",
          "Idefix": "#7fd8b4", "Toplam": "#9085e9"}


def tl(v, dec=0):
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def money(v):
    if abs(v) >= 1_000_000:
        return tl(v / 1_000_000, 2) + " Mn ₺"
    if abs(v) >= 10_000:
        return tl(v / 1000, 1) + " B ₺"
    return tl(v, 0) + " ₺"


def panel(d):
    tot = d["total"]
    data = {s: d.get(s, [0, 0, 0]) for s in STORES[1:]}
    data["Trendyol"] = [round(tot[i] - sum(data[s][i] for s in STORES[1:]), 2) for i in range(3)]
    data["Toplam"] = tot
    aov = tl(tot[0] / tot[1], 0) + " ₺" if tot[1] else "—"
    tiles = "".join(
        f'<div class="tile"><span class="tl">{l}</span><span class="tv">{v}</span></div>'
        for l, v in (("Ciro", money(tot[0])), ("Sipariş", tl(tot[1])),
                     ("Satılan adet", tl(tot[2])), ("Ort. sepet tutarı", aov)))
    rows = "".join(
        ('<tr class="tot">' if s == "Toplam" else "<tr>")
        + f'<th><span class="sw" style="background:{COLORS[s]}"></span>{s}</th>'
        f'<td><span class="v">{tl(data[s][1])}</span></td><td><span class="v">{tl(data[s][2])}</span></td>'
        f'<td><span class="v">{money(data[s][0])}</span></td></tr>'
        for s in STORES + ["Toplam"])
    return ('<!--TODAY--><div class="panel today"><div class="ph"><h2>Bugün · anlık</h2>'
            f'<span class="live">{d["asof"]} itibarıyla</span></div>'
            f'<div class="tiles t4">{tiles}</div>'
            '<div class="tw"><table class="tt"><thead><tr><th>Mağaza</th><th>Sipariş</th>'
            '<th>Satılan adet</th><th>Ciro</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            '<p class="legend">Gün henüz bitmediği için karşılaştırma yok. Rakamlar belirtilen saate kadar '
            'oluşan siparişleri kapsar, iptaller hariç.</p></div><!--/TODAY-->')


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    page, pw, jpath = sys.argv[1:]
    d = json.load(open(jpath, encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        inner = os.path.join(tmp, "inner.html")
        rebuild.decrypt(page, pw, inner)
        html = open(inner, encoding="utf-8").read()
        new, n = re.subn(r"<!--TODAY-->.*?<!--/TODAY-->", lambda _: panel(d), html, flags=re.S)
        if n != 1:
            sys.exit("TODAY işaretleri bulunamadı")
        open(inner, "w", encoding="utf-8").write(new)
        rebuild.encrypt(inner, pw, page)
    print("güncellendi:", d["asof"])


if __name__ == "__main__":
    main()
