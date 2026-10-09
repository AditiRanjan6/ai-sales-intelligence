import csv
import io
import re
import uuid

from app.database import get_connection

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MAX_IMPORT_ROWS = 5000
PREVIEW_LIMIT = 10

REQUIRED_COLUMNS = [
    "lead_id",
    "company_name",
    "industry",
    "company_size",
    "annual_revenue",
    "location",
    "lead_source",
    "website_activity",
    "email_engagement",
    "technology_fit",
    "buying_signal",
    "deal_size",
    "interactions",
    "last_activity_days",
    "converted",
]

ALLOWED_VALUES = {
    "company_size": {"11-50", "51-200", "201-500", "501-1000", "1001-5000"},
    "website_activity": {"Low", "Medium", "High"},
    "email_engagement": {"Low", "Medium", "High"},
    "technology_fit": {"Low", "Medium", "High"},
    "buying_signal": {"Weak", "Moderate", "Strong"},
}

COLUMN_ALIASES = {
    "lead_id": {"lead_id", "leadid", "lead id"},
    "company_name": {"company_name", "companyname", "company name"},
    "industry": {"industry"},
    "company_size": {"company_size", "companysize", "company size"},
    "annual_revenue": {"annual_revenue", "annualrevenue", "annual revenue"},
    "location": {"location"},
    "lead_source": {"lead_source", "leadsource", "lead source"},
    "website_activity": {"website_activity", "websiteactivity", "website activity"},
    "email_engagement": {"email_engagement", "emailengagement", "email engagement"},
    "technology_fit": {"technology_fit", "technologyfit", "technology fit"},
    "buying_signal": {"buying_signal", "buyingsignal", "buying signal"},
    "deal_size": {"deal_size", "dealsize", "deal size"},
    "interactions": {"interactions"},
    "last_activity_days": {"last_activity_days", "lastactivitydays", "last activity days"},
    "converted": {"converted"},
}

PREVIEW_STORE: dict[str, dict] = {}


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _canonicalize_key(raw_key: str | None) -> str | None:
    if raw_key is None:
        return None
    normalized = _normalize_header(raw_key)
    for canonical, aliases in COLUMN_ALIASES.items():
        if normalized in {_normalize_header(alias) for alias in aliases}:
            return canonical
    return None


def _read_text_from_bytes(raw_bytes: bytes) -> str:
    if not raw_bytes:
        raise ValueError("The uploaded CSV file is empty.")
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"CSV uploads must be {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB or smaller.")
    if b"\x00" in raw_bytes:
        raise ValueError("The uploaded file is not a valid CSV file.")

    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("The uploaded CSV file uses an unsupported encoding.")


def _parse_number(raw_value: object, field_name: str, *, integer: bool = False) -> float | int:
    value = str(raw_value or "").strip()
    if not value:
        raise ValueError(f"{field_name} is required.")

    cleaned = value.replace("$", "").replace(",", "").replace("%", "").strip()
    if cleaned.lower() in {"n/a", "na", "null", "none"}:
        raise ValueError(f"{field_name} is required.")

    try:
        parsed = float(cleaned)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc

    if integer and not parsed.is_integer():
        raise ValueError(f"{field_name} must be a whole number.")

    return int(parsed) if integer else parsed


def _parse_bool(raw_value: object, field_name: str) -> int:
    value = str(raw_value or "").strip().lower()
    if not value:
        raise ValueError(f"{field_name} is required.")

    truthy = {"1", "true", "yes", "y", "t"}
    falsy = {"0", "false", "no", "n", "f"}

    if value in truthy:
        return 1
    if value in falsy:
        return 0
    raise ValueError(f"{field_name} must be one of: true/false, yes/no, or 1/0.")


def _validate_enum(field_name: str, value: str, allowed_values: set[str]) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required.")
    if normalized not in allowed_values:
        valid_values = ", ".join(sorted(allowed_values))
        raise ValueError(f"{field_name} must be one of: {valid_values}.")
    return normalized


def _build_sample_row(lead_id: str, company_name: str, company_size: str, annual_revenue: str) -> dict:
    return {
        "lead_id": lead_id,
        "company_name": company_name,
        "industry": "SaaS",
        "company_size": company_size,
        "annual_revenue": annual_revenue,
        "location": "New York",
        "lead_source": "LinkedIn",
        "website_activity": "High",
        "email_engagement": "High",
        "technology_fit": "High",
        "buying_signal": "Strong",
        "deal_size": "90000",
        "interactions": "12",
        "last_activity_days": "3",
        "converted": "1",
    }


def get_sample_csv_text() -> str:
    sample_rows = [
        _build_sample_row("L1001", "Northwind Labs", "51-200", "18000000"),
        _build_sample_row("L1002", "Blue Harbor Group", "201-500", "42000000"),
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS)
    writer.writeheader()
    writer.writerows(sample_rows)
    return output.getvalue()


