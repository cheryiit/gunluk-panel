# Günlük Kazanç Paneli

Portföydeki fonların günlük kazancını gösteren statik sayfa. GitHub Pages üzerinde yayınlanır,
fiyatlar her iş günü GitHub Actions ile otomatik güncellenir.

## Nasıl çalışır

- **`holdings.json`** — fon kodları ve adetler. **Tek düzenlenecek dosya budur.**
  Adet değiştirmek / fon eklemek-çıkarmak için bu dosyayı düzenleyip commitle; sayfa gerisini kendisi hesaplar.
- **`fetch_prices.py`** — Fintables'tan (TEFAS verisi) fiyatları çeker, `data.json`'a günlük kayıt ekler.
  Tüm fiyatlar çekilemezse hiçbir şey yazmaz (bozuk veri koruması).
- **`data.json`** — gün gün fiyat geçmişi. Elle düzenleme; Actions doldurur.
  `arsiv_p1` anahtarı 21.08.2026'da çıkılan eski P1 portföyünün kaydıdır, sayfa okumaz.
- **`.github/workflows/guncelle.yml`** — hafta içi 10:40 ve 15:30 (TR) otomatik çalışır.
  Elle tetiklemek için: Actions sekmesi → *Fiyat Guncelle* → *Run workflow*.
- **`index.html`** — sayfa. Hiçbir dış girdi kabul etmez; yalnızca depodaki `holdings.json` +
  `data.json` verisini gösterir. Dışarıdan manipüle edilemez — veriyi sadece depoya yazma
  yetkisi olanlar değiştirebilir.

## Notlar

- Fon fiyatları günde bir kez açıklanır; sayfadaki "son fiyat" bir önceki iş gününün fiyatı olabilir.
- Kazanç rakamları stopaj öncesi brüt rakamlardır.
- İzlenen sepet: **SKOR v4 #1** (TLY %35,2 · TP2 %17,3 · DFI %9,4 · PTO %8,1 · IJZ %7,2 ·
  IHC %6,0 · LPH %5,2 · GPG %5,2 · RBR %3,7 · HEH %2,6). P1'den 21.08.2026'da geçildi;
  adetler geçiş planındaki hedef TL tutarlarının o günkü fiyatlara bölünmesiyle bulundu.
- Geçmiş 21.08.2026'da sıfırdan başlar (yeni sepetin öncesi yok); grafik ve gün gün kartları
  ikinci kayıttan itibaren dolar.
- Sayfa mobil uyumludur; grafikte ipucu için dokunman yeterli.
