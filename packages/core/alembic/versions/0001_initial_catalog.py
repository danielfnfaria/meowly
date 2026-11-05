"""initial catalog: owners, components, templates, environments

Revision ID: 0001
Revises:
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _entity_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "owners",
        *_entity_columns(),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_owners"),
    )
    op.create_index("ix_owners_slug", "owners", ["slug"], unique=True)

    op.create_table(
        "components",
        *_entity_columns(),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("repo_url", sa.String(500), nullable=True),
        sa.Column("system", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_components"),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"], name="fk_components_owner_id_owners"),
    )
    op.create_index("ix_components_slug", "components", ["slug"], unique=True)

    op.create_table(
        "templates",
        *_entity_columns(),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("source_path", sa.String(500), nullable=True),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_templates"),
    )
    op.create_index("ix_templates_slug", "templates", ["slug"], unique=True)

    op.create_table(
        "environments",
        *_entity_columns(),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_environments"),
    )
    op.create_index("ix_environments_slug", "environments", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_table("environments")
    op.drop_table("templates")
    op.drop_table("components")
    op.drop_table("owners")
