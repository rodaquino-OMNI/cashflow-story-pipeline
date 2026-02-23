"""Cash flow statement calculations."""

from decimal import Decimal
from src.models import PeriodResult


def calculate_cash_flow(period_result: PeriodResult) -> PeriodResult:
    """
    Calculate cash flow statement from period results.

    Structure:
    1. Operating Cash Flow (OCF):
        Net Income + D&A - Working Capital Investment = Cash from Operations

    2. Investing Cash Flow (ICF):
        - CAPEX (delta PP&E + Depreciation, requires prior period)
        - Other capital investment
        = Cash used in Investing
        Without prior period, CAPEX defaults to zero; uses other_capital_investment.

    3. Financing Cash Flow (FCF_fin):
        Delta Debt + Delta Equity (requires prior period)
        = Cash from Financing
        Without prior period, defaults to zero.

    4. Net Cash Flow:
        NCF = OCF + ICF + FCF_fin

    5. Free Cash Flow:
        FCF = OCF - abs(ICF)

    Args:
        period_result: PeriodResult with income statement, WC, and capital metrics

    Returns:
        PeriodResult: Updated copy with cash flow metrics populated
    """
    ZERO = Decimal("0")

    # 1. Operating Cash Flow (indirect method)
    # OCF = Net Income + D&A - Working Capital Investment
    ocf = (
        period_result.net_income
        + period_result.depreciation_amortization
        - period_result.working_capital_investment
    )

    # 2. Investing Cash Flow
    # CAPEX = delta PP&E + Depreciation (requires prior period; default to 0)
    capex = ZERO
    other_invest = period_result.other_capital_investment
    icf = -capex - other_invest

    # 3. Financing Cash Flow
    # Delta Debt + Delta Equity (requires prior period; default to 0)
    fcf_fin = ZERO

    # 4. Net Cash Flow
    ncf = ocf + icf + fcf_fin

    # 5. Free Cash Flow = OCF - abs(ICF)
    fcf = ocf - abs(icf)

    return period_result.model_copy(update={
        "operating_cash_flow": ocf,
        "investing_cash_flow": icf,
        "financing_cash_flow": fcf_fin,
        "net_cash_flow": ncf,
        "free_cash_flow": fcf,
    })
