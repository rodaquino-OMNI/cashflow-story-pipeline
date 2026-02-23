# ADR-004: Configuration-Driven Account Mapping

## Status
Accepted

## Date
2026-02-23

## Context
Different companies use different charts of accounts. AUSTA Group has specific needs: account 4.2 (administrative expenses) contains R$33M that should be reclassified to 4.1 (service costs) because much of admin is actually direct service delivery. Hardcoding account mappings makes the system single-company. The CashFlow Story methodology requires mapping raw accounts to 4 Chapters (Profitability, Working Capital, Other Capital, Funding). Supporting unlimited companies without code changes is a core requirement.

## Decision
Use YAML configuration files per company to map ERP account codes to CashFlow Story chapters.

**Key features:**
- Wildcard matching: `"3.1.*"` matches all revenue sub-accounts
- Reclassifications: explicitly move accounts between chapters with audit trail
- Exclusions: ignore already-reclassified accounts
- Industry-specific threshold overrides (healthcare vs manufacturing vs retail)
- Subcategories: hospital AR by payer type (Operadoras/SUS/Particular)
- Power of One sensitivity settings per company

**Example flow:**
```yaml
account_mapping:
  cogs:
    accounts: ["4.1"]
    reclassifications:
      - from: "4.2.01"  # Personnel costs
        to: "4.1"       # Reclassify to service costs
        description: "Hospital nursing staff are direct service labor"
```

## Consequences

### Positive
- New company = new YAML file, zero code changes
- Reclassification logic is transparent and auditable
- Config version control via git (every change tracked)
- Non-developers can adjust mappings after training
- Easy A/B testing: create alternate configs without forking codebase
- Supports unlimited companies without touching Python code

### Negative
- YAML syntax errors can be hard to debug (wrong indentation, quote issues)
- Complex mapping rules may be hard to express in YAML
- No validation until runtime (typos in account numbers not caught until processing)

### Risks
- Incorrect mapping produces wrong financials → mitigated by:
  1. Validation step that checks all material accounts are mapped
  2. Balance sheet equation validation (Assets = Liabilities + Equity)
  3. Comparison report showing before/after reclassifications
  4. Sample output review before first run

## Implementation
- config/companies/<name>.yaml per company
- Schema validation via Pydantic ConfigModel
- Unmapped account detection and reporting
- Override mechanism for thresholds (inherits from default.yaml)
