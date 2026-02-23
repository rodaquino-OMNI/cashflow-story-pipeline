# ADR-001: Python Pipeline over Node.js/React

## Status
Accepted

## Date
2026-02-23

## Context
The existing EnterpriseCashFlow codebase is a React 18 SPA with 15,000+ lines of JavaScript, 1,010 tests (87 failing), and multi-provider AI integration. The actual business need is automated batch processing of ERP XML exports into CashFlow Story reports. The React app requires manual browser interaction, cannot access local files directly, and cannot run on a schedule.

## Decision
Build the pipeline in Python 3.11+ using pandas, lxml, openpyxl, and the Anthropic SDK.

**Rationale:**
- pandas is the gold standard for financial data manipulation
- lxml/ElementTree provide mature, battle-tested XML parsing
- openpyxl generates Excel with conditional formatting (traffic lights)
- Python is the language of choice for data pipelines and automation
- Easy scheduling via cron, systemd, or file watchers
- The Anthropic Python SDK is first-class
- Smaller codebase: ~2,000 focused lines vs 15,000+ in React

## Consequences

### Positive
- ~2,000 lines of focused code vs 15,000+ in React
- Native file system access for ERP XML ingestion
- Easy automation (cron, watchdog, CLI)
- Mature financial data ecosystem (pandas, numpy)
- Simpler testing (pure functions, no DOM mocking)
- Much lower cognitive load for new contributors

### Negative
- Existing calculations.js (~1,000 lines) must be ported to Python
- Team may need Python familiarity
- Existing React UI work is not directly reusable

### Risks
- Porting financial formulas introduces regression risk → mitigated by comprehensive test fixtures with known outputs from calculations.js
- Python ecosystem fragmentation → mitigated by pinned versions in requirements and lock file approach
