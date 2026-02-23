"""Financial data models using Pydantic v2 with Decimal fields for precision."""

from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class AccountEntry(BaseModel):
    """
    Represents a single account entry from ERP balancete or fluxo de caixa.
    
    Attributes:
        code: Account code (e.g., "1.1.1" or "4100")
        description: Account description in Portuguese
        opening_balance: Saldo inicial (Decimal for precision)
        total_debits: Débitos (D)
        total_credits: Créditos (C)
        closing_balance: Saldo final
        period: Period identifier (e.g., "202401", "Jan/25")
    """
    code: str = Field(..., description="Account code from ERP")
    description: str = Field(..., description="Account description")
    opening_balance: Decimal = Field(default=Decimal("0"), description="Opening balance")
    total_debits: Decimal = Field(default=Decimal("0"), description="Total debits")
    total_credits: Decimal = Field(default=Decimal("0"), description="Total credits")
    closing_balance: Decimal = Field(default=Decimal("0"), description="Closing balance")
    period: str = Field(..., description="Period identifier")

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class MappedData(BaseModel):
    """
    Complete mapped financial data from Chapter 1-4 ERP inputs.
    All values use Decimal for precision.
    
    Attributes:
        company: Company CNPJ or identifier
        period: Period (e.g., "202401")
        period_type: "month", "quarter", or "year"
        days_in_period: Number of days in period
        
        # Chapter 1: Profitability
        gross_revenue: Receita bruta
        returns_deductions: Devoluções e deduções
        net_revenue: Receita líquida
        cogs: Custo de Mercadoria Vendida (COGS)
        gross_profit: Lucro bruto
        operating_expenses: Despesas operacionais
        ebitda: EBITDA (Lucro operacional antes de D&A)
        depreciation_amortization: Depreciação e amortização
        ebit: EBIT (Lucro operacional)
        financial_expenses: Despesas financeiras
        financial_income: Receita financeira
        other_income_expenses: Outras receitas/despesas
        ebt: EBT (Lucro antes de impostos)
        
        # Chapter 2: Working Capital Components
        accounts_receivable: Contas a receber
        inventory: Estoques
        accounts_payable: Contas a pagar
        
        # Chapter 3: Other Capital (OC)
        ppe_gross: Imobilizado bruto (PP&E)
        accumulated_depreciation: Depreciação acumulada
        intangibles: Intangível
        other_assets: Outros ativos não circulantes
        other_liabilities: Outros passivos não circulantes
        
        # Chapter 4: Funding
        cash: Caixa e equivalentes
        short_term_debt: Dívida de curto prazo
        long_term_debt: Dívida de longo prazo
        shareholders_equity: Patrimônio líquido
        
        # Additional metadata
        metadata: Optional dictionary with source info, flags, etc.
    """
    company: str = Field(..., description="Company CNPJ or identifier")
    period: str = Field(..., description="Period identifier (e.g., '202401')")
    period_type: str = Field(default="month", description="Period type: 'month', 'quarter', or 'year'")
    days_in_period: int = Field(default=30, description="Number of days in period")
    
    # Chapter 1: Profitability
    gross_revenue: Decimal = Field(default=Decimal("0"), description="Receita bruta")
    returns_deductions: Decimal = Field(default=Decimal("0"), description="Devoluções e deduções")
    net_revenue: Decimal = Field(default=Decimal("0"), description="Receita líquida")
    cogs: Decimal = Field(default=Decimal("0"), description="COGS - Custo de mercadoria vendida")
    gross_profit: Decimal = Field(default=Decimal("0"), description="Lucro bruto")
    operating_expenses: Decimal = Field(default=Decimal("0"), description="Despesas operacionais")
    ebitda: Decimal = Field(default=Decimal("0"), description="EBITDA")
    depreciation_amortization: Decimal = Field(default=Decimal("0"), description="D&A")
    ebit: Decimal = Field(default=Decimal("0"), description="EBIT - Lucro operacional")
    financial_expenses: Decimal = Field(default=Decimal("0"), description="Despesas financeiras")
    financial_income: Decimal = Field(default=Decimal("0"), description="Receita financeira")
    other_income_expenses: Decimal = Field(default=Decimal("0"), description="Outras receitas/despesas")
    ebt: Decimal = Field(default=Decimal("0"), description="EBT - Lucro antes de impostos")
    
    # Chapter 2: Working Capital Components
    accounts_receivable: Decimal = Field(default=Decimal("0"), description="Contas a receber")
    inventory: Decimal = Field(default=Decimal("0"), description="Estoques")
    accounts_payable: Decimal = Field(default=Decimal("0"), description="Contas a pagar")
    
    # Chapter 3: Other Capital (OC)
    ppe_gross: Decimal = Field(default=Decimal("0"), description="Imobilizado bruto")
    accumulated_depreciation: Decimal = Field(default=Decimal("0"), description="Depreciação acumulada")
    intangibles: Decimal = Field(default=Decimal("0"), description="Intangível")
    other_assets: Decimal = Field(default=Decimal("0"), description="Outros ativos")
    other_liabilities: Decimal = Field(default=Decimal("0"), description="Outros passivos")
    
    # Chapter 4: Funding
    cash: Decimal = Field(default=Decimal("0"), description="Caixa e equivalentes")
    short_term_debt: Decimal = Field(default=Decimal("0"), description="Dívida de curto prazo")
    long_term_debt: Decimal = Field(default=Decimal("0"), description="Dívida de longo prazo")
    shareholders_equity: Decimal = Field(default=Decimal("0"), description="Patrimônio líquido")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class PeriodResult(BaseModel):
    """
    Complete calculated results for a single period.
    Contains all income statement, working capital, cash flow, and ratio calculations.
    
    Attributes:
        period: Period identifier
        
        # Income Statement (Chapter 1)
        gross_revenue, returns_deductions, net_revenue, cogs, gross_profit,
        operating_expenses, ebitda, depreciation_amortization, ebit,
        financial_expenses, financial_income, other_income_expenses, ebt,
        irpj_tax, csll_tax, net_income
        
        # Working Capital (Chapter 2)
        accounts_receivable, inventory, accounts_payable,
        days_sales_outstanding (DSO), days_inventory_outstanding (DIO),
        days_payable_outstanding (DPO), cash_conversion_cycle (CCC),
        working_capital_investment
        
        # Other Capital (Chapter 3)
        ppe_net, intangibles_net, other_capital_investment
        
        # Funding (Chapter 4)
        total_debt, debt_to_equity, net_debt, shareholders_equity
        
        # Cash Flow Statement
        operating_cash_flow, investing_cash_flow, financing_cash_flow,
        net_cash_flow, free_cash_flow
        
        # Financial Ratios
        current_ratio, quick_ratio, debt_to_equity_ratio, roe, roa, roce
    """
    period: str = Field(..., description="Period identifier")
    
    # Chapter 1: Income Statement
    gross_revenue: Decimal = Field(default=Decimal("0"))
    returns_deductions: Decimal = Field(default=Decimal("0"))
    net_revenue: Decimal = Field(default=Decimal("0"))
    cogs: Decimal = Field(default=Decimal("0"))
    gross_profit: Decimal = Field(default=Decimal("0"))
    gross_margin_pct: Decimal = Field(default=Decimal("0"))
    operating_expenses: Decimal = Field(default=Decimal("0"))
    ebitda: Decimal = Field(default=Decimal("0"))
    ebitda_margin_pct: Decimal = Field(default=Decimal("0"))
    depreciation_amortization: Decimal = Field(default=Decimal("0"))
    ebit: Decimal = Field(default=Decimal("0"))
    ebit_margin_pct: Decimal = Field(default=Decimal("0"))
    financial_expenses: Decimal = Field(default=Decimal("0"))
    financial_income: Decimal = Field(default=Decimal("0"))
    other_income_expenses: Decimal = Field(default=Decimal("0"))
    ebt: Decimal = Field(default=Decimal("0"))
    irpj_tax: Decimal = Field(default=Decimal("0"))
    csll_tax: Decimal = Field(default=Decimal("0"))
    net_income: Decimal = Field(default=Decimal("0"))
    net_margin_pct: Decimal = Field(default=Decimal("0"))
    
    # Chapter 2: Working Capital
    accounts_receivable: Decimal = Field(default=Decimal("0"))
    inventory: Decimal = Field(default=Decimal("0"))
    accounts_payable: Decimal = Field(default=Decimal("0"))
    days_sales_outstanding: Decimal = Field(default=Decimal("0"), alias="dso")
    days_inventory_outstanding: Decimal = Field(default=Decimal("0"), alias="dio")
    days_payable_outstanding: Decimal = Field(default=Decimal("0"), alias="dpo")
    cash_conversion_cycle: Decimal = Field(default=Decimal("0"), alias="ccc")
    working_capital: Decimal = Field(default=Decimal("0"))
    working_capital_investment: Decimal = Field(default=Decimal("0"))
    
    # Chapter 3: Other Capital
    ppe_net: Decimal = Field(default=Decimal("0"))
    intangibles_net: Decimal = Field(default=Decimal("0"))
    other_capital_net: Decimal = Field(default=Decimal("0"))
    other_capital_investment: Decimal = Field(default=Decimal("0"))
    
    # Chapter 4: Funding
    total_debt: Decimal = Field(default=Decimal("0"))
    net_debt: Decimal = Field(default=Decimal("0"))
    shareholders_equity: Decimal = Field(default=Decimal("0"))
    
    # Cash Flow Statement
    operating_cash_flow: Decimal = Field(default=Decimal("0"))
    investing_cash_flow: Decimal = Field(default=Decimal("0"))
    financing_cash_flow: Decimal = Field(default=Decimal("0"))
    net_cash_flow: Decimal = Field(default=Decimal("0"))
    free_cash_flow: Decimal = Field(default=Decimal("0"))
    
    # Financial Ratios
    current_ratio: Decimal = Field(default=Decimal("0"))
    quick_ratio: Decimal = Field(default=Decimal("0"))
    debt_to_equity: Decimal = Field(default=Decimal("0"))
    roe_pct: Decimal = Field(default=Decimal("0"))
    roa_pct: Decimal = Field(default=Decimal("0"))
    roce_pct: Decimal = Field(default=Decimal("0"))

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}
        populate_by_name = True


