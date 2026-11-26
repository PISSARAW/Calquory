.PHONY: demo test

demo:
	@set -eu; bundle=$$(mktemp); trap 'rm -f "$$bundle"' EXIT; python3 -m calquory reduce examples/events.json examples/policy.json > "$$bundle"; cat "$$bundle"; python3 -m calquory replay "$$bundle"

test:
	python3 -m unittest discover -s tests -v

.PHONY: setup quality

setup:
	git config --local core.hooksPath .githooks

quality:
	sh quality/gate.sh staged
