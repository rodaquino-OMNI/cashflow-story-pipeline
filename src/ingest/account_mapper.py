"""Account mapping from ERP codes to financial categories."""

from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from src.models import AccountEntry, MappedData

# Maps YAML config keys → MappedData field names
_CATEGORY_FIELD_MAP: dict[str, str] = {
    "revenue": "gross_revenue",
    "deductions": "returns_deductions",
    "cogs": "cogs",
    "operating_expenses": "operating_expenses",
    "financial_revenue": "financial_income",
    "financial_expenses": "financial_expenses",
    "accounts_receivable": "accounts_receivable",
    "inventory": "inventory",
    "accounts_payable": "accounts_payable",
    "fixed_assets": "ppe_gross",
    "short_term_debt": "short_term_debt",
    "long_term_debt": "long_term_debt",
    "equity": "shareholders_equity",
    "cash": "cash",
}


class AccountMapper:
    """Maps ERP account codes to financial categories (Chapter 1-4)."""

    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        self.raw_config: dict[str, Any] = {}
        self.categories: dict[str, dict[str, Any]] = {}
        self.reclassifications: list[dict[str, str]] = []
        self.exclusions: set = set()
        # Flat mapping: account_prefix -> category_key (e.g. "3.1" -> "revenue")
        self.mapping: dict[str, str] = {}
        self.company_name: str = ""
        self.load_config()

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def load_config(self) -> None:
        """Load and parse the YAML mapping configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path, encoding="utf-8") as fh:
            self.raw_config = yaml.safe_load(fh)

        self.company_name = self.raw_config.get("company", {}).get("name", "")

        acct_map = self.raw_config.get("account_mapping", {})
        for category_key, cfg in acct_map.items():
            if not isinstance(cfg, dict):
                continue
            prefixes = cfg.get("accounts", [])
            excludes = cfg.get("exclude", [])
            reclasses = cfg.get("reclassifications", [])

            self.categories[category_key] = {
                "prefixes": prefixes,
                "excludes": excludes,
            }

            # Populate flat mapping: each prefix -> category_key
            for prefix in prefixes:
                self.mapping[prefix] = category_key

            # Populate exclusions set
            for ex in excludes:
                self.exclusions.add(ex)

            for rc in reclasses:
                self.reclassifications.append(
                    {"from": rc["from"], "to": rc["to"]}
                )
                # Reclassified sources also map to the target category
                self.mapping[rc["from"]] = rc["to"]

    # ------------------------------------------------------------------
    # Account mapping
    # ------------------------------------------------------------------

    def map_accounts(
        self,
        accounts: list[AccountEntry],
        period: str,
    ) -> MappedData:
        """Map raw AccountEntry list into aggregated MappedData."""
        if not self.categories:
            self.load_config()

        # Step 1: apply reclassifications — change the effective code
        effective: dict[str, str] = {}
        for entry in accounts:
            new_code = entry.code
            for rc in self.reclassifications:
                if entry.code == rc["from"] or entry.code.startswith(rc["from"] + "."):
                    new_code = rc["to"]
                    break
            effective[entry.code] = new_code

        # Step 2: aggregate by category
        totals: dict[str, Decimal] = {k: Decimal("0") for k in self.categories}

        for entry in accounts:
            ecode = effective[entry.code]
            matched = False
            for cat_key, cat_cfg in self.categories.items():
                excludes = cat_cfg["excludes"]
                if any(entry.code == ex or entry.code.startswith(ex + ".") for ex in excludes):
                    continue
                for prefix in cat_cfg["prefixes"]:
                    if ecode == prefix or ecode.startswith(prefix + "."):
                        totals[cat_key] += entry.closing_balance
                        matched = True
                        break
                if matched:
                    break

        # Step 3: build MappedData kwargs
        kwargs: dict[str, Any] = {
            "company": self.company_name,
            "period": period,
        }
        for cat_key, field_name in _CATEGORY_FIELD_MAP.items():
            if cat_key in totals:
                kwargs[field_name] = totals[cat_key]

        # Derived values
        gross_rev = kwargs.get("gross_revenue", Decimal("0"))
        deductions = kwargs.get("returns_deductions", Decimal("0"))
        net_rev = gross_rev + deductions
        kwargs["net_revenue"] = net_rev

        cogs = kwargs.get("cogs", Decimal("0"))
        kwargs["gross_profit"] = net_rev + cogs

        opex = kwargs.get("operating_expenses", Decimal("0"))
        kwargs["ebitda"] = kwargs["gross_profit"] + opex

        kwargs["ebit"] = kwargs["ebitda"] + kwargs.get("depreciation_amortization", Decimal("0"))

        fin_income = kwargs.get("financial_income", Decimal("0"))
        fin_expense = kwargs.get("financial_expenses", Decimal("0"))
        kwargs["ebt"] = kwargs["ebit"] + fin_income + fin_expense

        return MappedData(**kwargs)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_mapping(self, mapped: MappedData) -> tuple[bool, list[str]]:
        """Validate mapped data against business rules."""
        messages: list[str] = []
        is_valid = True

        if mapped.gross_revenue <= Decimal("0"):
            messages.append("WARN: gross_revenue <= 0")
            is_valid = False

        if mapped.gross_revenue != Decimal("0") and abs(mapped.cogs) > abs(mapped.gross_revenue):
            messages.append("WARN: |COGS| exceeds |gross_revenue|")

        if mapped.accounts_receivable < Decimal("0"):
            messages.append("WARN: accounts_receivable < 0")

        if mapped.shareholders_equity == Decimal("0"):
            messages.append("WARN: shareholders_equity is zero")
            is_valid = False

        return is_valid, messages
