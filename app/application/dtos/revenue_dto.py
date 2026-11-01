"""Data transfer objects for Revenue Streams and Forecasts."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class RevenueStreamDTO:
    id: UUID
    scenario_id: UUID
    stream_code: str
    stream_name: str
    method_code: str
    gst_treatment_code: str
    gst_rate_pct: Optional[Decimal]
    unit_code: Optional[str]
    notes: Optional[str]


@dataclass
class RevenueForecastPeriodDTO:
    id: UUID
    revenue_stream_id: UUID
    period_id: UUID
    period_label: str
    period_sequence: int
    calculation_mode: str
    capacity_text: Optional[str]
    utilisation_pct_text: Optional[str]
    units_text: Optional[str]
    price_per_unit_text: Optional[str]
    operating_days_text: Optional[str]
    growth_pct_text: Optional[str]
    gross_billing_rupees: Decimal
    output_tax_rupees: Decimal
    net_revenue_rupees: Decimal