class AnalysisResult(BaseModel):
    """
    Complete CashFlow Story analysis result combining all periods and insights.
    
    Attributes:
        company: Company identifier
        generated_at: Timestamp of analysis generation
        periods: List of PeriodResult for each period analyzed
        variances: Dictionary of variance analysis by metric
        power_of_one: List of PowerOfOneLever impacts
        cash_quality: List of CashQualityMetric grades
        marginal_cash_flow: Marginal cash flow metrics
        growth_cash_impact: Impact of growth on cash
        three_big_measures: Top 3 cash flow measures (net CF, OCF, marginal CF)
        ai_insights: Optional AI-generated insights narrative (when --no-ai not set)
        audit_trail: Dictionary with audit trail of processing steps
    """
    company: str = Field(..., description="Company identifier")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")
    periods: List[PeriodResult] = Field(default_factory=list, description="Results for each period")
    variances: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Variance analysis")
    power_of_one: List["PowerOfOneLever"] = Field(default_factory=list, description="Power of One levers")
    cash_quality: List["CashQualityMetric"] = Field(default_factory=list, description="Cash quality metrics")
    marginal_cash_flow: Optional[Dict[str, Decimal]] = Field(default=None, description="Marginal cash flow")
    growth_cash_impact: Optional[Dict[str, Decimal]] = Field(default=None, description="Growth impact")
    three_big_measures: Optional["ThreeBigMeasures"] = Field(default=None, description="Top 3 measures")
    ai_insights: Optional[str] = Field(default=None, description="AI-generated narrative insights")
    audit_trail: Dict[str, Any] = Field(default_factory=dict, description="Processing audit trail")

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


# Forward references for circular imports
from src.models.cashflow_story import PowerOfOneLever, CashQualityMetric, ThreeBigMeasures

AnalysisResult.model_rebuild()
