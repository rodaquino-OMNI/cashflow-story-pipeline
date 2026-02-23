"""Parser for ERP XML files (balancete and fluxo de caixa formats)."""

import re
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
import xml.etree.ElementTree as ET

from src.models import AccountEntry


class ERPXMLParser:
    """
    Parses ERP XML files in Brazilian formats (balancete, fluxo de caixa).

    Supports multiple XML structures from common Brazilian ERP systems:
    - Balancete de Verificação (trial balance)
    - Fluxo de Caixa (cash flow statement)

    Attributes:
        file_path: Path to XML file
        encoding: Detected file encoding (UTF-8, Latin-1, etc)
        format: Detected XML format type
    """

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"XML file not found: {self.file_path}")
        self.encoding: str = "UTF-8"
        self.format: Optional[str] = None

    # ------------------------------------------------------------------
    # Encoding / format detection
    # ------------------------------------------------------------------

    def detect_encoding(self) -> str:
        """Read first 200 bytes and extract encoding from XML declaration."""
        with open(self.file_path, "rb") as fh:
            raw = fh.read(200)
        match = re.search(rb"encoding=[\"']([^\"']+)[\"']", raw)
        if match:
            self.encoding = match.group(1).decode("ascii")
        else:
            self.encoding = "UTF-8"
        return self.encoding

    def detect_format(self) -> str:
        """Auto-detect XML format by inspecting the root element tag."""
        self.detect_encoding()
        tree = ET.parse(str(self.file_path))
        root = tree.getroot()
        tag = root.tag.lower()
        if "balancete" in tag:
            self.format = "balancete"
        elif "fluxo" in tag:
            self.format = "fluxo_caixa"
        else:
            self.format = "unknown"
        return self.format

    # ------------------------------------------------------------------
    # Brazilian number helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_decimal(text: Optional[str]) -> Decimal:
        """Convert a Brazilian-format number string to Decimal.

        Handles '1.234,56' → Decimal('1234.56') and plain '1234.56'.
        """
        if not text:
            return Decimal("0")
        text = text.strip()
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        return Decimal(text)

    # ------------------------------------------------------------------
    # Balancete parser
    # ------------------------------------------------------------------

    def parse_balancete(self) -> List[AccountEntry]:
        """Parse balancete de verificação XML.

        Returns both top-level <conta> entries and nested <subconta> entries
        so downstream mappers can apply reclassifications by sub-account code.
        """
        self.detect_encoding()
        tree = ET.parse(str(self.file_path))
        root = tree.getroot()

        period = self._extract_period(root)

        entries: List[AccountEntry] = []
        contas = root.find("contas")
        if contas is None:
            return entries

        for conta in contas.findall("conta"):
            subcats = conta.find("subcategorias")
            if subcats is not None:
                # Parent is a roll-up — emit children only to avoid double-counting
                for sub in subcats.findall("subconta"):
                    sub_entry = self._subconta_to_entry(sub, period)
                    if sub_entry is not None:
                        entries.append(sub_entry)
            else:
                entry = self._conta_to_entry(conta, period)
                if entry is not None:
                    entries.append(entry)

        return entries

    # ------------------------------------------------------------------
    # Fluxo de caixa parser
    # ------------------------------------------------------------------

    def parse_fluxo_caixa(self) -> List[AccountEntry]:
        """Parse fluxo de caixa XML (<atividade> elements)."""
        self.detect_encoding()
        tree = ET.parse(str(self.file_path))
        root = tree.getroot()

        period = self._extract_period(root)

        entries: List[AccountEntry] = []
        for atividade in root.iter("atividade"):
            codigo = (atividade.findtext("codigo") or "").strip()
            descricao = (atividade.findtext("descricao") or "").strip()
            valor = self._parse_decimal(atividade.findtext("valor"))
            periodo_text = (atividade.findtext("periodo") or period).strip()

            entries.append(
                AccountEntry(
                    code=codigo,
                    description=descricao,
                    opening_balance=Decimal("0"),
                    total_debits=Decimal("0"),
                    total_credits=Decimal("0"),
                    closing_balance=valor,
                    period=periodo_text,
                )
            )

        return entries

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_period(root: ET.Element) -> str:
        empresa = root.find("empresa")
        if empresa is not None:
            el = empresa.find("periodo")
            if el is not None and el.text:
                return el.text.strip()
        return ""

    def _conta_to_entry(self, conta: ET.Element, period: str) -> Optional[AccountEntry]:
        codigo = (conta.findtext("codigo") or "").strip()
        descricao = (conta.findtext("descricao") or "").strip()

        opening = self._parse_decimal(conta.findtext("saldo_inicial"))
        closing_final = conta.findtext("saldo_final")
        closing_saldo = conta.findtext("saldo")

        if closing_final is not None:
            closing = self._parse_decimal(closing_final)
        elif closing_saldo is not None:
            closing = self._parse_decimal(closing_saldo)
        else:
            closing = Decimal("0")

        return AccountEntry(
            code=codigo,
            description=descricao,
            opening_balance=opening,
            total_debits=Decimal("0"),
            total_credits=Decimal("0"),
            closing_balance=closing,
            period=period,
        )

    def _subconta_to_entry(self, sub: ET.Element, period: str) -> Optional[AccountEntry]:
        codigo = (sub.findtext("codigo") or "").strip()
        descricao = (sub.findtext("descricao") or "").strip()
        saldo = self._parse_decimal(sub.findtext("saldo"))

        return AccountEntry(
            code=codigo,
            description=descricao,
            opening_balance=Decimal("0"),
            total_debits=Decimal("0"),
            total_credits=Decimal("0"),
            closing_balance=saldo,
            period=period,
        )
