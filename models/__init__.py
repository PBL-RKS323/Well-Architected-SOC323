from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Waktu UTC tanpa info zona (kolom DateTime di MySQL/PostgreSQL disimpan naive)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
