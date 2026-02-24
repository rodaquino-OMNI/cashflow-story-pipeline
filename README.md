# CashFlow Story Pipeline

Automated financial analysis pipeline that transforms ERP data into board-ready CashFlow Story insights using Alan Miltz's methodology.

**Problem:** Companies growing revenue while cash evaporates (the "40% Rule"). Financial controllers spend 5-10 days manually building reports from ERP exports.

**Solution:** Drop an XML/XLSX from your ERP into the pipeline and get AI-powered CashFlow Story analysis in under 5 minutes.

## Architecture

```
ERP XML/XLSX --> [Ingest & Map] --> [Calculate 4 Chapters] --> [Claude AI] --> Reports
                                                                                ├── XLSX (traffic-light grading)
                                                                                ├── HTML (interactive dashboard)
                                                                                ├── PDF  (board meeting ready)
                                                                                └── JSON (API / integrations)
```

Built on Alan Miltz's **CashFlow Story** methodology (from Verne Harnish's *Scaling Up*):

| Concept | Description |
|---------|-------------|
| **4 Chapters** | Profitability, Working Capital, Other Capital, Funding |
| **Power of One** | 7 levers showing how a 1% change impacts profit, cash, and value |
| **Cash Quality** | G/A/B grading for every key metric |
| **Three Big Measures** | Net CF, Operating CF, Marginal CF |
| **Marginal Cash Flow** | Does growth help or hurt your cash position? |

---

## Prerequisites

- **Python 3.11+** (tested on 3.11 and 3.12)
- **pip** (comes with Python)
- **Anthropic API key** (for AI narrative generation — optional, pipeline works without it)

### System dependencies (PDF generation only)

PDF reports require WeasyPrint system libraries. Skip this if you only need XLSX/HTML/JSON output.

```bash
# macOS
brew install pango gdk-pixbuf libffi

# Ubuntu / Debian
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Or skip PDF and use --format excel --format html
```

---

## Installation

### Option A: Local install (recommended for development)

```bash
# 1. Clone the repository
git clone https://github.com/rodaquino-OMNI/cashflow-story-pipeline.git
cd cashflow-story-pipeline

# 2. Create virtual environment and install
make install
# Or manually:
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configure environment
cp config/env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Verify installation
make test
```

### Option B: Docker (recommended for production)

```bash
# 1. Clone and configure
git clone https://github.com/rodaquino-OMNI/cashflow-story-pipeline.git
cd cashflow-story-pipeline
cp config/env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Build and run
docker compose up --build

# Or build manually
docker build -t cashflow-story-pipeline .
docker run --env-file .env -v ./input:/app/input -v ./output:/app/output \
  cashflow-story-pipeline run \
  --input /app/input/balancete.xml \
  --config config/companies/austa.yaml \
  --output /app/output
```

---

## Configuration

### Environment variables

Copy the example file and fill in your values:

```bash
cp config/env.example .env
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | For AI narratives | — | Get yours at [console.anthropic.com](https://console.anthropic.com/) |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-6` | Claude model to use |
| `ANTHROPIC_TEMPERATURE` | No | `0.3` | AI temperature (0.0-1.0) |

> The pipeline has **graceful degradation** — if no API key is set or the AI call fails, it logs a warning and continues without AI insights. Use `--no-ai` to skip AI explicitly.

### Company configuration

Each company needs a YAML config file that maps ERP account codes to CashFlow Story categories.

```bash
# Use the AUSTA template as a starting point
cp config/companies/austa.yaml config/companies/mycompany.yaml
```

The config file contains:

```yaml
company:
  name: "My Company Name"
  cnpj: "00.000.000/0001-00"

account_mapping:
  revenue:
    label: "Receita"
    accounts: ["3.1"]             # ERP account code prefixes
  deductions:
    label: "Deduções"
    accounts: ["3.2"]
  cogs:
    label: "Custo de Mercadoria"
    accounts: ["4.1"]
  operating_expenses:
    label: "Despesas Operacionais"
    accounts: ["4.2"]
  # ... more categories (cash, AR, AP, debt, equity, etc.)

reclassifications:                 # Move accounts between categories
  - from: "4.2.01"
    to: "cogs"
  - from: "4.2.02"
    to: "cogs"

exclusions:                        # Exclude from operating_expenses after reclassification
  - "4.2.01"
  - "4.2.02"
```

