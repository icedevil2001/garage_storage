"""remove box name unique constraint

Revision ID: xxx
Revises: previous_revision
Create Date: 2023-12-29 08:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # SQLite doesn't support dropping constraints directly
    # We need to recreate the table
    with op.batch_alter_table('box') as batch_op:
        batch_op.drop_constraint('unique_name', type_='unique')

def downgrade():
    with op.batch_alter_table('box') as batch_op:
        batch_op.create_unique_constraint('unique_name', ['name'])
