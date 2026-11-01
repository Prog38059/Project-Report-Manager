"""Income Tax estimation engine for project report projections."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.common.exceptions import ValidationError
from app.common.types import ConstitutionCode


@dataclass
class TaxCalculationResult:
    """Estimated tax calculations for a projection period."""
    book_pbt_paise: int
    book_depreciation_paise: int
    tax_depreciation_paise: int
    taxable_income_paise: int
    effective_tax_rate_pct: Decimal
    tax_provision_paise: int
    pat_paise: int


class TaxProvisionCalculator:
    """Calculates estimated income tax provision by entity constitution."""

    DEFAULT_TAX_RATES = {
        ConstitutionCode.PRIVATE_LIMITED: Decimal("25.17"),  # 22% Sec 115BAA + 10% Surcharge + 4% Cess
        ConstitutionCode.LLP: Decimal("31.20"),              # 30% Flat + 4% Cess
        ConstitutionCode.PARTNERSHIP: Decimal("31.20"),      # 30% Flat + 4% Cess
        ConstitutionCode.PROPRIETORSHIP: Decimal("31.20"),   # Top slab estimate + 4% Cess
        ConstitutionCode.INDIVIDUAL: Decimal("31.20"),
        ConstitutionCode.HUF: Decimal("31.20"),
    }

    @classmethod
    def calculate_tax(
        cls,
        book_pbt_paise: int,
        book_depreciation_paise: int,
        tax_depreciation_paise: int,
        constitution_code: ConstitutionCode,
        custom_tax_rate_pct: Optional[Decimal] = None,
        brought_forward_loss_paise: int = 0,
    ) -> TaxCalculationResult:
        """
        Calculates taxable income and tax provision.
        Taxable Income = Book PBT + Book Dep - Tax Dep - Loss B/F
        """
        # Add back book depreciation and deduct tax depreciation
        adjusted_income_paise = book_pbt_paise + book_depreciation_paise - tax_depreciation_paise

        # Deduct brought forward losses if positive
        if adjusted_income_paise > 0 and brought_forward_loss_paise > 0:
            loss_absorbed = min(adjusted_income_paise, brought_forward_loss_paise)
            taxable_income_paise = adjusted_income_paise - loss_absorbed
        else:
            taxable_income_paise = max(0, adjusted_income_paise)

        rate_pct = custom_tax_rate_pct if custom_tax_rate_pct is not None else cls.DEFAULT_TAX_RATES.get(constitution_code, Decimal("25.17"))
        if not isinstance(rate_pct, Decimal):
            raise TypeError("tax rate must be Decimal")

        if taxable_income_paise <= 0 or book_pbt_paise <= 0:
            tax_provision_paise = 0
        else:
            tax_dec = Decimal(taxable_income_paise) * (rate_pct / Decimal("100"))
            tax_provision_paise = int(tax_dec.quantize(Decimal("1")))

        pat_paise = book_pbt_paise - tax_provision_paise

        return TaxCalculationResult(
            book_pbt_paise=book_pbt_paise,
            book_depreciation_paise=book_depreciation_paise,
            tax_depreciation_paise=tax_depreciation_paise,
            taxable_income_paise=taxable_income_paise,
            effective_tax_rate_pct=rate_pct,
            tax_provision_paise=tax_provision_paise,
            pat_paise=pat_paise,
        )
