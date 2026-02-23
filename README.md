# CashFlow Story Pipeline

Automated financial analysis pipeline that transforms ERP data into board-ready CashFlow Story insights.

**Problem:** Companies growing revenue while cash evaporates (the "40% Rule"). Financial controllers spend 5-10 days manually building reports from ERP exports.

**Solution:** Drop XML from your ERP into a folder → get AI-powered CashFlow Story analysis in under 5 minutes.

## Architecture

```
ERP XML/XLSX → [Ingest & Map] → [Calculate 4 Chapters] → [Claude AI Analysis] → Reports
                                                                                   ├── XLSX (traffic lights)
                                                                                   ├── HTML (dashboard)
                                                                                   ├── PDF  (board meeting)
                                                                                   └── JSON (integrations)
```

Built on Alan Miltz's **CashFlow Story** methodology (from Verne Harnish's *Scaling Up*):

- **4 Chapters:** Profitability → Working Capital → Other Capital → Funding
- **Power of One:** 7 levers that improve profit, cash, and business value
- **Cash Quality:** G/A/B grading for every key metric
- **Marginal Cash Flow:** Does growth help or hurt your cash?

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url>
cd cashflow-story-pipeline
make install

# 2. Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 3. Run with sample data
make run

# 4. Run without AI (calculations only)
make run-no-ai
```

## Usage

```bash
# Process ERP export
cashflow run --input /path/to/xml --config austa --output ./reports/

# Watch folder for new files (auto-process)
cashflow watch --folder /erp/exports/ --config austa

# Validate configuration
cashflow validate --config austa

# Run without AI analysis
cashflow run --input /path/to/xml --config austa --no-ai
```

## Adding a New Company

Create a YAML config file — no code changes needed:

```bash
cp config/companies/austa.yaml config/companies/newclient.yaml
# Edit account_mapping to match client's chart of accounts
cashflow run --input /data/newclient/ --config newclient
```

## Project Structure

```
cashflow-story-pipeline/
├── config/              # Company configs (YAML)
│   ├── default.yaml     # Global defaults
│   ├── thresholds.yaml  # G/A/B grading thresholds
│   └── companies/       # Per-company account mappings
├── src/
│   ├── ingest/          # XML/XLSX parsing + account mapping
│   ├── models/          # Pydantic data models
│   ├── calc/            # Financial calculations (pure functions)
│   ├── ai/              # Claude integration + prompts
│   ├── output/          # Report generation (XLSX/HTML/PDF/JSON)
│   └── utils/           # Formatters, validators, logging
├── tests/               # pytest test suite
├── templates/           # Jinja2 report templates
├── scripts/             # Automation (file watcher, cron)
└── docs/                # ADRs, PRD, Technical Spec
```

## Documentation

- [Product Requirements](docs/PRD.md) — What we're building and why
- [Technical Specification](docs/TECHNICAL_SPEC.md) — How every module works
- [Architecture Decision Records](docs/ADR/) — Why we chose this approach

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Python pipeline | pandas + lxml + openpyxl are unbeatable for financial data |
| Batch over web app | ERP data is structured; automation beats interaction |
| Claude only (v1) | Best at financial analysis + Portuguese; add providers later |
| Config-driven mapping | New company = new YAML, zero code changes |
| CashFlow Story native | 4 Chapters, Power of One, Cash Quality as first-class features |
| Immutable stages | Full audit trail, reproducible, independently testable |

See [docs/ADR/](docs/ADR/) for detailed rationale on each decision.

## Development

```bash
make install       # Create venv, install deps
make test          # Run tests
make lint          # Check code style (ruff)
make typecheck     # Run mypy
make test-cov      # Tests with coverage report
```

## Implementation Roadmap

| Phase | What | Timeline |
|-------|------|----------|
| M1 | Foundation: models, config, Brazilian tax | Week 1 |
| M2 | Calculations: all calc/ modules ported + tested | Week 2 |
| M3 | Ingestion: XML parser + account mapper | Week 3 |
| M4 | AI: Claude integration with Portuguese prompts | Week 3 |
| M5 | Reports: XLSX + HTML + PDF generation | Week 4 |
| M6 | Automation: file watcher, CLI, cron | Week 4 |
| M7 | Validation: end-to-end with real AUSTA data | Week 5 |

## License

MIT
