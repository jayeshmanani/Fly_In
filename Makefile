install:
	uv sync --python 3.12

run:
	@uv run python3 -m src.main $(MAP)

debug:
	@uv run python3 -m pdb -m src.main $(MAP)

lint:
	uv run flake8 src
	uv run mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src
	uv run mypy src --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete

fclean: clean
	rm -rf .venv

fc: fclean

.PHONY: install run debug lint lint-strict clean fclean fc