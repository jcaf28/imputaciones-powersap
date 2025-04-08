# PATH: backend/alembic/versions/2b980b53ad6b_añadir_campo_timestampinput_a_.py

"""Añadir campo TimestampInput a Imputaciones

Revision ID: 2b980b53ad6b
Revises: a5295bc970b9
Create Date: 2025-02-10 13:39:50.294108

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Identificadores de la migración
revision = '2b980b53ad6b'
down_revision = 'a5295bc970b9'
branch_labels = None
depends_on = None

def upgrade():
    # Añadir la columna sin valores nulos
    op.add_column('Imputaciones', sa.Column('TimestampInput', sa.DateTime(), nullable=True))

    # Asignar valores iniciales: TimestampInput = FechaImp a las 00:00:00
    op.execute('UPDATE "Imputaciones" SET "TimestampInput" = CAST("FechaImp" AS TIMESTAMP)')

def downgrade():
    # Eliminar la columna si se hace rollback
    op.drop_column('Imputaciones', 'TimestampInput')

