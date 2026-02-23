"""AI-powered CashFlow Story analyst for narrative generation."""

import os
import logging
import json
from typing import Optional, Dict, Any, List
from decimal import Decimal

from src.models import AnalysisResult
from src.ai.prompts import PROMPTS, SYSTEM_PROMPT


def _to_float(value: Any) -> Any:
    """Recursively convert Decimal values to float for JSON serialization."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _to_float(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_float(item) for item in value]
    return value


class CashFlowStoryAnalyst:
    """
    Generates AI-powered narrative insights for CashFlow Story analysis.

    Uses LLM (Claude or similar) to create:
    - Executive summary of cash flow story
    - Variance analysis and trends
    - Risk assessment and warnings
    - Cash flow quality assessment
    - Strategic recommendations
    - Board-ready narrative

    Attributes:
        model: LLM model name (e.g., "claude-opus-4")
        api_key: API key for LLM access
        temperature: LLM temperature (0.0-1.0, default 0.7)
        logger: Logger instance
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: Optional[str] = None,
        temperature: float = 0.3,
    ) -> None:
        """
        Initialize CashFlow Story analyst.

        Args:
            model: LLM model name
            api_key: API key for LLM (from env if None)
            temperature: LLM creativity parameter
        """
        self.model = model
        self.api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
        self.temperature = temperature
        self.logger = logging.getLogger(__name__)

    def _build_context(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Build comprehensive analysis context for prompt.

        Extracts key metrics and findings for LLM input:
        - All period results and calculations
        - Power of One levers
        - Cash quality grades
        - Variances and trends
        - Three Big Measures

        Args:
            analysis_result: Complete analysis results

        Returns:
            Dict[str, Any]: Structured context for prompt building
        """
        context: Dict[str, Any] = {
            "company": analysis_result.company,
            "periods_count": len(analysis_result.periods),
        }

        # Extract latest period data
        if analysis_result.periods:
            latest = analysis_result.periods[-1]

            # Chapter 1: Profitability
            context["gross_revenue"] = float(latest.gross_revenue)
            context["returns_deductions"] = float(latest.returns_deductions)
            context["net_revenue"] = float(latest.net_revenue)
            context["cogs"] = float(latest.cogs)
            context["gross_profit"] = float(latest.gross_profit)
            context["gross_margin_pct"] = float(latest.gross_margin_pct)
            context["operating_expenses"] = float(latest.operating_expenses)
            context["ebitda"] = float(latest.ebitda)
            context["ebitda_margin_pct"] = float(latest.ebitda_margin_pct)
            context["depreciation_amortization"] = float(latest.depreciation_amortization)
            context["ebit"] = float(latest.ebit)
            context["ebit_margin_pct"] = float(latest.ebit_margin_pct)
            context["financial_expenses"] = float(latest.financial_expenses)
            context["financial_income"] = float(latest.financial_income)
            context["other_income_expenses"] = float(latest.other_income_expenses)
            context["ebt"] = float(latest.ebt)
            context["irpj_tax"] = float(latest.irpj_tax)
            context["csll_tax"] = float(latest.csll_tax)
            context["net_income"] = float(latest.net_income)
            context["net_margin_pct"] = float(latest.net_margin_pct)

            # Chapter 2: Working Capital
            context["accounts_receivable"] = float(latest.accounts_receivable)
            context["inventory"] = float(latest.inventory)
            context["accounts_payable"] = float(latest.accounts_payable)
            context["days_sales_outstanding"] = float(latest.days_sales_outstanding)
            context["days_inventory_outstanding"] = float(latest.days_inventory_outstanding)
            context["days_payable_outstanding"] = float(latest.days_payable_outstanding)
            context["cash_conversion_cycle"] = float(latest.cash_conversion_cycle)
            context["working_capital"] = float(latest.working_capital)
            context["working_capital_investment"] = float(latest.working_capital_investment)

            # Chapter 3: Other Capital
            context["ppe_net"] = float(latest.ppe_net)
            context["intangibles_net"] = float(latest.intangibles_net)
            context["other_capital_net"] = float(latest.other_capital_net)
            context["other_capital_investment"] = float(latest.other_capital_investment)

            # Chapter 4: Funding
            context["total_debt"] = float(latest.total_debt)
            context["net_debt"] = float(latest.net_debt)
            context["shareholders_equity"] = float(latest.shareholders_equity)
            context["debt_to_equity"] = float(latest.debt_to_equity)

            # Cash Flow Statement
            context["operating_cash_flow"] = float(latest.operating_cash_flow)
            context["investing_cash_flow"] = float(latest.investing_cash_flow)
            context["financing_cash_flow"] = float(latest.financing_cash_flow)
            context["net_cash_flow"] = float(latest.net_cash_flow)
            context["free_cash_flow"] = float(latest.free_cash_flow)

            # Financial Ratios
            context["current_ratio"] = float(latest.current_ratio)
            context["quick_ratio"] = float(latest.quick_ratio)
            context["roe_pct"] = float(latest.roe_pct)
            context["roa_pct"] = float(latest.roa_pct)
            context["roce_pct"] = float(latest.roce_pct)

        # Power of One levers
        context["power_of_one"] = [
            {
                "lever": lever.lever,
                "label_pt": lever.label_pt,
                "current_value": float(lever.current_value),
                "profit_impact": float(lever.profit_impact),
                "cash_impact": float(lever.cash_impact),
            }
            for lever in analysis_result.power_of_one
        ]

        # Cash quality metrics
        context["cash_quality"] = [
            {
                "metric": metric.metric,
                "label_pt": metric.label_pt,
                "value": float(metric.value),
                "grade": metric.grade,
            }
            for metric in analysis_result.cash_quality
        ]

        # Three Big Measures
        if analysis_result.three_big_measures is not None:
            tbm = analysis_result.three_big_measures
            context["three_big_measures"] = {
                "net_cash_flow": float(tbm.net_cash_flow),
                "operating_cash_flow": float(tbm.operating_cash_flow),
                "marginal_cash_flow": float(tbm.marginal_cash_flow),
                "interpretations": tbm.interpretations,
            }

        # Marginal cash flow
        if analysis_result.marginal_cash_flow is not None:
            context["marginal_cash_flow"] = _to_float(analysis_result.marginal_cash_flow)

        # Variances
        context["variances"] = analysis_result.variances

        return context

    def _build_prompt(
        self,
        context: Dict[str, Any],
        section: str = "cashflow_story_narrative",
    ) -> str:
        """
        Build LLM prompt for specific analysis section.

        Uses templates from src.ai.prompts for consistent formatting.

        Args:
            context: Analysis context from _build_context
            section: Which section to generate

        Returns:
            str: Formatted prompt for LLM
        """
        template = PROMPTS[section]

        if section == "cashflow_story_narrative":
            # Determine latest period label
            periods_count = context.get("periods_count", 0)
            period_label = f"Período mais recente (de {periods_count} período(s) analisado(s))"
            return template.format(
                company=context["company"],
                period=period_label,
                context=str(context),
            )

        return template.format(context=str(context))

    def analyze(self, analysis_result: AnalysisResult) -> str:
        """
        Generate complete board narrative from analysis results.

        Creates a comprehensive, in Portuguese, executive summary covering:
        1. Cash flow story across 4 chapters
        2. Key risks and opportunities
        3. Power of One levers for management
        4. Recommendations for improvement

        Args:
            analysis_result: Complete AnalysisResult with all calculations

        Returns:
            str: Portuguese narrative ready for board presentation
        """
        if self.api_key is None:
            raise ValueError(
                "ANTHROPIC_API_KEY não configurada. "
                "Configure a variável de ambiente ou passe api_key."
            )

        import anthropic

        context = self._build_context(analysis_result)
        prompt = self._build_prompt(context, section="cashflow_story_narrative")

        self.logger.info(
            "Calling Anthropic API: model=%s, section=cashflow_story_narrative",
            self.model,
        )

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=self.temperature,
        )

        return response.content[0].text
