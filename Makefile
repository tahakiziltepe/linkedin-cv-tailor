.PHONY: setup doctor run web daily hash-users test test-live test-all test-clean check

# Bagimliliklari kur ve ortam sagligini dogrula
setup:
	uv sync
	uv run python doctor.py

# Ortam saglik kontrolu (API anahtar tarasi, typst, tracker, promptlar)
doctor:
	uv run python doctor.py

# Offline test paketi (ag/API yok; yayin oncesi zorunlu kapi)
test:
	uv run pytest -q -m "not live"

# Gercek Gemini cagrisi yapan opt-in testler (kota harcar)
test-live:
	RUN_LIVE_TESTS=1 uv run pytest -q -m live

# Offline + canli testler
test-all: test test-live

# Temiz makine simulasyonu (yavas; varsayilan testlere girmez)
test-clean:
	uv run pytest -q -m clean

# Tek komutta yayin oncesi kontrol: sozdizimi + doctor (offline) + testler
check:
	uv run python -m py_compile main.py doctor.py src/*.py webapp/web_app.py tools/*.py
	uv run python doctor.py --offline
	$(MAKE) test

# Manuel CV uretimi. Ornek: make run ARGS='-q "data engineer" -n 3'
run:
	uv run python main.py $(ARGS)

# Web paneli (localhost:5000)
web:
	uv run python webapp/web_app.py

# Gunluk toplu tur (config.toml'daki sorgular)
daily:
	./run_daily.sh

# users.json duz metin sifrelerini hash'e gecir (bir kez calistirmak yeterli)
hash-users:
	uv run python tools/hash_users.py
