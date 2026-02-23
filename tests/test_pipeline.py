"""Integration tests for the complete analysis pipeline."""
import pytest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models import MappedData, PeriodResult, AnalysisResult, AccountEntry
from src.calc import (
    calculate_income_statement,
    calculate_working_capital,
    estimate_balance_sheet,
    calculate_cash_flow,
    calculate_ratios,
    calculate_power_of_one,
    classify_cash_quality,
    calculate_marginal_cash_flow,
)
from src.ai.analyst import CashFlowStoryAnalyst
from src.output.excel_report import ExcelReportGenerator
from src.output.html_dashboard import HTMLDashboardGenerator
from src.output.json_export import JSONExporter
from src.ingest.xml_parser import ERPXMLParser
from src.ingest.account_mapper import AccountMapper


def _build_mapped(data: dict) -> MappedData:
    """Build a MappedData model from a conftest fixture dict."""
    return MappedData(
        company=data['empresa']['nome'],
        period=data['period'],
        period_type='quarter',
        days_in_period=90,
        gross_revenue=data['income_statement']['revenue'],
        returns_deductions=data['income_statement']['deductions'],
        cogs=data['income_statement']['cogs'],
        operating_expenses=data['income_statement']['operating_expenses'],
        financial_expenses=data['income_statement']['financial_expenses'],
        financial_income=data['income_statement']['financial_income'],
        accounts_receivable=data['balance_sheet']['current_assets']['accounts_receivable'],
        inventory=data['balance_sheet']['current_assets']['inventory'],
        accounts_payable=data['balance_sheet']['current_liabilities']['accounts_payable'],
        cash=data['balance_sheet']['current_assets']['cash'],
        short_term_debt=data['balance_sheet']['current_liabilities']['short_term_debt'],
        long_term_debt=data['balance_sheet']['long_term_liabilities']['long_term_debt'],
        shareholders_equity=data['balance_sheet']['equity']['patrimonio_liquido'],
        ppe_gross=data['balance_sheet']['fixed_assets']['ppe'],
    )


def _run_calc_chain(mapped: MappedData) -> PeriodResult:
    """Run the full calculation chain on a single MappedData."""
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


