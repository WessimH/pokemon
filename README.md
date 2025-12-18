# Pokemon Game

A Django-based Pokemon Game project.

## Requirements

- Python >= 3.13
- [Poetry](https://python-poetry.org/)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd pokemon
    ```

2.  **Install dependencies:**

    ```bash
    poetry install
    ```

3.  **Activate the Virtual Environment:**

    You can spawn a new shell within the virtual environment:

    ```bash
    poetry env activate
    ```

    Alternatively, to activate it in your current shell:

    ```bash
    source $(poetry env info --path)/bin/activate
    ```

## Usage

This project uses a custom Poetry script to simplify Django management commands.

**Start the development server:**

```bash
# If you have activated the virtual environment:
manage runserver

# If you are running from outside the virtual environment:
poetry run manage runserver
```

**Run other Django commands:**

```bash
manage makemigrations
manage migrate
manage createsuperuser
```

## Docker

You can also run the project using Docker.

1.  **Build and start the container:**
    ```bash
    docker-compose up --build
    ```

2.  **Access the application:**
    Open http://localhost:8000 in your browser.

## Code Quality

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

**Run linter:**
```bash
poetry run ruff check .
```

**Run linter and auto-fix:**
```bash
poetry run ruff check --fix .
```

**Run formatter:**
```bash
poetry run ruff format .
```

```

## CI/CD

This project uses **GitHub Actions** for Continuous Integration.
On every push and pull request to `main`, the following checks are run:
*   `ruff check .`: Lints the code.
*   `ruff format --check .`: Verifies code formatting.

## Project Structure

- `manage.py`: Django's command-line utility.
- `config/`: Configuration root for the project (settings, urls, etc).
- `pyproject.toml`: Project metadata and dependencies.
