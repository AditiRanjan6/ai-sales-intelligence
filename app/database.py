import csv
import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = Path(
    os.environ.get("DATABASE_PATH", BASE_DIR / "data" / "sales_intelligence.db")
)


def get_connection():
    """Create and return a SQLite database connection."""
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the leads table and seed demo data only when it is empty."""

    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                industry TEXT NOT NULL,
                company_size TEXT NOT NULL,
                annual_revenue REAL NOT NULL,
                location TEXT NOT NULL,
                lead_source TEXT NOT NULL,
                website_activity TEXT NOT NULL,
                email_engagement TEXT NOT NULL,
                technology_fit TEXT NOT NULL,
                buying_signal TEXT NOT NULL,
                deal_size REAL NOT NULL,
                interactions INTEGER NOT NULL,
                last_activity_days INTEGER NOT NULL,
                converted INTEGER NOT NULL
            )
            """
        )

        has_leads = connection.execute(
            "SELECT 1 FROM leads LIMIT 1"
        ).fetchone()
        if has_leads is None:
            demo_data_path = BASE_DIR / "data" / "leads.csv"
            with demo_data_path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                leads = [
                    (
                        lead["lead_id"],
                        lead["company_name"],
                        lead["industry"],
                        lead["company_size"],
                        float(lead["annual_revenue"]),
                        lead["location"],
                        lead["lead_source"],
                        lead["website_activity"],
                        lead["email_engagement"],
                        lead["technology_fit"],
                        lead["buying_signal"],
                        float(lead["deal_size"]),
                        int(lead["interactions"]),
                        int(lead["last_activity_days"]),
                        int(lead["converted"]),
                    )
                    for lead in reader
                ]

            if not leads:
                raise RuntimeError(f"No demo leads found in {demo_data_path}.")

            connection.executemany(
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                leads,
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()