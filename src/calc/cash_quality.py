"""Cash quality classification (G/A/B grades)."""

from decimal import Decimal
from typing import Literal

from src.models import CashQualityMetric, PeriodResult


def classify_cash_quality(period_result: PeriodResult) -> list[CashQualityMetric]:
    """
    Classify cash quality on multiple dimensions (G/A/B grades).

    Metrics classified:

    1. OPERATING CASH FLOW MARGIN (OCF / Revenue):
       G (Good): >= 25% (strong operational cash generation)
       A (Average): >= 10% (acceptable)
       B (Below Avg): < 10% (weak operational cash flow)

    2. FREE CASH FLOW % (FCF / Revenue):
       G: >= 0% (positive FCF)
       A: >= -5% (minor cash burn)
       B: < -5% of Revenue (burning cash)

    3. WORKING CAPITAL / REVENUE:
       G: <= 10% (efficient WC)
       A: <= 20%
       B: > 20% (capital intensive)

    4. CASH CONVERSION CYCLE (days):
       G: <= 30 days (quick conversion)
       A: <= 60 days
       B: > 60 days (long cycle)

    5. NET DEBT / EBITDA:
       G: <= 2x (low leverage)
       A: <= 4x
       B: > 4x (high leverage)

    6. INTEREST COVERAGE (EBIT / Financial Expenses):
       G: >= 5x (strong coverage)
       A: >= 3x
       B: < 3x (weak coverage)

    Args:
        period_result: PeriodResult with all calculations

    Returns:
        List[CashQualityMetric]: All 6 metrics with grades and thresholds
    """
    ZERO = Decimal("0")
    pr = period_result

    def _safe_div(numerator: Decimal, denominator: Decimal) -> Decimal:
        """Return numerator / denominator, or ZERO when denominator is zero."""
        if denominator == ZERO:
            return ZERO
        return numerator / denominator

    def _grade_higher(value: Decimal, good: Decimal, avg: Decimal) -> Literal["G", "A", "B"]:
        """Higher is better: G if >= good, A if >= avg, else B."""
        if value >= good:
            return "G"
        if value >= avg:
            return "A"
        return "B"

    def _grade_lower(value: Decimal, good: Decimal, avg: Decimal) -> Literal["G", "A", "B"]:
        """Lower is better: G if <= good, A if <= avg, else B."""
        if value <= good:
            return "G"
        if value <= avg:
            return "A"
        return "B"

    metrics: list[CashQualityMetric] = []

    # 1. OCF MARGIN: operating_cash_flow / net_revenue * 100
    ocf_margin = _safe_div(pr.operating_cash_flow, pr.net_revenue) * Decimal("100")
    metrics.append(CashQualityMetric(
        metric="ocf_margin",
        label_pt="Margem Fluxo de Caixa Operacional %",
        value=ocf_margin,
        threshold_good=Decimal("25"),
        threshold_average=Decimal("10"),
        direction="higher",
        grade=_grade_higher(ocf_margin, Decimal("25"), Decimal("10")),
    ))

    # 2. FREE CASH FLOW %: free_cash_flow / net_revenue * 100
    fcf_pct = _safe_div(pr.free_cash_flow, pr.net_revenue) * Decimal("100")
    metrics.append(CashQualityMetric(
        metric="free_cash_flow",
        label_pt="Fluxo de Caixa Livre %",
        value=fcf_pct,
        threshold_good=ZERO,
        threshold_average=Decimal("-5"),
        direction="higher",
        grade=_grade_higher(fcf_pct, ZERO, Decimal("-5")),
    ))

    # 3. WC / REVENUE %: working_capital / net_revenue * 100
    wc_pct = _safe_div(pr.working_capital, pr.net_revenue) * Decimal("100")
    metrics.append(CashQualityMetric(
        metric="wc_revenue",
        label_pt="Capital de Giro / Receita %",
        value=wc_pct,
        threshold_good=Decimal("10"),
        threshold_average=Decimal("20"),
        direction="lower",
        grade=_grade_lower(wc_pct, Decimal("10"), Decimal("20")),
    ))

    # 4. CCC DAYS: cash_conversion_cycle
    ccc = pr.cash_conversion_cycle
    metrics.append(CashQualityMetric(
        metric="ccc_days",
        label_pt="Ciclo de Conversão de Caixa (dias)",
        value=ccc,
        threshold_good=Decimal("30"),
        threshold_average=Decimal("60"),
        direction="lower",
        grade=_grade_lower(ccc, Decimal("30"), Decimal("60")),
    ))

    # 5. NET DEBT / EBITDA
    nd_ebitda = _safe_div(pr.net_debt, pr.ebitda)
    metrics.append(CashQualityMetric(
        metric="net_debt_ebitda",
        label_pt="Dívida Líquida / EBITDA",
        value=nd_ebitda,
        threshold_good=Decimal("2"),
        threshold_average=Decimal("4"),
        direction="lower",
        grade=_grade_lower(nd_ebitda, Decimal("2"), Decimal("4")),
    ))

    # 6. INTEREST COVERAGE: EBIT / financial_expenses
    int_cov = _safe_div(pr.ebit, pr.financial_expenses)
    metrics.append(CashQualityMetric(
        metric="interest_coverage",
        label_pt="Cobertura de Juros",
        value=int_cov,
        threshold_good=Decimal("5"),
        threshold_average=Decimal("3"),
        direction="higher",
        grade=_grade_higher(int_cov, Decimal("5"), Decimal("3")),
    ))

    return metrics
