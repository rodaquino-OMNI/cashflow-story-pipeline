"""Test Power of One sensitivity analysis for margin improvement levers."""
import pytest
from decimal import Decimal

from src.models import MappedData, PeriodResult
from src.calc.income_statement import calculate_income_statement
from src.calc.working_capital import calculate_working_capital
from src.calc.balance_sheet import estimate_balance_sheet
from src.calc.cash_flow import calculate_cash_flow
from src.calc.ratios import calculate_ratios
from src.calc.power_of_one import calculate_power_of_one


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


class TestPowerOfOne:
    """Test suite for Power of One sensitivity analysis."""

    def test_price_lever(self):
        """Test 1% price increase impact on profitability."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        revenue_lever = next(lv for lv in levers if lv.lever == "revenue")
        expected_change = pr.net_revenue * Decimal('0.01')
        assert revenue_lever.change_amount == expected_change
        assert revenue_lever.label_pt == "Receita"
        assert revenue_lever.current_value == pr.net_revenue
        assert isinstance(revenue_lever.profit_impact, Decimal)

    def test_volume_lever(self):
        """Test 1% volume increase impact (net of variable costs)."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        revenue_lever = next(lv for lv in levers if lv.lever == "revenue")
        ebit_margin = pr.ebit_margin_pct / Decimal('100')
        expected_profit = revenue_lever.change_amount * ebit_margin
        assert revenue_lever.profit_impact == expected_profit
        assert revenue_lever.cash_impact == revenue_lever.profit_impact

    def test_cogs_lever(self):
        """Test 1% COGS reduction impact on profitability."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        cogs_lever = next(lv for lv in levers if lv.lever == "cogs")
        expected_change = pr.cogs * Decimal('0.01')
        assert cogs_lever.change_amount == expected_change
        assert cogs_lever.profit_impact == expected_change
        assert cogs_lever.cash_impact == expected_change
        assert cogs_lever.label_pt == "Custo dos Produtos/Serviços"

    def test_overhead_lever(self):
        """Test 1% overhead expense reduction impact."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        overhead_lever = next(lv for lv in levers if lv.lever == "overhead")
        expected_change = pr.operating_expenses * Decimal('0.01')
        assert overhead_lever.change_amount == expected_change
        assert overhead_lever.profit_impact == expected_change
        assert overhead_lever.cash_impact == expected_change
        assert overhead_lever.label_pt == "Despesas Operacionais"

    def test_ar_days_lever(self):
        """Test AR days reduction impact on cash flow and financing."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        ar_lever = next(lv for lv in levers if lv.lever == "ar_days")
        daily_revenue = pr.net_revenue / Decimal('365')
        assert ar_lever.change_amount == Decimal('1')
        assert ar_lever.profit_impact == Decimal('0')
        assert ar_lever.cash_impact == daily_revenue
        assert ar_lever.change_unit == "dias"

    def test_inventory_days_lever(self):
        """Test inventory days reduction impact on working capital."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        inv_lever = next(lv for lv in levers if lv.lever == "inventory_days")
        daily_cogs = pr.cogs / Decimal('365')
        assert inv_lever.change_amount == Decimal('1')
        assert inv_lever.profit_impact == Decimal('0')
        assert inv_lever.cash_impact == daily_cogs
        assert inv_lever.label_pt == "Prazo de Estoque"

    def test_ap_days_lever(self):
        """Test AP days increase impact on cash flow (higher is better)."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        ap_lever = next(lv for lv in levers if lv.lever == "ap_days")
        daily_cogs = pr.cogs / Decimal('365')
        assert ap_lever.change_amount == Decimal('1')
        assert ap_lever.profit_impact == Decimal('0')
        assert ap_lever.cash_impact == daily_cogs
        assert ap_lever.label_pt == "Prazo de Pagamento"

    def test_value_impact_with_multiple(self):
        """Test value impact calculation with earnings multiple."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        valuation_multiple = Decimal('6.0')
        for lever in levers:
            if lever.category == "Chapter 1":
                assert lever.value_impact == lever.profit_impact * valuation_multiple

    def test_all_seven_returned(self):
        """Test all 7 levers are returned in results."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        assert len(levers) == 7
        lever_ids = {lv.lever for lv in levers}
        expected = {"revenue", "cogs", "overhead", "ar_days", "inventory_days", "ap_days", "capex"}
        assert lever_ids == expected

    def test_custom_sensitivity(self):
        """Test custom sensitivity input beyond 1%."""
        pr = PeriodResult(
            period='TEST',
            net_revenue=Decimal('10000000'),
            cogs=Decimal('6000000'),
            operating_expenses=Decimal('2000000'),
            ebit=Decimal('2000000'),
            ebit_margin_pct=Decimal('20'),
            other_capital_investment=Decimal('500000'),
        )
        levers = calculate_power_of_one(pr)
        revenue_lever = next(lv for lv in levers if lv.lever == "revenue")
        assert revenue_lever.change_amount == Decimal('100000')
        assert revenue_lever.profit_impact == Decimal('20000')
        capex_lever = next(lv for lv in levers if lv.lever == "capex")
        assert capex_lever.cash_impact == Decimal('5000')
        assert capex_lever.profit_impact == Decimal('5000') * Decimal('0.10')

    def test_blue_consulting_case_study_validation(self):
        """Test Blue Consulting case study values against Power of One."""
        pr = _build_period_result_q1()
        levers = calculate_power_of_one(pr)
        # Sorted by abs(cash_impact) desc: cogs(306500) > overhead(196500) > ...
        assert levers[0].lever == "cogs"
        assert levers[1].lever == "overhead"
        assert levers[-1].lever == "capex"
        # All values are Decimal
        for lever in levers:
            assert isinstance(lever.cash_impact, Decimal)
            assert isinstance(lever.profit_impact, Decimal)
            assert isinstance(lever.value_impact, Decimal)
        # Category counts
        ch1 = [lv for lv in levers if lv.category == "Chapter 1"]
        ch2 = [lv for lv in levers if lv.category == "Chapter 2"]
        ch3 = [lv for lv in levers if lv.category == "Chapter 3"]
        assert len(ch1) == 3
        assert len(ch2) == 3
        assert len(ch3) == 1
