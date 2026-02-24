"""Brazilian tax calculations (IRPJ and CSLL)."""

from decimal import Decimal


def calculate_brazilian_tax(
    ebt: Decimal,
    period_months: int = 1
) -> tuple[Decimal, Decimal]:
    """
    Calculate Brazilian income taxes (IRPJ + CSLL) on EBT.

    Tax rates:
    - IRPJ (Imposto de Renda): 15% base + 10% surtax on monthly profit > R$20,000
    - CSLL (Contribuição Social): 9% on EBT

    Formula:
        Monthly Profit = EBT / period_months
        if Monthly Profit > R$20,000:
            IRPJ = (15% + 10%) * EBT = 25% * EBT
        else:
            IRPJ = 15% * EBT
        CSLL = 9% * EBT
        Total Tax = IRPJ + CSLL

    Args:
        ebt: Earnings Before Tax (Lucro Antes de Impostos)
        period_months: Number of months in period (1-12, default 1)

    Returns:
        Tuple[Decimal, Decimal]: (irpj_tax, csll_tax)

    Returns:
        Tuple[Decimal, Decimal]: (irpj_tax, csll_tax)
    """
    ZERO = Decimal("0")
    IRPJ_BASE_RATE = Decimal("0.15")
    IRPJ_SURTAX_RATE = Decimal("0.10")
    MONTHLY_THRESHOLD = Decimal("20000")
    CSLL_RATE = Decimal("0.09")

    if not isinstance(ebt, Decimal):
        ebt = Decimal(str(ebt))

    # No tax on zero or negative EBT
    if ebt <= ZERO:
        return ZERO, ZERO

    months = Decimal(str(period_months)) if period_months >= 1 else Decimal("1")
    monthly_profit = ebt / months

    # IRPJ base (15% on full EBT)
    irpj_base = ebt * IRPJ_BASE_RATE

    # 10% surtax on portion exceeding R$20,000/month
    irpj_surtax = ZERO
    if monthly_profit > MONTHLY_THRESHOLD:
        surtax_base = ebt - (MONTHLY_THRESHOLD * months)
        irpj_surtax = max(ZERO, surtax_base) * IRPJ_SURTAX_RATE

    irpj = irpj_base + irpj_surtax

    # CSLL (9% on full EBT)
    csll = ebt * CSLL_RATE

    return irpj, csll
