"""Working capital and operating cycle calculation engine.

Implements component holding days, current operating assets, current operating liabilities,
net working capital identity (Golden Fixture D), and bank MPBF / cash credit limits.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.money import paise_to_rupees, rupees_to_paise


@dataclass
class WorkingCapitalAssumptions:
    """Holding day parameters for working capital components."""
    rm_holding_days: Decimal = Decimal("30")
    wip_holding_days: Decimal = Decimal("15")
    fg_holding_days: Decimal = Decimal("15")
    debtor_collection_days: Decimal = Decimal("45")
    creditor_payment_days: Decimal = Decimal("30")
    other_current_asset_paise: int = 0
    other_current_liability_paise: int = 0
    bank_margin_pct: Decimal = Decimal("25.0")  # Standard 25% promoter margin under Nayak/Tandon


@dataclass
class WorkingCapitalResult:
    """Calculated working capital components for a period."""
    period_id: UUID
    period_sequence: int
    raw_material_paise: int
    wip_paise: int
    finished_goods_paise: int
    total_inventory_paise: int
    trade_receivables_paise: int
    other_current_assets_paise: int
    total_current_assets_paise: int  # (excluding opening cash for operating WC)

    trade_payables_paise: int
    other_current_liabilities_paise: int
    total_current_liabilities_paise: int

    net_working_capital_paise: int
    working_capital_gap_paise: int
    assessed_bank_limit_paise: int
    promoter_margin_paise: int


class WorkingCapitalCalculator:
    """Calculates component-wise working capital requirements."""

    @staticmethod
    def calculate_period_working_capital(
        period_id: UUID,
        period_sequence: int,
        annual_raw_material_cost_paise: int,
        annual_total_direct_cost_paise: int,
        annual_cost_of_production_paise: int,
        annual_net_sales_paise: int,
        assumptions: WorkingCapitalAssumptions,
        days_in_period: int = 365,
    ) -> WorkingCapitalResult:
        """Calculates working capital requirements based on holding days."""
        if days_in_period <= 0:
            raise ValidationError("Days in period must be positive.")

        denom = Decimal(days_in_period)

        # 1. Raw Materials
        rm_dec = Decimal(annual_raw_material_cost_paise) * (assumptions.rm_holding_days / denom)
        rm_paise = int(rm_dec.quantize(Decimal("1")))

        # 2. WIP
        wip_dec = Decimal(annual_total_direct_cost_paise) * (assumptions.wip_holding_days / denom)
        wip_paise = int(wip_dec.quantize(Decimal("1")))

        # 3. Finished Goods
        fg_dec = Decimal(annual_cost_of_production_paise) * (assumptions.fg_holding_days / denom)
        fg_paise = int(fg_dec.quantize(Decimal("1")))

        total_inv_paise = rm_paise + wip_paise + fg_paise

        # 4. Receivables / Debtors
        debtors_dec = Decimal(annual_net_sales_paise) * (assumptions.debtor_collection_days / denom)
        debtors_paise = int(debtors_dec.quantize(Decimal("1")))

        other_ca = assumptions.other_current_asset_paise
        total_ca = total_inv_paise + debtors_paise + other_ca

        # 5. Trade Payables / Creditors (on RM purchases)
        creditors_dec = Decimal(annual_raw_material_cost_paise) * (assumptions.creditor_payment_days / denom)
        creditors_paise = int(creditors_dec.quantize(Decimal("1")))

        other_cl = assumptions.other_current_liability_paise
        total_cl = creditors_paise + other_cl

        # Net Working Capital Identity (Fixture D): Current Assets - Current Liabilities
        nwc_paise = total_ca - total_cl

        # Bank Assessment
        wc_gap_paise = max(0, total_ca - creditors_paise)
        margin_pct = assumptions.bank_margin_pct / Decimal("100")
        promoter_margin_paise = int((Decimal(wc_gap_paise) * margin_pct).quantize(Decimal("1")))
        bank_limit_paise = max(0, wc_gap_paise - promoter_margin_paise)

        return WorkingCapitalResult(
            period_id=period_id,
            period_sequence=period_sequence,
            raw_material_paise=rm_paise,
            wip_paise=wip_paise,
            finished_goods_paise=fg_paise,
            total_inventory_paise=total_inv_paise,
            trade_receivables_paise=debtors_paise,
            other_current_assets_paise=other_ca,
            total_current_assets_paise=total_ca,
            trade_payables_paise=creditors_paise,
            other_current_liabilities_paise=other_cl,
            total_current_liabilities_paise=total_cl,
            net_working_capital_paise=nwc_paise,
            working_capital_gap_paise=wc_gap_paise,
            assessed_bank_limit_paise=bank_limit_paise,
            promoter_margin_paise=promoter_margin_paise,
        )


def calculate_net_working_capital_identity(
    current_assets_paise: int,
    current_liabilities_paise: int,
) -> int:
    """Calculates Net Working Capital identity = Current Assets - Current Liabilities (Golden Fixture D)."""
    return current_assets_paise - current_liabilities_paise

