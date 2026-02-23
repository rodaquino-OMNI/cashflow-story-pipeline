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
    pass
