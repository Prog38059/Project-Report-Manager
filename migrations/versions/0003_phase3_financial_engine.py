"""Phase 3 Financial Engine Schema and Statement Catalogue Seed Data

Revision ID: 0003_phase3_financial_engine
Revises: 0002_phase2_inputs
Create Date: 2026-11-01 14:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003_phase3_financial_engine'
down_revision: Union[str, None] = '0002_phase2_inputs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. statement_line_definitions
    op.create_table(
        'statement_line_definitions',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('line_code', sa.String(60), nullable=False, unique=True),
        sa.Column('statement_type', sa.String(20), nullable=False),
        sa.Column('display_name', sa.String(180), nullable=False),
        sa.Column('parent_line_code', sa.String(60), nullable=True),
        sa.Column('line_kind', sa.String(20), nullable=False),
        sa.Column('normal_balance', sa.String(10), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('formula_code', sa.String(60), nullable=True),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )
    op.create_index('idx_stmt_line_code', 'statement_line_definitions', ['line_code'])
    op.create_index('idx_stmt_line_type', 'statement_line_definitions', ['statement_type'])

    # 2. entity_statement_mappings
    op.create_table(
        'entity_statement_mappings',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('constitution_code', sa.String(30), nullable=False),
        sa.Column('reporting_basis_code', sa.String(40), nullable=False),
        sa.Column('statement_type', sa.String(20), nullable=False),
        sa.Column('line_code', sa.String(60), sa.ForeignKey('statement_line_definitions.line_code', ondelete='CASCADE'), nullable=False),
        sa.Column('display_label', sa.String(180), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('required_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('effective_from', sa.Date(), nullable=True),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.UniqueConstraint('constitution_code', 'reporting_basis_code', 'statement_type', 'line_code', 'effective_from', name='uq_entity_stmt_map'),
    )
    op.create_index('idx_stmt_map_lookup', 'entity_statement_mappings', ['constitution_code', 'reporting_basis_code', 'statement_type'])

    # 3. calculation_runs
    op.create_table(
        'calculation_runs',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_id', sa.CHAR(36), sa.ForeignKey('project_scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_number', sa.Integer(), nullable=False),
        sa.Column('engine_version', sa.String(40), nullable=False),
        sa.Column('input_hash', sa.CHAR(64), nullable=False),
        sa.Column('run_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('run_status', sa.String(20), nullable=False),
        sa.Column('prepared_by_label', sa.String(100), nullable=True),
        sa.Column('summary_note', sa.Text(), nullable=True),
        sa.Column('validation_error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('validation_warning_count', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('scenario_id', 'run_number', name='uq_scenario_run_number'),
    )
    op.create_index('idx_calc_runs_scenario', 'calculation_runs', ['scenario_id'])
    op.create_index('idx_calc_runs_project', 'calculation_runs', ['project_id'])

    # 4. calculation_run_snapshots
    op.create_table(
        'calculation_run_snapshots',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('calculation_run_id', sa.CHAR(36), sa.ForeignKey('calculation_runs.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('snapshot_schema_version', sa.String(30), nullable=False),
        sa.Column('input_snapshot_json', sa.Text(), nullable=False),
        sa.Column('input_hash', sa.CHAR(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. statement_line_results
    op.create_table(
        'statement_line_results',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('calculation_run_id', sa.CHAR(36), sa.ForeignKey('calculation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_id', sa.CHAR(36), sa.ForeignKey('project_periods.id', ondelete='CASCADE'), nullable=False),
        sa.Column('statement_type', sa.String(20), nullable=False),
        sa.Column('line_code', sa.String(60), nullable=False),
        sa.Column('line_label_snapshot', sa.String(180), nullable=False),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('formula_reference', sa.String(60), nullable=True),
        sa.Column('trace_json', sa.Text(), nullable=True),
        sa.UniqueConstraint('calculation_run_id', 'period_id', 'statement_type', 'line_code', name='uq_calc_period_stmt_line'),
    )
    op.create_index('idx_stmt_results_lookup', 'statement_line_results', ['calculation_run_id', 'statement_type', 'period_id'])

    # 6. loan_schedule_results
    op.create_table(
        'loan_schedule_results',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('calculation_run_id', sa.CHAR(36), sa.ForeignKey('calculation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_facility_id', sa.CHAR(36), nullable=True),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('opening_balance_paise', sa.BigInteger(), nullable=False),
        sa.Column('disbursement_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('payment_paise', sa.BigInteger(), nullable=False),
        sa.Column('interest_paise', sa.BigInteger(), nullable=False),
        sa.Column('principal_paise', sa.BigInteger(), nullable=False),
        sa.Column('closing_balance_paise', sa.BigInteger(), nullable=False),
        sa.UniqueConstraint('calculation_run_id', 'loan_facility_id', 'installment_number', name='uq_loan_sched_inst'),
    )
    op.create_index('idx_loan_sched_run', 'loan_schedule_results', ['calculation_run_id'])

    # 7. asset_schedule_results
    op.create_table(
        'asset_schedule_results',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('calculation_run_id', sa.CHAR(36), sa.ForeignKey('calculation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_item_id', sa.CHAR(36), nullable=True),
        sa.Column('period_id', sa.CHAR(36), sa.ForeignKey('project_periods.id', ondelete='CASCADE'), nullable=False),
        sa.Column('opening_gross_paise', sa.BigInteger(), nullable=False),
        sa.Column('additions_paise', sa.BigInteger(), nullable=False),
        sa.Column('disposals_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('closing_gross_paise', sa.BigInteger(), nullable=False),
        sa.Column('depreciation_paise', sa.BigInteger(), nullable=False),
        sa.Column('accumulated_depreciation_paise', sa.BigInteger(), nullable=False),
        sa.Column('closing_nbv_paise', sa.BigInteger(), nullable=False),
        sa.UniqueConstraint('calculation_run_id', 'asset_item_id', 'period_id', name='uq_asset_sched_period'),
    )
    op.create_index('idx_asset_sched_run', 'asset_schedule_results', ['calculation_run_id'])

    # --- Seed Standard Statement Line Definitions ---
    stmt_lines_table = sa.table(
        'statement_line_definitions',
        sa.column('id', sa.CHAR(36)),
        sa.column('line_code', sa.String(60)),
        sa.column('statement_type', sa.String(20)),
        sa.column('display_name', sa.String(180)),
        sa.column('parent_line_code', sa.String(60)),
        sa.column('line_kind', sa.String(20)),
        sa.column('normal_balance', sa.String(10)),
        sa.column('sort_order', sa.Integer()),
        sa.column('is_required', sa.Boolean()),
        sa.column('formula_code', sa.String(60)),
        sa.column('active_flag', sa.Boolean()),
    )

    seed_lines = [
        # Profit & Loss
        ('GROSS_REVENUE', 'PL', 'Gross Billing / Revenue from Operations', None, 'INPUT', 'CREDIT', 10, True, 'REVENUE_SUM'),
        ('OUTPUT_GST', 'PL', 'Less: Output GST', None, 'INPUT', 'DEBIT', 20, False, 'GST_OUT_SUM'),
        ('NET_REVENUE', 'PL', 'Net Revenue from Operations', None, 'SUBTOTAL', 'CREDIT', 30, True, 'GROSS_REVENUE - OUTPUT_GST'),
        ('RAW_MATERIAL_COST', 'PL', 'Raw Material Consumed', None, 'INPUT', 'DEBIT', 40, True, 'RM_EXPENSE_SUM'),
        ('OTHER_DIRECT_COSTS', 'PL', 'Direct / Power / Fuel / Consumables', None, 'INPUT', 'DEBIT', 50, False, 'DIRECT_EXPENSE_SUM'),
        ('TOTAL_DIRECT_COSTS', 'PL', 'Total Direct Costs', None, 'SUBTOTAL', 'DEBIT', 60, True, 'RAW_MATERIAL_COST + OTHER_DIRECT_COSTS'),
        ('GROSS_PROFIT', 'PL', 'Gross Profit', None, 'SUBTOTAL', 'CREDIT', 70, True, 'NET_REVENUE - TOTAL_DIRECT_COSTS'),
        ('EMPLOYEE_EXPENSES', 'PL', 'Employee Benefit Expenses', None, 'INPUT', 'DEBIT', 80, True, 'STAFF_EXPENSE_SUM'),
        ('ADMIN_EXPENSES', 'PL', 'Administrative & General Expenses', None, 'INPUT', 'DEBIT', 90, True, 'ADMIN_EXPENSE_SUM'),
        ('SELLING_EXPENSES', 'PL', 'Selling & Distribution Expenses', None, 'INPUT', 'DEBIT', 100, False, 'SELLING_EXPENSE_SUM'),
        ('TOTAL_OPEX', 'PL', 'Total Operating Expenses', None, 'SUBTOTAL', 'DEBIT', 110, True, 'EMPLOYEE + ADMIN + SELLING'),
        ('EBITDA', 'PL', 'Operating Profit (EBITDA)', None, 'SUBTOTAL', 'CREDIT', 120, True, 'GROSS_PROFIT - TOTAL_OPEX'),
        ('DEPRECIATION', 'PL', 'Depreciation & Amortisation', None, 'CALCULATED', 'DEBIT', 130, True, 'BOOK_DEPRECIATION'),
        ('EBIT', 'PL', 'Earnings Before Interest & Tax (EBIT)', None, 'SUBTOTAL', 'CREDIT', 140, True, 'EBITDA - DEPRECIATION'),
        ('FINANCE_COSTS', 'PL', 'Finance Costs / Loan Interest', None, 'CALCULATED', 'DEBIT', 150, True, 'TERM_INTEREST + WC_INTEREST'),
        ('PBT', 'PL', 'Profit Before Tax (PBT)', None, 'SUBTOTAL', 'CREDIT', 160, True, 'EBIT - FINANCE_COSTS'),
        ('TAX_PROVISION', 'PL', 'Provision for Income Tax', None, 'CALCULATED', 'DEBIT', 170, True, 'TAX_CALCULATOR'),
        ('PAT', 'PL', 'Profit After Tax (PAT)', None, 'TOTAL', 'CREDIT', 180, True, 'PBT - TAX_PROVISION'),

        # Balance Sheet
        ('FIXED_ASSETS_NET', 'BS', 'Property, Plant & Equipment (Net)', None, 'CALCULATED', 'DEBIT', 210, True, 'NET_FIXED_ASSETS'),
        ('INVENTORY_TOTAL', 'BS', 'Inventories (RM, WIP, Finished Goods)', None, 'CALCULATED', 'DEBIT', 220, True, 'TOTAL_INVENTORY'),
        ('TRADE_RECEIVABLES', 'BS', 'Trade Receivables (Debtors)', None, 'CALCULATED', 'DEBIT', 230, True, 'TRADE_RECEIVABLES'),
        ('CASH_AND_BANK', 'BS', 'Cash & Bank Balances', None, 'CALCULATED', 'DEBIT', 240, True, 'CLOSING_CASH'),
        ('TOTAL_CURRENT_ASSETS', 'BS', 'Total Current Assets', None, 'SUBTOTAL', 'DEBIT', 250, True, 'SUM_CURRENT_ASSETS'),
        ('TOTAL_ASSETS', 'BS', 'Total Assets', None, 'TOTAL', 'DEBIT', 260, True, 'FIXED_ASSETS_NET + TOTAL_CURRENT_ASSETS'),
        ('NET_WORTH', 'BS', 'Proprietor Capital / Partners Equity / Net Worth', None, 'CALCULATED', 'CREDIT', 270, True, 'CLOSING_NET_WORTH'),
        ('LONG_TERM_DEBT', 'BS', 'Term Borrowings (Secured Term Loans)', None, 'CALCULATED', 'CREDIT', 280, True, 'CLOSING_TERM_DEBT'),
        ('SHORT_TERM_WC_DEBT', 'BS', 'Short-Term Borrowings (Bank Working Capital)', None, 'CALCULATED', 'CREDIT', 290, True, 'WC_BANK_LIMIT'),
        ('TRADE_PAYABLES', 'BS', 'Trade Payables (Creditors)', None, 'CALCULATED', 'CREDIT', 300, True, 'TRADE_PAYABLES'),
        ('OTHER_CURRENT_LIAB', 'BS', 'Other Current Liabilities & Provisions (Tax etc.)', None, 'CALCULATED', 'CREDIT', 310, True, 'OTHER_CL'),
        ('TOTAL_CURRENT_LIAB', 'BS', 'Total Current Liabilities', None, 'SUBTOTAL', 'CREDIT', 320, True, 'SUM_CURRENT_LIABILITIES'),
        ('TOTAL_LIABILITIES_EQUITY', 'BS', 'Total Liabilities & Equity', None, 'TOTAL', 'CREDIT', 330, True, 'NET_WORTH + DEBT + CURRENT_LIAB'),

        # Cash Flow Statement (Indirect Method)
        ('CF_OP_PROFIT', 'CASH_FLOW', 'Operating Cash Flow before Working Capital (PAT + Dep)', None, 'CALCULATED', 'CREDIT', 410, True, 'PAT + DEPRECIATION'),
        ('CF_WC_CHANGES', 'CASH_FLOW', 'Working Capital Adjustments', None, 'CALCULATED', 'NEUTRAL', 420, True, 'DELTA_NWC'),
        ('CF_NET_OPERATING', 'CASH_FLOW', 'Net Cash from Operating Activities', None, 'SUBTOTAL', 'CREDIT', 430, True, 'CF_OP_PROFIT + CF_WC_CHANGES'),
        ('CF_CAPEX', 'CASH_FLOW', 'Capital Expenditure (Purchase of Fixed Assets)', None, 'CALCULATED', 'DEBIT', 440, True, 'TOTAL_CAPEX'),
        ('CF_NET_INVESTING', 'CASH_FLOW', 'Net Cash from Investing Activities', None, 'SUBTOTAL', 'DEBIT', 450, True, '- CF_CAPEX'),
        ('CF_EQUITY_INTRODUCED', 'CASH_FLOW', 'Capital / Equity Introduced', None, 'CALCULATED', 'CREDIT', 460, False, 'FRESH_EQUITY'),
        ('CF_LOAN_DISBURSEMENT', 'CASH_FLOW', 'Term Loan Disbursements', None, 'CALCULATED', 'CREDIT', 470, False, 'LOAN_DISBURSEMENT'),
        ('CF_LOAN_REPAYMENT', 'CASH_FLOW', 'Repayment of Term Borrowings', None, 'CALCULATED', 'DEBIT', 480, False, 'LOAN_PRINCIPAL_REPAID'),
        ('CF_DRAWINGS', 'CASH_FLOW', 'Drawings / Dividends Paid', None, 'CALCULATED', 'DEBIT', 490, False, 'DRAWINGS'),
        ('CF_NET_FINANCING', 'CASH_FLOW', 'Net Cash from Financing Activities', None, 'SUBTOTAL', 'CREDIT', 500, True, 'EQUITY + LOANS - REPAYMENTS - DRAWINGS'),
        ('NET_CASH_FLOW', 'CASH_FLOW', 'Net Increase / (Decrease) in Cash & Cash Equivalents', None, 'SUBTOTAL', 'NEUTRAL', 510, True, 'OP + INV + FIN'),
        ('OPENING_CASH', 'CASH_FLOW', 'Cash & Bank Balances at Beginning of Period', None, 'CALCULATED', 'DEBIT', 520, True, 'PRIOR_CLOSING_CASH'),
        ('CLOSING_CASH', 'CASH_FLOW', 'Cash & Bank Balances at End of Period', None, 'TOTAL', 'DEBIT', 530, True, 'OPENING_CASH + NET_CASH_FLOW'),
    ]

    op.bulk_insert(
        stmt_lines_table,
        [
            {
                'id': str(uuid.uuid4()),
                'line_code': code,
                'statement_type': stype,
                'display_name': dname,
                'parent_line_code': parent,
                'line_kind': lkind,
                'normal_balance': nbal,
                'sort_order': sorder,
                'is_required': req,
                'formula_code': form,
                'active_flag': True,
            }
            for code, stype, dname, parent, lkind, nbal, sorder, req, form in seed_lines
        ],
    )


def downgrade() -> None:
    op.drop_table('asset_schedule_results')
    op.drop_table('loan_schedule_results')
    op.drop_table('statement_line_results')
    op.drop_table('calculation_run_snapshots')
    op.drop_table('calculation_runs')
    op.drop_table('entity_statement_mappings')
    op.drop_table('statement_line_definitions')
