"""biodata user telepon gender tgl lahir

Revision ID: e7f81a2b3c4d
Revises: a7d3e91c5f20
Create Date: 2026-11-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7f81a2b3c4d'
down_revision = 'a7d3e91c5f20'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('telepon', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('jenis_kelamin', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('tanggal_lahir', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('tanggal_lahir')
        batch_op.drop_column('jenis_kelamin')
        batch_op.drop_column('telepon')
