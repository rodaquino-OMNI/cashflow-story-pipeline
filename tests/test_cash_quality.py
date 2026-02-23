"""Test cash quality scoring and grading system."""
import pytest
from decimal import Decimal

from src.models import MappedData, PeriodResult
from src.calc.income_statement import calculate_income_statement
from src.calc.working_capital import calculate_working_capital
from src.calc.balance_sheet import estimate_balance_sheet
from src.calc.cash_flow import calculate_cash_flow
from src.calc.ratios import calculate_ratios
from src.calc.cash_quality import classify_cash_quality


def _build_period_result_q1() -> PeriodResult:
    """Build a full PeriodResult from AUSTA Q1 data through the calc chain."""
    mapped = MappedData(
        company='AUSTA', period='Q1_2025', period_type='quarter', days_in_period=91,
        gross_revenue=Decimal('40100000'), returns_deductions=Decimal('2500000'),
        cogs=Decimal('30650000'), operating_expenses=Decimal('19650000'),
        financial_expenses=Decimal('1200000'), financial_income=Decimal('150000'),
        accounts_receivable=Decimal('18500000'), inventory=Decimal('3200000'),
        accounts_payable=Decimal('8900000'), cash=Decimal('1200000'),
        short_term_debt=Decimal('12000000'), long_term_debt=Decimal('25000000'),
        shareholders_equity=Decimal('35000000'), ppe_gross=Decimal('45000000'),
    )
    is_result = calculate_income_statement(mapped)
    wc_result = calculate_working_capital(mapped, days_in_period=mapped.days_in_period)
    merged = is_result.model_copy(update={
        'days_sales_outstanding': wc_result.days_sales_outstanding,
        'days_inventory_outstanding': wc_result.days_inventory_outstanding,
        'days_payable_outstanding': wc_result.days_payable_outstanding,
        'cash_conversion_cycle': wc_result.cash_conversion_cycle,
        'working_capital': wc_result.working_capital,
        'working_capital_investment': wc_result.working_capital_investment,
    })
    bs_result = estimate_balance_sheet(merged)
    cf_result = calculate_cash_flow(bs_result)
    return calculate_ratios(cf_result)


def _make_pr(**kwargs) -> PeriodResult:
    """Create a PeriodResult with specified fields for targeted grading tests."""
    defaults = {'period': 'TEST'}
    defaults.update(kwargs)
    return PeriodResult(**defaults)


class TestCashQuality:
    """Test suite for cash quality assessment."""

    def test_good_gross_margin(self):
        """Test cash quality scoring with good gross margin (>40%)."""
        pr = _make_pr(
            operating_cash_flow=Decimal('30000'),
            net_revenue=Decimal('100000'),
        )
        metrics = classify_cash_quality(pr)
        ocf = next(m for m in metrics if m.metric == "ocf_margin")
        assert ocf.grade == "G"
        assert ocf.value == Decimal('30')
        assert ocf.direction == "higher"
        assert ocf.threshold_good == Decimal('25')

    def test_average_gross_margin(self):
        """Test cash quality scoring with average gross margin."""
        pr = _make_pr(
            operating_cash_flow=Decimal('15000'),
            net_revenue=Decimal('100000'),
        )
        metrics = classify_cash_quality(pr)
        ocf = next(m for m in metrics if m.metric == "ocf_margin")
        assert ocf.grade == "A"
        assert ocf.value == Decimal('15')

    def test_bad_gross_margin(self):
        """Test cash quality scoring with bad gross margin (<20%)."""
        pr = _make_pr(
            operating_cash_flow=Decimal('5000'),
            net_revenue=Decimal('100000'),
        )
        metrics = classify_cash_quality(pr)
        ocf = next(m for m in metrics if m.metric == "ocf_margin")
        assert ocf.grade == "B"
        assert ocf.value == Decimal('5')

    def test_good_ar_days(self):
        """Test cash quality with good AR days (<60)."""
        pr = _make_pr(
            cash_conversion_cycle=Decimal('25'),
            net_revenue=Decimal('100000'),
        )
        metrics = classify_cash_quality(pr)
        ccc = next(m for m in metrics if m.metric == "ccc_days")
        assert ccc.grade == "G"
        assert ccc.value == Decimal('25')
        assert ccc.direction == "lower"

    def test_bad_ar_days(self):
        """Test cash quality with bad AR days (>120)."""
        pr = _make_pr(
            cash_conversion_cycle=Decimal('90'),
            net_revenue=Decimal('100000'),
        )
        metrics = classify_cash_quality(pr)
        ccc = next(m for m in metrics if m.metric == "ccc_days")
        assert ccc.grade == "B"
        assert ccc.value == Decimal('90')

    def test_ap_days_impact(self):
        """Test AP days impact on cash quality (higher is better)."""
        pr = _make_pr(
            working_capital=Decimal('8000'),
            net_revenue=Decimal('100000'),
        )
        metrics = classify_cash_quality(pr)
        wc = next(m for m in metrics if m.metric == "wc_revenue")
        assert wc.grade == "G"
        assert wc.value == Decimal('8')
        assert wc.label_pt == "Capital de Giro / Receita %"

    def test_healthcare_overrides(self):
        """Test healthcare industry-specific overrides in grading."""
        pr = _make_pr(
            ebit=Decimal('50000'),
            financial_expenses=Decimal('5000'),
            net_debt=Decimal('80000'),
            ebitda=Decimal('60000'),
            net_revenue=Decimal('100000'),
        )
        metrics = classify_cash_quality(pr)
        ic = next(m for m in metrics if m.metric == "interest_coverage")
        assert ic.grade == "G"
        assert ic.value == Decimal('10')
        nd = next(m for m in metrics if m.metric == "net_debt_ebitda")
        assert nd.grade == "G"

    def test_blue_consulting_grades(self):
        """Test Blue Consulting case study cash quality grades."""
        pr = _build_period_result_q1()
        metrics = classify_cash_quality(pr)
        by_metric = {m.metric: m for m in metrics}
        # OCF margin: deeply negative → B
        assert by_metric["ocf_margin"].grade == "B"
        # FCF: deeply negative → B
        assert by_metric["free_cash_flow"].grade == "B"
        # WC/Revenue: 12800000/37600000*100 = 34.04% > 20 → B
        assert by_metric["wc_revenue"].grade == "B"
        # CCC: ~27.8 days <= 30 → G
        assert by_metric["ccc_days"].grade == "G"
        # Interest coverage: ebit negative / fin_expenses → B
        assert by_metric["interest_coverage"].grade == "B"
        # All values are Decimal
        for m in metrics:
            assert isinstance(m.value, Decimal)

    def test_all_metrics_returned(self):
        """Test all metrics are returned in results."""
        pr = _build_period_result_q1()
        metrics = classify_cash_quality(pr)
        assert len(metrics) == 6
        metric_ids = {m.metric for m in metrics}
        expected = {"ocf_margin", "free_cash_flow", "wc_revenue", "ccc_days", "net_debt_ebitda", "interest_coverage"}
        assert metric_ids == expected
        for m in metrics:
            assert m.grade in ("G", "A", "B")
            assert m.direction in ("higher", "lower")
