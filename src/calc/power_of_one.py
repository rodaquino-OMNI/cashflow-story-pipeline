"""Power of One analysis - sensitivity of 1% changes on profit and cash."""

from decimal import Decimal
from typing import List
from src.models import PeriodResult, PowerOfOneLever


def calculate_power_of_one(period_result: PeriodResult) -> List[PowerOfOneLever]:
    """
    Calculate Power of One analysis: impact of 1% change on each lever.
    
    The 7 Key Levers (with 1% change impact):
    
    1. REVENUE LEVER (Chapter 1):
       1% increase in Revenue → Profit impact = 1% × Revenue × (EBIT margin %)
       Cash impact = Similar to profit impact (no working capital change for steady state)
    
    2. COGS LEVER (Chapter 1):
       1% reduction in COGS → Profit impact = 1% × COGS
       Cash impact = Profit impact
    
    3. OPERATING EXPENSE LEVER (Chapter 1):
       1% reduction in OpEx → Profit impact = 1% × OpEx
       Cash impact = Profit impact
    
    4. ACCOUNTS RECEIVABLE LEVER (Chapter 2):
       10-day reduction in DSO → WC freed = (AR / 30) × 10 days
       Cash impact = WC freed
       Profit impact = 0 (but enables reinvestment)
    
    5. INVENTORY LEVER (Chapter 2):
       10-day reduction in DIO → WC freed = (Inventory / 30) × 10 days
       Cash impact = WC freed
       Profit impact = 0
    
    6. ACCOUNTS PAYABLE LEVER (Chapter 2):
       10-day increase in DPO → WC needed = (AP / 30) × 10 days
       Cash impact = WC needed (negative)
       Profit impact = 0
    
    7. CAPEX LEVER (Chapter 3):
       1% reduction in CAPEX → Cash impact = 1% × CAPEX
       Profit impact = Proportional reduction in future depreciation
    
    Args:
        period_result: PeriodResult with all calculations
    
    Returns:
        List[PowerOfOneLever]: All 7 levers with their impacts
        
    TODO: Calculate all 7 levers
    TODO: Compute profit and cash impact for each
    TODO: Create PowerOfOneLever objects for each lever
    TODO: Return sorted by impact magnitude
    """
    pass
