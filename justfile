# Task runner: https://github.com/casey/just
# Requires: `uv`, `npm`, and `just`.
# Editable package path under `src/` (passed to `coverage run --source`).

# List all the justfile recipes.
help:
    just --list --list-prefix 'just '

# Remove all the Python and Node.js cache files
clean-pyc:
    find . -name '*.pyc' -exec rm -f {} +
    find . -name '*.pyo' -exec rm -f {} +
    find . -name '*~' -exec rm -f {} +

# Remove all the database files.
clean-db:
    find . -type f \( -name '*.db' -o -name '*.sqlite3' -o -name '*.sqlite' -o -name '*.sqlite3-journal' \) -not -path './.venv/*' -not -path './node_modules/*' -delete
    rm -f demo/db.sqlite3 test_wagtail_daisIE.db

# Install the dependencies.
install: clean-db clean-pyc
    uv sync --dev
    npm ci

# Lint the server code with uv.
lint-server:
    uv run ruff format --check .
    uv run ruff check .
    SKIP=ruff-check,ruff-format,lint:css,lint:format uv run prek run --all-files

# Lint the client code with Prettier.
lint-client:
    npm run lint --loglevel silent

# Run all linters.
lint: lint-server lint-client

# Format the server code with uv.
format-server:
    uv run ruff check . --fix
    uv run ruff format .
    SKIP=ruff-check,ruff-format,lint:css,lint:format uv run prek run --all-files

# Format the client code with Prettier.
format-client:
    npm run format

# Run all formatters.
format: format-server format-client

# Run tests with pytest.
test:
    uv run pytest

test-lowest-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    lowest_python=$(uv run python -c 'import tomllib; print(tomllib.load(open("pyproject.toml","rb"))["project"]["requires-python"].removeprefix(">=").strip())')
    uv run --isolated --python "$lowest_python" --resolution lowest-direct pytest

test-highest-deps:
    uv run --isolated --with 'Django, Wagtail' pytest

# Run tests with coverage.
coverage:
    uv run pytest --cov src/wagtail_daisIE
    uv run coverage report -m
    uv run coverage html

# Make migrations and migrate the database.
migrate:
    uv run ./demo/manage.py makemigrations
    uv run ./demo/manage.py migrate

# Compile the global CSS for the demo site.
compile-global-css:
    npm run compile-global-css

# Collect static assets for development server
collectstatic:
    yes yes | uv run ./demo/manage.py collectstatic

# Run the development server at the given host and port.
runserver:
    uv run ./demo/manage.py runserver

# Load the initial data into the database.
load_initial_data:
    uv run ./demo/manage.py load_initial_data

# Open a shell to the demo application.
shell:
    uv run ./demo/manage.py shell

# Run the demo application.
demo: clean-db migrate load_initial_data collectstatic runserver
