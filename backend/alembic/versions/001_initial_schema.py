"""Initial database schema with admins and notices tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Admins Table
    op.create_table(
        'admins',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_admins_id'), 'admins', ['id'], unique=False)
    op.create_index(op.f('ix_admins_email'), 'admins', ['email'], unique=True)

    # 2. Create Notices Table (with Phase 3 extensibility fields)
    op.create_table(
        'notices',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('notice_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='General'),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_file_path', sa.String(length=512), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('issuer_admin_id', sa.String(length=36), sa.ForeignKey('admins.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('publication_status', sa.String(length=20), nullable=False, server_default='published'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        # Phase 3 Fields
        sa.Column('sha256_hash', sa.String(length=64), nullable=True),
        sa.Column('digital_signature', sa.Text(), nullable=True),
        sa.Column('signing_key_id', sa.String(length=100), nullable=True),
        sa.Column('signed_metadata', sa.Text(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_notices_id'), 'notices', ['id'], unique=False)
    op.create_index(op.f('ix_notices_notice_id'), 'notices', ['notice_id'], unique=True)
    op.create_index(op.f('ix_notices_issuer_admin_id'), 'notices', ['issuer_admin_id'], unique=False)
    op.create_index(op.f('ix_notices_publication_status'), 'notices', ['publication_status'], unique=False)
    op.create_index(op.f('ix_notices_sha256_hash'), 'notices', ['sha256_hash'], unique=False)


def downgrade() -> None:
    op.drop_table('notices')
    op.drop_table('admins')

