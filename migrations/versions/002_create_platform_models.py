"""create platform models

Revision ID: 002_create_platform_models
Revises: 001_create_users_table
Create Date: 2026-11-04 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_create_platform_models'
down_revision: Union[str, None] = '001_create_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Admin Users table
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_users_username'), 'admin_users', ['username'], unique=True)

    # 2. Categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)

    # 3. Videos table
    op.create_table(
        'videos',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('telegram_file_id', sa.String(length=255), nullable=True),
        sa.Column('telegram_file_unique_id', sa.String(length=255), nullable=True),
        sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True),
        sa.Column('telegram_message_id', sa.BigInteger(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_videos_created_at'), 'videos', ['created_at'], unique=False)
    op.create_index(op.f('ix_videos_status'), 'videos', ['status'], unique=False)
    op.create_index(op.f('ix_videos_telegram_file_id'), 'videos', ['telegram_file_id'], unique=False)
    op.create_index(op.f('ix_videos_telegram_file_unique_id'), 'videos', ['telegram_file_unique_id'], unique=True)
    op.create_index(op.f('ix_videos_title'), 'videos', ['title'], unique=False)

    # 4. Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('admin_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_admin_id'), 'audit_logs', ['admin_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)

    # 5. Collections table
    op.create_table(
        'collections',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_video_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['cover_video_id'], ['videos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_collections_status'), 'collections', ['status'], unique=False)

    # 6. Upload Jobs table
    op.create_table(
        'upload_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('progress', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('video_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_upload_jobs_status'), 'upload_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_upload_jobs_video_id'), 'upload_jobs', ['video_id'], unique=False)

    # 7. Video Categories association table
    op.create_table(
        'video_categories',
        sa.Column('video_id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('video_id', 'category_id')
    )

    # 8. Collection Videos association table
    op.create_table(
        'collection_videos',
        sa.Column('collection_id', sa.Uuid(), nullable=False),
        sa.Column('video_id', sa.Uuid(), nullable=False),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('collection_id', 'video_id')
    )
    op.create_index(op.f('ix_collection_videos_position'), 'collection_videos', ['position'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_collection_videos_position'), table_name='collection_videos')
    op.drop_table('collection_videos')
    op.drop_table('video_categories')
    op.drop_index(op.f('ix_upload_jobs_video_id'), table_name='upload_jobs')
    op.drop_index(op.f('ix_upload_jobs_status'), table_name='upload_jobs')
    op.drop_table('upload_jobs')
    op.drop_index(op.f('ix_collections_status'), table_name='collections')
    op.drop_table('collections')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_admin_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_videos_title'), table_name='videos')
    op.drop_index(op.f('ix_videos_telegram_file_unique_id'), table_name='videos')
    op.drop_index(op.f('ix_videos_telegram_file_id'), table_name='videos')
    op.drop_index(op.f('ix_videos_status'), table_name='videos')
    op.drop_index(op.f('ix_videos_created_at'), table_name='videos')
    op.drop_table('videos')
    op.drop_index(op.f('ix_categories_slug'), table_name='categories')
    op.drop_table('categories')
    op.drop_index(op.f('ix_admin_users_username'), table_name='admin_users')
    op.drop_table('admin_users')

