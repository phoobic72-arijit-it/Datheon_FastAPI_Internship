# Task 4: Microservice with Background Tasks and Docker

A FastAPI service that returns a job ID immediately and dispatches a real
HTTP webhook asynchronously using BackgroundTasks and httpx.AsyncClient.
This task is standalone; Tasks 1, 2, and 3 do not need to be running.

## Screenshot requirements covered

- FastAPI BackgroundTasks runs an async webhook-dispatch function.
- The submission route returns HTTP 202 and a job ID.
- Status changes through queued, processing, succeeded, or failed.
- Per-client rate limiting protects POST /webhooks.
- Multi-stage Dockerfile with a separate dependency build stage.
- Slim runtime, non-root user, exec-form Uvicorn command, and health check.
- Docker Compose provides a ready-to-run container configuration.
- README includes curl commands and Swagger instructions.

## Requirements

For local Python use: Python 3.10+ and pip.
For the container deliverable: Docker Desktop for Mac with Apple silicon.
Docker Desktop includes Docker Engine, the CLI, and Compose.
No email account, SMTP credentials, external webhook account, database,
Node.js, or frontend is required for the built-in demonstration.

## Option A: Run locally with Python

Extract this folder onto your Desktop, then run:

```bash
cd ~/Desktop/Task_4_Background_Tasks_Docker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8004 --no-proxy-headers
```

Open [Swagger UI](http://127.0.0.1:8004/docs).
This runs the API locally but does not demonstrate containerization.
Stop it with Control + C before using Docker on the same host port.

## Option B: Run the required Docker container

1. Install [Docker Desktop for Apple silicon](https://docs.docker.com/desktop/setup/install/mac-install/).
2. Open Docker Desktop and wait until the engine is running.
3. Run:

```bash
cd ~/Desktop/Task_4_Background_Tasks_Docker
docker compose up --build -d
docker compose ps
```

If Homebrew is installed, Docker Desktop can also be installed from Terminal:

```bash
brew install --cask docker-desktop
open -a Docker
```

Complete Docker Desktop's first-run setup before running Compose.

Open [Swagger UI](http://127.0.0.1:8004/docs).
Docker maps Mac port 8004 to container port 8000. The Dockerfile sets
APP_PORT=8000, so its built-in callback uses the correct internal port.
You do not need a Mac Python environment when using only Docker.

Useful commands:

```bash
docker compose logs -f
docker compose down
```

Control + C exits the log viewer; docker compose down stops the container.
For a plain Docker CLI alternative:

```bash
docker build -t task4-webhook .
docker run --rm --name task4-webhook -p 127.0.0.1:8004:8000 task4-webhook
```

## Files

| File | Purpose |
|---|---|
| main.py | Routes, background scheduling, and local receiver |
| worker.py | Async HTTP delivery, HMAC signature, retries, and job state |
| rate_limit.py | Bounded per-client sliding-window limiter |
| schemas.py | Pydantic request and response models |
| requirements.txt | All Python dependencies |
| Dockerfile | Multi-stage non-root container image |
| compose.yaml | One-command local container deployment |
| .dockerignore | Excludes environments, secrets, and caches from build context |
| .gitignore | Excludes generated local files from Git |
| INSTALL_MAC.md | Short installation and terminal instructions |

## Use the service

POST /webhooks accepts:

```json
{"event": "book.created", "message": "A new book was added successfully."}
```

The response is HTTP 202 with a queued job ID. After the response,
BackgroundTasks runs the async dispatcher. By default, it POSTs to this
service's /demo/webhook endpoint over actual HTTP, using an HMAC signature.
The receiver verifies the signature and records the delivery.

Copy the job ID into GET /jobs/{job_id}. The status becomes succeeded after
a successful 2xx response. GET /demo/deliveries shows the received event.
GET /jobs lists recent jobs; GET /health returns the health status.
The submission response also supplies a Location header for the job URL.

## curl examples

```bash
curl -i -X POST http://127.0.0.1:8004/webhooks \
  -H 'Content-Type: application/json' \
  -d '{"event":"book.created","message":"A new book was added successfully."}'

curl http://127.0.0.1:8004/jobs
curl http://127.0.0.1:8004/demo/deliveries
curl http://127.0.0.1:8004/health
```

## Rate limiting and errors

The default limit is 5 submission attempts per client IP per
60 seconds. The next request in that window receives 429 and Retry-After.
Health checks, job lookups, and the callback receiver do not consume this quota.
Do not trust client-supplied forwarded IP headers; the supplied commands disable
proxy-header processing. Behind a real proxy, configure trusted proxy handling
and an appropriate shared limiter before scaling.

| Status | Meaning |
|---|---|
| 202 | Webhook job accepted |
| 404 | Unknown or evicted job |
| 422 | Invalid input |
| 429 | Submission rate limit reached |
| 503 | All retained job slots are still active |

Failed deliveries are retried up to 3 total attempts for network errors,
HTTP 429, and HTTP 5xx. Other non-success responses fail without retry.
Each attempt times out after 5 seconds. Job responses expose status and a
generic error, rather than the remote response body or configured URL.
The same job ID is sent as Idempotency-Key on every attempt; the demo receiver
deduplicates IDs while they remain in its recent-delivery history.

## Optional configuration

No .env file is required or automatically loaded. Set environment variables
in Terminal before starting Python, or add them to compose.yaml environment:

| Variable | Default | Meaning |
|---|---|---|
| APP_PORT | 8004 locally; 8000 in Docker | Port used to construct the default callback URL |
| WEBHOOK_URL | Local /demo/webhook | Fixed destination selected by the operator |
| WEBHOOK_SIGNING_SECRET | Random at process startup | HMAC-SHA256 signing key |
| RATE_LIMIT_REQUESTS | 5 | Allowed submissions per window |
| RATE_LIMIT_WINDOW_SECONDS | 60 | Sliding-window duration |

For an external webhook, configure a destination you control, use HTTPS,
and set a private signing secret. The signature is sha256= followed by
the HMAC-SHA256 hex digest of the exact request body. No third-party
requests are made with the default configuration. Clients cannot supply
arbitrary destination URLs through the API. Redirects are not followed.
If changing the local Uvicorn port, set APP_PORT to match it.

## Background processing scope

FastAPI BackgroundTasks is an in-process mechanism, not a durable queue.
Jobs and rate-limit counters reset on restart; abrupt termination can lose
pending work. History retains at most 500 jobs and 100 demo deliveries.
Run one worker for this task's in-memory state. The Docker runtime and
Compose settings provide container deployment, but durable production jobs
would require an external queue/store. This demo API has no user authentication.

## GitHub

Extract and upload Task_4_Background_Tasks_Docker beside the other task
folders in Datheon_FastAPI_Internship. Include Dockerfile and compose.yaml;
exclude .venv, caches, and any private configuration. Upload the extracted
folder rather than only the ZIP if you want GitHub to display the code.

## References

- [FastAPI BackgroundTasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Docker Desktop Homebrew cask](https://formulae.brew.sh/cask/docker-desktop)
