"""Phase 2 Project Inputs Schema and Seed Data

Revision ID: 0002_phase2_inputs
Revises: 0001_phase1_foundation
Create Date: 2026-11-01 12:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002_phase2_inputs'
down_revision: Union[str, None] = '0001_phase1_foundation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. project_cost_heads
    op.create_table(
        'project_cost_heads',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('head_code', sa.String(40), nullable=False, unique=True),
        sa.Column('head_name', sa.String(150), nullable=False),
        sa.Column('category_code', sa.String(30), nullable=False),
        sa.Column('capitalisation_default', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )
    op.create_index('idx_cost_heads_code', 'project_cost_heads', ['head_code'])

    # 2. project_cost_items
    op.create_table(
        'project_cost_items',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('scenario_id', sa.CHAR(36), sa.ForeignKey('project_scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cost_head_id', sa.CHAR(36), sa.ForeignKey('project_cost_heads.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('quantity_decimal_text', sa.String(80), nullable=True),
        sa.Column('unit_code', sa.String(30), nullable=True),
        sa.Column('rate_decimal_text', sa.String(80), nullable=True),
        sa.Column('basic_amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('gst_rate_pct_text', sa.String(40), nullable=True),
        sa.Column('gst_amount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('eligible_itc_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('non_creditable_tax_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('capitalised_amount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('project_cash_requirement_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('payment_due_date', sa.Date(), nullable=True),
        sa.Column('supplier_name', sa.String(200), nullable=True),
        sa.Column('source_id', sa.CHAR(36), sa.ForeignKey('project_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_cost_items_scenario', 'project_cost_items', ['scenario_id'])
    op.create_index('idx_cost_items_head', 'project_cost_items', ['cost_head_id'])

    # 3. funding_heads
    op.create_table(
        'funding_heads',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('funding_code', sa.String(40), nullable=False, unique=True),
        sa.Column('funding_name', sa.String(150), nullable=False),
        sa.Column('funding_category', sa.String(30), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )
    op.create_index('idx_funding_heads_code', 'funding_heads', ['funding_code'])

    # 4. funding_sources
    op.create_table(
        'funding_sources',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('scenario_id', sa.CHAR(36), sa.ForeignKey('project_scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('funding_head_id', sa.CHAR(36), sa.ForeignKey('funding_heads.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('source_name', sa.String(200), nullable=False),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('expected_date', sa.Date(), nullable=True),
        sa.Column('status_code', sa.String(20), nullable=False, server_default='PROPOSED'),
        sa.Column('loan_facility_id', sa.CHAR(36), nullable=True),
        sa.Column('source_id', sa.CHAR(36), sa.ForeignKey('project_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('terms_note', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
    )
    op.create_index('idx_funding_sources_scenario', 'funding_sources', ['scenario_id'])
    op.create_index('idx_funding_sources_head', 'funding_sources', ['funding_head_id'])

    # 5. revenue_methods
    op.create_table(
        'revenue_methods',
        sa.Column('method_code', sa.String(40), primary_key=True),
        sa.Column('method_name', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )

    # 6. revenue_streams
    op.create_table(
        'revenue_streams',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('scenario_id', sa.CHAR(36), sa.ForeignKey('project_scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stream_code', sa.String(40), nullable=False),
        sa.Column('stream_name', sa.String(150), nullable=False),
        sa.Column('method_code', sa.String(40), sa.ForeignKey('revenue_methods.method_code', ondelete='RESTRICT'), nullable=False),
        sa.Column('unit_code', sa.String(30), nullable=True),
        sa.Column('gst_treatment_code', sa.String(30), nullable=False),
        sa.Column('gst_rate_pct_text', sa.String(40), nullable=True),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
        sa.UniqueConstraint('scenario_id', 'stream_code', name='uq_revenue_streams_code'),
    )
    op.create_index('idx_revenue_streams_scenario', 'revenue_streams', ['scenario_id'])

    # 7. revenue_forecasts
    op.create_table(
        'revenue_forecasts',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('revenue_stream_id', sa.CHAR(36), sa.ForeignKey('revenue_streams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_id', sa.CHAR(36), sa.ForeignKey('project_periods.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calculation_mode', sa.String(20), nullable=False, server_default='DRIVER'),
        sa.Column('capacity_decimal_text', sa.String(80), nullable=True),
        sa.Column('utilisation_pct_text', sa.String(40), nullable=True),
        sa.Column('units_decimal_text', sa.String(80), nullable=True),
        sa.Column('price_per_unit_decimal_text', sa.String(80), nullable=True),
        sa.Column('operating_days_decimal_text', sa.String(80), nullable=True),
        sa.Column('growth_pct_text', sa.String(40), nullable=True),
        sa.Column('gross_billing_override_paise', sa.BigInteger(), nullable=True),
        sa.Column('source_id', sa.CHAR(36), sa.ForeignKey('project_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
        sa.UniqueConstraint('revenue_stream_id', 'period_id', name='uq_revenue_forecasts_stream_period'),
    )
    op.create_index('idx_revenue_forecasts_stream', 'revenue_forecasts', ['revenue_stream_id'])
    op.create_index('idx_revenue_forecasts_period', 'revenue_forecasts', ['period_id'])

    # 8. expense_heads
    op.create_table(
        'expense_heads',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('expense_code', sa.String(40), nullable=False, unique=True),
        sa.Column('expense_name', sa.String(150), nullable=False),
        sa.Column('expense_group', sa.String(30), nullable=False),
        sa.Column('default_cost_behaviour', sa.String(20), nullable=False),
        sa.Column('default_projection_method', sa.String(30), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )
    op.create_index('idx_expense_heads_code', 'expense_heads', ['expense_code'])

    # 9. expense_forecasts
    op.create_table(
        'expense_forecasts',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('scenario_id', sa.CHAR(36), sa.ForeignKey('project_scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expense_head_id', sa.CHAR(36), sa.ForeignKey('expense_heads.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('period_id', sa.CHAR(36), sa.ForeignKey('project_periods.id', ondelete='CASCADE'), nullable=False),
        sa.Column('projection_method', sa.String(30), nullable=False),
        sa.Column('base_amount_paise', sa.BigInteger(), nullable=True),
        sa.Column('growth_pct_text', sa.String(40), nullable=True),
        sa.Column('revenue_pct_text', sa.String(40), nullable=True),
        sa.Column('unit_cost_decimal_text', sa.String(80), nullable=True),
        sa.Column('quantity_driver_code', sa.String(60), nullable=True),
        sa.Column('manual_amount_paise', sa.BigInteger(), nullable=True),
        sa.Column('source_id', sa.CHAR(36), sa.ForeignKey('project_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
        sa.UniqueConstraint('scenario_id', 'expense_head_id', 'period_id', name='uq_expense_forecasts_scenario_head_period'),
    )
    op.create_index('idx_expense_forecasts_scenario', 'expense_forecasts', ['scenario_id'])
    op.create_index('idx_expense_forecasts_head', 'expense_forecasts', ['expense_head_id'])
    op.create_index('idx_expense_forecasts_period', 'expense_forecasts', ['period_id'])

    # 10. industry_templates
    op.create_table(
        'industry_templates',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('industry_code', sa.String(50), nullable=False, unique=True),
        sa.Column('industry_name', sa.String(150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_version', sa.String(30), nullable=False, server_default='1.0'),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )
    op.create_index('idx_industry_templates_code', 'industry_templates', ['industry_code'])

    # 11. industry_template_fields
    op.create_table(
        'industry_template_fields',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('industry_template_id', sa.CHAR(36), sa.ForeignKey('industry_templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_code', sa.String(40), nullable=False),
        sa.Column('field_code', sa.String(60), nullable=False),
        sa.Column('field_label', sa.String(150), nullable=False),
        sa.Column('input_type', sa.String(25), nullable=False),
        sa.Column('unit_code', sa.String(30), nullable=True),
        sa.Column('required_flag', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('default_value_text', sa.Text(), nullable=True),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('idx_template_fields_template', 'industry_template_fields', ['industry_template_id'])

    # 12. historical_statement_lines
    op.create_table(
        'historical_statement_lines',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('project_id', sa.CHAR(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_id', sa.CHAR(36), sa.ForeignKey('project_periods.id', ondelete='CASCADE'), nullable=False),
        sa.Column('statement_type', sa.String(20), nullable=False),
        sa.Column('line_code', sa.String(60), nullable=False),
        sa.Column('line_label', sa.String(180), nullable=False),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('source_id', sa.CHAR(36), sa.ForeignKey('project_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_imported', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('mapping_status', sa.String(20), nullable=False, server_default='UNREVIEWED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_label', sa.String(100), nullable=True),
        sa.Column('updated_by_label', sa.String(100), nullable=True),
        sa.UniqueConstraint(
            'project_id', 'period_id', 'statement_type', 'line_code',
            name='uq_historical_statement_lines_item',
        ),
    )
    op.create_index('idx_historical_lines_project', 'historical_statement_lines', ['project_id'])
    op.create_index('idx_historical_lines_period', 'historical_statement_lines', ['period_id'])

    # --- Seed data for Master Heads, Revenue Methods, and Starter Industry Templates ---
    _seed_master_data()


def _seed_master_data():
    conn = op.get_bind()

    # Seed Revenue Methods
    methods = [
        ("CAPACITY_UTILISATION_PRICE", "Capacity x Utilisation x Price", "Capacity per operating period x Utilisation % x Operating periods x Selling price per unit"),
        ("UNITS_PRICE", "Units x Price", "Quantity sold x Selling price per unit"),
        ("CUSTOMERS_AVERAGE_BILL", "Customers x Average Bill", "Number of customers/covers x Average bill per customer"),
        ("OCCUPANCY_RATE", "Occupancy-based Rate", "Available unit-days x Occupancy % x Average rate per occupied unit"),
        ("RENTAL_UNITS_RATE", "Rental Units Rate", "Rentable units x Occupancy % x Rent per unit per period"),
        ("HEADCOUNT_BILLING", "Headcount / Billable Utilisation", "Available hours x Billable utilisation % x Billing rate"),
        ("TURNOVER_GROWTH", "Turnover Growth %", "Prior period gross billing x (1 + growth rate)"),
        ("MANUAL", "Manual Amount", "Direct user entry with explicit GST-inclusive/exclusive declaration"),
        ("CUSTOM_REGISTERED_METHOD", "Custom Formula", "Configured user-defined method"),
    ]
    for code, name, desc in methods:
        conn.execute(
            sa.text("INSERT INTO revenue_methods (method_code, method_name, description, active_flag) VALUES (:c, :n, :d, 1)"),
            {"c": code, "n": name, "d": desc},
        )

    # Seed Project Cost Heads
    cost_heads = [
        (str(uuid.uuid4()), "LAND", "Land & Site Development", "LAND", True, 10),
        (str(uuid.uuid4()), "BUILDING_CIVIL", "Building & Civil Works", "BUILDING", True, 20),
        (str(uuid.uuid4()), "PLANT_MACHINERY", "Plant & Machinery / Equipment", "PLANT", True, 30),
        (str(uuid.uuid4()), "ELECTRICAL_INSTALL", "Electrical Installation & Substation", "PLANT", True, 40),
        (str(uuid.uuid4()), "FURNITURE_FIXTURES", "Furniture, Fixtures & Office Equipment", "OTHER_FIXED_ASSET", True, 50),
        (str(uuid.uuid4()), "VEHICLES", "Commercial Vehicles / Transport", "OTHER_FIXED_ASSET", True, 60),
        (str(uuid.uuid4()), "PREOPERATIVE_EXP", "Pre-operative & Preliminary Expenses", "PREOPERATIVE", False, 70),
        (str(uuid.uuid4()), "SECURITY_DEPOSITS", "Security Deposits (Power / Rent / Utilities)", "DEPOSIT", False, 80),
        (str(uuid.uuid4()), "CONTINGENCY", "Provision for Contingencies", "CONTINGENCY", True, 90),
        (str(uuid.uuid4()), "WC_MARGIN", "Margin Money for Working Capital", "WORKING_CAPITAL_MARGIN", False, 100),
    ]
    for uid, code, name, cat, cap, order in cost_heads:
        conn.execute(
            sa.text("INSERT INTO project_cost_heads (id, head_code, head_name, category_code, capitalisation_default, sort_order, active_flag) VALUES (:id, :c, :n, :cat, :cap, :so, 1)"),
            {"id": uid, "c": code, "n": name, "cat": cat, "cap": cap, "so": order},
        )

    # Seed Funding Heads
    funding_heads = [
        (str(uuid.uuid4()), "PROMOTER_EQUITY", "Promoter's Capital / Equity Contribution", "PROMOTER", 10),
        (str(uuid.uuid4()), "TERM_LOAN_BANK", "Bank Term Loan (Senior Debt)", "TERM_LOAN", 20),
        (str(uuid.uuid4()), "UNSECURED_LOAN", "Unsecured Loans from Promoters / Relatives", "UNSECURED_LOAN", 30),
        (str(uuid.uuid4()), "GOVT_SUBSIDY", "Government Capital Investment Subsidy", "SUBSIDY", 40),
        (str(uuid.uuid4()), "SEED_GRANT", "Seed Fund / Innovation Grant", "GRANT", 50),
        (str(uuid.uuid4()), "WC_BANK_FACILITY", "Bank Working Capital Limit (CC / OD)", "WORKING_CAPITAL", 60),
    ]
    for uid, code, name, cat, order in funding_heads:
        conn.execute(
            sa.text("INSERT INTO funding_heads (id, funding_code, funding_name, funding_category, sort_order, active_flag) VALUES (:id, :c, :n, :cat, :so, 1)"),
            {"id": uid, "c": code, "n": name, "cat": cat, "so": order},
        )

    # Seed Expense Heads
    expense_heads = [
        (str(uuid.uuid4()), "EXP_RAW_MATERIAL", "Cost of Raw Materials / Direct Inputs", "DIRECT", "VARIABLE", "PERCENT_REVENUE", 10),
        (str(uuid.uuid4()), "EXP_POWER_FUEL", "Power, Fuel & Utilities", "DIRECT", "SEMI_VARIABLE", "FIXED_AMOUNT", 20),
        (str(uuid.uuid4()), "EXP_DIRECT_LABOUR", "Direct Factory Wages & Labour", "DIRECT", "VARIABLE", "GROWTH", 30),
        (str(uuid.uuid4()), "EXP_SALARIES_ADMIN", "Salaries & Administrative Staff", "ADMIN", "FIXED", "GROWTH", 40),
        (str(uuid.uuid4()), "EXP_RENT", "Factory / Office Rent", "ADMIN", "FIXED", "GROWTH", 50),
        (str(uuid.uuid4()), "EXP_REPAIRS_MAINT", "Repairs & Maintenance", "ADMIN", "SEMI_VARIABLE", "GROWTH", 60),
        (str(uuid.uuid4()), "EXP_INSURANCE", "Insurance (Assets / Plant / Stocks)", "ADMIN", "FIXED", "GROWTH", 70),
        (str(uuid.uuid4()), "EXP_SELLING_MKTG", "Selling, Advertising & Distribution", "SELLING", "VARIABLE", "PERCENT_REVENUE", 80),
        (str(uuid.uuid4()), "EXP_LEGAL_PROF", "Legal, Audit & Professional Fees", "ADMIN", "FIXED", "GROWTH", 90),
        (str(uuid.uuid4()), "EXP_MISC_ADMIN", "Printing, Stationery & Misc Expenses", "ADMIN", "FIXED", "GROWTH", 100),
    ]
    for uid, code, name, grp, beh, meth, order in expense_heads:
        conn.execute(
            sa.text("INSERT INTO expense_heads (id, expense_code, expense_name, expense_group, default_cost_behaviour, default_projection_method, sort_order, active_flag) VALUES (:id, :c, :n, :g, :b, :m, :so, 1)"),
            {"id": uid, "c": code, "n": name, "g": grp, "b": beh, "m": meth, "so": order},
        )

    # Seed 10 Starter Industry Templates
    templates = [
        ("IND_MANUFACTURING", "Manufacturing", "Production capacity, utilisation, yield, selling price, raw materials and factory overheads."),
        ("IND_TRADING", "Wholesale / Retail Trading", "Turnover growth, purchase markup, inventory turns, receivables and payables."),
        ("IND_HOSPITAL", "Hospital / Healthcare Clinic", "Beds, bed occupancy %, procedure counts, average billing per patient, department staffing."),
        ("IND_HOTEL", "Hotel & Hospitality", "Available rooms, occupancy %, average daily rate (ADR), food and banquet revenue."),
        ("IND_RESTAURANT", "Restaurant / F&B Outlet", "Dining covers/seats, table turns, average bill value, food cost % and delivery aggregators."),
        ("IND_EV_CHARGING", "EV Charging Station", "Charging guns, charging sessions/day, kWh/session, tariff/kWh, power input tariff."),
        ("IND_TRANSPORT", "Transport & Logistics Fleet", "Fleet vehicles, trips per month, trip distance (km), freight rate per tonne/km, fuel cost."),
        ("IND_EDUCATION", "School / Educational Institution", "Student enrolment, fee structure, collection efficiency, teacher-student ratios."),
        ("IND_RENTAL", "Commercial / Residential Rental Property", "Rentable square footage / units, occupancy %, base rent per sqft, escalation %."),
        ("IND_SERVICES", "Professional & IT Services", "Consultants / billable staff, billable utilisation %, hourly / daily billing rate, project delivery cycles."),
    ]
    for code, name, desc in templates:
        t_id = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO industry_templates (id, industry_code, industry_name, description, template_version, active_flag) VALUES (:id, :c, :n, :d, '1.0', 1)"),
            {"id": t_id, "c": code, "n": name, "d": desc},
        )
        # Add basic template fields per industry
        f_id = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO industry_template_fields (id, industry_template_id, module_code, field_code, field_label, input_type, unit_code, required_flag, sort_order) VALUES (:id, :tid, 'REVENUE', 'PRIMARY_DRIVER', 'Primary Operating Driver', 'DECIMAL', 'UNITS', 1, 10)"),
            {"id": f_id, "tid": t_id},
        )


def downgrade() -> None:
    op.drop_table('historical_statement_lines')
    op.drop_table('industry_template_fields')
    op.drop_table('industry_templates')
    op.drop_table('expense_forecasts')
    op.drop_table('expense_heads')
    op.drop_table('revenue_forecasts')
    op.drop_table('revenue_streams')
    op.drop_table('revenue_methods')
    op.drop_table('funding_sources')
    op.drop_table('funding_heads')
    op.drop_table('project_cost_items')
    op.drop_table('project_cost_heads')
