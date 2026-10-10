import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main


class LeadDeletionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test_leads.db"
        self.create_test_database()
        self.connection_patch = patch.object(
            main,
            "get_connection",
            side_effect=self.get_test_connection,
        )
        self.connection_patch.start()
        self.username_patch = patch.object(main, "AUTH_USERNAME", "test-user")
        self.password_patch = patch.object(main, "AUTH_PASSWORD", "test-password")
        self.username_patch.start()
        self.password_patch.start()
        self.client = TestClient(main.app)

    def tearDown(self):
        self.connection_patch.stop()
        self.username_patch.stop()
        self.password_patch.stop()
        self.temp_dir.cleanup()

    def get_test_connection(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def create_test_database(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE leads (
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
                connection.executemany(
                    """
                    INSERT INTO leads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "LEAD-1", "Northwind", "Technology", "1001-5000",
                            5000000, "Seattle", "Website", "High", "High",
                            "High", "Strong", 1000, 5, 1, 0,
                        ),
                        (
                            "LEAD-2", "Contoso", "Retail", "51-200",
                            2500000, "Boston", "Referral", "Medium", "Medium",
                            "Medium", "Moderate", 2000, 3, 5, 1,
                        ),
                    ],
                )

    def test_delete_updates_analytics_for_remaining_database_records(self):
        response = self.client.delete(
            "/leads/lead-1",
            auth=("test-user", "test-password"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["lead_id"], "lead-1")
        self.assertEqual(
            self.client.get("/leads", auth=("test-user", "test-password")).json()[
                "total_leads"
            ],
            1,
        )
        summary = self.client.get(
            "/analytics/summary",
            auth=("test-user", "test-password"),
        ).json()
        self.assertEqual(summary["total_leads"], 1)
        self.assertEqual(summary["converted_leads"], 1)
        self.assertEqual(summary["conversion_rate"], 100)
        self.assertEqual(summary["pipeline_value"], 2000)

    def test_invalid_and_missing_lead_ids_return_client_errors(self):
        invalid_response = self.client.delete(
            "/leads/%20",
            auth=("test-user", "test-password"),
        )
        missing_response = self.client.delete(
            "/leads/UNKNOWN",
            auth=("test-user", "test-password"),
        )

        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(
            self.client.get("/leads", auth=("test-user", "test-password")).json()[
                "total_leads"
            ],
            2,
        )

    def test_delete_requires_existing_authentication(self):
        response = self.client.delete("/leads/LEAD-1")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            self.client.get("/leads", auth=("test-user", "test-password")).json()[
                "total_leads"
            ],
            2,
        )


if __name__ == "__main__":
    unittest.main()