Validate your config before running:

```bash
cashflow validate --config config/companies/mycompany.yaml
```

### Threshold configuration

Cash quality grading thresholds are in `config/thresholds.yaml`. Defaults follow Alan Miltz's benchmarks. Override per-industry if needed.

---

## Usage

### CLI commands

```bash
# Activate virtual environment (if not using Docker)
source .venv/bin/activate

# Run analysis on an ERP export
cashflow run \
  --input /path/to/balancete.xml \
  --config config/companies/austa.yaml \
  --output ./output/ \
  --format excel --format html --format json

# Run without AI narrative (calculations only)
cashflow run \
  --input /path/to/balancete.xml \
  --config config/companies/austa.yaml \
  --output ./output/ \
  --no-ai

# Watch folder for new ERP files (auto-process)
cashflow watch \
  --folder /erp/exports/ \
  --config config/companies/austa.yaml \
  --output ./output/ \
  --interval 60

# Validate a company configuration
cashflow validate --config config/companies/austa.yaml

# Show help
cashflow --help
cashflow run --help
```

### CLI options reference

| Command | Option | Description |
|---------|--------|-------------|
| `run` | `--input, -i` | Path to ERP data file (XML or XLSX) — **required** |
| `run` | `--config, -c` | Company config file path (default: `config.yaml`) |
| `run` | `--output, -o` | Output directory (default: `output/`) |
| `run` | `--format, -f` | Output format: `excel`, `html`, `pdf`, `json` (repeatable) |
| `run` | `--no-ai` | Skip AI narrative generation |
| `run` | `--verbose, -v` | Enable debug logging |
| `watch` | `--folder, -f` | Folder to watch for ERP files — **required** |
| `watch` | `--interval` | Check interval in seconds (default: 60) |
| `validate` | `--config, -c` | Config file to validate — **required** |

### Using with Docker Compose

```bash
# Place your ERP file in ./input/
mkdir -p input output
cp /path/to/balancete.xml input/

# Run with default config (austa)
docker compose up

# Run with custom config
docker compose run pipeline run \
  --input /app/input/balancete.xml \
  --config config/companies/mycompany.yaml \
  --output /app/output \
  --format json
```

### Python API

```python
from dotenv import load_dotenv
load_dotenv()

from src.pipeline import CashFlowStoryPipeline

pipeline = CashFlowStoryPipeline(
    config_name="austa",
    config_path="config/companies/austa.yaml"
)

result = pipeline.run(
    input_path="data/balancete.xml",
    output_path="output/",
    options={
        "no_ai": False,
        "format": ["excel", "html", "json"],
    }
)

# Access results programmatically
print(f"Company: {result.company}")
print(f"Periods: {len(result.periods)}")
print(f"Power of One levers: {len(result.power_of_one)}")
print(f"Cash quality metrics: {len(result.cash_quality)}")
print(f"AI insights: {result.ai_insights[:200] if result.ai_insights else 'N/A'}")
```

---

## Output formats

### XLSX (Excel)

Traffic-light color-coded workbook with 10 sheets:

- Income Statement (DRE)
- Working Capital analysis
- Other Capital analysis
- Funding structure
- Cash Flow Statement
- Power of One (7 levers)
- Cash Quality (G/A/B grades)
- Financial Ratios
- Marginal Cash Flow
- Three Big Measures

### HTML (Dashboard)

Interactive single-page dashboard with Chart.js visualizations, expandable chapters, and KPI cards. Opens in any browser.

### PDF (Board report)

Print-ready document formatted for board meetings. Requires WeasyPrint system dependencies.

### JSON (API)

Machine-readable output with all calculated fields, Power of One levers, cash quality metrics, and AI insights. Suitable for downstream integrations.

---

## Pipeline stages

The pipeline runs 6 stages in sequence, each producing an immutable result:

