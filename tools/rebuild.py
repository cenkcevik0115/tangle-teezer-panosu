#!/usr/bin/env python3
"""
Tangle Teezer performans panosu — sifreleme/cozme araci.

Pano, GitHub Pages uzerinde tek bir index.html olarak yayinlanir. Panonun tum
icerigi (stiller + HTML + veri betigi) gzip'lenip AES-256-GCM ile sifrelenmis
olarak sayfanin icine gomulur; anahtar paroladan PBKDF2-SHA256 (250.000 tur)
ile turetilir. Bu betik iki isi yapar:

  python3 rebuild.py decrypt index.html <PAROLA> inner.html
      Yayindaki index.html icindeki sifreli blogu cozer ve duzenlenebilir
      kaynagi (inner.html) yazar. inner.html bir <style> blogu, panonun HTML'i
      ve verilerin bulundugu <script> blogundan olusur.

  python3 rebuild.py encrypt inner.html <PAROLA> index.html
      Duzenlenmis kaynagi yeniden sifreler ve yayina hazir index.html'i yazar
      (parola ekrani + sifreli blok).

Parola hicbir yerde saklanmaz; her calistirmada arguman olarak verilir.
"""

import base64
import gzip
import hashlib
import os
import sys

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # pragma: no cover
    sys.exit("Eksik bagimlilik: pip install cryptography --break-system-packages")

ITER = 250_000
MARK = 'octet-stream">'
END = "</" + "script>"

GATE = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Korumalı Pano</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%94%92%3C/text%3E%3C/svg%3E">
<style>
  :root{ color-scheme: dark; }
  html,body{ height:100%; }
  body{ margin:0; background:#000; color:#fff;
        font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif; }
  #gate{ min-height:100dvh; display:grid; place-items:center; padding:24px; }
  .box{ width:100%; max-width:380px; background:#0e0e10;
        border:1px solid rgba(255,255,255,.20); border-radius:18px; padding:30px 28px 26px; }
  .lock{ font-size:26px; line-height:1; margin-bottom:16px; }
  h1{ font-family:"Manrope",system-ui,sans-serif; font-size:20px; font-weight:800;
      letter-spacing:-.018em; margin:0 0 7px; }
  p.hint{ font-size:13px; color:#8f8d87; margin:0 0 20px; line-height:1.55; }
  label{ display:block; font-size:12.5px; font-weight:500; margin-bottom:7px; color:#c3c2b7; }
  input{ width:100%; padding:12px 14px; font-size:15px; font-family:inherit;
         border:1px solid rgba(255,255,255,.22); border-radius:10px; background:#16161a;
         color:#fff; box-sizing:border-box; }
  input:focus{ outline:2px solid #9085e9; outline-offset:1px; border-color:transparent; }
  button{ width:100%; margin-top:13px; padding:12px 16px; font-size:14.5px; font-weight:700;
          font-family:inherit; color:#0b0b0f; background:#9085e9; border:0; border-radius:10px; cursor:pointer; }
  button:hover{ background:#a79ef0; }
  button:disabled{ opacity:.55; cursor:default; }
  .err{ margin-top:13px; font-size:13px; color:#e66767; min-height:18px; }
</style>
</head>
<body>
<div id="gate">
  <form class="box" id="f">
    <div class="lock">&#128274;</div>
    <h1>Bu pano korumalıdır</h1>
    <p class="hint">İçeriği görüntülemek için parolayı girin. Veriler sayfa içinde şifrelenmiş olarak tutulur ve yalnızca tarayıcınızda çözülür.</p>
    <label for="p">Parola</label>
    <input id="p" type="password" autocomplete="current-password" autofocus>
    <button id="b" type="submit">Panoyu aç</button>
    <div class="err" id="e"></div>
  </form>
</div>
<script id="payload" type="application/octet-stream">__BLOB__@@END@@
<script>
(function(){
  const ITER = 250000;
  const b64 = document.getElementById('payload').textContent.trim();
  const f = document.getElementById('f'), inp = document.getElementById('p'),
        btn = document.getElementById('b'), err = document.getElementById('e');

  function bytes(s){ const bin = atob(s); const u = new Uint8Array(bin.length);
    for (let i=0;i<bin.length;i++) u[i]=bin.charCodeAt(i); return u; }

  async function open_(pw){
    const raw = bytes(b64);
    const salt = raw.slice(0,16), iv = raw.slice(16,28), ct = raw.slice(28);
    const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw),
                   'PBKDF2', false, ['deriveKey']);
    const key = await crypto.subtle.deriveKey(
      { name:'PBKDF2', salt, iterations:ITER, hash:'SHA-256' }, base,
      { name:'AES-GCM', length:256 }, false, ['decrypt']);
    const out = await crypto.subtle.decrypt({ name:'AES-GCM', iv }, key, ct);
    const ds = new DecompressionStream('gzip');
    const stream = new Blob([out]).stream().pipeThrough(ds);
    return await new Response(stream).text();
  }

  function render(html){
    document.body.innerHTML = html;
    document.body.querySelectorAll('script').forEach(old => {
      const s = document.createElement('script');
      for (const a of old.attributes) s.setAttribute(a.name, a.value);
      s.textContent = old.textContent;
      old.replaceWith(s);
    });
    try { sessionStorage.setItem('ttp', '1'); } catch(_){}
  }

  f.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    err.textContent = ''; btn.disabled = true; btn.textContent = 'Açılıyor…';
    try {
      render(await open_(inp.value));
    } catch(_) {
      err.textContent = 'Parola hatalı.';
      btn.disabled = false; btn.textContent = 'Panoyu aç';
      inp.select();
    }
  });
})();
@@END@@
</body>
</html>
"""


def decrypt(path_in: str, password: str, path_out: str) -> None:
    page = open(path_in, encoding="utf-8").read()
    a = page.index(MARK) + len(MARK)
    z = page.index(END, a)
    raw = base64.b64decode(page[a:z])
    salt, iv, ct = raw[:16], raw[16:28], raw[28:]
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITER, 32)
    inner = gzip.decompress(AESGCM(key).decrypt(iv, ct, None)).decode("utf-8")
    open(path_out, "w", encoding="utf-8").write(inner)
    print(f"cozuldu -> {path_out} ({len(inner)} karakter)")


def encrypt(path_in: str, password: str, path_out: str) -> None:
    inner = open(path_in, encoding="utf-8").read()
    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITER, 32)
    ct = AESGCM(key).encrypt(iv, gzip.compress(inner.encode("utf-8"), 9), None)
    blob = base64.b64encode(salt + iv + ct).decode()
    page = GATE.replace("__BLOB__", blob).replace("@@END@@", END)
    open(path_out, "w", encoding="utf-8").write(page)
    print(f"sifrelendi -> {path_out} ({len(page)} bayt, blob {len(blob)})")


def main() -> None:
    if len(sys.argv) != 5 or sys.argv[1] not in ("decrypt", "encrypt"):
        sys.exit(__doc__)
    mode, src, pw, dst = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    (decrypt if mode == "decrypt" else encrypt)(src, pw, dst)


if __name__ == "__main__":
    main()
