"""Data validation functions."""

from decimal import Decimal
from typing import Tuple, List
from src.models import PeriodResult, MappedData

_TOLERANCE = Decimal("0.01")  # 1% tolerance for balance sheet equation


def validate_balance_sheet(period_result: PeriodResult) -> Tuple[bool, List[str]]:
    """
    Validate balance sheet equation: Assets = Liabilities + Equity.

    Derives cash from net_debt = total_debt - cash, so cash = total_debt - net_debt.
    """
    messages: List[str] = []
    is_valid = True

    # Derive cash: net_debt = total_debt - cash => cash = total_debt - net_debt
    cash = period_result.total_debt - period_result.net_debt

    # Estimated total assets
    total_assets = (
        period_result.accounts_receivable
        + period_result.inventory
        + cash
        + period_result.ppe_net
        + period_result.intangibles_net
        + max(Decimal("0"), period_result.other_capital_net)
    )

    # Estimated total liabilities + equity
    total_liab_equity = (
        period_result.total_debt
        + period_result.shareholders_equity
        + period_result.accounts_payable
    )

    if total_assets <= 0:
        messages.append("Error: Total assets must be positive")
        is_valid = False

    if total_liab_equity <= 0:
        messages.append("Error: Total liabilities + equity must be positive")
        is_valid = False

    if total_assets > 0 and total_liab_equity > 0:
        diff = abs(total_assets - total_liab_equity)
        tolerance_amt = total_assets * _TOLERANCE
        if diff > tolerance_amt:
            messages.append(
                f"Warning: Balance sheet imbalance of R${diff:,.2f} "
                f"(Assets={total_assets:,.2f}, L+E={total_liab_equity:,.2f})"
            )

    if period_result.shareholders_equity < 0:
        messages.append("Warning: Negative shareholders equity — possible insolvency")

    return is_valid, messages


def validate_cash_reconciliation(period_result: PeriodResult) -> Tuple[bool, List[str]]:
    """
    Validate that OCF + ICF + financing = net_cash_flow.
    """
    messages: List[str] = []

    # If no cash flows populated, skip
    if (period_result.operating_cash_flow == 0
            and period_result.investing_cash_flow == 0
            and period_result.financing_cash_flow == 0
            and period_result.net_cash_flow == 0):
        return True, messages

    calc_net = (
        period_result.operating_cash_flow
        + period_result.investing_cash_flow
        + period_result.financing_cash_flow
    )

    diff = abs(calc_net - period_result.net_cash_flow)

    if period_result.net_cash_flow == 0:
        return True, messages

    tolerance_amt = abs(period_result.net_cash_flow) * _TOLERANCE
    if diff > tolerance_amt:
        messages.append(
            f"Warning: Cash flow reconciliation difference of R${diff:,.2f} "
            f"(Computed={calc_net:,.2f}, Stored={period_result.net_cash_flow:,.2f})"
        )
        return False, messages

    return True, messages


def validate_period_data(mapped: MappedData) -> Tuple[bool, List[str]]:
    """
    Validate period data for completeness and reasonableness.
    """
    messages: List[str] = []
    is_valid = True

    if mapped.gross_revenue <= 0:
        messages.append("Error: Gross revenue must be positive")
        is_valid = False

    if mapped.cogs < 0:
        messages.append("Error: COGS cannot be negative")
        is_valid = False

    if mapped.gross_revenue > 0 and mapped.cogs > mapped.gross_revenue:
        messages.append("Warning: COGS exceeds gross revenue (negative gross margin)")

    if mapped.accounts_receivable < 0:
        messages.append("Error: Accounts receivable cannot be negative")
        is_valid = False

    if mapped.inventory < 0:
        messages.append("Error: Inventory cannot be negative")
        is_valid = False

    if mapped.accounts_payable < 0:
        messages.append("Error: Accounts payable cannot be negative")
        is_valid = False

    if mapped.shareholders_equity == 0:
        messages.append("Warning: Zero shareholders equity")

    if not mapped.period:
        messages.append("Error: Period identifier is required")
        is_valid = False

    return is_valid, messages
