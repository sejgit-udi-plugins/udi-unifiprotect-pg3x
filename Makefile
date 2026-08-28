ENTRY = udi-unifiprotect-pg3x.py

.PHONY: all check clean sync-version

all: check

check:
	xmllint --noout profile/nodedef/nodedefs.xml profile/editor/editors.xml

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +

sync-version:
	python3 scripts/sync_version.py --entry $(ENTRY)
