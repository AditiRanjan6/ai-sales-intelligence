# AI Sales & Customer Intelligence Platform

## Setup

From the project root, create and activate a virtual environment, then install
the application dependencies:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Seed the demo leads

Run this once from the project root to initialize the SQLite database and load
the 20 demo leads from `data/leads.csv`:

```powershell
python -m app.seed_database
```

The API also initializes the database on startup, but seeding is required to
load the demo dataset into a new database.

## Run the application

From the project root:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open the dashboard at <http://127.0.0.1:8000/dashboard> and the interactive API
documentation at <http://127.0.0.1:8000/docs>.

## Deploy to Render

Connect this repository to Render and create a Blueprint from `render.yaml`.
The Blueprint defines the Python web service, production start command, and a
persistent disk mounted at `/var/data`. The disk requires a paid Render web
service; the configured Starter plan is intentional because a local/container
filesystem is not durable across deployments.

Render supplies `PORT`. The Blueprint sets `PYTHON_VERSION` and
`DATABASE_PATH`; the application uses the configured SQLite path and creates
the schema if it is missing. Startup does not seed or replace leads. The
existing database on a developer's computer is not automatically copied to
Render, so migrate any required lead data to the mounted disk using a secure
backup/restore process before relying on it.

**Security limitation:** the dashboard, lead APIs, API documentation, and CSV
import endpoints currently have no authentication or authorization. Do not
put confidential lead data on a public deployment until access controls are
added. CSV uploads are size- and row-limited, but those limits do not prevent
anonymous reads, imports, or repeated requests. Import previews are held in
process memory, so run a single web instance and worker unless preview state is
moved to shared storage.
