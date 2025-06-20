"""empty message

Revision ID: cf1ec034dc71
Revises: 4d20295b22c7, add_is_cancelled_column
Create Date: 2025-05-09 12:33:17.090244

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf1ec034dc71'
down_revision = ('4d20295b22c7', 'add_is_cancelled_column')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
