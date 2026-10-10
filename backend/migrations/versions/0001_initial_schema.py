"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("device_type", sa.String(length=80), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("firmware_version", sa.String(length=80), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_devices_ip_address", "devices", ["ip_address"])
    op.create_index("ux_devices_name", "devices", ["name"], unique=True)
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("source_event_id", sa.String(length=128), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=True),
        sa.Column("source_ip", sa.String(length=45), nullable=False),
        sa.Column("destination_ip", sa.String(length=45), nullable=False),
        sa.Column("transport_protocol", sa.String(length=16), nullable=False),
        sa.Column("destination_port", sa.Integer(), nullable=False),
        sa.Column("application_protocol", sa.String(length=32), nullable=False),
        sa.Column("http_method", sa.String(length=12), nullable=True),
        sa.Column("request_path", sa.String(length=512), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("detection_rule_ids", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.String(length=1000), nullable=False),
        sa.Column("origin", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("score_contributions", sa.JSON(), nullable=False),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("origin", "source_event_id", name="uq_events_origin_source_event_id"),
    )
    op.create_index("ix_events_device_id", "events", ["device_id"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_origin", "events", ["origin"])
    op.create_index("ix_events_severity", "events", ["severity"])
    op.create_index("ix_events_source_ip", "events", ["source_ip"])
    op.create_index("ix_events_timestamp", "events", ["event_timestamp"])
    op.create_table(
        "discovery_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("target_cidr", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column("host_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discovery_jobs_requested_at", "discovery_jobs", ["requested_at"])
    op.create_table(
        "discovered_hosts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("mac_address", sa.String(length=32), nullable=True),
        sa.Column("evidence", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["discovery_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discovered_hosts_ip_address", "discovered_hosts", ["ip_address"])


def downgrade() -> None:
    op.drop_index("ix_discovered_hosts_ip_address", table_name="discovered_hosts")
    op.drop_table("discovered_hosts")
    op.drop_index("ix_discovery_jobs_requested_at", table_name="discovery_jobs")
    op.drop_table("discovery_jobs")
    op.drop_index("ix_events_timestamp", table_name="events")
    op.drop_index("ix_events_source_ip", table_name="events")
    op.drop_index("ix_events_severity", table_name="events")
    op.drop_index("ix_events_origin", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_index("ix_events_device_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ux_devices_name", table_name="devices")
    op.drop_index("ix_devices_ip_address", table_name="devices")
    op.drop_table("devices")