def _existing_lead_ids() -> set[str]:
    connection = get_connection()
    rows = connection.execute("SELECT lead_id FROM leads").fetchall()
    connection.close()
    return {str(row["lead_id"]).upper() for row in rows}


def _validate_and_normalize_rows(raw_rows: list[dict], existing_ids: set[str]) -> tuple[list[dict], list[dict], list[dict]]:
    valid_rows: list[dict] = []
    invalid_rows: list[dict] = []
    preview_rows: list[dict] = []
    seen_ids: set[str] = set()

    for row_number, row in enumerate(raw_rows, start=2):
        if row is None or not any(str(value or "").strip() for value in row.values()):
            continue

        cleaned_row: dict[str, str] = {}
        for raw_key, raw_value in row.items():
            canonical = _canonicalize_key(raw_key)
            if canonical is None:
                continue
            cleaned_row[canonical] = str(raw_value or "").strip()

        row_errors: list[str] = []
        if not str(cleaned_row.get("lead_id", "")).strip():
            cleaned_row["lead_id"] = f"IMP-{uuid.uuid4().hex[:8]}"
            row_errors.append("lead_id was blank; a safe generated ID was assigned.")

        try:
            cleaned_row["company_name"] = str(cleaned_row.get("company_name", "")).strip()
            if not cleaned_row["company_name"]:
                raise ValueError("company_name is required.")

            for field in [
                "industry",
                "company_size",
                "location",
                "lead_source",
                "website_activity",
                "email_engagement",
                "technology_fit",
                "buying_signal",
            ]:
                if not str(cleaned_row.get(field, "")).strip():
                    raise ValueError(f"{field} is required.")

            cleaned_row["company_size"] = _validate_enum(
                "company_size",
                cleaned_row.get("company_size", ""),
                ALLOWED_VALUES["company_size"],
            )
            cleaned_row["website_activity"] = _validate_enum(
                "website_activity",
                cleaned_row.get("website_activity", ""),
                ALLOWED_VALUES["website_activity"],
            )
            cleaned_row["email_engagement"] = _validate_enum(
                "email_engagement",
                cleaned_row.get("email_engagement", ""),
                ALLOWED_VALUES["email_engagement"],
            )
            cleaned_row["technology_fit"] = _validate_enum(
                "technology_fit",
                cleaned_row.get("technology_fit", ""),
                ALLOWED_VALUES["technology_fit"],
            )
            cleaned_row["buying_signal"] = _validate_enum(
                "buying_signal",
                cleaned_row.get("buying_signal", ""),
                ALLOWED_VALUES["buying_signal"],
            )
            cleaned_row["annual_revenue"] = _parse_number(cleaned_row.get("annual_revenue"), "annual_revenue")
            cleaned_row["deal_size"] = _parse_number(cleaned_row.get("deal_size"), "deal_size")
            cleaned_row["interactions"] = _parse_number(cleaned_row.get("interactions"), "interactions", integer=True)
            cleaned_row["last_activity_days"] = _parse_number(cleaned_row.get("last_activity_days"), "last_activity_days", integer=True)
            cleaned_row["converted"] = _parse_bool(cleaned_row.get("converted"), "converted")
        except ValueError as exc:
            row_errors.append(str(exc))

        normalized_lead_id = str(cleaned_row.get("lead_id", "")).upper()
        if normalized_lead_id in existing_ids:
            row_errors.append("lead_id already exists in the database and will be skipped on import.")
        if normalized_lead_id in seen_ids:
            row_errors.append("Duplicate lead_id detected within this CSV import.")

        if not row_errors:
            seen_ids.add(normalized_lead_id)
            valid_row = {
                "row_number": row_number,
                "lead_id": cleaned_row["lead_id"],
                "company_name": cleaned_row["company_name"],
                "industry": cleaned_row["industry"],
                "company_size": cleaned_row["company_size"],
                "annual_revenue": cleaned_row["annual_revenue"],
                "location": cleaned_row["location"],
                "lead_source": cleaned_row["lead_source"],
                "website_activity": cleaned_row["website_activity"],
                "email_engagement": cleaned_row["email_engagement"],
                "technology_fit": cleaned_row["technology_fit"],
                "buying_signal": cleaned_row["buying_signal"],
                "deal_size": cleaned_row["deal_size"],
                "interactions": cleaned_row["interactions"],
                "last_activity_days": cleaned_row["last_activity_days"],
                "converted": cleaned_row["converted"],
            }
            valid_rows.append(valid_row)
            if len(preview_rows) < PREVIEW_LIMIT:
                preview_rows.append({
                    "row_number": row_number,
                    "lead_id": valid_row["lead_id"],
                    "company_name": valid_row["company_name"],
                    "industry": valid_row["industry"],
                    "location": valid_row["location"],
                    "deal_size": valid_row["deal_size"],
                    "status": "valid",
                })
        else:
            invalid_rows.append({
                "row_number": row_number,
                "lead_id": cleaned_row.get("lead_id") or "",
                "company_name": cleaned_row.get("company_name") or "",
                "errors": list(dict.fromkeys(row_errors)),
            })

    return valid_rows, invalid_rows, preview_rows


