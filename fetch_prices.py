# -*- coding: utf-8 -*-
"""Fintables'tan fon fiyatlarini ceker, data.json'a gunluk kayit ekler.

Once curl ile dener; Cloudflare engeline takilirsa Playwright (gercek Chromium)
ile tekrar dener. Fiyatlarin tamami cekilemezse ya da bir fiyat sifir/negatifse
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


def parse_price(html, kaynak, kod):
    m = PRICE_RE.search(html)
    if not m:
        snippet = re.sub(r"\s+", " ", html[:250])
        raise ValueError(f"{kod} {kaynak}: fiyat bulunamadi ({len(html)} bayt): {snippet}")
    price = float(m.group(1))
    if price <= 0:
        raise ValueError(f"{kod} {kaynak}: fiyat <= 0")
    return price


def curl_fetch(kod):
    # Python'un TLS imzasi Cloudflare'e takildigi icin curl kullaniyoruz.
    cmd = ["curl", "-s", "-m", "40", BASE + kod,
           "-H", f"User-Agent: {UA}",
           "-H", "Accept: text/html",
           "-H", "Accept-Language: tr-TR,tr;q=0.9,en;q=0.8"]
    last_err = None
    for attempt in range(2):
        try:
            html = subprocess.run(cmd, capture_output=True, timeout=60,
                                  check=True).stdout.decode("utf-8", "replace")
            if "Just a moment" in html:
                raise ValueError("Cloudflare engeli")
            return parse_price(html, "curl", kod)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if "Cloudflare" in str(e):
                break  # engel kalici, tekrar denemenin anlami yok
            time.sleep(4)
    raise RuntimeError(str(last_err))


def browser_fetch(kodlar):
    """Cloudflare'in otomatik kontrolunu gercek Chromium ile gec."""
    from playwright.sync_api import sync_playwright
    fiyat = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(user_agent=UA, locale="tr-TR",
                            timezone_id="Europe/Istanbul")
        pg = ctx.new_page()
        for kod in kodlar:
            pg.goto(BASE + kod, wait_until="domcontentloaded", timeout=60000)
            html = ""
            for _ in range(40):  # challenge'in cozulmesini bekle (en cok 40 sn)
                html = pg.content()
                if PRICE_RE.search(html):
                    break
                pg.wait_for_timeout(1000)
            fiyat[kod] = parse_price(html, "browser", kod)
            print(f"{kod}: {fiyat[kod]} (browser)")
        b.close()
    return fiyat


def main():
    with open("holdings.json", encoding="utf-8") as f:
        kodlar = [x["kod"] for x in json.load(f)["fonlar"]]

    fiyat, kalan = {}, []
    for kod in kodlar:
        try:
            fiyat[kod] = curl_fetch(kod)
            print(f"{kod}: {fiyat[kod]}")
        except Exception as e:  # noqa: BLE001
            print(f"{kod}: curl basarisiz ({e}), tarayici kuyruguna alindi")
            kalan.append(kod)

    if kalan:
        fiyat.update(browser_fetch(kalan))

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
