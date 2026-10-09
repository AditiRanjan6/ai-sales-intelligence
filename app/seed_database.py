from app.database import get_connection, initialize_database


def seed_database():
    initialize_database()
    connection = get_connection()
    try:
        lead_count = connection.execute(
            "SELECT COUNT(*) FROM leads"
        ).fetchone()[0]
    finally:
        connection.close()

    print(f"Database initialized with {lead_count} leads.")


if __name__ == "__main__":
    seed_database()