"""Marginal cash flow calculation for growth analysis."""

from decimal import Decimal
from typing import Dict
from src.models import PeriodResult


def calculate_marginal_cash_flow(period_result: PeriodResult) -> Dict[str, Decimal]:
    """
    Calculate marginal cash flow impact for growth scenarios.
    
    Formula: Marginal Cash Flow % = (FCF % - WC %) × Growth Rate
    
    Measures the cash generated (or consumed) per unit of revenue growth:
    - High positive MCF: Growth generates cash
    - Low/negative MCF: Growth consumes cash
    
    Components:
    - FCF % = Free Cash Flow / Revenue
    - WC % = Working Capital Investment / Revenue
    - MCF % = FCF % - WC %
    
    For growth scenarios:
    - If 10% revenue growth → Cash impact = MCF % × 10%
    
    Args:
        period_result: PeriodResult with OCF, CAPEX, WC data
    
    Returns:
        Dict[str, Decimal]: Marginal cash flow metrics
            {
                'fcf_percent': Free Cash Flow %,
                'wc_percent': Working Capital %,
                'mcf_percent': Marginal Cash Flow %,
                'cash_per_1pct_growth': Cash generated per 1% revenue growth
            }
    
    TODO: Calculate FCF and WC as percentages of revenue
    TODO: Calculate marginal cash flow difference
    TODO: Project cash impact per 1% growth
    TODO: Return dictionary with all metrics
    """
    pass
