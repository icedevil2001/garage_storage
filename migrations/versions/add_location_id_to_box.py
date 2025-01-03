from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'add_location_id_to_box'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add the location_id column to the Box table
    op.add_column('box', sa.Column('location_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_box_location', 'box', 'location', ['location_id'], ['id'])

def downgrade():
    # Remove the location_id column from the Box table
    op.drop_constraint('fk_box_location', 'box', type_='foreignkey')
    op.drop_column('box', 'location_id')
