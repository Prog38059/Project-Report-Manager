"""Pure domain cross-statement financial validation and reconciliation engine.

Audits integrated statements, funding reconciliation, loan service, and appraisal ratios
against core accounting invariants and bank appraisal benchmarks.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from app.common.money import format_inr, paise_to_rupees
from app.domain.financial.appraisal import ProjectAppraisalSummary
from app.domain.financial.statement_pipeline import PeriodFinancialStatements


class ValidationSeverity(str, Enum):
    ERROR = "ERROR"        # Material error; prevents final report approval
    WARNING = "WARNING"    # Significant warning; requires user attention or override
    INFO = "INFO"          # Informational note / advisory benchmark guidance


@dataclass
class ValidationIssue:
    """A detected financial or structural validation issue."""
    rule_code: str
    severity: ValidationSeverity
    scope_code: str
    message: str
    period_sequence: Optional[int] = None
    expected_value_text: Optional[str] = None
    actual_value_text: Optional[str] = None
    is_overridable: bool = False
    suggested_action: Optional[str] = None


class FinancialValidationEngine:
    """Evaluates projection runs against mandatory invariants and lender underwriting rules."""

    @classmethod
    def audit_projection(
        cls,
        statements: List[PeriodFinancialStatements],
        appraisal: ProjectAppraisalSummary,
        funding_gap_paise: int = 0,
        min_acceptable_dscr: Decimal = Decimal("1.25"),
        max_acceptable_der: Decimal = Decimal("3.00"),
        min_acceptable_cr: Decimal = Decimal("1.33"),
    ) -> List[ValidationIssue]:
        """Runs the complete battery of cross-statement audit and integrity rules."""
        issues: List[ValidationIssue] = []

        # 1. Fundamental Accounting Invariant: Balance Sheet Balance (VAL-BS-001)
        for stmt in statements:
            if stmt.balance_difference_paise != 0:
                issues.append(
                    ValidationIssue(
                        rule_code="VAL-BS-001",
                        severity=ValidationSeverity.ERROR,
                        scope_code="BALANCE_SHEET",
                        period_sequence=stmt.period_sequence,
                        message=f"Balance Sheet out of balance in Period {stmt.period_sequence} ({stmt.period_label}) by ₹{paise_to_rupees(stmt.balance_difference_paise)}.",
                        expected_value_text="₹0.00 difference",
                        actual_value_text=f"₹{paise_to_rupees(stmt.balance_difference_paise)} difference",
                        is_overridable=False,
                        suggested_action="Review asset capitalization, retained earnings, or loan schedule postings. Unexplained plugs are strictly forbidden.",
                    )
                )

        # 2. Solvency Invariant: No Negative Closing Cash (VAL-CASH-001)
        for stmt in statements:
            if stmt.closing_cash_paise < 0:
                issues.append(
                    ValidationIssue(
                        rule_code="VAL-CASH-001",
                        severity=ValidationSeverity.ERROR,
                        scope_code="CASH_FLOW",
                        period_sequence=stmt.period_sequence,
                        message=f"Projected closing cash is negative in Period {stmt.period_sequence} ({format_inr(paise_to_rupees(stmt.closing_cash_paise))}).",
                        expected_value_text="Cash >= ₹0.00",
                        actual_value_text=format_inr(paise_to_rupees(stmt.closing_cash_paise)),
                        is_overridable=False,
                        suggested_action="Increase promoter equity, arrange working capital bank finance, or adjust revenue/debt repayment schedules.",
                    )
                )

        # 3. Project Funding Reconciliation (VAL-FUND-001)
        if funding_gap_paise != 0:
            sev = ValidationSeverity.ERROR if funding_gap_paise > 0 else ValidationSeverity.WARNING
            diff_label = "Shortfall" if funding_gap_paise > 0 else "Surplus"
            issues.append(
                ValidationIssue(
                    rule_code="VAL-FUND-001",
                    severity=sev,
                    scope_code="FUNDING",
                    message=f"Funding Reconciliation {diff_label} of {format_inr(paise_to_rupees(abs(funding_gap_paise)))}.",
                    expected_value_text="Funding Gap = ₹0.00",
                    actual_value_text=f"Gap = {format_inr(paise_to_rupees(funding_gap_paise))}",
                    is_overridable=True,
                    suggested_action="Ensure total project cost items exactly equal total funding sources (Debt + Equity + Subsidy).",
                )
            )

        # 4. Lender DSCR Coverage Benchmarks (VAL-DSCR-001, VAL-DSCR-002)
        if appraisal.average_gross_dscr is not None:
            if appraisal.average_gross_dscr < Decimal("1.00"):
                issues.append(
                    ValidationIssue(
                        rule_code="VAL-DSCR-001",
                        severity=ValidationSeverity.ERROR,
                        scope_code="COVERAGE",
                        message=f"Average DSCR ({appraisal.average_gross_dscr}) is below 1.00. Operational cash generation cannot service scheduled debt.",
                        expected_value_text="DSCR >= 1.00",
                        actual_value_text=f"Average DSCR = {appraisal.average_gross_dscr}",
                        is_overridable=False,
                        suggested_action="Lengthen loan tenure, negotiate a longer moratorium, or reduce debt component.",
                    )
                )
            elif appraisal.average_gross_dscr < min_acceptable_dscr:
                issues.append(
                    ValidationIssue(
                        rule_code="VAL-DSCR-002",
                        severity=ValidationSeverity.WARNING,
                        scope_code="COVERAGE",
                        message=f"Average DSCR ({appraisal.average_gross_dscr}) is below bank benchmark threshold of {min_acceptable_dscr}.",
                        expected_value_text=f"DSCR >= {min_acceptable_dscr}",
                        actual_value_text=f"Average DSCR = {appraisal.average_gross_dscr}",
                        is_overridable=True,
                        suggested_action="Review lender-specific DSCR policy or improve projected operating margins.",
                    )
                )

        # Period-wise DSCR dips
        for r in appraisal.period_ratios:
            if r.gross_dscr is not None and r.gross_dscr < Decimal("1.00"):
                issues.append(
                    ValidationIssue(
                        rule_code="VAL-DSCR-003",
                        severity=ValidationSeverity.WARNING,
                        scope_code="COVERAGE",
                        period_sequence=r.period_sequence,
                        message=f"DSCR dips to {r.gross_dscr} in Period {r.period_sequence} ({r.period_label}).",
                        expected_value_text="Period DSCR >= 1.00",
                        actual_value_text=f"DSCR = {r.gross_dscr}",
                        is_overridable=True,
                        suggested_action="Structure loan repayment with stepped/balloon installments to match ramp-up.",
                    )
                )

        # 5. Liquidity & Working Capital Health (VAL-CR-001)
        for r in appraisal.period_ratios:
            if r.current_ratio is not None:
                if r.current_ratio < Decimal("1.00"):
                    issues.append(
                        ValidationIssue(
                            rule_code="VAL-CR-001",
                            severity=ValidationSeverity.WARNING,
                            scope_code="LIQUIDITY",
                            period_sequence=r.period_sequence,
                            message=f"Current Ratio is {r.current_ratio} in Period {r.period_sequence} ({r.period_label}), indicating negative net working capital.",
                            expected_value_text="Current Ratio >= 1.00",
                            actual_value_text=f"CR = {r.current_ratio}",
                            is_overridable=True,
                            suggested_action="Infuse long-term working capital margin or reduce short-term trade liabilities.",
                        )
                    )
                elif r.current_ratio < min_acceptable_cr:
                    issues.append(
                        ValidationIssue(
                            rule_code="VAL-CR-002",
                            severity=ValidationSeverity.INFO,
                            scope_code="LIQUIDITY",
                            period_sequence=r.period_sequence,
                            message=f"Current Ratio is {r.current_ratio} in Period {r.period_sequence}, below Tandon/Nayak norm of {min_acceptable_cr}.",
                            expected_value_text=f"CR >= {min_acceptable_cr}",
                            actual_value_text=f"CR = {r.current_ratio}",
                            is_overridable=True,
                            suggested_action="Bank appraisal guidelines normally expect CR >= 1.33:1 for working capital limits.",
                        )
                    )

        # 6. Financial Leverage: Debt-Equity Ratio (VAL-DER-001)
        for r in appraisal.period_ratios:
            if r.debt_equity_ratio is not None and r.debt_equity_ratio > max_acceptable_der:
                issues.append(
                    ValidationIssue(
                        rule_code="VAL-DER-001",
                        severity=ValidationSeverity.WARNING,
                        scope_code="LEVERAGE",
                        period_sequence=r.period_sequence,
                        message=f"Debt-Equity Ratio is {r.debt_equity_ratio}:1 in Period {r.period_sequence}, exceeding prudent norm of {max_acceptable_der}:1.",
                        expected_value_text=f"DER <= {max_acceptable_der}:1",
                        actual_value_text=f"DER = {r.debt_equity_ratio}:1",
                        is_overridable=True,
                        suggested_action="Increase promoter equity contribution or subordinated unsecured loans.",
                    )
                )

        # 7. Break-Even Capacity Utilization Warning (VAL-BEP-001)
        for r in appraisal.period_ratios:
            if r.break_even_capacity_pct > Decimal("80.00"):
                issues.append(
                    ValidationIssue(
                        rule_code="VAL-BEP-001",
                        severity=ValidationSeverity.WARNING,
                        scope_code="PROFITABILITY",
                        period_sequence=r.period_sequence,
                        message=f"Break-even capacity utilization is high at {r.break_even_capacity_pct}% in Period {r.period_sequence}.",
                        expected_value_text="BEP <= 70.00%",
                        actual_value_text=f"BEP = {r.break_even_capacity_pct}%",
                        is_overridable=True,
                        suggested_action="Review high fixed costs or enhance contribution margin by reducing variable costs.",
                    )
                )

        return issues
