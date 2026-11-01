"""Phase 5 Reporting, Templates, and Generated Reports Schema

Revision ID: 0005_phase5_reporting
Revises: 0004_phase4_appraisal_and_validation
Create Date: 2026-11-01 18:00:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = '0005_phase5_reporting'
down_revision: Union[str, None] = '0004_phase4_appraisal_and_validation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. report_templates
    report_templates = op.create_table(
        'report_templates',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('template_code', sa.String(50), unique=True, nullable=False),
        sa.Column('template_name', sa.String(160), nullable=False),
        sa.Column('output_type', sa.String(15), nullable=False),
        sa.Column('constitution_code', sa.String(30), nullable=True),
        sa.Column('bank_name', sa.String(160), nullable=True),
        sa.Column('template_version', sa.String(30), default='1.0', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('active_flag', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. report_template_sections
    report_template_sections = op.create_table(
        'report_template_sections',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('report_template_id', sa.CHAR(36), sa.ForeignKey('report_templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_code', sa.String(60), nullable=False),
        sa.Column('section_title', sa.String(180), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('default_included', sa.Boolean(), default=True, nullable=False),
        sa.Column('required_flag', sa.Boolean(), default=False, nullable=False),
        sa.Column('renderer_key', sa.String(60), nullable=False),
        sa.UniqueConstraint('report_template_id', 'section_code', name='uq_template_section_code'),
    )
    op.create_index('idx_tmpl_section_lookup', 'report_template_sections', ['report_template_id', 'sort_order'])

    # 3. generated_reports
    op.create_table(
        'generated_reports',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_id', sa.CHAR(36), sa.ForeignKey('project_scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calculation_run_id', sa.CHAR(36), sa.ForeignKey('calculation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_template_id', sa.CHAR(36), sa.ForeignKey('report_templates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('report_version', sa.String(30), default='1.0', nullable=False),
        sa.Column('output_type', sa.String(15), nullable=False),
        sa.Column('stored_relative_path', sa.Text(), nullable=False),
        sa.Column('file_hash', sa.CHAR(64), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generation_status', sa.String(20), default='SUCCESS', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index('idx_gen_reports_run', 'generated_reports', ['calculation_run_id', 'report_template_id'])
    op.create_index('idx_gen_reports_proj', 'generated_reports', ['project_id', 'output_type'])

    # 4. Seed Standard Report Templates
    now = datetime.now(timezone.utc)
    cma_id = str(uuid.uuid4())
    dpr_id = str(uuid.uuid4())
    summary_id = str(uuid.uuid4())

    op.bulk_insert(
        report_templates,
        [
            {
                'id': cma_id,
                'template_code': 'TMPL_CMA_BANK',
                'template_name': 'Standard Bank CMA & Project Appraisal Book',
                'output_type': 'MULTI',
                'constitution_code': None,
                'bank_name': None,
                'template_version': '1.0',
                'description': 'Comprehensive bank credit appraisal report with horizontal 7-year statements, DSCR, break-even, and audit disclosures.',
                'active_flag': True,
                'created_at': now,
            },
            {
                'id': dpr_id,
                'template_code': 'TMPL_DPR_EXPANDED',
                'template_name': 'Comprehensive Detailed Project Report (DPR)',
                'output_type': 'MULTI',
                'constitution_code': None,
                'bank_name': None,
                'template_version': '1.0',
                'description': 'Full detailed project report including promoter background, technical specifications, and integrated financial forecasts.',
                'active_flag': True,
                'created_at': now,
            },
            {
                'id': summary_id,
                'template_code': 'TMPL_EXEC_SUMMARY',
                'template_name': 'Executive Summary & Key Financial Indicators',
                'output_type': 'MULTI',
                'constitution_code': None,
                'bank_name': None,
                'template_version': '1.0',
                'description': 'Concise 2-page executive summary covering project cost, means of finance, key returns, and banking ratios.',
                'active_flag': True,
                'created_at': now,
            },
        ]
    )

    # 5. Seed Sections for Standard CMA Template
    sections = [
        ('COVER_SUMMARY', 'Cover Page & Executive Summary', 1, True, True, 'summary_renderer'),
        ('PROJECT_COST_MEANS', 'Project Cost & Means of Finance', 2, True, True, 'project_cost_renderer'),
        ('FINANCIAL_STATEMENTS', 'Projected Financial Statements (P&L, BS, Cash Flow)', 3, True, True, 'statements_renderer'),
        ('RATIOS_DSCR', 'Financial Ratios & Lender DSCR Analysis', 4, True, True, 'ratios_renderer'),
        ('BREAK_EVEN_RETURNS', 'Break-Even, NPV, Project IRR & Payback', 5, True, True, 'returns_renderer'),
        ('SENSITIVITY_MATRIX', 'Operational Sensitivity Analysis Matrix', 6, True, False, 'sensitivity_renderer'),
        ('LOAN_AMORTIZATION', 'Monthly Loan Repayment Schedule', 7, True, True, 'loan_renderer'),
        ('ASSET_DEPRECIATION', 'Fixed Assets & Depreciation Schedule', 8, True, True, 'asset_renderer'),
        ('AUDIT_VALIDATION', 'Cross-Statement Audit & Invariant Certificate', 9, True, True, 'validation_renderer'),
    ]

    section_rows = [
        {
            'id': str(uuid.uuid4()),
            'report_template_id': cma_id,
            'section_code': s[0],
            'section_title': s[1],
            'sort_order': s[2],
            'default_included': s[3],
            'required_flag': s[4],
            'renderer_key': s[5],
        }
        for s in sections
    ]
    op.bulk_insert(report_template_sections, section_rows)


def downgrade() -> None:
    op.drop_table('generated_reports')
    op.drop_table('report_template_sections')
    op.drop_table('report_templates')
