NAME = UniFi-Protect
ENTRY = udi-unifiprotect-pg3x.py
XML_FILES = profile/*/*.xml

.PHONY: all check clean format fulltest install install-eisy lint test coverage coverage-html coverage-report zip sync-version

all: lint test

check:
	xmllint --noout $(XML_FILES)

install:
	uv sync --dev --group lint

install-eisy:
	uv sync --dev

lint:
	uv run ruff check .

format:
	uv run ruff format .

sync-version:
	uv run python scripts/sync_version.py --entry $(ENTRY)

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage

test:
	uv run pytest

coverage:
	uv run pytest --cov=nodes --cov=utils --cov-report=term-missing

coverage-html:
	uv run pytest --cov=nodes --cov=utils --cov-report=html --cov-report=term-missing

fulltest:
	uv run pre-commit run --all-files

zip:
	@test -f zip_exclude.lst || (echo "zip_exclude.lst missing" && exit 1)
	zip -x@zip_exclude.lst -r $(NAME).zip *
