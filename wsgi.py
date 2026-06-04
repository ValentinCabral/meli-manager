"""WSGI entry point for production (gunicorn)."""
import database as db

db.init_db()

from app import app

if __name__ == "__main__":
    app.run()
