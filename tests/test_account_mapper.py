"""Tests for account mapper.

Covers config loading, account-to-category mapping, reclassifications,
exclusions, edge cases, and an end-to-end integration with the XML parser.
"""

import pytest
from decimal import Decimal

from src.ingest.account_mapper import AccountMapper
from src.models import AccountEntry, MappedData


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONFIG_PATH = "config/companies/austa.yaml"
MISSING_CONFIG = "/nonexistent/config.yaml"


def _make_entry(
    code: str,
    description: str,
    closing_balance: Decimal,
    period: str = "Q1",
) -> AccountEntry:
    """Helper: build a minimal AccountEntry with only required fields."""
    return AccountEntry(
        code=code,
        description=description,
        closing_balance=closing_balance,
        period=period,
    )


# ---------------------------------------------------------------------------
# TestAccountMapper
# ---------------------------------------------------------------------------


class TestAccountMapper:
    """Unit tests for AccountMapper."""

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def test_load_config(self):
        """Verify config loads successfully from austa.yaml."""
        mapper = AccountMapper(CONFIG_PATH)

        # Categories dict should contain at least the standard keys
        assert "revenue" in mapper.categories
        assert "cogs" in mapper.categories
        assert "operating_expenses" in mapper.categories
        assert "equity" in mapper.categories
        assert mapper.company_name == "AUSTA Group"

    def test_config_not_found_raises(self):
        """Verify FileNotFoundError is raised for a missing config path."""
        with pytest.raises(FileNotFoundError):
            AccountMapper(MISSING_CONFIG)

    def test_flat_mapping_built_from_config(self):
        """Verify the flat prefix→category mapping is populated after load."""
        mapper = AccountMapper(CONFIG_PATH)

        # Direct prefix mappings from austa.yaml accounts lists
        assert mapper.mapping.get("3.1") == "revenue"
        assert mapper.mapping.get("3.2") == "deductions"
        assert mapper.mapping.get("4.1") == "cogs"
        assert mapper.mapping.get("4.2") == "operating_expenses"
        assert mapper.mapping.get("1.1.01") == "cash"

    def test_reclassifications_loaded_from_config(self):
        """Verify reclassification rules are parsed from the YAML."""
        mapper = AccountMapper(CONFIG_PATH)

        # austa.yaml defines two reclassifications for cogs
        from_codes = [rc["from"] for rc in mapper.reclassifications]
        assert "4.2.01" in from_codes
        assert "4.2.02" in from_codes

    def test_exclusions_loaded_from_config(self):
        """Verify exclusion codes are populated from the YAML."""
        mapper = AccountMapper(CONFIG_PATH)

        # operating_expenses section excludes 4.2.01 and 4.2.02
        assert "4.2.01" in mapper.exclusions
        assert "4.2.02" in mapper.exclusions

    # ------------------------------------------------------------------
    # map_accounts — return type and period
    # ------------------------------------------------------------------

    def test_map_returns_mapped_data_type(self):
        """Verify map_accounts() always returns a MappedData instance."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.1", "Receita", Decimal("100"))]
        result = mapper.map_accounts(entries, "Q1")

        assert isinstance(result, MappedData)

    def test_mapped_data_period_is_preserved(self):
        """Verify the period argument is stored in the returned MappedData."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.1", "Receita", Decimal("100"))]
        result = mapper.map_accounts(entries, "Q1_2025")

        assert result.period == "Q1_2025"

    def test_mapped_data_company_from_config(self):
        """Verify MappedData.company matches the YAML company name."""
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts([], "Q1")

        assert result.company == "AUSTA Group"

    # ------------------------------------------------------------------
    # map_accounts — known account mappings
    # ------------------------------------------------------------------

    def test_map_known_revenue_account(self):
        """Account code 3.1 must accumulate into gross_revenue."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.1", "Receita", Decimal("1000000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.gross_revenue == Decimal("1000000")

    def test_map_known_deductions_account(self):
        """Account code 3.2 must accumulate into returns_deductions."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.2", "Deduções", Decimal("-250000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.returns_deductions == Decimal("-250000")

    def test_map_known_cogs_account(self):
        """Account code 4.1 must accumulate into cogs."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("4.1", "CPV", Decimal("-500000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.cogs == Decimal("-500000")

    def test_map_known_operating_expenses_account(self):
        """Account code 4.2 sub-account (non-excluded) maps to operating_expenses."""
        mapper = AccountMapper(CONFIG_PATH)
        # 4.2.03 is not excluded and sits under 4.2
        entries = [_make_entry("4.2.03", "Vendas", Decimal("-100000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.operating_expenses == Decimal("-100000")

    def test_map_known_cash_account(self):
        """Account code 1.1.01 must accumulate into cash."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("1.1.01", "Caixa", Decimal("1200000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.cash == Decimal("1200000")

    def test_map_known_accounts_receivable(self):
        """Account code 1.1.03 must accumulate into accounts_receivable."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("1.1.03", "CR", Decimal("18500000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.accounts_receivable == Decimal("18500000")

    def test_map_known_accounts_payable(self):
        """Account code 2.1.01 must accumulate into accounts_payable."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("2.1.01", "Fornecedores", Decimal("8900000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.accounts_payable == Decimal("8900000")

    def test_map_known_equity_account(self):
        """Account code 2.3 must accumulate into shareholders_equity."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("2.3", "PL", Decimal("35000000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.shareholders_equity == Decimal("35000000")

    def test_map_known_short_term_debt(self):
        """Account code 2.1.02 must accumulate into short_term_debt."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("2.1.02", "Emprestimo CP", Decimal("12000000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.short_term_debt == Decimal("12000000")

    def test_map_known_long_term_debt(self):
        """Account code 2.2.01 must accumulate into long_term_debt."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("2.2.01", "Emprestimo LP", Decimal("25000000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.long_term_debt == Decimal("25000000")

    def test_map_known_financial_income(self):
        """Account code 3.3 must accumulate into financial_income."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.3", "Rec Fin", Decimal("150000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.financial_income == Decimal("150000")

    def test_map_known_financial_expenses(self):
        """Account code 4.3 must accumulate into financial_expenses."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("4.3", "Desp Fin", Decimal("-1200000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.financial_expenses == Decimal("-1200000")

    def test_map_known_inventory(self):
        """Account code 1.1.04 must accumulate into inventory."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("1.1.04", "Estoque", Decimal("3200000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.inventory == Decimal("3200000")

    def test_map_known_fixed_assets(self):
        """Account code 1.2.03 must accumulate into ppe_gross."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("1.2.03", "Imobilizado", Decimal("45000000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.ppe_gross == Decimal("45000000")

    # ------------------------------------------------------------------
    # map_accounts — unmapped / unknown accounts
    # ------------------------------------------------------------------

    def test_unmapped_account_ignored(self):
        """Unmapped account code must not affect any category totals."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("9.9.99", "Unknown", Decimal("500"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.gross_revenue == Decimal("0")
        assert result.cogs == Decimal("0")
        assert result.operating_expenses == Decimal("0")
        assert result.cash == Decimal("0")

    def test_unmapped_account_does_not_raise(self):
        """Processing an unmapped account must not raise an exception."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("9.9.99", "Unknown", Decimal("500"))]
        # Should complete without error
        result = mapper.map_accounts(entries, "Q1")
        assert isinstance(result, MappedData)

    # ------------------------------------------------------------------
    # map_accounts — empty input
    # ------------------------------------------------------------------

    def test_empty_entries_returns_zero_mapped(self):
        """Empty account list must return MappedData with all zero monetary fields."""
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts([], "Q1")

        assert result.gross_revenue == Decimal("0")
        assert result.returns_deductions == Decimal("0")
        assert result.cogs == Decimal("0")
        assert result.operating_expenses == Decimal("0")
        assert result.financial_income == Decimal("0")
        assert result.financial_expenses == Decimal("0")
        assert result.accounts_receivable == Decimal("0")
        assert result.inventory == Decimal("0")
        assert result.accounts_payable == Decimal("0")
        assert result.ppe_gross == Decimal("0")
        assert result.short_term_debt == Decimal("0")
        assert result.long_term_debt == Decimal("0")
        assert result.shareholders_equity == Decimal("0")
        assert result.cash == Decimal("0")

    def test_empty_entries_derived_fields_are_zero(self):
        """Derived fields (net_revenue, gross_profit, ebitda, ebit, ebt) must be zero for empty input."""
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts([], "Q1")

        assert result.net_revenue == Decimal("0")
        assert result.gross_profit == Decimal("0")
        assert result.ebitda == Decimal("0")
        assert result.ebit == Decimal("0")
        assert result.ebt == Decimal("0")

    # ------------------------------------------------------------------
    # map_accounts — reclassifications
    # ------------------------------------------------------------------

    def test_reclassification_4201_to_cogs(self):
        """Account 4.2.01 must be reclassified to 4.1 (cogs), not operating_expenses."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("4.2.01", "Pessoal Serv", Decimal("-6500000"))]
        result = mapper.map_accounts(entries, "Q1")

        # Reclassified to cogs — must appear there
        assert result.cogs == Decimal("-6500000")
        # Must NOT appear in operating_expenses
        assert result.operating_expenses == Decimal("0")

    def test_reclassification_4202_to_cogs(self):
        """Account 4.2.02 must be reclassified to 4.1 (cogs), not operating_expenses."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("4.2.02", "Materiais Serv", Decimal("-1750000"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.cogs == Decimal("-1750000")
        assert result.operating_expenses == Decimal("0")

    def test_reclassification_cogs_accumulates_with_direct_cogs(self):
        """Reclassified amounts must add to direct COGS amounts."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("4.1", "CPV direto", Decimal("-22400000")),
            _make_entry("4.2.01", "Pessoal reclass", Decimal("-6500000")),
            _make_entry("4.2.02", "Materiais reclass", Decimal("-1750000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        expected_cogs = Decimal("-22400000") + Decimal("-6500000") + Decimal("-1750000")
        assert result.cogs == expected_cogs

    def test_excluded_codes_absent_from_operating_expenses(self):
        """Codes 4.2.01 and 4.2.02 must NOT count toward operating_expenses."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("4.2.01", "Pessoal", Decimal("-6500000")),
            _make_entry("4.2.02", "Materiais", Decimal("-1750000")),
            _make_entry("4.2.03", "Vendas", Decimal("-5200000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        # Only 4.2.03 should land in operating_expenses
        assert result.operating_expenses == Decimal("-5200000")

    # ------------------------------------------------------------------
    # map_accounts — prefix matching (sub-accounts)
    # ------------------------------------------------------------------

    def test_sub_account_prefix_matched_to_parent_category(self):
        """A sub-account (e.g. 1.1.03.01) under a mapped prefix maps correctly."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("1.1.03.01", "CR Operadoras", Decimal("8950000")),
            _make_entry("1.1.03.02", "CR SUS", Decimal("6200000")),
            _make_entry("1.1.03.03", "CR Particular", Decimal("3350000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        expected_ar = Decimal("8950000") + Decimal("6200000") + Decimal("3350000")
        assert result.accounts_receivable == expected_ar

    # ------------------------------------------------------------------
    # map_accounts — derived fields
    # ------------------------------------------------------------------

    def test_net_revenue_derived_from_gross_and_deductions(self):
        """net_revenue = gross_revenue + returns_deductions."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("3.1", "Receita", Decimal("1000000")),
            _make_entry("3.2", "Deduções", Decimal("-100000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        assert result.net_revenue == Decimal("900000")

    def test_gross_profit_derived_correctly(self):
        """gross_profit = net_revenue + cogs."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("3.1", "Receita", Decimal("1000000")),
            _make_entry("3.2", "Deduções", Decimal("-100000")),
            _make_entry("4.1", "CPV", Decimal("-400000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        # net_revenue = 1000000 + (-100000) = 900000
        # gross_profit = 900000 + (-400000) = 500000
        assert result.gross_profit == Decimal("500000")

    def test_ebitda_derived_correctly(self):
        """ebitda = gross_profit + operating_expenses."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("3.1", "Receita", Decimal("1000000")),
            _make_entry("4.1", "CPV", Decimal("-400000")),
            _make_entry("4.2.03", "Opex", Decimal("-200000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        # net_revenue = 1000000 (no deductions)
        # gross_profit = 1000000 + (-400000) = 600000
        # ebitda = 600000 + (-200000) = 400000
        assert result.ebitda == Decimal("400000")

    def test_ebt_derived_includes_financial_items(self):
        """ebt = ebit + financial_income + financial_expenses."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("3.1", "Receita", Decimal("1000000")),
            _make_entry("4.1", "CPV", Decimal("-400000")),
            _make_entry("4.2.03", "Opex", Decimal("-100000")),
            _make_entry("3.3", "Rec Fin", Decimal("50000")),
            _make_entry("4.3", "Desp Fin", Decimal("-80000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        # ebit = ebitda + 0 depreciation = 1000000 - 400000 - 100000 = 500000
        # ebt = 500000 + 50000 + (-80000) = 470000
        assert result.ebt == Decimal("470000")

    # ------------------------------------------------------------------
    # map_accounts — multiple entries and aggregation
    # ------------------------------------------------------------------

    def test_multiple_revenue_entries_aggregate(self):
        """Multiple entries under the same category must be summed."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("3.1", "Receita Jan", Decimal("400000")),
            _make_entry("3.1", "Receita Fev", Decimal("350000")),
            _make_entry("3.1", "Receita Mar", Decimal("250000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        assert result.gross_revenue == Decimal("1000000")

    def test_mixed_categories_do_not_cross_contaminate(self):
        """Values for different categories must not bleed into each other."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("3.1", "Receita", Decimal("1000000")),
            _make_entry("4.1", "CPV", Decimal("-500000")),
            _make_entry("1.1.01", "Caixa", Decimal("200000")),
        ]
        result = mapper.map_accounts(entries, "Q1")

        assert result.gross_revenue == Decimal("1000000")
        assert result.cogs == Decimal("-500000")
        assert result.cash == Decimal("200000")
        # Other fields remain zero
        assert result.accounts_receivable == Decimal("0")
        assert result.inventory == Decimal("0")

    # ------------------------------------------------------------------
    # validate_mapping
    # ------------------------------------------------------------------

    def test_validate_mapping_fails_for_zero_revenue(self):
        """validate_mapping returns False when gross_revenue == 0."""
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts([], "Q1")
        is_valid, messages = mapper.validate_mapping(result)

        assert is_valid is False
        assert any("gross_revenue" in m for m in messages)

    def test_validate_mapping_passes_with_positive_revenue_and_equity(self):
        """validate_mapping returns True for positive revenue and non-zero equity."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [
            _make_entry("3.1", "Receita", Decimal("1000000")),
            _make_entry("2.3", "PL", Decimal("500000")),
        ]
        result = mapper.map_accounts(entries, "Q1")
        is_valid, messages = mapper.validate_mapping(result)

        assert is_valid is True
        assert messages == []

    def test_validate_mapping_warns_negative_revenue(self):
        """validate_mapping flags gross_revenue <= 0."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.1", "Receita negativa", Decimal("-1"))]
        result = mapper.map_accounts(entries, "Q1")
        is_valid, messages = mapper.validate_mapping(result)

        # negative revenue also triggers the warning
        assert is_valid is False

    def test_validate_mapping_warns_zero_equity(self):
        """validate_mapping flags zero shareholders_equity."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.1", "Receita", Decimal("500000"))]
        # No equity entry → shareholders_equity defaults to 0
        result = mapper.map_accounts(entries, "Q1")
        is_valid, messages = mapper.validate_mapping(result)

        assert is_valid is False
        assert any("shareholders_equity" in m for m in messages)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_zero_balance_entry_does_not_affect_totals(self):
        """An entry with closing_balance=0 must not change category totals."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("3.1", "Receita zero", Decimal("0"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.gross_revenue == Decimal("0")

    def test_large_decimal_values_preserved(self):
        """Very large Decimal values must be stored without rounding errors."""
        mapper = AccountMapper(CONFIG_PATH)
        large_value = Decimal("999999999999.99")
        entries = [_make_entry("3.1", "Receita grande", large_value)]
        result = mapper.map_accounts(entries, "Q1")

        assert result.gross_revenue == large_value

    def test_negative_decimal_values_preserved(self):
        """Negative Decimal values (cost entries) must be signed correctly."""
        mapper = AccountMapper(CONFIG_PATH)
        entries = [_make_entry("4.1", "CPV negativo", Decimal("-12345678.99"))]
        result = mapper.map_accounts(entries, "Q1")

        assert result.cogs == Decimal("-12345678.99")

    # ------------------------------------------------------------------
    # End-to-end: XML parser → AccountMapper
    # ------------------------------------------------------------------

    def test_end_to_end_with_xml_parser(self):
        """Integration: parse sample_balancete.xml then map all accounts."""
        from src.ingest.xml_parser import ERPXMLParser

        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts(entries, "Q1_2025")

        assert isinstance(result, MappedData)
        assert result.period == "Q1_2025"

    def test_end_to_end_revenue_value(self):
        """Integration: gross_revenue matches XML account 3.1 saldo."""
        from src.ingest.xml_parser import ERPXMLParser

        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts(entries, "Q1_2025")

        # XML 3.1 <saldo>40100000.00</saldo>
        assert result.gross_revenue == Decimal("40100000.00")

    def test_end_to_end_cogs_includes_reclassified(self):
        """Integration: cogs total includes reclassified sub-accounts 4.2.01 + 4.2.02."""
        from src.ingest.xml_parser import ERPXMLParser

        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts(entries, "Q1_2025")

        # 4.1=-22400000, 4.2.01=-6500000, 4.2.02=-1750000 all land in cogs
        expected_cogs = Decimal("-22400000") + Decimal("-6500000") + Decimal("-1750000")
        assert result.cogs == expected_cogs

    def test_end_to_end_operating_expenses_excludes_reclassified(self):
        """Integration: operating_expenses excludes 4.2.01 and 4.2.02 sub-accounts."""
        from src.ingest.xml_parser import ERPXMLParser

        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts(entries, "Q1_2025")

        # Only 4.2.03 + 4.2.04 + 4.2.05 contribute to operating_expenses
        expected_opex = Decimal("-5200000") + Decimal("-4100000") + Decimal("-2100000")
        assert result.operating_expenses == expected_opex

    def test_end_to_end_accounts_receivable_sum_of_subcontas(self):
        """Integration: accounts_receivable is sum of three 1.1.03.xx sub-accounts."""
        from src.ingest.xml_parser import ERPXMLParser

        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts(entries, "Q1_2025")

        # 1.1.03.01=8950000, 1.1.03.02=6200000, 1.1.03.03=3350000
        expected_ar = Decimal("8950000") + Decimal("6200000") + Decimal("3350000")
        assert result.accounts_receivable == expected_ar

    def test_end_to_end_all_fields_populated(self):
        """Integration: key balance-sheet fields are non-zero after parsing real XML."""
        from src.ingest.xml_parser import ERPXMLParser

        parser = ERPXMLParser("tests/fixtures/sample_balancete.xml")
        entries = parser.parse_balancete()
        mapper = AccountMapper(CONFIG_PATH)
        result = mapper.map_accounts(entries, "Q1_2025")

        # Cash: XML 1.1.01 saldo_final=1200000
        assert result.cash == Decimal("1200000.00")
        # Inventory: XML 1.1.04 saldo_final=3200000
        assert result.inventory == Decimal("3200000.00")
        # PP&E: XML 1.2.03 saldo_final=45000000
        assert result.ppe_gross == Decimal("45000000.00")
        # Accounts payable: XML 2.1.01 saldo_final=8900000
        assert result.accounts_payable == Decimal("8900000.00")
        # Short-term debt: XML 2.1.02 saldo_final=12000000
        assert result.short_term_debt == Decimal("12000000.00")
        # Long-term debt: XML 2.2.01 saldo_final=25000000
        assert result.long_term_debt == Decimal("25000000.00")
        # Equity: XML 2.3 saldo_final=35000000
        assert result.shareholders_equity == Decimal("35000000.00")
        # Financial income: XML 3.3 saldo=150000
        assert result.financial_income == Decimal("150000.00")
        # Financial expenses: XML 4.3 saldo=-1200000
        assert result.financial_expenses == Decimal("-1200000.00")
