"""Phase 4 Appraisal Metrics and Validation Results Schema

Revision ID: 0004_phase4_appraisal_and_validation
Revises: 0003_phase3_financial_engine
Create Date: 2026-11-01 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004_phase4_appraisal_and_validation'
down_revision: Union[str, None] = '0003_phase3_financial_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ratio_results
    op.create_table(
        'ratio_results',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('calculation_run_id', sa.CHAR(36), sa.ForeignKey('calculation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_id', sa.CHAR(36), sa.ForeignKey('project_periods.id', ondelete='CASCADE'), nullable=True),
        sa.Column('ratio_code', sa.String(60), nullable=False),
        sa.Column('numerator_value_text', sa.String(100), nullable=True),
        sa.Column('denominator_value_text', sa.String(100), nullable=True),
        sa.Column('ratio_value_text', sa.String(100), nullable=True),
        sa.Column('unit_code', sa.String(20), nullable=True),
        sa.Column('method_code', sa.String(60), nullable=False),
        sa.Column('interpretation_code', sa.String(40), nullable=True),
        sa.Column('benchmark_note', sa.Text(), nullable=True),
    )
    op.create_index('idx_ratio_run_code', 'ratio_results', ['calculation_run_id', 'ratio_code'])
    op.create_index('idx_ratio_run_period', 'ratio_results', ['calculation_run_id', 'period_id'])

    # 2. validation_results
    op.create_table(
        'validation_results',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('calculation_run_id', sa.CHAR(36), sa.ForeignKey('calculation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_code', sa.String(60), nullable=False),
        sa.Column('severity', sa.String(15), nullable=False),
        sa.Column('scope_code', sa.String(30), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('expected_value_text', sa.String(120), nullable=True),
        sa.Column('actual_value_text', sa.String(120), nullable=True),
        sa.Column('resolution_status', sa.String(20), nullable=False, server_default='OPEN'),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('resolved_by_label', sa.String(100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_val_results_run_sev', 'validation_results', ['calculation_run_id', 'severity'])


def downgrade() -> None:
    op.drop_table('validation_results')
    op.drop_table('ratio_results')
