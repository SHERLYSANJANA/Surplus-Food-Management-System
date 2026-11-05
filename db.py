import os
import psycopg


def get_connected():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RuntimeError("DB_PASSWORD environment variable is not set.")
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "food_redistribution"),
        user=os.environ.get("DB_USER", "postgres"),
        password=password,
        connect_timeout=5,
    )
