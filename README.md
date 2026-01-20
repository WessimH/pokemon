# Pokemon

A Django-based application for managing Pokemon data.

## Prerequisites

- Python 3.13
- [Poetry](https://python-poetry.org/) (for dependency management)
- [Docker](https://www.docker.com/) (optional, for containerized execution)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd pokemon
    ```

2.  **Install dependencies:**

    ```bash
    poetry install
    ```

## Usage

### Running Locally

1.  **Apply migrations:**

    ```bash
    poetry run python manage.py migrate
    ```

2.  **Start the development server:**

    ```bash
    poetry run python manage.py runserver
    ```

    The application will be available at `http://127.0.0.1:8000/`.

### Running with Docker

1.  **Build the Docker image:**

    ```bash
    docker build -t pokemon-app .
    ```

2.  **Run the container:**

    ```bash
    docker run -p 8000:8000 pokemon-app
    ```

    The application will be available at `http://localhost:8000/`.

### Code Quality

This project uses `ruff` for linting and formatting.

-   **Run linting checks:**

    ```bash
    poetry run ruff check .
    ```

-   **Run formatting checks:**

    ```bash
    poetry run ruff format --check .
    ```
