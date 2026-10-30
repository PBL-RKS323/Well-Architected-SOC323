"""spesifikasi dan garansi produk

Revision ID: a7d3e91c5f20
Revises: 4866341725b7
Create Date: 2026-10-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7d3e91c5f20'
down_revision = '4866341725b7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('produk', schema=None) as batch_op:
        batch_op.add_column(sa.Column('spesifikasi', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('garansi', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('produk', schema=None) as batch_op:
        batch_op.drop_column('garansi')
        batch_op.drop_column('spesifikasi')
