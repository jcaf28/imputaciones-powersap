"""v2: eliminar cargadoEnTareaReal y OpMinC

Revision ID: c1a2b3v20001
Revises: 8e210f7369bd
Create Date: 2026-02-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3v20001'
down_revision: Union[str, None] = '8e210f7369bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('Tabla_Central', 'cargadoEnTareaReal')
    op.drop_column('Areas', 'OpMinC')


def downgrade() -> None:
    op.add_column('Areas', sa.Column('OpMinC', sa.String(), nullable=True))
    op.add_column('Tabla_Central', sa.Column('cargadoEnTareaReal', sa.Boolean(), server_default=sa.text('true'), nullable=True))