| Stage | Module | Description |
|-------|--------|-------------|
| 1. Ingest | `src/ingest/xml_parser.py` | Parse ERP XML/XLSX with XXE protection and encoding detection |
| 2. Map | `src/ingest/account_mapper.py` | Map ERP account codes to CashFlow Story categories via YAML config |
| 3. Calculate | `src/calc/` | Run all calculations: income statement, working capital, cash flow, ratios, Power of One, cash quality, marginal CF |
| 4. Compare | `src/calc/` | Multi-period variance analysis (when multiple periods provided) |
| 5. Synthesize | `src/ai/analyst.py` | Generate AI narrative insights using Claude (skippable with `--no-ai`) |
| 6. Export | `src/output/` | Render reports in requested formats (XLSX, HTML, PDF, JSON) |

Full audit trail is preserved at every stage.

---

## Deployment

### Docker (recommended)

```bash
# Build the image
docker build -t cashflow-story-pipeline .

# Run a one-off analysis
docker run --rm \
  --env-file .env \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  cashflow-story-pipeline run \
  --input /app/input/balancete.xml \
  --config config/companies/austa.yaml \
  --output /app/output \
  --format excel --format html --format json

# Run with Docker Compose (mounts input/output automatically)
docker compose up
```

### Docker Compose for automated processing

```yaml
# docker-compose.yml is included in the repo
services:
  pipeline:
    build: .
    volumes:
      - ./input:/app/input
      - ./output:/app/output
      - ./.env:/app/.env:ro
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    command: run --input /app/input --output /app/output --config config/companies/austa.yaml
```

### Cron job (bare metal)

```bash
# Process ERP exports every hour
0 * * * * cd /opt/cashflow-story-pipeline && \
  .venv/bin/python -m src.main run \
  --input /erp/exports/latest.xml \
  --config config/companies/austa.yaml \
  --output /reports/ \
  --format excel --format html >> /var/log/cashflow.log 2>&1
```

### File watcher (continuous)

```bash
# Run as a systemd service or in tmux/screen
cashflow watch \
  --folder /erp/exports/ \
  --config config/companies/austa.yaml \
  --output /reports/ \
  --interval 60
```

### CI/CD

GitHub Actions CI is included (`.github/workflows/ci.yml`):

- Runs on push/PR to `main`
- Tests on Python 3.11 and 3.12
- Lints with ruff
- Reports test coverage

---

## Development

### Quick commands

```bash
make install       # Create venv, install all deps
make test          # Run full test suite (196 tests)
make test-cov      # Tests with coverage report
make lint          # Check code style (ruff)
make lint-fix      # Auto-fix lint issues
make typecheck     # Run mypy type checker
make clean         # Remove build artifacts and caches
```

### Running tests directly

```bash
# Full suite
python -m pytest tests/ -v --tb=short

# With coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Single test file
python -m pytest tests/test_power_of_one.py -v

# Single test
python -m pytest tests/test_cash_quality.py::TestCashQuality::test_good_gross_margin -v
```

### Test coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| `src/calc/` (all calculations) | 50+ | 95-100% |
| `src/ingest/xml_parser.py` | 33 | 78% |
| `src/ingest/account_mapper.py` | 50 | 95% |
| `src/ai/analyst.py` | 40 | 99% |
| `src/output/` (all generators) | 30 | 78-98% |
| `src/pipeline.py` (integration) | 15 | 66% |
| **Total** | **196** | **71%** |

### Adding a new calculation module

1. Create the module in `src/calc/` as a pure function
2. Accept `PeriodResult` (or `MappedData`), return updated `PeriodResult`
3. Use `Decimal` for all arithmetic (no `float`)
4. Add tests in `tests/test_<module>.py`
5. Wire it into the calculation chain in `src/calc/__init__.py`

---

## Project structure

