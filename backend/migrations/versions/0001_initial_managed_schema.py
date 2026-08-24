"""Adopt existing schema and add managed v2 tables without dropping user data."""
import uuid

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_managed_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This first managed migration is intentionally additive. It can adopt an
    # existing SQLite/PostgreSQL database produced by older application builds.
    from database import Base
    import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    inspector = sa.inspect(bind)
    material_columns = {column["name"] for column in inspector.get_columns("materials")}
    if "public_id" not in material_columns:
        op.add_column("materials", sa.Column("public_id", sa.String(length=36), nullable=True))
        rows = bind.execute(sa.text("SELECT id FROM materials")).fetchall()
        for row in rows:
            bind.execute(
                sa.text("UPDATE materials SET public_id = :public_id WHERE id = :id"),
                {"public_id": str(uuid.uuid4()), "id": row[0]},
            )
        op.create_index("ix_materials_public_id", "materials", ["public_id"], unique=True)


def downgrade():
    # Destructive downgrade is deliberately disabled for an adopted production database.
    pass

