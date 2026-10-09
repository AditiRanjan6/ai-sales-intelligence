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
    """Create the leads table if it does not already exist."""

    connection = get_connection()

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

    connection.commit()
    connection.close()