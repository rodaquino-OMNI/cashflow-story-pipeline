"""Balance sheet estimation and calculations."""

from src.models import PeriodResult


def estimate_balance_sheet(period_result: PeriodResult) -> PeriodResult:
    """
    Estimate balance sheet derived aggregates from a PeriodResult.

    The incoming PeriodResult already has balance sheet line items populated
    by calculate_income_statement (which forwards MappedData fields):
      - ppe_net = ppe_gross - accumulated_depreciation
      - intangibles_net = intangibles
      - other_capital_net = other_assets - other_liabilities
      - total_debt = short_term_debt + long_term_debt
      - net_debt = total_debt - cash
      - shareholders_equity (passthrough)
      - accounts_receivable, inventory, accounts_payable (passthrough)

    This function computes the remaining derived BS aggregate:
      - other_capital_investment = other_capital_net
        (Without a prior period, the full balance is the investment proxy.)

    Args:
        period_result: PeriodResult with balance sheet items already set.

    Returns:
        PeriodResult: Updated copy with other_capital_investment computed.
    """
    # Without a prior period, other_capital_investment equals the current
    # other_capital_net balance (net non-current assets minus non-current
    # liabilities, excluding PP&E and intangibles).
    other_capital_investment = period_result.other_capital_net

    return period_result.model_copy(update={
        "other_capital_investment": other_capital_investment,
    })
