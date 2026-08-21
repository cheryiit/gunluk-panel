# Günlük Kazanç Paneli

Portföydeki fonların günlük kazancını gösteren statik sayfa. GitHub Pages üzerinde yayınlanır,
fiyatlar her iş günü GitHub Actions ile otomatik güncellenir.

## Nasıl çalışır

- **`holdings.json`** — fon kodları ve adetler. **Tek düzenlenecek dosya budur.**
  Adet değiştirmek / fon eklemek-çıkarmak için bu dosyayı düzenleyip commitle; sayfa gerisini kendisi hesaplar.
- **`fetch_prices.py`** — Fintables'tan (TEFAS verisi) fiyatları çeker, `data.json`'a günlük kayıt ekler.
  Tüm fiyatlar çekilemezse hiçbir şey yazmaz (bozuk veri koruması).
- **`data.json`** — gün gün fiyat geçmişi. Elle düzenleme; Actions doldurur.
- **`.github/workflows/guncelle.yml`** — hafta içi 10:40 ve 15:30 (TR) otomatik çalışır.
  Elle tetiklemek için: Actions sekmesi → *Fiyat Guncelle* → *Run workflow*.
- **`index.html`** — sayfa. Hiçbir dış girdi kabul etmez; yalnızca depodaki `holdings.json` +
  `data.json` verisini gösterir. Dışarıdan manipüle edilemez — veriyi sadece depoya yazma
  yetkisi olanlar değiştirebilir.

## Notlar

- Fon fiyatları günde bir kez açıklanır; sayfadaki "son fiyat" bir önceki iş gününün fiyatı olabilir.
- Kazanç rakamları stopaj öncesi brüt rakamlardır.
- Geçmiş 17.08.2026 anlık görüntüsüyle tohumlanmıştır; grafik zamanla uzar.
