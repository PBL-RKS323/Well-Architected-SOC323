"""tabel_erd_kategori_favorit_kupon_pembayaran

Revision ID: 92b0fc79db2a
Revises: e7f81a2b3c4d
Create Date: 2026-11-10 05:12:15.652847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92b0fc79db2a'
down_revision = 'e7f81a2b3c4d'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Tabel Kategori
    if 'kategori' not in existing_tables:
        op.create_table(
            'kategori',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('nama', sa.String(length=50), nullable=False),
            sa.Column('slug', sa.String(length=60), nullable=False),
            sa.Column('ikon', sa.String(length=50), nullable=True),
            sa.Column('deskripsi', sa.String(length=255), nullable=True),
            sa.Column('urutan', sa.Integer(), nullable=False, default=0),
            sa.Column('aktif', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('nama'),
            sa.UniqueConstraint('slug')
        )
        op.create_index('ix_kategori_slug', 'kategori', ['slug'], unique=True)

    # 2. Tabel Kupon
    if 'kupon' not in existing_tables:
        op.create_table(
            'kupon',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('kode', sa.String(length=30), nullable=False),
            sa.Column('deskripsi', sa.String(length=200), nullable=True),
            sa.Column('tipe', sa.String(length=10), nullable=False, default='persen'),
            sa.Column('nilai', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('min_belanja', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
            sa.Column('maks_potongan', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('kuota', sa.Integer(), nullable=False, default=100),
            sa.Column('terpakai', sa.Integer(), nullable=False, default=0),
            sa.Column('berlaku_mulai', sa.DateTime(), nullable=True),
            sa.Column('berlaku_sampai', sa.DateTime(), nullable=True),
            sa.Column('aktif', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('kode')
        )
        op.create_index('ix_kupon_kode', 'kupon', ['kode'], unique=True)

    # 3. Tabel Favorit
    if 'favorit' not in existing_tables:
        op.create_table(
            'favorit',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('produk_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['produk_id'], ['produk.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'produk_id', name='uq_favorit_user_produk')
        )
        op.create_index('ix_favorit_produk_id', 'favorit', ['produk_id'], unique=False)
        op.create_index('ix_favorit_user_id', 'favorit', ['user_id'], unique=False)

    # 4. Tabel Pembayaran
    if 'pembayaran' not in existing_tables:
        op.create_table(
            'pembayaran',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('pesanan_id', sa.Integer(), nullable=False),
            sa.Column('metode_pembayaran', sa.String(length=30), nullable=False, default='transfer'),
            sa.Column('jumlah', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('bukti_bayar', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
            sa.Column('diverifikasi_oleh', sa.Integer(), nullable=True),
            sa.Column('catatan_verifikasi', sa.String(length=255), nullable=True),
            sa.Column('waktu_bayar', sa.DateTime(), nullable=False),
            sa.Column('waktu_verifikasi', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['diverifikasi_oleh'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['pesanan_id'], ['pesanan.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_pembayaran_pesanan_id', 'pembayaran', ['pesanan_id'], unique=False)
        op.create_index('ix_pembayaran_status', 'pembayaran', ['status'], unique=False)

    # 5. Kolom pada Pesanan
    pesanan_cols = [c['name'] for c in inspector.get_columns('pesanan')]
    with op.batch_alter_table('pesanan', schema=None) as batch_op:
        if 'diskon' not in pesanan_cols:
            batch_op.add_column(sa.Column('diskon', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'))
        if 'kupon_id' not in pesanan_cols:
            batch_op.add_column(sa.Column('kupon_id', sa.Integer(), nullable=True))
            batch_op.create_index(batch_op.f('ix_pesanan_kupon_id'), ['kupon_id'], unique=False)
            batch_op.create_foreign_key('fk_pesanan_kupon_id', 'kupon', ['kupon_id'], ['id'], ondelete='SET NULL')

    # 6. Kolom pada Produk
    produk_cols = [c['name'] for c in inspector.get_columns('produk')]
    with op.batch_alter_table('produk', schema=None) as batch_op:
        if 'kategori_id' not in produk_cols:
            batch_op.add_column(sa.Column('kategori_id', sa.Integer(), nullable=True))
            batch_op.create_index(batch_op.f('ix_produk_kategori_id'), ['kategori_id'], unique=False)
            batch_op.create_foreign_key('fk_produk_kategori_id', 'kategori', ['kategori_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('produk', schema=None) as batch_op:
        batch_op.drop_constraint('fk_produk_kategori_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_produk_kategori_id'))
        batch_op.drop_column('kategori_id')

    with op.batch_alter_table('pesanan', schema=None) as batch_op:
        batch_op.drop_constraint('fk_pesanan_kupon_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_pesanan_kupon_id'))
        batch_op.drop_column('kupon_id')
        batch_op.drop_column('diskon')

    op.drop_table('pembayaran')
    op.drop_table('favorit')
    op.drop_table('kupon')
    op.drop_table('kategori')
