import csv

from app.database import get_connection, initialize_database


def seed_database():
    initialize_database()

    connection = get_connection()

    with open("data/leads.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for lead in reader:
            connection.execute(
                """
                INSERT OR REPLACE INTO leads (
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
                ),
            )

    connection.commit()
    connection.close()

    print("Database seeded successfully.")
    print("20 lead records imported.")


if __name__ == "__main__":
    seed_database()