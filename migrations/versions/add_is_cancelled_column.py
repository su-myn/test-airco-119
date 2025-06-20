# Create a new migration file in the migrations folder
# For example: migrations/versions/add_is_cancelled_column.py

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_is_cancelled_column'
down_revision = None  # Replace with the ID of the previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Add is_cancelled column to booking_form table
    op.add_column('booking_form', sa.Column('is_cancelled', sa.Boolean(), nullable=False, server_default='0'))

def downgrade():
    # Remove is_cancelled column from booking_form table
    op.drop_column('booking_form', 'is_cancelled')