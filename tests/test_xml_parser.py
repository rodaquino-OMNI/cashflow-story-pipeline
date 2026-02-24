"""Tests for ERP XML parser."""
import pytest
from decimal import Decimal
from pathlib import Path

from src.ingest.xml_parser import ERPXMLParser

FIXTURE_PATH = "tests/fixtures/sample_balancete.xml"
FIXTURE_ABS = str(Path(__file__).parent / "fixtures" / "sample_balancete.xml")


class TestERPXMLParser:
    """Unit tests for ERPXMLParser covering balancete parsing and helpers."""

    # ------------------------------------------------------------------
    # Instantiation / file guards
    # ------------------------------------------------------------------

    def test_file_not_found_raises(self):
        """Verify FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            ERPXMLParser("/nonexistent/file.xml")

    def test_file_size_limit(self, tmp_path):
        """Verify ValueError for files exceeding 50 MB."""
        big_file = tmp_path / "big.xml"
        big_file.write_bytes(b"x" * (51 * 1024 * 1024))
        with pytest.raises(ValueError, match="too large"):
            ERPXMLParser(str(big_file))

    def test_constructor_succeeds_for_valid_file(self):
        """Constructor should not raise for an existing file within size limit."""
        parser = ERPXMLParser(FIXTURE_ABS)
        assert parser.file_path.exists()

    # ------------------------------------------------------------------
    # Encoding detection
    # ------------------------------------------------------------------

    def test_detect_encoding_utf8(self):
        """Verify UTF-8 encoding is detected from the XML declaration."""
        parser = ERPXMLParser(FIXTURE_ABS)
        encoding = parser.detect_encoding()
        assert encoding.upper() == "UTF-8"
        assert parser.encoding.upper() == "UTF-8"

    def test_detect_encoding_updates_instance_attribute(self):
        """detect_encoding() must update self.encoding, not just return a value."""
        parser = ERPXMLParser(FIXTURE_ABS)
        returned = parser.detect_encoding()
        assert returned == parser.encoding

    def test_detect_encoding_defaults_to_utf8_when_missing(self, tmp_path):
        """Files without an encoding declaration default to UTF-8."""
        no_decl = tmp_path / "nodecl.xml"
        no_decl.write_text("<balancete><empresa></empresa><contas></contas></balancete>", encoding="utf-8")
        parser = ERPXMLParser(str(no_decl))
        encoding = parser.detect_encoding()
        assert encoding.upper() == "UTF-8"

    # ------------------------------------------------------------------
    # Brazilian decimal helper
    # ------------------------------------------------------------------

    def test_parse_decimal_brazilian_format_full(self):
        """'1.234,56' -> Decimal('1234.56') — thousands dot, comma decimal."""
        assert ERPXMLParser._parse_decimal("1.234,56") == Decimal("1234.56")

    def test_parse_decimal_comma_only(self):
        """'1234,56' -> Decimal('1234.56') — comma as decimal separator only."""
        assert ERPXMLParser._parse_decimal("1234,56") == Decimal("1234.56")

    def test_parse_decimal_plain_dot(self):
        """'1234.56' -> Decimal('1234.56') — standard decimal dot."""
        assert ERPXMLParser._parse_decimal("1234.56") == Decimal("1234.56")

    def test_parse_decimal_empty_string(self):
        """Empty string should return Decimal('0')."""
        assert ERPXMLParser._parse_decimal("") == Decimal("0")

    def test_parse_decimal_none(self):
        """None should return Decimal('0')."""
        assert ERPXMLParser._parse_decimal(None) == Decimal("0")

    def test_parse_decimal_negative_value(self):
        """Negative values with Brazilian format are parsed correctly."""
        assert ERPXMLParser._parse_decimal("-22.400.000,00") == Decimal("-22400000.00")

    def test_parse_decimal_zero(self):
        """'0' should return Decimal('0')."""
        assert ERPXMLParser._parse_decimal("0") == Decimal("0")

    def test_parse_decimal_returns_decimal_type(self):
        """Return type must always be Decimal, not float or int."""
        result = ERPXMLParser._parse_decimal("100,00")
        assert isinstance(result, Decimal)

    # ------------------------------------------------------------------
    # parse_balancete — entry count and structure
    # ------------------------------------------------------------------

    def test_parse_balancete_returns_entries(self):
        """Parse sample XML and verify at least 5 entries are returned."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        assert len(entries) >= 5

    def test_parse_balancete_all_entries_have_required_fields(self):
        """Every AccountEntry must have code, description, and closing_balance."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        for entry in entries:
            assert hasattr(entry, "code"), "Entry missing 'code'"
            assert hasattr(entry, "description"), "Entry missing 'description'"
            assert hasattr(entry, "closing_balance"), "Entry missing 'closing_balance'"
            assert entry.code != "", f"Empty code found in entry: {entry}"

    def test_parse_balancete_returns_list(self):
        """parse_balancete() must return a list."""
        parser = ERPXMLParser(FIXTURE_ABS)
        result = parser.parse_balancete()
        assert isinstance(result, list)

    # ------------------------------------------------------------------
    # parse_balancete — Decimal precision
    # ------------------------------------------------------------------

    def test_parse_balancete_decimal_precision(self):
        """Closing balance of all entries must be Decimal, not float."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        for entry in entries:
            assert isinstance(entry.closing_balance, Decimal), (
                f"closing_balance for {entry.code} is {type(entry.closing_balance)}, expected Decimal"
            )

    def test_parse_balancete_cash_closing_balance(self):
        """Account 1.1.01 (Caixa) closing balance must match XML saldo_final."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        # 1.1.01 has no subcategorias — emitted as a direct conta entry
        caixa = next((e for e in entries if e.code == "1.1.01"), None)
        assert caixa is not None, "Entry 1.1.01 (Caixa) not found"
        assert caixa.closing_balance == Decimal("1200000.00")

    def test_parse_balancete_inventory_closing_balance(self):
        """Account 1.1.04 (Estoque) closing balance must match XML saldo_final."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        estoque = next((e for e in entries if e.code == "1.1.04"), None)
        assert estoque is not None, "Entry 1.1.04 (Estoque) not found"
        assert estoque.closing_balance == Decimal("3200000.00")

    def test_parse_balancete_revenue_saldo_balance(self):
        """Account 3.1 uses <saldo> instead of <saldo_final>; value must be correct."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        receita = next((e for e in entries if e.code == "3.1"), None)
        assert receita is not None, "Entry 3.1 (Receita de Vendas) not found"
        assert receita.closing_balance == Decimal("40100000.00")

    def test_parse_balancete_negative_balance(self):
        """Negative balances (expense accounts) must be preserved as Decimal."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        # Account 4.3 has saldo=-1200000.00
        desp_fin = next((e for e in entries if e.code == "4.3"), None)
        assert desp_fin is not None, "Entry 4.3 (Despesas Financeiras) not found"
        assert desp_fin.closing_balance == Decimal("-1200000.00")

    # ------------------------------------------------------------------
    # parse_balancete — subconta handling
    # ------------------------------------------------------------------

    def test_parse_balancete_subconta_handling(self):
        """Subconta entries must appear when parent has <subcategorias>."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        codes = {e.code for e in entries}
        # 1.1.03 has 3 subcontas
        assert "1.1.03.01" in codes, "Subconta 1.1.03.01 not found"
        assert "1.1.03.02" in codes, "Subconta 1.1.03.02 not found"
        assert "1.1.03.03" in codes, "Subconta 1.1.03.03 not found"

    def test_parse_balancete_parent_with_subcats_not_emitted(self):
        """Parent conta with subcategorias must NOT appear directly in entries."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        codes = {e.code for e in entries}
        # 1.1.03 and 4.2 both have subcategorias — parents must be suppressed
        assert "1.1.03" not in codes, "Parent 1.1.03 should not be emitted when subcontas exist"
        assert "4.2" not in codes, "Parent 4.2 should not be emitted when subcontas exist"

    def test_parse_balancete_all_subcontas_4_2(self):
        """All five subcontas of account 4.2 must appear in entries."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        codes = {e.code for e in entries}
        for expected in ("4.2.01", "4.2.02", "4.2.03", "4.2.04", "4.2.05"):
            assert expected in codes, f"Subconta {expected} not found in entries"

    def test_parse_balancete_subconta_saldo_value(self):
        """Subconta 1.1.03.01 closing balance must match XML <saldo> value."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        sub = next((e for e in entries if e.code == "1.1.03.01"), None)
        assert sub is not None, "Subconta 1.1.03.01 not found"
        assert sub.closing_balance == Decimal("8950000.00")

    def test_parse_balancete_subconta_negative_saldo(self):
        """Subconta 4.2.01 closing balance must be the correct negative Decimal."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        sub = next((e for e in entries if e.code == "4.2.01"), None)
        assert sub is not None, "Subconta 4.2.01 not found"
        assert sub.closing_balance == Decimal("-6500000.00")

    # ------------------------------------------------------------------
    # parse_balancete — period
    # ------------------------------------------------------------------

    def test_period_extraction(self):
        """Period extracted from <empresa><periodo> must be non-empty for all entries."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        assert len(entries) > 0
        for entry in entries:
            assert entry.period != "", f"Empty period on entry {entry.code}"

    def test_period_value_matches_xml(self):
        """Period string must exactly match the XML value '01/2025'."""
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        for entry in entries:
            assert entry.period == "01/2025", (
                f"Entry {entry.code} has period '{entry.period}', expected '01/2025'"
            )

    def test_period_empty_when_no_empresa_element(self, tmp_path):
        """Period defaults to empty string when <empresa> element is absent."""
        xml_no_period = tmp_path / "no_period.xml"
        xml_no_period.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<balancete>"
            "<contas>"
            "<conta>"
            "<codigo>1.1.01</codigo>"
            "<descricao>Caixa</descricao>"
            "<saldo_final>1000.00</saldo_final>"
            "</conta>"
            "</contas>"
            "</balancete>",
            encoding="utf-8",
        )
        parser = ERPXMLParser(str(xml_no_period))
        entries = parser.parse_balancete()
        assert len(entries) == 1
        assert entries[0].period == ""

    # ------------------------------------------------------------------
    # parse_balancete — empty contas element
    # ------------------------------------------------------------------

    def test_parse_balancete_empty_contas_returns_empty_list(self, tmp_path):
        """When <contas> is present but empty, parse_balancete returns []."""
        xml_empty = tmp_path / "empty.xml"
        xml_empty.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<balancete><empresa><periodo>01/2025</periodo></empresa>"
            "<contas></contas></balancete>",
            encoding="utf-8",
        )
        parser = ERPXMLParser(str(xml_empty))
        entries = parser.parse_balancete()
        assert entries == []

    def test_parse_balancete_no_contas_returns_empty_list(self, tmp_path):
        """When <contas> element is absent, parse_balancete returns []."""
        xml_no_contas = tmp_path / "nocontas.xml"
        xml_no_contas.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<balancete><empresa><periodo>01/2025</periodo></empresa></balancete>",
            encoding="utf-8",
        )
        parser = ERPXMLParser(str(xml_no_contas))
        entries = parser.parse_balancete()
        assert entries == []

    # ------------------------------------------------------------------
    # parse_balancete — total entry count
    # ------------------------------------------------------------------

    def test_parse_balancete_total_entry_count(self):
        """Sample XML should produce exactly 20 entries (direct contas + subcontas)."""
        # Direct contas without subcategorias:
        #   1.1.01, 1.1.04, 1.2.03, 2.1.01, 2.1.02, 2.2.01, 2.3,
        #   3.1, 3.2, 3.3, 4.1, 4.3  =>  12 entries
        # Subcontas of 1.1.03: 1.1.03.01, 1.1.03.02, 1.1.03.03  =>  3 entries
        # Subcontas of 4.2: 4.2.01, 4.2.02, 4.2.03, 4.2.04, 4.2.05  =>  5 entries
        # Total: 20
        parser = ERPXMLParser(FIXTURE_ABS)
        entries = parser.parse_balancete()
        assert len(entries) == 20
