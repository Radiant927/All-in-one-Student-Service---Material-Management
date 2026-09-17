"""Harden stocktake snapshots and individual item reconciliation."""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = "0002_stocktake_hardening"
down_revision = "0001_initial_managed_schema"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    stocktake_columns = {column["name"] for column in inspector.get_columns("stocktakes")}
    if "cancelled_at" not in stocktake_columns:
        op.add_column("stocktakes", sa.Column("cancelled_at", sa.String(length=30), nullable=True))

    entry_columns = {column["name"] for column in inspector.get_columns("stocktake_entries")}
    if "counted" not in entry_columns:
        op.add_column(
            "stocktake_entries",
            sa.Column("counted", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        bind.execute(sa.text(
            "UPDATE stocktake_entries SET counted = true "
            "WHERE actual_quantity IS NOT NULL OR stocktake_id IN "
            "(SELECT id FROM stocktakes WHERE status = 'completed')"
        ))

    if "stocktake_item_checks" not in inspector.get_table_names():
        op.create_table(
            "stocktake_item_checks",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("stocktake_entry_id", sa.Integer(), nullable=False),
            sa.Column("inventory_item_id", sa.Integer(), nullable=True),
            sa.Column("item_code", sa.String(length=100), nullable=False),
            sa.Column("expected", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("scanned", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("scanned_at", sa.String(length=30), nullable=True),
            sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory_items.id"]),
            sa.ForeignKeyConstraint(["stocktake_entry_id"], ["stocktake_entries.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stocktake_entry_id", "item_code"),
        )
        op.create_index(
            "ix_stocktake_item_checks_stocktake_entry_id",
            "stocktake_item_checks",
            ["stocktake_entry_id"],
        )
        op.create_index(
            "ix_stocktake_item_checks_inventory_item_id",
            "stocktake_item_checks",
            ["inventory_item_id"],
        )

    # Old in-progress documents do not contain item-level snapshots and cannot be safely resumed.
    cancelled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bind.execute(
        sa.text(
            "UPDATE stocktakes SET status = 'cancelled', cancelled_at = :cancelled_at "
            "WHERE status = 'in_progress'"
        ),
        {"cancelled_at": cancelled_at},
    )

    # Repair legacy rows whose storage location belongs to another warehouse.
    for table in ("inventory_batches", "inventory_items"):
        bind.execute(sa.text(
            f"UPDATE {table} SET location_id = NULL "
            f"WHERE location_id IS NOT NULL AND NOT EXISTS ("
            f"SELECT 1 FROM storage_locations "
            f"WHERE storage_locations.id = {table}.location_id "
            f"AND storage_locations.warehouse_id = {table}.warehouse_id)"
        ))


def downgrade():
    op.drop_index("ix_stocktake_item_checks_inventory_item_id", table_name="stocktake_item_checks")
    op.drop_index("ix_stocktake_item_checks_stocktake_entry_id", table_name="stocktake_item_checks")
    op.drop_table("stocktake_item_checks")
    op.drop_column("stocktake_entries", "counted")
    op.drop_column("stocktakes", "cancelled_at")
