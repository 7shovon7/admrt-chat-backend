"""delivery status added to chat

Revision ID: d892c93ed29d
Revises: 930c63f9dff8
Create Date: 2024-05-15 09:16:52.653461

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd892c93ed29d'
down_revision = '930c63f9dff8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chat', sa.Column('delivered', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chat', 'delivered')
    # ### end Alembic commands ###
