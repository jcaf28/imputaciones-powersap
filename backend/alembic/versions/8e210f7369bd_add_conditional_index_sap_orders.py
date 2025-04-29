"""add_conditional_index_sap_orders

Revision ID: 8e210f7369bd
Revises: 93cb897356a6
Create Date: 2025-04-29 15:09:40.162815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e210f7369bd'
down_revision: Union[str, None] = '93cb897356a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sap_orders_lookup
        ON "Sap_Orders" ("Project","Vertice","CarNumber","OperationActivity")
        WHERE "ActiveOrder" IS TRUE;
        """
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_sap_orders_lookup;')
