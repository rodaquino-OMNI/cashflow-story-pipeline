"""Financial calculations module for CashFlow Story."""

from src.calc.income_statement import calculate_income_statement
from src.calc.working_capital import calculate_working_capital
from src.calc.cash_flow import calculate_cash_flow
from src.calc.ratios import calculate_ratios
from src.calc.power_of_one import calculate_power_of_one
from src.calc.cash_quality import classify_cash_quality
from src.calc.marginal_cashflow import calculate_marginal_cash_flow
from src.calc.brazilian_tax import calculate_brazilian_tax

__all__ = [
    "calculate_income_statement",
    "calculate_working_capital",
    "calculate_cash_flow",
    "calculate_ratios",
    "calculate_power_of_one",
    "classify_cash_quality",
    "calculate_marginal_cash_flow",
    "calculate_brazilian_tax",
]
