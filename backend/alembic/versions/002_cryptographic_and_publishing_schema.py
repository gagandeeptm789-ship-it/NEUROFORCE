"""Cryptographic signatures and secure publishing schema extensions

Revision ID: 002_crypto_publishing
Revises: 001_initial_schema
Create Date: 2026-11-06 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_crypto_publishing'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 3 Fields
    op.add_column('notices', sa.Column('hash_algorithm', sa.String(length=32), nullable=False, server_default='SHA-256'))
    op.add_column('notices', sa.Column('signature_algorithm', sa.String(length=32), nullable=False, server_default='Ed25519'))
    op.add_column('notices', sa.Column('metadata_version', sa.String(length=16), nullable=False, server_default='1.0'))
    op.add_column('notices', sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True))

    # Phase 4 Fields
    op.add_column('notices', sa.Column('distribution_status', sa.String(length=32), nullable=False, server_default='DRAFT'))
    op.add_column('notices', sa.Column('qr_code_path', sa.String(length=512), nullable=True))
    op.add_column('notices', sa.Column('verification_url', sa.String(length=512), nullable=True))
    op.add_column('notices', sa.Column('watermarked_file_path', sa.String(length=512), nullable=True))
    op.add_column('notices', sa.Column('published_file_path', sa.String(length=512), nullable=True))
    op.add_column('notices', sa.Column('watermark_version', sa.String(length=32), nullable=True))
    op.add_column('notices', sa.Column('watermark_reference', sa.String(length=128), nullable=True))
    op.add_column('notices', sa.Column('publication_timestamp', sa.DateTime(timezone=True), nullable=True))

    op.create_index(op.f('ix_notices_distribution_status'), 'notices', ['distribution_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notices_distribution_status'), table_name='notices')
    op.drop_column('notices', 'publication_timestamp')
    op.drop_column('notices', 'watermark_reference')
    op.drop_column('notices', 'watermark_version')
    op.drop_column('notices', 'published_file_path')
    op.drop_column('notices', 'watermarked_file_path')
    op.drop_column('notices', 'verification_url')
    op.drop_column('notices', 'qr_code_path')
    op.drop_column('notices', 'distribution_status')
    op.drop_column('notices', 'signed_at')
    op.drop_column('notices', 'metadata_version')
    op.drop_column('notices', 'signature_algorithm')
    op.drop_column('notices', 'hash_algorithm')

