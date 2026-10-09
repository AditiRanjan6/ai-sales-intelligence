# AI Sales & Customer Intelligence Platform

An interactive sales intelligence dashboard built with **Python, FastAPI, SQLite, HTML, CSS, and JavaScript**. The platform helps users evaluate sales leads, prioritize high-potential prospects, analyze pipeline performance, and import lead data through CSV files.

## Live Demo

- **Live Dashboard:** https://ai-sales-intelligence-51hp.onrender.com/dashboard
- **GitHub Repository:** https://github.com/AditiRanjan6/ai-sales-intelligence
- **API Documentation:** https://ai-sales-intelligence-51hp.onrender.com/docs

The live application uses HTTP Basic Authentication. Enter the credentials configured for the deployment when prompted.

> **Demo environment:** The application is hosted on Render's free web service. The instance may sleep after inactivity, resulting in a delay on the first request. Its SQLite database is stored under `/tmp`, which is ephemeral. Data changes may be lost after restarts or redeployments. Use fictional demo data only.

## Features

### Sales Dashboard
- Overview of total leads, hot leads, conversion rate, and pipeline value.
- Priority pipeline displaying company, industry, location, deal size, score, and priority.
- Lead distribution and sales intelligence insights.

### Lead Scoring and Recommendations
- Rule-based lead scoring to help prioritize prospects.
- Hot and warm lead classification.
- Actionable recommendations based on lead information and scoring rules.

### Lead Management
- Lead listing and individual lead details.
- Company search and pipeline exploration.
- SQLite-backed data storage.

### CSV Import
- Upload and preview lead data.
- Validate imported records before confirmation.
- Review import feedback and update the lead database.

### Security
- Environment-variable-based HTTP Basic Authentication.
- Protected dashboard, lead and analytics endpoints, CSV import routes, API documentation, and OpenAPI schema.
- Public health-check endpoint for deployment monitoring.
- Production startup fails safely if authentication credentials are missing.

### Deployment
- Render-compatible Python web service.
- Automatic database schema initialization.
- Automatic loading of the 20 fictional demo leads when the database contains no leads.
- Existing lead records are preserved during normal initialization.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Templates | Jinja2 |
| Data import | CSV |
| Server | Uvicorn |
| Hosting | Render |

## Project Structure

```text
ai-sales-intelligence/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── scoring.py
│   ├── seed_database.py
│   ├── import_service.py
│   └── services/
│       └── recommendations.py
├── data/
│   └── leads.csv
├── frontend/
│   ├── static/
│   │   └── style.css
│   └── templates/
│       └── dashboard.html
├── requirements.txt
├── render.yaml
├── .gitignore
└── README.md
```

## Local Installation

### 1. Clone the repository

```powershell
git clone https://github.com/AditiRanjan6/ai-sales-intelligence.git
cd ai-sales-intelligence
```

### 2. Create and activate a virtual environment

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution in the current terminal, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Start the application

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open the following URLs in your browser:

- Dashboard: http://127.0.0.1:8000/dashboard
- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

In local development, authentication remains disabled when both authentication variables are unset. Configure both variables if you want to test authenticated access locally.

## Environment Variables

Configure these variables in your deployment environment.

| Variable | Purpose |
|---|---|
| `APP_ENV` | Set to `production` on Render |
| `BASIC_AUTH_USERNAME` | Username required for HTTP Basic Authentication |
| `BASIC_AUTH_PASSWORD` | Strong, unique authentication password |
| `DATABASE_PATH` | Path to the SQLite database file |
| `PYTHON_VERSION` | Python version used by the Render service |
| `PORT` | Port supplied by Render |

For Render, the application is configured to use:

```text
APP_ENV=production
DATABASE_PATH=/tmp/sales_intelligence.db
```

Set `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` in the Render service's environment-variable settings. Do not commit real credentials to GitHub.

## Database and Demo Data

The application initializes its database schema on startup. When the selected database contains no leads, the initialization process loads the 20 fictional demo leads from `data/leads.csv`.

If leads already exist, normal initialization preserves them instead of replacing the database contents.

For local development, you can also initialize the demo database with:

```powershell
python -m app.seed_database
```

The deployed free instance uses temporary `/tmp` storage. A restart or redeployment may remove the database and any leads imported into it. The application can then recreate its demo dataset on startup.

## API and Health Check

FastAPI provides interactive API documentation at `/docs` and an OpenAPI schema at `/openapi.json`. These endpoints are protected by HTTP Basic Authentication in production.

The `/health` endpoint remains public for Render health monitoring.

## Deployment on Render

The repository includes `render.yaml` for configuring the web service.

1. Push the project to GitHub.
2. Create a Render Web Service connected to the repository, or use the Blueprint workflow if supported by your account.
3. Configure the required environment variables.
4. Deploy the latest commit.
5. Open the dashboard URL and authenticate.

The current configuration uses Render's free web service and a SQLite database under `/tmp`. The service may spin down after inactivity, and local database changes are not durable. A persistent disk requires a paid plan, so it is not included in the current free deployment.

## Security Notes

- Never commit passwords, tokens, or other secrets.
- Use a strong, unique password for the deployed application.
- Share authentication credentials only with intended users.
- Use fictional demo records in the public demonstration environment.
- Do not use the current ephemeral SQLite deployment for important business data.
- Use a persistent, appropriately secured database before relying on the application for production customer records.

## Author

**Aditi Ranjan**

- GitHub: https://github.com/AditiRanjan6
- LinkedIn: Aditi Ranjan

---

*Built as a sales intelligence project demonstrating API development, database integration, lead scoring, data import workflows, authentication, and cloud deployment.*