"""row level security policies

Revision ID: 1e1050af2630
Revises: a6ecc3b84511
Create Date: 2026-09-13 16:43:44.617732

"""

from collections.abc import Sequence

from alembic import op

revision: str = "1e1050af2630"
down_revision: str | Sequence[str] | None = "57c2b59760fa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_POLICIES = [
    ("datastores", "integrations_by_user_strict"),
    ("datastore_certificates", "certificates_by_user_strict"),
    ("datastore_secrets", "secrets_by_user_strict"),
    ("user_llm", "user_hosted_llm_by_user_strict"),
]

_POLICY_EXPR = (
    "organization_id = current_setting('app.organization_id', true)::uuid "
    "AND user_id = current_setting('app.user_id', true)::uuid"
)


def upgrade() -> None:
    for table, policy_name in _POLICIES:
        op.execute(f"ALTER TABLE integration.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE integration.{table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {policy_name} ON integration.{table}
            FOR ALL
            USING ({_POLICY_EXPR})
            WITH CHECK ({_POLICY_EXPR})
        """)


def downgrade() -> None:
    for table, policy_name in _POLICIES:
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON integration.{table}")
        op.execute(f"ALTER TABLE integration.{table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE integration.{table} DISABLE ROW LEVEL SECURITY")
