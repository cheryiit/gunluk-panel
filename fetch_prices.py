# -*- coding: utf-8 -*-
"""Fintables'tan fon fiyatlarini ceker, data.json'a gunluk kayit ekler.

Guvenlik: fiyatlarin tamami cekilemezse ya da bir fiyat sifir/negatifse
data.json'a DOKUNMADAN hata koduyla cikar; bozuk veri asla yazilmaz.
"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

BASE = "https://fintables.com/fonlar/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
PRICE_RE = re.compile(r'\\?"price\\?":\s*([0-9]+(?:\.[0-9]+)?)')


def fetch_price(kod):
    # Python'un TLS imzasi Cloudflare'e takildigi icin curl kullaniyoruz.
    cmd = ["curl", "-s", "-m", "40", BASE + kod,
           "-H", f"User-Agent: {UA}",
           "-H", "Accept: text/html",
           "-H", "Accept-Language: tr-TR,tr;q=0.9,en;q=0.8"]
    last_err = None
    for attempt in range(4):
        try:
            html = subprocess.run(cmd, capture_output=True, timeout=60,
                                  check=True).stdout.decode("utf-8", "replace")
            m = PRICE_RE.search(html)
            if not m:
                raise ValueError("sayfada fiyat bulunamadi")
            price = float(m.group(1))
            if price <= 0:
                raise ValueError("fiyat <= 0")
            return price
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{kod}: fiyat cekilemedi: {last_err}")


def main():
    with open("holdings.json", encoding="utf-8") as f:
        kodlar = [x["kod"] for x in json.load(f)["fonlar"]]

    fiyat = {}
    for kod in kodlar:
        fiyat[kod] = fetch_price(kod)
        print(f"{kod}: {fiyat[kod]}")

    # Turkiye saatiyle bugunun tarihi
    bugun = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d")

    try:
        with open("data.json", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"snapshots": []}

    snaps = data["snapshots"]
    if snaps and snaps[-1]["tarih"] == bugun:
        snaps[-1]["fiyat"] = fiyat          # ayni gun ikinci calisma: guncelle
    elif snaps and snaps[-1]["fiyat"] == fiyat:
        print("Fiyatlar degismemis (hafta sonu / henuz aciklanmamis), kayit eklenmedi.")
        return
    else:
        snaps.append({"tarih": bugun, "fiyat": fiyat})

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"data.json guncellendi: {len(snaps)} kayit, son: {bugun}")


if __name__ == "__main__":
    sys.exit(main())
