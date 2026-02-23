"""Cash quality classification (G/A/B grades)."""

from decimal import Decimal
from typing import List
from src.models import PeriodResult, CashQualityMetric


def classify_cash_quality(period_result: PeriodResult) -> List[CashQualityMetric]:
    """
    Classify cash quality on multiple dimensions (G/A/B grades).
    
    Metrics classified:
    
    1. OPERATING CASH FLOW MARGIN (OCF / Revenue):
       G (Good): > 25% (strong operational cash generation)
       A (Average): 10-25% (acceptable)
       B (Below Avg): < 10% (weak operational cash flow)
    
    2. FREE CASH FLOW (OCF - CAPEX):
       G: > 0 (positive FCF)
       A: 0 to negative up to -5% of Revenue
       B: < -5% of Revenue (burning cash)
    
    3. WORKING CAPITAL / REVENUE:
       G: < 10% (efficient WC)
       A: 10-20%
       B: > 20% (capital intensive)
    
    4. CASH CONVERSION CYCLE (days):
       G: < 30 days (quick conversion)
       A: 30-60 days
       B: > 60 days (long cycle)
    
    5. NET DEBT / EBITDA:
       G: < 2x (low leverage)
       A: 2-4x
       B: > 4x (high leverage)
    
    6. INTEREST COVERAGE (EBIT / Financial Expenses):
       G: > 5x (strong coverage)
       A: 3-5x
       B: < 3x (weak coverage)
    
    Args:
        period_result: PeriodResult with all calculations
    
    Returns:
        List[CashQualityMetric]: All metrics with grades and thresholds
        
    TODO: Calculate all 6 cash quality metrics
    TODO: Determine grade (G/A/B) based on thresholds
    TODO: Create CashQualityMetric objects
    TODO: Return sorted by importance
    """
    pass