```
cashflow-story-pipeline/
├── config/
│   ├── companies/
│   │   └── austa.yaml          # AUSTA account mapping (reference config)
│   ├── default.yaml            # Global pipeline defaults
│   ├── thresholds.yaml         # G/A/B grading thresholds
│   └── env.example             # Environment variable template
├── src/
│   ├── main.py                 # CLI entry point (Click)
│   ├── pipeline.py             # 6-stage orchestrator
│   ├── ingest/
│   │   ├── xml_parser.py       # ERP XML parser (defusedxml, XXE-safe)
│   │   ├── xlsx_parser.py      # ERP Excel parser
│   │   └── account_mapper.py   # YAML-driven account mapping
│   ├── models/
│   │   ├── financial_data.py   # MappedData, PeriodResult, AnalysisResult
│   │   └── cashflow_story.py   # PowerOfOneLever, CashQualityMetric, etc.
│   ├── calc/
│   │   ├── income_statement.py # DRE waterfall + margins
│   │   ├── working_capital.py  # DSO, DIO, DPO, CCC, WC investment
│   │   ├── balance_sheet.py    # PP&E, intangibles, other capital
│   │   ├── cash_flow.py        # OCF, ICF, FCF, net CF (indirect method)
│   │   ├── ratios.py           # Current, quick, D/E, ROE, ROA, ROCE
│   │   ├── brazilian_tax.py    # IRPJ + CSLL with surtax thresholds
│   │   ├── power_of_one.py     # 7 levers: price, volume, COGS, overhead, AR, inv, AP
│   │   ├── cash_quality.py     # 6 metrics with G/A/B grading
│   │   └── marginal_cashflow.py# FCF% vs WC% growth analysis
│   ├── ai/
│   │   ├── analyst.py          # Claude API integration (Anthropic SDK)
│   │   └── prompts.py          # Portuguese prompt templates (6 sections)
│   ├── output/
│   │   ├── excel_report.py     # XLSX with traffic-light formatting
│   │   ├── html_dashboard.py   # Single-page HTML + Chart.js
│   │   ├── pdf_report.py       # WeasyPrint PDF for board meetings
│   │   └── json_export.py      # JSON with Decimal serialization
│   └── utils/
│       ├── formatters.py       # BRL currency, percentage formatters
│       ├── validators.py       # Input validation helpers
│       └── logger.py           # Structured logging setup
├── tests/
│   ├── conftest.py             # Shared fixtures (AUSTA Q1/Q2 data)
│   ├── fixtures/
│   │   └── sample_balancete.xml# Reference ERP XML file
│   ├── test_brazilian_tax.py
│   ├── test_power_of_one.py
│   ├── test_cash_quality.py
│   ├── test_xml_parser.py
│   ├── test_account_mapper.py
│   ├── test_analyst.py
│   ├── test_output.py
│   └── test_pipeline.py
├── .github/workflows/ci.yml   # GitHub Actions (pytest + ruff + coverage)
├── Dockerfile                  # Python 3.11-slim + WeasyPrint deps
├── docker-compose.yml          # One-command deployment
├── Makefile                    # Dev shortcuts
├── pyproject.toml              # Project metadata, deps, tool config
└── .dockerignore
```

---

## Key design decisions

| Decision | Rationale |
|----------|-----------|
| **Python 3.11+ pipeline** | pandas + lxml + openpyxl are unbeatable for financial data |
| **Batch over web app** | ERP data is structured; automation beats interaction |
| **Decimal everywhere** | Financial calculations require exact precision (no float) |
| **Config-driven mapping** | New company = new YAML file, zero code changes |
| **CashFlow Story native** | 4 Chapters, Power of One, Cash Quality as first-class concepts |
| **Immutable pipeline stages** | Full audit trail, reproducible results, independently testable |
| **defusedxml** | XXE protection for untrusted XML input |
| **Graceful AI degradation** | Pipeline works without API key (calculations always run) |
| **Pydantic v2** | Type-safe models with field validation and serialization |
| **Portuguese (pt-BR)** | All labels, prompts, and narratives in Brazilian Portuguese |

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
# Check your .env file exists and has the key
cat .env | grep ANTHROPIC_API_KEY

# Or run without AI
cashflow run --input data.xml --config config/companies/austa.yaml --no-ai
```

### "FileNotFoundError: Config not found"

```bash
# Pass the full path to the config file
cashflow run --input data.xml --config config/companies/austa.yaml --output ./output/
```

### "WeasyPrint / PDF generation fails"

Install system dependencies or skip PDF format:

```bash
# macOS
brew install pango gdk-pixbuf libffi

# Or just use other formats
cashflow run --input data.xml --config config/companies/austa.yaml --format excel --format html
```

### "Docker build fails"

```bash
# Ensure Docker is running
docker info

# Build with verbose output
docker build --no-cache -t cashflow-story-pipeline .
```

### Tests fail after changes

```bash
# Run full test suite
make test

# Run with verbose output to see failures
python -m pytest tests/ -v --tb=long
```

---

## License

MIT
