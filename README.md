# Buzzer.py

A real-time quiz buzzer built with Flask and Socket.IO. One player hosts a
game, while others join it to buzz, submit guesses, and track scores.

## Run locally

Install the Python dependencies and start the development server:

```sh
poetry install
poetry run python buzzapp/app.py
```

Open <http://127.0.0.1:5000> in a browser. The local server uses a
development-only session key; do not use it for a public deployment.

## Development checks

Run the configured checks from the repository root:

```sh
poetry run ruff check buzzapp
poetry run mypy
```

## Deploy to Render

Deploy this as a **Web Service**, not a Static Site: the application needs a
single HTTP service that can also accept Socket.IO WebSocket connections.

1. Commit and push `pyproject.toml` and `poetry.lock` to the branch that
   Render should deploy.
2. In the Render Dashboard, select **New > Web Service** and connect the
   repository.
3. Use these service settings:

   | Setting | Value |
   | --- | --- |
   | Runtime | `Python 3` |
   | Root Directory | Leave empty |
   | Build Command | `poetry install --only main` |
   | Start Command | `poetry run python buzzapp/app.py` |
   | Health Check Path | `/health` |

4. Add these environment variables in Render:

   | Name | Value |
   | --- | --- |
   | `PYTHON_VERSION` | `3.14.6` |
   | `SECRET_KEY` | A newly generated, high-entropy secret |

5. Create the service. Render assigns an `onrender.com` URL once the first
   deploy completes, and pushes to the configured branch trigger future
   deploys.

The app reads Render's `PORT` environment variable and binds to `0.0.0.0`
automatically. Render supports WebSocket connections on the same public port.

Game state is currently held in memory, so run exactly one service instance.
Scaling to multiple instances would require shared state and Socket.IO message
queue support (for example, Redis).
