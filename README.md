# tangle-teezer-panosu

Raporlar GitHub Pages üzerinde yayınlanır.

| Sayfa | Yol | Durum |
|---|---|---|
| Raporlar (ana sayfa) | `index.html` | açık |
| Tangle Teezer Performans Panosu | `performans/index.html` | parola korumalı |
| Trendyol Reklam Performansı | `reklam/index.html` | parola korumalı |

Korumalı sayfaların içeriği gzip'lenip AES-256-GCM ile şifrelenmiş olarak sayfaya
gömülüdür; anahtar paroladan PBKDF2-SHA256 (250.000 tur) ile türetilir ve çözme
işlemi yalnızca tarayıcıda yapılır.

## Güncelleme

```bash
# yayındaki sayfayı düzenlenebilir kaynağa çevir
python3 tools/rebuild.py decrypt reklam/index.html '<PAROLA>' inner.html

# inner.html'i düzenle, sonra yeniden şifrele
python3 tools/rebuild.py encrypt inner.html '<PAROLA>' reklam/index.html
```

`inner.html` şifrelenmemiş veriyi içerir — repoya commit etmeyin.
