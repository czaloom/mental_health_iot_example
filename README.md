# AWS SAM High Stress Detector

Serverless sample that ingests environmental telemetry from CSV, stores high stress readings in PostgreSQL, and exposes SAM-backed APIs for the agent and alert workflows.

## Prerequisites

- Docker (for the local PostgreSQL container)
- AWS SAM CLI
- Python 3.11

## Quick Start (Local)

1. `make install` - create the virtualenv and install dependencies.
2. `source .venv/bin/activate` - activate virtualenv.
3. `make build` - package the SAM application.
4. `make pg-up` - start the PostgreSQL container (first run creates it).
5. `make pg-init` - load the schema from `db/init.sql`.
6. `make run-local` - launch the local API using `env.local.json`.

Use `make pg-down` to stop the container and `make pg-reset` to remove it when you are done.

## API Testing

Run these commands in a separate terminal while the local API is running:

1. `make curl-post-alerts` - returns an empty list before any data is ingested.
2. `make curl-post-agent` - triggers the agent to process the default CSV and returns total vs high stress counts.
3. `make curl-post-alerts` - now shows the two most recent alerts (limit configurable via payload).

Adjust the API base URL by overriding the `API_URL` variable, for example `API_URL=http://localhost:3000 make curl-post-alerts`.

## Python Tests

- `make test-agent` - runs the agent Lambda entry point using the local database.
- `make test-alerts` - runs the alerts Lambda entry point using the local database.

Ensure PostgreSQL is running (`make pg-up` and `make pg-init`) before executing either command.
