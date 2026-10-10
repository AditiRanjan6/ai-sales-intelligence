import os
import secrets
from pathlib import Path

from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from app.database import get_connection, initialize_database
from app.import_service import MAX_FILE_SIZE_BYTES, create_preview, confirm_import, get_sample_csv_text
from app.scoring import calculate_lead_score, get_priority
from app.services.recommendations import generate_lead_recommendation

# --------------------------------------------------
# Application
# --------------------------------------------------

def _get_basic_auth_credentials():
    username = os.getenv("BASIC_AUTH_USERNAME")
    password = os.getenv("BASIC_AUTH_PASSWORD")
    is_production = os.getenv("APP_ENV", "").lower() == "production"

    if username is None and password is None:
        if is_production:
            raise RuntimeError(
                "BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD must be set in production."
            )
        return None, None

    if not username or not password:
        raise RuntimeError(
            "BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD must both be set."
        )

    return username, password


AUTH_USERNAME, AUTH_PASSWORD = _get_basic_auth_credentials()
basic_auth = HTTPBasic(auto_error=False)

app = FastAPI(
    title="AI Sales & Customer Intelligence Platform",
    description="Business intelligence and AI-powered sales research platform.",
    version="0.3.0",
)


# --------------------------------------------------
# Startup
# --------------------------------------------------

initialize_database()

BASE_DIR = Path(__file__).resolve().parent.parent


@app.middleware("http")
async def require_basic_auth(request: Request, call_next):
    if request.url.path == "/health" or AUTH_USERNAME is None:
        return await call_next(request)

    try:
        credentials = await basic_auth(request)
    except HTTPException:
        credentials = None

    if (
        credentials is None
        or not secrets.compare_digest(
            credentials.username.encode("utf-8"),
            AUTH_USERNAME.encode("utf-8"),
        )
        or not secrets.compare_digest(
            credentials.password.encode("utf-8"),
            AUTH_PASSWORD.encode("utf-8"),
        )
    ):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Sales Intelligence"'},
        )

    return await call_next(request)


app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "frontend" / "static"
    ),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "frontend" / "templates"
)


@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request
        }
    )

# --------------------------------------------------
# Lead helpers
# --------------------------------------------------

def enrich_lead(lead):
    """Add calculated score and priority to a lead."""

    lead = dict(lead)

    score = calculate_lead_score(lead)

    lead["lead_score"] = score
    lead["priority"] = get_priority(score)

    return lead


def get_all_leads():
    """Retrieve all leads from SQLite."""

    connection = get_connection()

    rows = connection.execute(
        "SELECT * FROM leads ORDER BY lead_id"
    ).fetchall()

    connection.close()

    return rows


# --------------------------------------------------
# Basic endpoints
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AI Sales Intelligence API is running",
        "status": "online",
        "version": "0.3.0",
        "database": "SQLite",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
    }


# --------------------------------------------------
# Lead endpoints
# --------------------------------------------------

@app.get("/leads")
def get_leads():
    """Return all leads with calculated scores."""

    leads = get_all_leads()

    enriched_leads = [
        enrich_lead(lead)
        for lead in leads
    ]

    return {
        "total_leads": len(enriched_leads),
        "leads": enriched_leads,
    }


@app.get("/leads/{lead_id}")
def get_lead(lead_id: str):
    """Return one lead by ID."""

    connection = get_connection()

    lead = connection.execute(
        """
        SELECT *
        FROM leads
        WHERE UPPER(lead_id) = UPPER(?)
        """,
        (lead_id,),
    ).fetchone()

    connection.close()

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail=f"Lead '{lead_id}' not found.",
        )

    enriched_lead = enrich_lead(lead)
    enriched_lead["recommendation"] = generate_lead_recommendation(
        enriched_lead
    )

    return enriched_lead


@app.delete("/leads/{lead_id}")
def delete_lead(lead_id: str):
    """Delete one lead by ID."""

    normalized_lead_id = lead_id.strip()
    if not normalized_lead_id:
        raise HTTPException(
            status_code=400,
            detail="A valid lead ID is required.",
        )

    connection = get_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM leads WHERE UPPER(lead_id) = UPPER(?)",
            (normalized_lead_id,),
        )
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Lead '{normalized_lead_id}' not found.",
            )

        connection.commit()
    finally:
        connection.close()

    return {
        "message": "Lead deleted successfully.",
        "lead_id": normalized_lead_id,
    }


# --------------------------------------------------
# Analytics
# --------------------------------------------------

@app.get("/analytics/summary")
def analytics_summary():
    """Return high-level sales intelligence metrics."""

    leads = get_all_leads()

    enriched_leads = [
        enrich_lead(lead)
        for lead in leads
    ]

    total_leads = len(enriched_leads)

    hot_leads = sum(
        lead["priority"] == "HOT"
        for lead in enriched_leads
    )

    warm_leads = sum(
        lead["priority"] == "WARM"
        for lead in enriched_leads
    )

    cold_leads = sum(
        lead["priority"] == "COLD"
        for lead in enriched_leads
    )

    converted_leads = sum(
        int(lead["converted"])
        for lead in enriched_leads
    )

    conversion_rate = (
        converted_leads / total_leads * 100
        if total_leads
        else 0
    )

    pipeline_value = sum(
        float(lead["deal_size"])
        for lead in enriched_leads
    )

    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "converted_leads": converted_leads,
        "conversion_rate": round(conversion_rate, 2),
        "pipeline_value": pipeline_value,
    }


# --------------------------------------------------
# CSV import endpoints
# --------------------------------------------------

@app.get("/lead-import/sample-csv")
def download_sample_csv():
    """Download a ready-to-use example CSV for importing leads."""
    csv_text = get_sample_csv_text()
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=lead_import_sample.csv",
        },
    )


@app.post("/lead-import/preview")
async def preview_csv_upload(file: UploadFile = File(...)):
    """Validate an uploaded CSV file and return preview data without writing to the database."""
    if file is None:
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    try:
        contents = await file.read(MAX_FILE_SIZE_BYTES + 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file could not be read.") from exc

    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"CSV uploads must be {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB or smaller.",
        )

    try:
        result = await run_in_threadpool(create_preview, contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="The CSV could not be processed. Please try again.") from exc

    return result


@app.post("/lead-import/confirm")
def confirm_csv_import(payload: dict = Body(...)):
    """Import only the valid rows associated with a previously-validated preview."""
    preview_id = payload.get("preview_id") if isinstance(payload, dict) else None

    if not str(preview_id).strip():
        raise HTTPException(status_code=400, detail="A valid import preview is required.")

    try:
        result = confirm_import(str(preview_id).strip())
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="The import preview is invalid or expired.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Import failed. The database transaction was rolled back.") from exc

    return result