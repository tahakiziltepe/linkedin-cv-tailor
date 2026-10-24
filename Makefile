.PHONY: setup doctor run web daily hash-users

# Bagimliliklari kur ve ortam sagligini dogrula
setup:
	uv sync
	uv run python doctor.py

# Ortam saglik kontrolu (API anahtar tarasi, typst, tracker)
doctor:
	uv run python doctor.py

# Manuel CV uretimi. Ornek: make run ARGS='-q "data engineer" -n 3'
run:
	uv run python main.py $(ARGS)

# Web paneli (localhost:5000)
web:
	uv run python webapp/web_app.py

# Gunluk toplu tur (config.toml'daki sorgular)
daily:
	./run_daily.sh

# users.json duz metin sifrelerini hash'e gecir (birkel kez calistirmak yeterli)
hash-users:
	uv run python tools/hash_users.py
