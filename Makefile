quickstart:
	pip install --upgrade pip && \
	pip install -r requirements.txt && \
	python run_fetcher.py --once && \
	python advisor.py --once

fetch:
	python run_fetcher.py

advisor:
	python advisor.py --once

live:
	python advisor.py

test:
	pytest --cov=app tests/ && flake8 . --exit-zero

docker-up:
	docker-compose up -d
