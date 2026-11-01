"""Revenue domain entities, projection models, and tax rules."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.money import rupees_to_paise
from app.common.types import GstTreatmentCode, RevenueCalculationMode, RevenueMethodCode


@dataclass
class RevenueStream:
    """A product or service line generating revenue."""
    id: UUID
    scenario_id: UUID
    stream_code: str
    stream_name: str
    method_code: RevenueMethodCode
    gst_treatment_code: GstTreatmentCode
    gst_rate_pct_text: Optional[str] = None
    unit_code: Optional[str] = None
    active_flag: bool = True
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.stream_code or not self.stream_code.strip():
            raise ValidationError("Stream code cannot be empty.")
        if not self.stream_name or not self.stream_name.strip():
            raise ValidationError("Stream name cannot be empty.")


@dataclass
class RevenueForecast:
    """Projected driver parameters or manual amounts for a revenue stream and period."""
    id: UUID
    revenue_stream_id: UUID
    period_id: UUID
    calculation_mode: RevenueCalculationMode
    capacity_decimal_text: Optional[str] = None
    utilisation_pct_text: Optional[str] = None
    units_decimal_text: Optional[str] = None
    price_per_unit_decimal_text: Optional[str] = None
    operating_days_decimal_text: Optional[str] = None
    growth_pct_text: Optional[str] = None
    gross_billing_override_paise: Optional[int] = None
    source_id: Optional[UUID] = None
    notes: Optional[str] = None

    @classmethod
    def calculate_stream_period(
        cls,
        method_code: RevenueMethodCode,
        gst_treatment: GstTreatmentCode,
        gst_rate_pct: Optional[Decimal],
        calculation_mode: RevenueCalculationMode,
        capacity: Optional[Decimal] = None,
        utilisation_pct: Optional[Decimal] = None,
        units: Optional[Decimal] = None,
        price_per_unit: Optional[Decimal] = None,
        operating_days: Optional[Decimal] = None,
        prior_gross_rupees: Optional[Decimal] = None,
        growth_pct: Optional[Decimal] = None,
        manual_override_paise: Optional[int] = None,
    ) -> dict[str, int]:
        """
        Calculates gross billing, output tax, and net revenue in integer paise.
        """
        # If manual override
        if calculation_mode == RevenueCalculationMode.MANUAL_OVERRIDE:
            if manual_override_paise is None or manual_override_paise < 0:
                raise ValidationError("Manual gross billing override cannot be negative.")
            gross_paise = manual_override_paise
        else:
            # Driver-based computation
            gross_rupees = Decimal("0")
            if method_code == RevenueMethodCode.CAPACITY_UTILISATION_PRICE:
                cap = capacity or Decimal("0")
                util = (utilisation_pct or Decimal("0")) / Decimal("100")
                price = price_per_unit or Decimal("0")
                # If operating_days is provided, capacity is per-day; otherwise capacity is annual
                days = operating_days if operating_days is not None else Decimal("1")
                gross_rupees = cap * util * days * price

            elif method_code == RevenueMethodCode.UNITS_PRICE:
                qty = units or Decimal("0")
                price = price_per_unit or Decimal("0")
                gross_rupees = qty * price

            elif method_code == RevenueMethodCode.CUSTOMERS_AVERAGE_BILL:
                cust = units or Decimal("0")
                bill = price_per_unit or Decimal("0")
                gross_rupees = cust * bill

            elif method_code in (RevenueMethodCode.OCCUPANCY_RATE, RevenueMethodCode.RENTAL_UNITS_RATE):
                tot_units = units or capacity or Decimal("0")
                occ = (utilisation_pct or Decimal("0")) / Decimal("100")
                rate = price_per_unit or Decimal("0")
                days = operating_days if operating_days is not None else Decimal("1")
                gross_rupees = tot_units * occ * days * rate

            elif method_code == RevenueMethodCode.HEADCOUNT_BILLING:
                hours = units or Decimal("0")
                billable_util = (utilisation_pct or Decimal("100")) / Decimal("100")
                rate = price_per_unit or Decimal("0")
                gross_rupees = hours * billable_util * rate

            elif method_code == RevenueMethodCode.TURNOVER_GROWTH:
                prior = prior_gross_rupees or Decimal("0")
                growth = (growth_pct or Decimal("0")) / Decimal("100")
                gross_rupees = prior * (Decimal("1") + growth)

            else:
                gross_rupees = (units or Decimal("0")) * (price_per_unit or Decimal("0"))

            gross_paise = rupees_to_paise(gross_rupees)

        # Tax separation
        rate = gst_rate_pct if gst_rate_pct is not None else Decimal("0")

        if gst_treatment in (
            GstTreatmentCode.EXEMPT,
            GstTreatmentCode.NIL_RATED,
            GstTreatmentCode.ZERO_RATED,
            GstTreatmentCode.OUT_OF_SCOPE,
            GstTreatmentCode.NOT_APPLICABLE,
        ) or rate == Decimal("0"):
            net_paise = gross_paise
            output_tax_paise = 0
        elif gst_treatment == GstTreatmentCode.TAXABLE_INCLUSIVE:
            gross_dec = Decimal(gross_paise)
            net_dec = gross_dec / (Decimal("1") + (rate / Decimal("100")))
            net_paise = int(net_dec.quantize(Decimal("1")))
            output_tax_paise = gross_paise - net_paise
        elif gst_treatment == GstTreatmentCode.TAXABLE_EXCLUSIVE:
            # gross_paise is basic net before tax
            net_paise = gross_paise
            tax_dec = Decimal(net_paise) * (rate / Decimal("100"))
            output_tax_paise = int(tax_dec.quantize(Decimal("1")))
            gross_paise = net_paise + output_tax_paise
        else:
            # REVIEW_REQUIRED or default
            net_paise = gross_paise
            output_tax_paise = 0

        return {
            "gross_billing_paise": gross_paise,
            "output_tax_paise": output_tax_paise,
            "net_revenue_paise": net_paise,
        }
