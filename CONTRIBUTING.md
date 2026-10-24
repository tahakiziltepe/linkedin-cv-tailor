# Katkı Rehberi

Katkılara açığım. Proje kişisel otomasyon kökenli; küçük ve odaklı PR'lar
tercih edilir.

## Bir sorun mu buldun?

1. README'nin "1 yıl sonra muhtemelen bozulacak şeyler" bölümüne bak:
   genelde ya Gemini modeli kapalıdır (5.1) ya da scrape boş döner (5.2).
2. Model kapanması (404) için: hata metnini ve önerilen yeni model adını
   içeren bir issue aç.

## Kod değişikligi icin

1. Depoyu fork'la ve clone'la; `uv sync` ile .venv kur.
2. `uv run python doctor.py` ile ortamın sağlıklı oldugunu doğrula.
3. Degisikligi kucuk ve tek amaclu tut; aciklamayi PR metnine yaz.
4. README'yi güncelle (uyarlar, komutlar, arıza notları).
5. Test yoksa en azindan `uv run python -m py_compile main.py src/*.py`
   calistir.

## Bilinmesi gereken

- Lisans MIT; katkilariniz da MIT altında kabul edilebilir.
- Bu repo kişisel kullanım için yazıldı; ticari garantisi yoktur.