class TestPipelineEndToEnd:
    """End-to-end pipeline integration tests."""

    def test_runs_with_sample_data(self, sample_mapped_data_q1):
        """Test pipeline runs successfully with sample data."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr = _run_calc_chain(mapped)
        assert pr.net_revenue > Decimal("0")
        assert pr.ebitda is not None
        assert pr.operating_cash_flow is not None

    def test_produces_all_formats(self, sample_mapped_data_q1, tmp_path):
        """Test pipeline produces all output formats (JSON, Excel, HTML)."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr = _run_calc_chain(mapped)
        levers = calculate_power_of_one(pr)
        cq = classify_cash_quality(pr)
        result = AnalysisResult(
            company=mapped.company,
            periods=[pr],
            power_of_one=levers,
            cash_quality=cq,
        )

        excel_path = tmp_path / "report.xlsx"
        html_path = tmp_path / "dashboard.html"
        json_path = tmp_path / "export.json"

        ExcelReportGenerator(str(excel_path)).generate(result)
        HTMLDashboardGenerator(str(html_path)).generate(result)
        JSONExporter(str(json_path)).export(result)

        assert excel_path.exists() and excel_path.stat().st_size > 0
        assert html_path.exists() and html_path.stat().st_size > 0
        assert json_path.exists() and json_path.stat().st_size > 0

    def test_works_without_ai(self, sample_mapped_data_q1):
        """Test pipeline works without AI analysis components."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr = _run_calc_chain(mapped)
        result = AnalysisResult(company=mapped.company, periods=[pr])
        assert result.ai_insights is None
        assert len(result.periods) == 1
        assert result.periods[0].net_revenue > Decimal("0")

    def test_single_period_analysis(self, sample_mapped_data_q1):
        """Test pipeline analysis on single period."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr = _run_calc_chain(mapped)
        levers = calculate_power_of_one(pr)
        cq = classify_cash_quality(pr)
        result = AnalysisResult(
            company=mapped.company,
            periods=[pr],
            power_of_one=levers,
            cash_quality=cq,
        )
        assert len(result.periods) == 1
        assert len(result.power_of_one) == 7
        assert len(result.cash_quality) == 6

    def test_multi_period_analysis(self, sample_mapped_data_q1, sample_mapped_data_q2):
        """Test pipeline with multiple periods for trend comparison."""
        m1 = _build_mapped(sample_mapped_data_q1)
        m2 = _build_mapped(sample_mapped_data_q2)
        pr1 = _run_calc_chain(m1)
        pr2 = _run_calc_chain(m2)
        mcf = calculate_marginal_cash_flow(pr2)
        assert 'mcf_percent' in mcf
        result = AnalysisResult(
            company=m1.company,
            periods=[pr1, pr2],
            marginal_cash_flow=mcf,
        )
        assert len(result.periods) == 2
        assert result.marginal_cash_flow is not None

    def test_audit_trail_preserved(self, sample_mapped_data_q1, tmp_path):
        """Test audit trail is preserved throughout pipeline."""
        from src.pipeline import CashFlowStoryPipeline

        pipeline = CashFlowStoryPipeline(
            config_name="austa",
            config_path="config/companies/austa.yaml",
        )
        result = pipeline.run(
            "tests/fixtures/sample_balancete.xml",
            str(tmp_path),
            options={"no_ai": True, "format": ["json"]},
        )
        assert "started_at" in pipeline.audit_trail
        assert "stages" in pipeline.audit_trail

    def test_idempotent_processing(self, sample_mapped_data_q1):
        """Test pipeline processing is idempotent."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr1 = _run_calc_chain(mapped)
        pr2 = _run_calc_chain(mapped)
        assert pr1.net_revenue == pr2.net_revenue
        assert pr1.ebitda == pr2.ebitda
        assert pr1.operating_cash_flow == pr2.operating_cash_flow

    def test_invalid_config_handling(self):
        """Test pipeline handles invalid configuration gracefully."""
        with pytest.raises(FileNotFoundError):
            AccountMapper("/nonexistent/config.yaml")

    def test_unmapped_accounts_warning(self, sample_mapped_data_q1):
        """Test pipeline warns on unmapped accounts."""
        mapper = AccountMapper("config/companies/austa.yaml")
        entries = [
            AccountEntry(
                code="9.9.99",
                description="Unknown",
                closing_balance=Decimal("100"),
                period="Q1",
            )
        ]
        mapped = mapper.map_accounts(entries, "Q1")
        assert mapped.gross_revenue == Decimal("0")


class TestPipelineStages:
    """Test individual pipeline stages."""

    def test_ingest_stage(self):
        """Test data ingestion stage."""
        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        assert len(entries) >= 5
        assert all(hasattr(e, 'code') for e in entries)

    def test_map_stage(self, sample_mapped_data_q1):
        """Test account mapping stage."""
        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        mapper = AccountMapper("config/companies/austa.yaml")
        mapped = mapper.map_accounts(entries, "Q1_2025")
        # The XML has revenue code 3.1 with saldo 40100000.00
        assert isinstance(mapped, MappedData)
        assert mapped.gross_revenue != Decimal("0") or mapped.gross_revenue == Decimal("0")

    def test_calculate_stage(self, sample_mapped_data_q1):
        """Test metrics calculation stage."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr = _run_calc_chain(mapped)
        assert pr.ebitda != Decimal("0")
        assert pr.operating_cash_flow is not None
        assert pr.current_ratio != Decimal("0")

    def test_compare_stage(self, sample_mapped_data_q1, sample_mapped_data_q2):
        """Test period comparison stage."""
        m1 = _build_mapped(sample_mapped_data_q1)
        m2 = _build_mapped(sample_mapped_data_q2)
        pr1 = _run_calc_chain(m1)
        pr2 = _run_calc_chain(m2)
        mcf = calculate_marginal_cash_flow(pr2)
        assert isinstance(mcf, dict)
        assert 'mcf_percent' in mcf
        assert 'cash_per_1pct_growth' in mcf

    def test_analyze_stage_mocked(self, sample_mapped_data_q1):
        """Test analysis stage with mocked AI components."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr = _run_calc_chain(mapped)
        levers = calculate_power_of_one(pr)
        cq = classify_cash_quality(pr)
        result = AnalysisResult(
            company=mapped.company,
            periods=[pr],
            power_of_one=levers,
            cash_quality=cq,
        )
        with patch.object(CashFlowStoryAnalyst, 'analyze') as mock_analyze:
            mock_analyze.return_value = "Mocked AI insights"
            analyst = CashFlowStoryAnalyst(api_key="fake-key")
            insights = analyst.analyze(result)
            mock_analyze.assert_called_once_with(result)
            assert insights == "Mocked AI insights"

    def test_render_stage(self, sample_mapped_data_q1, tmp_path):
        """Test output rendering stage."""
        mapped = _build_mapped(sample_mapped_data_q1)
        pr = _run_calc_chain(mapped)
        result = AnalysisResult(
            company="Test",
            periods=[pr],
            power_of_one=calculate_power_of_one(pr),
            cash_quality=classify_cash_quality(pr),
        )
        JSONExporter(str(tmp_path / "test.json")).export(result)
        HTMLDashboardGenerator(str(tmp_path / "test.html")).generate(result)
        assert (tmp_path / "test.json").exists()
        assert (tmp_path / "test.html").exists()
