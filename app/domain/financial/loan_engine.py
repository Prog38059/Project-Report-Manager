"""Loan amortization and debt service calculation engine.

Implements pure domain calculation for monthly loan amortization schedules,
EMI reducing-balance, equal principal, moratorium handling, and annual statement aggregation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.money import paise_to_rupees, rupees_to_paise


@dataclass
class MonthlyLoanInstallment:
    """A single monthly installment record."""
    month_number: int
    opening_principal_paise: int
    disbursement_paise: int
    interest_paise: int
    principal_paise: int
    total_installment_paise: int
    closing_principal_paise: int
    is_moratorium: bool = False


@dataclass
class AnnualLoanSummary:
    """Annual financial year loan roll-up for financial statement mapping."""
    period_id: UUID
    period_sequence: int
    opening_balance_paise: int
    disbursements_paise: int
    interest_expense_paise: int
    principal_repaid_paise: int
    closing_balance_paise: int
    current_maturity_next_year_paise: int
    total_debt_service_paise: int


def calculate_emi_paise(
    principal_paise: int,
    annual_rate_pct: Decimal,
    tenure_months: int,
) -> int:
    """
    Calculates monthly EMI in integer paise.
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    """
    if principal_paise <= 0:
        return 0
    if tenure_months <= 0:
        raise ValidationError("Loan tenure months must be positive.")
    if not isinstance(annual_rate_pct, Decimal):
        raise TypeError("annual_rate_pct must be Decimal")

    monthly_rate = (annual_rate_pct / Decimal("100")) / Decimal("12")
    if monthly_rate == Decimal("0"):
        return int((Decimal(principal_paise) / Decimal(tenure_months)).quantize(Decimal("1")))

    # Exact decimal exponentiation
    one_plus_r = Decimal("1") + monthly_rate
    factor = one_plus_r ** tenure_months
    emi_dec = Decimal(principal_paise) * monthly_rate * factor / (factor - Decimal("1"))
    return int(emi_dec.quantize(Decimal("1")))


def calculate_monthly_interest_paise(
    opening_principal_paise: int,
    annual_rate_pct: Decimal,
) -> int:
    """Calculates one-month periodic interest in integer paise (Golden Fixture E)."""
    if not isinstance(annual_rate_pct, Decimal):
        raise TypeError("annual_rate_pct must be Decimal")
    monthly_rate = (annual_rate_pct / Decimal("100")) / Decimal("12")
    interest_dec = Decimal(opening_principal_paise) * monthly_rate
    return int(interest_dec.quantize(Decimal("1")))


class LoanAmortizationCalculator:

    """Calculates granular monthly schedules and annual financial year roll-ups."""

    @staticmethod
    def calculate_monthly_schedule(
        sanctioned_amount_paise: int,
        annual_rate_pct: Decimal,
        tenure_months: int,
        moratorium_months: int = 0,
        repayment_method: str = "EMI_REDUCING",  # EMI_REDUCING, EQUAL_PRINCIPAL, INTEREST_ONLY
        service_moratorium_interest: bool = True,
    ) -> List[MonthlyLoanInstallment]:
        """Generates month-by-month loan repayment schedule."""
        if not isinstance(annual_rate_pct, Decimal):
            raise TypeError("annual_rate_pct must be Decimal")
        if sanctioned_amount_paise <= 0:
            return []

        monthly_rate = (annual_rate_pct / Decimal("100")) / Decimal("12")
        installments: List[MonthlyLoanInstallment] = []

        total_months = tenure_months
        amortization_months = max(1, tenure_months - moratorium_months)

        curr_principal = sanctioned_amount_paise
        # First month has opening disbursement
        is_first_month = True

        emi_paise = 0
        if repayment_method == "EMI_REDUCING":
            emi_paise = calculate_emi_paise(sanctioned_amount_paise, annual_rate_pct, amortization_months)

        fixed_principal_paise = 0
        if repayment_method == "EQUAL_PRINCIPAL":
            fixed_principal_paise = int((Decimal(sanctioned_amount_paise) / Decimal(amortization_months)).quantize(Decimal("1")))

        for m in range(1, total_months + 1):
            is_mora = m <= moratorium_months
            disbursement = sanctioned_amount_paise if is_first_month else 0
            is_first_month = False

            opening = curr_principal
            # Interest for the month
            interest_dec = Decimal(opening) * monthly_rate
            interest = int(interest_dec.quantize(Decimal("1")))

            if is_mora:
                principal = 0
                total_payment = interest if service_moratorium_interest else 0
                closing = opening + (0 if service_moratorium_interest else interest)
            else:
                if m == total_months:
                    # Final month clears exact remaining balance without residual rounding error
                    principal = opening
                    total_payment = principal + interest
                    closing = 0
                else:
                    if repayment_method == "EMI_REDUCING":
                        # Standard EMI
                        total_payment = emi_paise
                        principal = max(0, total_payment - interest)
                        # Avoid overpaying
                        if principal > opening:
                            principal = opening
                            total_payment = principal + interest
                        closing = opening - principal
                    elif repayment_method == "EQUAL_PRINCIPAL":
                        principal = min(opening, fixed_principal_paise)
                        total_payment = principal + interest
                        closing = opening - principal
                    else:
                        # Interest only
                        principal = 0
                        total_payment = interest
                        closing = opening

            installments.append(
                MonthlyLoanInstallment(
                    month_number=m,
                    opening_principal_paise=opening,
                    disbursement_paise=disbursement,
                    interest_paise=interest,
                    principal_paise=principal,
                    total_installment_paise=total_payment,
                    closing_principal_paise=closing,
                    is_moratorium=is_mora,
                )
            )
            curr_principal = closing
            if curr_principal <= 0 and not is_mora and m < total_months:
                break

        return installments

    @staticmethod
    def aggregate_to_annual_periods(
        monthly_schedule: List[MonthlyLoanInstallment],
        period_ids_and_months: List[tuple[UUID, int, int]],  # (period_id, period_sequence, month_count)
    ) -> List[AnnualLoanSummary]:
        """
        Rolls up monthly loan schedule into annual projection periods.
        Computes current maturity (principal falling due in subsequent 12 months).
        """
        summaries: List[AnnualLoanSummary] = []
        month_idx = 0
        total_schedule_len = len(monthly_schedule)

        for p_id, p_seq, num_months in period_ids_and_months:
            start_m = month_idx
            end_m = min(total_schedule_len, month_idx + num_months)
            chunk = monthly_schedule[start_m:end_m]
            month_idx = end_m

            if chunk:
                open_bal = chunk[0].opening_principal_paise
                disb = sum(i.disbursement_paise for i in chunk)
                interest = sum(i.interest_paise for i in chunk)
                repaid = sum(i.principal_paise for i in chunk)
                close_bal = chunk[-1].closing_principal_paise
            else:
                open_bal = summaries[-1].closing_balance_paise if summaries else 0
                disb = 0
                interest = 0
                repaid = 0
                close_bal = open_bal

            # Calculate current maturity for next 12 months
            next_12_months = monthly_schedule[end_m : min(total_schedule_len, end_m + 12)]
            current_mat = sum(i.principal_paise for i in next_12_months)

            summaries.append(
                AnnualLoanSummary(
                    period_id=p_id,
                    period_sequence=p_seq,
                    opening_balance_paise=open_bal,
                    disbursements_paise=disb,
                    interest_expense_paise=interest,
                    principal_repaid_paise=repaid,
                    closing_balance_paise=close_bal,
                    current_maturity_next_year_paise=current_mat,
                    total_debt_service_paise=interest + repaid,
                )
            )

        return summaries