def parse_csv_upload(raw_bytes: bytes) -> dict:
    text = _read_text_from_bytes(raw_bytes)
    cleaned = text.lstrip("\ufeff")
    if not cleaned.strip():
        raise ValueError("The uploaded CSV file is empty.")

    try:
        reader = csv.DictReader(io.StringIO(cleaned), skipinitialspace=True)
    except csv.Error as exc:
        raise ValueError("The CSV file could not be read. Please check the format and try again.") from exc

    if reader.fieldnames is None:
        raise ValueError("The CSV file is missing a header row.")

    header_names = [str(name or "").strip() for name in reader.fieldnames]
    if not any(header_names):
        raise ValueError("The CSV file is missing a header row.")

    seen_headers = {_canonicalize_key(name) for name in header_names}
    missing_required = [field for field in REQUIRED_COLUMNS if field not in seen_headers]
    if missing_required:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing_required))

    raw_rows = list(reader)
    if len(raw_rows) > MAX_IMPORT_ROWS:
        raise ValueError(f"CSV files are limited to {MAX_IMPORT_ROWS} rows per import.")

    existing_ids = _existing_lead_ids()
    valid_rows, invalid_rows, preview_rows = _validate_and_normalize_rows(raw_rows, existing_ids)
    duplicate_rows = sum(
        1
        for item in invalid_rows
        if any("Duplicate" in error or "already exists" in error for error in item["errors"])
    )

    return {
        "total_rows": len(raw_rows),
        "valid_rows": len(valid_rows),
        "invalid_rows": len(invalid_rows),
        "duplicate_conflicts": duplicate_rows,
        "preview_rows": preview_rows,
        "invalid_details": invalid_rows[:20],
        "valid_rows_data": valid_rows,
    }


def create_preview(raw_bytes: bytes) -> dict:
    preview = parse_csv_upload(raw_bytes)
    preview_id = uuid.uuid4().hex
    PREVIEW_STORE[preview_id] = preview
    preview["preview_id"] = preview_id
    return preview


def confirm_import(preview_id: str) -> dict:
    preview = PREVIEW_STORE.get(preview_id)
    if preview is None:
        raise KeyError("The import preview has expired or is invalid.")

    PREVIEW_STORE.pop(preview_id, None)
    valid_rows = preview.get("valid_rows_data", [])

    if not valid_rows:
        return {
            "preview_id": preview_id,
            "total_rows": preview.get("total_rows", 0),
            "records_imported": 0,
            "invalid_rows": preview.get("invalid_rows", 0),
            "duplicate_conflicts": preview.get("duplicate_conflicts", 0),
            "skipped_records": [],
            "message": "No valid records were available to import.",
        }

    connection = get_connection()
    imported_count = 0
    skipped_records: list[dict] = []
    seen_ids: set[str] = set()

    try:
        connection.execute("BEGIN")
        for row in valid_rows:
            lead_id = str(row["lead_id"]).strip()
            lookup_id = lead_id.upper()
            if lookup_id in seen_ids:
                skipped_records.append({"lead_id": lead_id, "reason": "Duplicate lead ID within this import."})
                continue

            existing = connection.execute(
                "SELECT 1 FROM leads WHERE UPPER(lead_id) = UPPER(?)",
                (lead_id,),
            ).fetchone()
            if existing is not None:
                skipped_records.append({"lead_id": lead_id, "reason": "lead_id already exists in the database."})
                continue

            connection.execute(
                """
                INSERT INTO leads (
                    lead_id,
                    company_name,
                    industry,
                    company_size,
                    annual_revenue,
                    location,
                    lead_source,
                    website_activity,
                    email_engagement,
                    technology_fit,
                    buying_signal,
                    deal_size,
                    interactions,
                    last_activity_days,
                    converted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    row["company_name"],
                    row["industry"],
                    row["company_size"],
                    float(row["annual_revenue"]),
                    row["location"],
                    row["lead_source"],
                    row["website_activity"],
                    row["email_engagement"],
                    row["technology_fit"],
                    row["buying_signal"],
                    float(row["deal_size"]),
                    int(row["interactions"]),
                    int(row["last_activity_days"]),
                    int(row["converted"]),
                ),
            )
            seen_ids.add(lookup_id)
            imported_count += 1

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "preview_id": preview_id,
        "total_rows": preview.get("total_rows", 0),
        "records_imported": imported_count,
        "invalid_rows": preview.get("invalid_rows", 0),
        "duplicate_conflicts": preview.get("duplicate_conflicts", 0) + len(skipped_records),
        "skipped_records": skipped_records,
        "message": f"Imported {imported_count} lead(s) successfully.",
    }
