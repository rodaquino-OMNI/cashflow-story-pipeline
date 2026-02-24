"""Income statement calculations (Chapter 1: Profitability)."""

from decimal import Decimal

from src.calc.brazilian_tax import calculate_brazilian_tax
from src.models import MappedData, PeriodResult


def calculate_income_statement(mapped: MappedData) -> PeriodResult:
    """
    Calculate complete income statement from mapped data.

    Full waterfall structure:
    1. Gross Revenue (Receita Bruta)
    2. - Returns & Deductions (Devoluções e Deduções)
    3. = Net Revenue (Receita Líquida)
    4. - COGS (Custo de Mercadoria Vendida)
    5. = Gross Profit (Lucro Bruto)
    6. - Operating Expenses (Despesas Operacionais)
    7. = EBITDA (Lucro Operacional antes de D&A)
    8. - Depreciation & Amortization (D&A)
    9. = EBIT (Lucro Operacional)
    10. - Financial Expenses (Despesas Financeiras)
    11. + Financial Income (Receita Financeira)
    12. ± Other Income/Expenses
    13. = EBT (Lucro Antes de Impostos)
    14. - IRPJ & CSLL Taxes
    15. = Net Income (Lucro Líquido)

    Margins calculated as: metric / net_revenue * 100

    Args:
        mapped: MappedData with financial inputs

    Returns:
        PeriodResult: Complete income statement with all metrics and margins
    """
    ZERO = Decimal("0")
    PERIOD_MONTHS = {"month": 1, "quarter": 3, "year": 12}

    # DRE Waterfall
    net_revenue = mapped.gross_revenue - mapped.returns_deductions
    if net_revenue < ZERO:
        import warnings
        warnings.warn(
            f"Net revenue is negative ({net_revenue}). "
            "Returns/deductions exceed gross revenue.",
            UserWarning,
            stacklevel=2,
        )
    gross_profit = net_revenue - mapped.cogs
    gross_margin_pct = (gross_profit / net_revenue * 100) if net_revenue != ZERO else ZERO
    ebitda = gross_profit - mapped.operating_expenses
    ebitda_margin_pct = (ebitda / net_revenue * 100) if net_revenue != ZERO else ZERO
    ebit = ebitda - mapped.depreciation_amortization
    ebit_margin_pct = (ebit / net_revenue * 100) if net_revenue != ZERO else ZERO
    ebt = ebit - mapped.financial_expenses + mapped.financial_income + mapped.other_income_expenses

    period_months = PERIOD_MONTHS.get(mapped.period_type, 1)
    irpj, csll = calculate_brazilian_tax(ebt, period_months)

    net_income = ebt - irpj - csll
    net_margin_pct = (net_income / net_revenue * 100) if net_revenue != ZERO else ZERO

    # Forward ALL MappedData fields into PeriodResult
    return PeriodResult(
        period=mapped.period,
        gross_revenue=mapped.gross_revenue,
        returns_deductions=mapped.returns_deductions,
        net_revenue=net_revenue,
        cogs=mapped.cogs,
        gross_profit=gross_profit,
        gross_margin_pct=gross_margin_pct,
        operating_expenses=mapped.operating_expenses,
        ebitda=ebitda,
        ebitda_margin_pct=ebitda_margin_pct,
        depreciation_amortization=mapped.depreciation_amortization,
        ebit=ebit,
        ebit_margin_pct=ebit_margin_pct,
        financial_expenses=mapped.financial_expenses,
        financial_income=mapped.financial_income,
        other_income_expenses=mapped.other_income_expenses,
        ebt=ebt,
        irpj_tax=irpj,
        csll_tax=csll,
        net_income=net_income,
        net_margin_pct=net_margin_pct,
        # Forward Chapter 2 fields
        accounts_receivable=mapped.accounts_receivable,
        inventory=mapped.inventory,
        accounts_payable=mapped.accounts_payable,
        # Forward Chapter 3 fields
        ppe_net=mapped.ppe_gross - mapped.accumulated_depreciation,
        intangibles_net=mapped.intangibles,
        other_capital_net=mapped.other_assets - mapped.other_liabilities,
        # Forward Chapter 4 fields
        total_debt=mapped.short_term_debt + mapped.long_term_debt,
        net_debt=(mapped.short_term_debt + mapped.long_term_debt) - mapped.cash,
        shareholders_equity=mapped.shareholders_equity,
    )
