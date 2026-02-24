"""Financial ratio calculations for performance analysis."""

from decimal import Decimal

from src.models import PeriodResult


def calculate_ratios(period_result: PeriodResult) -> PeriodResult:
    """
    Calculate key financial ratios from period results.

    Pure function: returns a new PeriodResult with ratio fields populated.
    All arithmetic uses Decimal for precision. Division by zero returns Decimal("0").

    Ratios calculated:
        - current_ratio:   Current Assets / Current Liabilities
        - quick_ratio:     (Current Assets - Inventory) / Current Liabilities
        - debt_to_equity:  Total Debt / Shareholders' Equity
        - roe_pct:         (Net Income / Shareholders' Equity) * 100
        - roa_pct:         (Net Income / Total Assets) * 100
        - roce_pct:        (EBIT * (1 - tax_rate) / Capital Employed) * 100

    Args:
        period_result: PeriodResult with balance sheet and income statement data.

    Returns:
        A new PeriodResult with the six ratio fields updated.
    """
    ZERO = Decimal("0")

    def safe_div(numerator: Decimal, denominator: Decimal) -> Decimal:
        """Return numerator / denominator, or ZERO when denominator is zero."""
        if denominator == ZERO:
            return ZERO
        return numerator / denominator

    pr = period_result

    # --- Derive cash from net_debt: cash = total_debt - net_debt ---
    cash = pr.total_debt - pr.net_debt

    # --- Current assets = accounts_receivable + inventory + cash ---
    current_assets = pr.accounts_receivable + pr.inventory + cash

    # --- Current liabilities (accounts_payable as proxy) ---
    current_liabilities = pr.accounts_payable

    # 1. Liquidity ratios
    current_ratio = safe_div(current_assets, current_liabilities)
    quick_ratio = safe_div(current_assets - pr.inventory, current_liabilities)

    # 2. Leverage ratio
    debt_to_equity = safe_div(pr.total_debt, pr.shareholders_equity)

    # 3. Profitability ratios
    roe_pct = safe_div(pr.net_income, pr.shareholders_equity) * Decimal("100")

    # Total assets = current_assets + ppe_net + intangibles_net + max(0, other_capital_net)
    total_assets = (
        current_assets
        + pr.ppe_net
        + pr.intangibles_net
        + max(ZERO, pr.other_capital_net)
    )
    roa_pct = safe_div(pr.net_income, total_assets) * Decimal("100")

    # ROCE: EBIT * (1 - effective_tax_rate) / (equity + debt) * 100
    total_tax = pr.irpj_tax + pr.csll_tax
    effective_tax_rate = safe_div(total_tax, pr.ebt) if pr.ebt > ZERO else Decimal("0.34")
    capital_employed = pr.shareholders_equity + pr.total_debt
    roce_pct = (
        safe_div(pr.ebit * (Decimal("1") - effective_tax_rate), capital_employed)
        * Decimal("100")
    )

    return pr.model_copy(
        update={
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "debt_to_equity": debt_to_equity,
            "roe_pct": roe_pct,
            "roa_pct": roa_pct,
            "roce_pct": roce_pct,
        }
    )
