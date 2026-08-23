# -*- coding: utf-8 -*-
"""Fon fiyat gecmisini ceker ve data.json'u sifirdan kurar.

Kaynak: Fintables'in TradingView-uyumlu gunluk seri ucu (barbar/udf/history).
Sayfa kazimasina gore avantaji: her barin GERCEK tarihi var, gecmis gunler de
geliyor. Bu yuzden data.json her calismada bastan uretilir -- workflow bir gun
calismasa bile eksik gun kendiliginden dolar, mukerrer kayit olusmaz.

Yalnizca TUM fonlarin fiyat verdigi "tam gunler" kaydedilir; bir fonun fiyati
henuz aciklanmamissa o gun hic yazilmaz (yarim gun sahte kazanc gostermesin).
Herhangi bir fon icin veri alinamazsa data.json'a DOKUNULMADAN hata ile cikilir.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone

UDF = "https://markets.fintables.com/barbar/udf/history"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
FROM, TO = 1700000000, 2000000000        # genis aralik: fonun tum gecmisi
BASLANGIC = "2026-08-21"                 # portfoyun izlenmeye baslandigi gun


def _seri(ham, kod):
    d = json.loads(ham)
    if d.get("s") != "ok" or not d.get("t"):
        raise ValueError(f"{kod}: seri yok (durum={d.get('s')})")
    out = {}
    for ts, kapanis in zip(d["t"], d["c"]):
        if kapanis and kapanis > 0:
            gun = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
            out[gun] = float(kapanis)
    if not out:
        raise ValueError(f"{kod}: gecerli kapanis yok")
    return out


def curl_seri(kod):
    url = f"{UDF}?symbol={kod}&resolution=D&from={FROM}&to={TO}"
    ham = subprocess.run(
        ["curl", "-s", "-m", "45", url, "-H", f"User-Agent: {UA}",
         "-H", "Accept: application/json", "-H", "Referer: https://fintables.com/"],
        capture_output=True, timeout=70, check=True).stdout.decode("utf-8", "replace")
    if "Just a moment" in ham or ham.lstrip().startswith("<"):
        raise ValueError("Cloudflare engeli")
    return _seri(ham, kod)


def tarayici_seri(kodlar):
    """curl engellenirse gercek Chromium ile ayni uca git."""
    from playwright.sync_api import sync_playwright
    sonuc = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(user_agent=UA, locale="tr-TR", timezone_id="Europe/Istanbul")
        pg = ctx.new_page()
        pg.goto("https://fintables.com/", wait_until="domcontentloaded", timeout=60000)
        for kod in kodlar:
            url = f"{UDF}?symbol={kod}&resolution=D&from={FROM}&to={TO}"
            ham = pg.evaluate(
                "async u => (await fetch(u, {headers: {'Accept': 'application/json'}})).text()", url)
            sonuc[kod] = _seri(ham, kod)
            print(f"{kod}: {len(sonuc[kod])} gun (tarayici)")
        b.close()
    return sonuc


def main():
    with open("holdings.json", encoding="utf-8") as f:
        kodlar = [x["kod"] for x in json.load(f)["fonlar"]]

    seri, kalan = {}, []
    for kod in kodlar:
        try:
            seri[kod] = curl_seri(kod)
            print(f"{kod}: {len(seri[kod])} gun")
        except Exception as e:                                    # noqa: BLE001
            print(f"{kod}: curl basarisiz ({e}), tarayici kuyruguna alindi")
            kalan.append(kod)
            time.sleep(1)
    if kalan:
        seri.update(tarayici_seri(kalan))

    eksik = [k for k in kodlar if k not in seri]
    if eksik:
        raise RuntimeError(f"veri alinamayan fonlar: {eksik}")

    # yalnizca her fonun fiyat verdigi gunler
    tam = set(seri[kodlar[0]])
    for k in kodlar[1:]:
        tam &= set(seri[k])
    gunler = sorted(g for g in tam if g >= BASLANGIC)
    if not gunler:
        raise RuntimeError(f"{BASLANGIC} sonrasi tam gun yok -- data.json korundu")

    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)
    data["snapshots"] = [{"tarih": g, "fiyat": {k: seri[k][g] for k in kodlar}}
                         for g in gunler]
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    atlanan = sorted(g for g in set().union(*seri.values()) if g >= BASLANGIC and g not in tam)
    print(f"data.json kuruldu: {len(gunler)} tam gun, {gunler[0]} -> {gunler[-1]}")
    if atlanan:
        print("henuz tamamlanmamis gunler (tum fonlar fiyat aciklamadi):", ", ".join(atlanan))


if __name__ == "__main__":
    sys.exit(main())
