"""Working capital calculations (Chapter 2: Working Capital)."""

from decimal import Decimal
from src.models import MappedData, PeriodResult


def calculate_working_capital(
    mapped: MappedData,
    days_in_period: int = 30
) -> PeriodResult:
    """
    Calculate working capital metrics (Chapter 2).
    
    Formulas:
    - DSO (Days Sales Outstanding):
        DSO = (Accounts Receivable / Net Revenue) × Days in Period
        Measures how many days to collect payment
    
    - DIO (Days Inventory Outstanding):
        DIO = (Inventory / COGS) × Days in Period
        Measures how many days inventory is held
    
    - DPO (Days Payable Outstanding):
        DPO = (Accounts Payable / COGS) × Days in Period
        Measures how many days before paying suppliers
    
    - CCC (Cash Conversion Cycle):
        CCC = DSO + DIO - DPO
        Measures working capital financing cycle
    
    - Working Capital:
        WC = AR + Inventory - AP
        Absolute working capital investment
    
    - WC Investment:
        Δ WC = Change in WC from prior period
        
    Args:
        mapped: MappedData with AR, Inventory, AP, Revenue, COGS
        days_in_period: Number of days in period (default 30)
    
    Returns:
        PeriodResult: Working capital metrics (WC chapter only)
        
    Raises:
        ValueError: If COGS or Revenue is zero (division by zero)
        
    TODO: Implement all formulas with safe division (handle zero)
    TODO: Calculate all 6 metrics
    TODO: Return PeriodResult with WC fields populated
    TODO: Handle negative working capital
    """
    ZERO = Decimal("0")
    days = Decimal(str(days_in_period))

    # Safe division helper
    def safe_div(num: Decimal, den: Decimal) -> Decimal:
        return num / den if den != ZERO else ZERO

    net_revenue = mapped.gross_revenue - mapped.returns_deductions

    # DSO = (AR / Net Revenue) * days_in_period
    dso = safe_div(mapped.accounts_receivable, net_revenue) * days

    # DIO = (Inventory / COGS) * days_in_period
    dio = safe_div(mapped.inventory, mapped.cogs) * days

    # DPO = (AP / COGS) * days_in_period
    dpo = safe_div(mapped.accounts_payable, mapped.cogs) * days

    # CCC = DSO + DIO - DPO
    ccc = dso + dio - dpo

    # Working Capital = AR + Inventory - AP
    wc = mapped.accounts_receivable + mapped.inventory - mapped.accounts_payable

    # WC Investment = WC (no prior period available, use current WC)
    wc_investment = wc

    return PeriodResult(
        period=mapped.period,
        accounts_receivable=mapped.accounts_receivable,
        inventory=mapped.inventory,
        accounts_payable=mapped.accounts_payable,
        days_sales_outstanding=dso,
        days_inventory_outstanding=dio,
        days_payable_outstanding=dpo,
        cash_conversion_cycle=ccc,
        working_capital=wc,
        working_capital_investment=wc_investment,
    )
