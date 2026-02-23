"""CashFlow Story analysis models for insights and narrative."""

from decimal import Decimal
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field


class PowerOfOneLever(BaseModel):
    """
    Represents a single lever in the Power of One analysis.
    Each lever shows how a 1% change impacts profit and cash flow.
    
    Attributes:
        lever: Lever identifier (e.g., "revenue", "cogs", "capex")
        label_pt: Portuguese label for display
        current_value: Current value of lever
        change_amount: Amount of change (e.g., 1% of revenue)
        change_unit: Unit of change (%, R$, days)
        profit_impact: Impact on net profit
        cash_impact: Impact on cash flow
        value_impact: Impact on enterprise value
        category: Category (Chapter 1-4 or other)
    """
    lever: str = Field(..., description="Lever identifier")
    label_pt: str = Field(..., description="Portuguese display label")
    current_value: Decimal = Field(..., description="Current value")
    change_amount: Decimal = Field(..., description="Change amount")
    change_unit: str = Field(default="%", description="Unit of change")
    profit_impact: Decimal = Field(default=Decimal("0"), description="Impact on profit")
    cash_impact: Decimal = Field(default=Decimal("0"), description="Impact on cash")
    value_impact: Decimal = Field(default=Decimal("0"), description="Impact on value")
    category: str = Field(default="", description="Category of lever")

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class CashQualityMetric(BaseModel):
    """
    Represents a cash quality metric with grade (Good/Average/Below Average).
    
    Attributes:
        metric: Metric identifier (e.g., "operating_cf_margin", "ccc_days")
        label_pt: Portuguese label
        value: Current value
        grade: Grade letter (G=Good, A=Average, B=Below Average)
        threshold_good: Threshold for "Good" grade
        threshold_average: Threshold for "Average" grade
        direction: "higher" if higher is better, "lower" if lower is better
    """
    metric: str = Field(..., description="Metric identifier")
    label_pt: str = Field(..., description="Portuguese label")
    value: Decimal = Field(..., description="Current value")
    grade: Literal["G", "A", "B"] = Field(default="A", description="Quality grade")
    threshold_good: Decimal = Field(default=Decimal("0"), description="Good threshold")
    threshold_average: Decimal = Field(default=Decimal("0"), description="Average threshold")
    direction: Literal["higher", "lower"] = Field(default="higher", description="Better direction")

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class FourChaptersSummary(BaseModel):
    """
    Summary of cash flow story across 4 chapters.
    
    Attributes:
        chapter_1_profit: Profitability chapter data (net_income, margin_pct, trends)
        chapter_2_working_capital: Working capital chapter data (investment, ccc, days)
        chapter_3_other_capital: Other capital chapter data (capex, intangibles)
        chapter_4_funding: Funding chapter data (debt, equity, debt_to_equity)
        overall_grade: Overall cash flow quality grade (G/A/B)
    """
    chapter_1_profit: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chapter 1 profitability summary"
    )
    chapter_2_working_capital: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chapter 2 working capital summary"
    )
    chapter_3_other_capital: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chapter 3 other capital summary"
    )
    chapter_4_funding: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chapter 4 funding summary"
    )
    overall_grade: Literal["G", "A", "B"] = Field(
        default="A",
        description="Overall cash flow quality grade"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class ThreeBigMeasures(BaseModel):
    """
    The three most important cash flow measures for board presentation.
    
    Attributes:
        net_cash_flow: Total change in cash (financing perspective)
        operating_cash_flow: Cash from operations (quality perspective)
        marginal_cash_flow: FCF % - Working Capital % (growth perspective)
        interpretations: Dictionary with interpretation text for each measure
    """
    net_cash_flow: Decimal = Field(..., description="Net change in cash")
    operating_cash_flow: Decimal = Field(..., description="Cash from operations")
    marginal_cash_flow: Decimal = Field(..., description="FCF% - WC% for growth analysis")
    interpretations: Dict[str, str] = Field(
        default_factory=dict,
        description="Portuguese interpretations for each measure"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}
