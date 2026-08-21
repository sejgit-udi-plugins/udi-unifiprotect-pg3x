
.PHONY: all check clean

all: check

check:
	xmllint --noout profile/nodedef/nodedefs.xml profile/editor/editors.xml

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
