"""Tests for AI analyst with mocked Anthropic API."""
import sys
import types
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from src.ai.analyst import CashFlowStoryAnalyst, _to_float
from src.models import AnalysisResult, PeriodResult


def _make_anthropic_mock(narrative_text="AI narrative response"):
    """
    Build a mock that stands in for the ``anthropic`` module.

    Because ``analyst.py`` uses a *local* ``import anthropic`` inside the
    ``analyze`` method, we cannot patch ``src.ai.analyst.anthropic`` (the
    attribute does not exist at module level).  Instead we inject a fake
    module into ``sys.modules`` so that the ``import`` statement inside
    ``analyze`` resolves to our mock.
    """
    mock_module = types.ModuleType("anthropic")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=narrative_text)]
    mock_client.messages.create.return_value = mock_response
    mock_module.Anthropic = MagicMock(return_value=mock_client)
    # Expose the inner client so tests can inspect calls
    mock_module._mock_client = mock_client
    return mock_module


class TestToFloat:
    def test_decimal_to_float(self):
        assert _to_float(Decimal("123.45")) == 123.45

    def test_dict_conversion(self):
        result = _to_float({"a": Decimal("1"), "b": Decimal("2")})
        assert result == {"a": 1.0, "b": 2.0}

    def test_list_conversion(self):
        result = _to_float([Decimal("1"), Decimal("2")])
        assert result == [1.0, 2.0]

    def test_passthrough_non_decimal(self):
        assert _to_float("hello") == "hello"
        assert _to_float(42) == 42

    def test_nested_dict_with_list(self):
        result = _to_float({"values": [Decimal("5"), Decimal("10")]})
        assert result == {"values": [5.0, 10.0]}

    def test_zero_decimal(self):
        assert _to_float(Decimal("0")) == 0.0

    def test_negative_decimal(self):
        assert _to_float(Decimal("-99.99")) == -99.99

    def test_empty_dict(self):
        assert _to_float({}) == {}

    def test_empty_list(self):
        assert _to_float([]) == []

    def test_none_passthrough(self):
        assert _to_float(None) is None


