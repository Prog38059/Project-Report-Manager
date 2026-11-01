"""Phase 1 Foundation Schema

Revision ID: 0001_phase1_foundation
Revises: None
Create Date: 2026-11-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_phase1_foundation'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. clients
    op.create_table(
        'clients',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('client_code', sa.String(30), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('client_category', sa.String(30), nullable=False, server_default='PERSON'),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('email', sa.String(254), nullable=True),
        sa.Column('address_text', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_clients_code', 'clients', ['client_code'])
    op.create_index('idx_clients_display_name', 'clients', ['display_name'])

    # 2. entities
    op.create_table(
        'entities',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('client_id', sa.CHAR(36), sa.ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('constitution_code', sa.String(30), nullable=False),
        sa.Column('legal_name', sa.String(250), nullable=False),
        sa.Column('trade_name', sa.String(250), nullable=True),
        sa.Column('business_description', sa.Text(), nullable=True),
        sa.Column('accounting_framework_code', sa.String(40), nullable=True),
        sa.Column('tax_profile_code', sa.String(40), nullable=True),
        sa.Column('date_of_formation', sa.Date(), nullable=True),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_entities_client_id', 'entities', ['client_id'])
    op.create_index('idx_entities_constitution', 'entities', ['constitution_code'])
    op.create_index('idx_entities_client_legal_name', 'entities', ['client_id', 'legal_name'])

    # 3. entity_members
    op.create_table(
        'entity_members',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('role_code', sa.String(35), nullable=False),
        sa.Column('pan_encrypted', sa.Text(), nullable=True),
        sa.Column('address_text', sa.Text(), nullable=True),
        sa.Column('contact_phone', sa.String(30), nullable=True),
        sa.Column('contact_email', sa.String(254), nullable=True),
        sa.Column('profit_share_pct', sa.String(40), nullable=True),
        sa.Column('shareholding_pct', sa.String(40), nullable=True),
        sa.Column('capital_commitment_paise', sa.BigInteger(), nullable=True),
        sa.Column('date_from', sa.Date(), nullable=True),
        sa.Column('date_to', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_entity_members_entity_id', 'entity_members', ['entity_id'])

    # 4. projects
    op.create_table(
        'projects',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('project_code', sa.String(30), nullable=False, unique=True),
        sa.Column('project_name', sa.String(250), nullable=False),
        sa.Column('industry_code', sa.String(40), nullable=True),
        sa.Column('business_model_code', sa.String(40), nullable=True),
        sa.Column('project_nature_code', sa.String(30), nullable=False, server_default='NEW'),
        sa.Column('location_address', sa.Text(), nullable=True),
        sa.Column('district', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('pin_code', sa.String(12), nullable=True),
        sa.Column('project_description', sa.Text(), nullable=True),
        sa.Column('implementation_start', sa.Date(), nullable=True),
        sa.Column('commercial_operation_date', sa.Date(), nullable=True),
        sa.Column('financial_year_start_month', sa.SmallInteger(), nullable=False, server_default='4'),
        sa.Column('currency_code', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('projection_granularity', sa.String(15), nullable=False, server_default='ANNUAL'),
        sa.Column('projection_year_count', sa.SmallInteger(), nullable=False, server_default='7'),
        sa.Column('projection_start_financial_year', sa.SmallInteger(), nullable=False, server_default='2026'),
        sa.Column('historical_data_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('historical_year_count', sa.SmallInteger(), nullable=True),
        sa.Column('statement_layout_code', sa.String(40), nullable=False, server_default='HORIZONTAL_YEAR_COLUMNS'),
        sa.Column('status_code', sa.String(30), nullable=False, server_default='DRAFT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_projects_entity_id', 'projects', ['entity_id'])
    op.create_index('idx_projects_code', 'projects', ['project_code'])

    # 5. project_sources
    op.create_table(
        'project_sources',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('source_type', sa.String(30), nullable=False),
        sa.Column('source_title', sa.String(250), nullable=False),
        sa.Column('source_party', sa.String(200), nullable=True),
        sa.Column('source_date', sa.DateTime(), nullable=True),
        sa.Column('source_reference', sa.String(120), nullable=True),
        sa.Column('verification_status', sa.String(25), nullable=False, server_default='UNVERIFIED'),
        sa.Column('review_note', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_project_sources_project_id', 'project_sources', ['project_id'])

    # 6. attachments (Resolving Gap B-1)
    op.create_table(
        'attachments',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=True),
        sa.Column('source_id', sa.CHAR(36), sa.ForeignKey('project_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('file_category', sa.String(35), nullable=False, server_default='GENERAL'),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('stored_relative_path', sa.Text(), nullable=False),
        sa.Column('mime_type', sa.String(120), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.CheckConstraint('project_id IS NOT NULL OR entity_id IS NOT NULL', name='chk_attachments_parent_present'),
    )
    op.create_index('idx_attachments_project_id', 'attachments', ['project_id'])
    op.create_index('idx_attachments_entity_id', 'attachments', ['entity_id'])
    op.create_index('idx_attachments_sha256', 'attachments', ['sha256_hash'])

    # 7. entity_identifiers
    op.create_table(
        'entity_identifiers',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('identifier_type', sa.String(30), nullable=False),
        sa.Column('identifier_value_encrypted', sa.Text(), nullable=False),
        sa.Column('identifier_value_hash', sa.String(128), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('verification_status', sa.String(25), nullable=False, server_default='UNVERIFIED'),
        sa.Column('source_attachment_id', sa.CHAR(36), sa.ForeignKey('attachments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_entity_identifiers_entity_type', 'entity_identifiers', ['entity_id', 'identifier_type'])
    op.create_index('idx_entity_identifiers_hash', 'entity_identifiers', ['identifier_value_hash'])

    # 8. Constitution extension tables
    op.create_table(
        'huf_details',
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('karta_member_id', sa.CHAR(36), sa.ForeignKey('entity_members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('formation_note', sa.Text(), nullable=True),
    )

    op.create_table(
        'proprietorship_details',
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('proprietor_member_id', sa.CHAR(36), sa.ForeignKey('entity_members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('business_start_date', sa.Date(), nullable=True),
    )

    op.create_table(
        'partnership_details',
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('deed_date', sa.Date(), nullable=True),
        sa.Column('registration_status', sa.String(25), nullable=True),
        sa.Column('deed_attachment_id', sa.CHAR(36), sa.ForeignKey('attachments.id', ondelete='SET NULL'), nullable=True),
    )

    op.create_table(
        'llp_details',
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('incorporation_date', sa.Date(), nullable=True),
        sa.Column('llp_agreement_date', sa.Date(), nullable=True),
        sa.Column('agreement_attachment_id', sa.CHAR(36), sa.ForeignKey('attachments.id', ondelete='SET NULL'), nullable=True),
    )

    op.create_table(
        'company_details',
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('incorporation_date', sa.Date(), nullable=True),
        sa.Column('company_class', sa.String(30), nullable=True),
        sa.Column('authorised_capital_paise', sa.BigInteger(), nullable=True),
        sa.Column('paid_up_capital_paise', sa.BigInteger(), nullable=True),
        sa.Column('registered_office_address', sa.Text(), nullable=True),
    )

    # 9. project_scenarios
    op.create_table(
        'project_scenarios',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_code', sa.String(30), nullable=False),
        sa.Column('scenario_name', sa.String(100), nullable=False),
        sa.Column('scenario_type', sa.String(25), nullable=False, server_default='BASE'),
        sa.Column('parent_scenario_id', sa.CHAR(36), sa.ForeignKey('project_scenarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('probability_pct', sa.String(40), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
        sa.UniqueConstraint('project_id', 'scenario_code', name='uq_project_scenarios_code'),
    )
    op.create_index('idx_project_scenarios_project_id', 'project_scenarios', ['project_id'])

    # 10. project_periods
    op.create_table(
        'project_periods',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_sequence', sa.SmallInteger(), nullable=False),
        sa.Column('period_role', sa.String(20), nullable=False, server_default='PROJECTION'),
        sa.Column('period_granularity', sa.String(15), nullable=False, server_default='ANNUAL'),
        sa.Column('period_label', sa.String(50), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False, server_default='FULL_YEAR'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('financial_year_label', sa.String(30), nullable=True),
        sa.Column('display_sequence', sa.SmallInteger(), nullable=False),
        sa.Column('is_report_column', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.UniqueConstraint('project_id', 'period_role', 'period_granularity', 'period_sequence', name='uq_project_periods_seq'),
    )
    op.create_index('idx_project_periods_project_id', 'project_periods', ['project_id'])
    op.create_index('idx_project_periods_display', 'project_periods', ['project_id', 'display_sequence'])

    # 11. audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('entity_id', sa.CHAR(36), sa.ForeignKey('entities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(40), nullable=False),
        sa.Column('record_type', sa.String(60), nullable=False),
        sa.Column('record_id', sa.String(36), nullable=False),
        sa.Column('before_json', sa.Text(), nullable=True),
        sa.Column('after_json', sa.Text(), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor_label', sa.String(100), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
    )
    op.create_index('idx_audit_events_rec', 'audit_events', ['record_type', 'record_id'])

    # 12. app_settings
    op.create_table(
        'app_settings',
        sa.Column('setting_key', sa.String(100), primary_key=True),
        sa.Column('setting_value', sa.Text(), nullable=False),
        sa.Column('setting_group', sa.String(50), nullable=False, server_default='GENERAL'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. backup_history
    op.create_table(
        'backup_history',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('backup_file_path', sa.Text(), nullable=False),
        sa.Column('backup_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='SUCCESS'),
        sa.Column('notes', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('backup_history')
    op.drop_table('app_settings')
    op.drop_table('audit_events')
    op.drop_table('project_periods')
    op.drop_table('project_scenarios')
    op.drop_table('company_details')
    op.drop_table('llp_details')
    op.drop_table('partnership_details')
    op.drop_table('proprietorship_details')
    op.drop_table('huf_details')
    op.drop_table('entity_identifiers')
    op.drop_table('attachments')
    op.drop_table('project_sources')
    op.drop_table('projects')
    op.drop_table('entity_members')
    op.drop_table('entities')
    op.drop_table('clients')