class TestCashFlowStoryAnalyst:
    def test_init_with_api_key(self):
        analyst = CashFlowStoryAnalyst(api_key="test-key")
        assert analyst.api_key == "test-key"
        assert analyst.model == "claude-sonnet-4-6"
        assert analyst.temperature == 0.3

    def test_init_from_env(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            analyst = CashFlowStoryAnalyst()
            assert analyst.api_key == "env-key"

    def test_init_custom_model(self):
        analyst = CashFlowStoryAnalyst(api_key="key", model="claude-opus-4-6")
        assert analyst.model == "claude-opus-4-6"

    def test_init_custom_temperature(self):
        analyst = CashFlowStoryAnalyst(api_key="key", temperature=0.7)
        assert analyst.temperature == 0.7

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            analyst = CashFlowStoryAnalyst()
            result = AnalysisResult(company="Test", periods=[PeriodResult(period="Q1")])
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                analyst.analyze(result)

    def test_build_context_extracts_metrics(self):
        pr = PeriodResult(
            period="Q1",
            net_revenue=Decimal("1000000"),
            ebitda=Decimal("200000"),
            operating_cash_flow=Decimal("150000"),
        )
        result = AnalysisResult(company="Test", periods=[pr])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert context["company"] == "Test"
        assert context["net_revenue"] == 1000000.0
        assert context["ebitda"] == 200000.0

    def test_build_context_operating_cash_flow(self):
        pr = PeriodResult(
            period="Q1",
            operating_cash_flow=Decimal("150000"),
        )
        result = AnalysisResult(company="Test", periods=[pr])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert context["operating_cash_flow"] == 150000.0

    def test_build_context_company_name(self):
        result = AnalysisResult(company="ACME Corp", periods=[PeriodResult(period="Q1")])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert context["company"] == "ACME Corp"

    def test_build_context_periods_count(self):
        periods = [PeriodResult(period=f"Q{i}") for i in range(1, 4)]
        result = AnalysisResult(company="Test", periods=periods)
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert context["periods_count"] == 3

    def test_build_context_uses_latest_period(self):
        p1 = PeriodResult(period="Q1", net_revenue=Decimal("500000"))
        p2 = PeriodResult(period="Q2", net_revenue=Decimal("800000"))
        result = AnalysisResult(company="Test", periods=[p1, p2])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        # Should use the last (latest) period
        assert context["net_revenue"] == 800000.0

    def test_build_context_no_periods(self):
        result = AnalysisResult(company="Test", periods=[])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert context["company"] == "Test"
        assert context["periods_count"] == 0
        # Should not contain period-specific keys when no periods present
        assert "net_revenue" not in context

    def test_build_context_three_big_measures(self):
        from src.models.cashflow_story import ThreeBigMeasures
        tbm = ThreeBigMeasures(
            net_cash_flow=Decimal("100000"),
            operating_cash_flow=Decimal("200000"),
            marginal_cash_flow=Decimal("50000"),
            interpretations={"net": "positive"},
        )
        result = AnalysisResult(
            company="Test",
            periods=[PeriodResult(period="Q1")],
            three_big_measures=tbm,
        )
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert "three_big_measures" in context
        assert context["three_big_measures"]["net_cash_flow"] == 100000.0
        assert context["three_big_measures"]["operating_cash_flow"] == 200000.0

    def test_build_context_power_of_one(self):
        from src.models.cashflow_story import PowerOfOneLever
        lever = PowerOfOneLever(
            lever="revenue",
            label_pt="Receita",
            current_value=Decimal("1000000"),
            change_amount=Decimal("10000"),
            profit_impact=Decimal("10000"),
            cash_impact=Decimal("8000"),
        )
        result = AnalysisResult(
            company="Test",
            periods=[PeriodResult(period="Q1")],
            power_of_one=[lever],
        )
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert len(context["power_of_one"]) == 1
        assert context["power_of_one"][0]["lever"] == "revenue"
        assert context["power_of_one"][0]["profit_impact"] == 10000.0

    def test_build_context_cash_quality(self):
        from src.models.cashflow_story import CashQualityMetric
        metric = CashQualityMetric(
            metric="operating_cf_margin",
            label_pt="Margem FCO",
            value=Decimal("0.15"),
            grade="G",
        )
        result = AnalysisResult(
            company="Test",
            periods=[PeriodResult(period="Q1")],
            cash_quality=[metric],
        )
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert len(context["cash_quality"]) == 1
        assert context["cash_quality"][0]["grade"] == "G"
        assert context["cash_quality"][0]["value"] == 0.15

    def test_build_context_variances_included(self):
        result = AnalysisResult(
            company="Test",
            periods=[PeriodResult(period="Q1")],
            variances={"net_revenue": {"absolute": 50000, "pct": 5.0}},
        )
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        assert context["variances"] == {"net_revenue": {"absolute": 50000, "pct": 5.0}}

    def test_build_prompt_uses_template(self):
        pr = PeriodResult(period="Q1", net_revenue=Decimal("1000"))
        result = AnalysisResult(company="TestCo", periods=[pr])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        prompt = analyst._build_prompt(context)
        assert "TestCo" in prompt

    def test_build_prompt_contains_period_info(self):
        pr = PeriodResult(period="Q1")
        result = AnalysisResult(company="TestCo", periods=[pr])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        prompt = analyst._build_prompt(context)
        # Prompt should reference how many periods were analyzed
        assert "1" in prompt

    def test_build_prompt_default_section_is_narrative(self):
        pr = PeriodResult(period="Q1")
        result = AnalysisResult(company="TestCo", periods=[pr])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        # Default section should render cashflow_story_narrative template
        prompt = analyst._build_prompt(context)
        assert "TestCo" in prompt
        # Template marker from prompts.py
        assert "board" in prompt.lower() or "cash" in prompt.lower()

    def test_build_prompt_executive_summary_section(self):
        pr = PeriodResult(period="Q1")
        result = AnalysisResult(company="TestCo", periods=[pr])
        analyst = CashFlowStoryAnalyst(api_key="fake")
        context = analyst._build_context(result)
        prompt = analyst._build_prompt(context, section="executive_summary")
        assert "executive summary" in prompt.lower() or "Context" in prompt

    def test_analyze_calls_api(self):
        mock_module = _make_anthropic_mock("AI narrative response")
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1", net_revenue=Decimal("1000"))
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key")
            narrative = analyst.analyze(result)

        assert narrative == "AI narrative response"
        mock_module._mock_client.messages.create.assert_called_once()

    def test_analyze_returns_text_from_first_content_block(self):
        mock_module = _make_anthropic_mock()
        # Override content to have two blocks
        block1 = MagicMock(text="First block content")
        block2 = MagicMock(text="Second block content")
        mock_module._mock_client.messages.create.return_value.content = [block1, block2]

        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key")
            narrative = analyst.analyze(result)

        # Should return only the first content block
        assert narrative == "First block content"

    def test_analyze_creates_client_with_api_key(self):
        mock_module = _make_anthropic_mock()
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="my-secret-key")
            analyst.analyze(result)

        mock_module.Anthropic.assert_called_once_with(api_key="my-secret-key")

    def test_analyze_uses_configured_model(self):
        mock_module = _make_anthropic_mock()
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key", model="claude-opus-4-6")
            analyst.analyze(result)

        call_kwargs = mock_module._mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-opus-4-6"

    def test_analyze_uses_configured_temperature(self):
        mock_module = _make_anthropic_mock()
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key", temperature=0.5)
            analyst.analyze(result)

        call_kwargs = mock_module._mock_client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5

    def test_analyze_sends_system_prompt(self):
        from src.ai.prompts import SYSTEM_PROMPT
        mock_module = _make_anthropic_mock()
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key")
            analyst.analyze(result)

        call_kwargs = mock_module._mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == SYSTEM_PROMPT

    def test_analyze_sends_user_message(self):
        mock_module = _make_anthropic_mock()
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="MyCompany", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key")
            analyst.analyze(result)

        call_kwargs = mock_module._mock_client.messages.create.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "MyCompany" in messages[0]["content"]

    def test_analyze_sets_max_tokens(self):
        mock_module = _make_anthropic_mock()
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key")
            analyst.analyze(result)

        call_kwargs = mock_module._mock_client.messages.create.call_args[1]
        assert call_kwargs["max_tokens"] == 4000

    def test_analyze_no_real_api_calls(self):
        """Verify test isolation: the real anthropic module is never called."""
        mock_module = _make_anthropic_mock("mocked")
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            pr = PeriodResult(period="Q1")
            result = AnalysisResult(company="Test", periods=[pr])
            analyst = CashFlowStoryAnalyst(api_key="test-key")
            analyst.analyze(result)

        # Confirm mock was used, not real client
        assert mock_module.Anthropic.called
        assert mock_module._mock_client.messages.create.called

    def test_api_key_none_when_env_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            analyst = CashFlowStoryAnalyst()
            assert analyst.api_key is None

    def test_explicit_api_key_overrides_env(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            analyst = CashFlowStoryAnalyst(api_key="explicit-key")
            assert analyst.api_key == "explicit-key"
