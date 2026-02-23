# Technical Specification: CashFlow Story Pipeline

**Version:** 1.0  
**Date:** 2026-02-23  
**Architecture:** Python 3.11+ Batch Processing Pipeline  
**Status:** Design Ready for Implementation

---

## 1. System Architecture

### High-Level Data Flow

```
┌─────────────────┐
│  ERP XML/XLSX   │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│   Ingest & Validation    │
│  (xml_parser.py          │
│   xlsx_parser.py)        │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Account Mapping        │
│  (account_mapper.py)     │
│  - Reclassifications     │
│  - Balance sheet check   │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Financial Calculation   │
│  (calc/*.py modules)     │
│  - 4 Chapters            │
│  - Power of One          │
│  - Cash Quality          │
│  - Marginal CF           │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   AI Analysis            │
│  (analyst.py)            │
│  - Claude integration    │
│  - Narrative generation  │
│  - Optional, graceful    │
│    fallback              │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Report Generation       │
│  (output/*.py modules)   │
│  ├─ XLSX (openpyxl)      │
│  ├─ HTML (Jinja2)        │
│  ├─ PDF (WeasyPrint)     │
│  └─ JSON (dataclasses)   │
└────────┬─────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Output Files                      │
│   ├─ reports/cashflow_2025-02.xlsx  │
│   ├─ reports/board_2025-02.pdf      │
│   ├─ reports/dashboard.html         │
│   └─ reports/analysis.json          │
└─────────────────────────────────────┘
```

### Key Principles

1. **Immutable stages:** Each stage produces new data, doesn't mutate input
2. **Pure functions:** Calculations have no side effects
3. **Audit trail:** Every transformation logged
4. **Graceful degradation:** Pipeline completes even if AI fails
5. **Configuration-driven:** No code changes for new companies

---

## 2. Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Runtime | Python | 3.11+ | Mature, type-safe, data science standard |
| Data models | Pydantic | 2.0+ | Type validation, JSON serialization, IDE support |
| Data manipulation | pandas | 2.0+ | Industry standard for financial data, fast |
| XML parsing | lxml | 5.0+ | Battle-tested, C accelerated, handles malformed |
| Excel generation | openpyxl | 3.1+ | Write Excel with formatting, charts, no dependencies |
| Templates | Jinja2 | 3.1+ | Flexible report templating, works for HTML |
| HTML→PDF | WeasyPrint | 60+ | Deterministic, CSS-based, no phantom/headless browser |
| Charting | matplotlib | 3.8+ | Static charts for reports, print-quality |
| Data viz (web) | Chart.js | 4.4+ | Lightweight JS library for HTML dashboard |
| AI/LLM | anthropic SDK | 0.40+ | Official Anthropic client, structured output |
| Config | PyYAML | 6.0+ | Human-readable configuration files |
| CLI | Click | 8.1+ | Type-safe CLI with validation |
| Logging | structlog | 24.0+ | Structured JSON logs, production-ready |
| File watching | watchdog | 4.0+ | Cross-platform file system events |
| Environment | python-dotenv | 1.0+ | Load API keys from .env (not in git) |
| Testing | pytest | 8.0+ | Test runner, fixtures, mocking |
| Coverage | pytest-cov | 5.0+ | Coverage measurement, HTML reports |
| Linting | ruff | 0.4+ | Fast Python linter, auto-format |
| Type checking | mypy | 1.10+ | Static type analysis, strict mode |

---

## 3. Module Architecture

### 3.1 Ingest Layer

**Path:** `src/ingest/`

#### xml_parser.py

**Purpose:** Parse TOTVS ERP XML export (balancete format)

**Function signature:**
```python
def parse_xml(filepath: str, encoding: str = "utf-8") -> list[AccountEntry]:
    """
    Parse TOTVS balancete XML export.
    
    Args:
        filepath: Path to XML file
        encoding: File encoding (default utf-8, fallback latin1)
    
    Returns:
        List of AccountEntry objects (parsed, not mapped)
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If XML structure is invalid
    """
```

**Input format (sample):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<root>
  <balancete>
    <conta>
      <codigo>1.1.01</codigo>  <!-- Account code -->
      <nome>Caixa</nome>        <!-- Account name -->
      <saldo_anterior>100000.00</saldo_anterior>
      <debitos>50000.00</debitos>
      <creditos>30000.00</creditos>
      <saldo_atual>120000.00</saldo_atual>
    </conta>
    <!-- more accounts... -->
  </balancete>
</root>
```

**Output:** `list[AccountEntry]` where:
```python
@dataclass
class AccountEntry:
    code: str                 # "1.1.01"
    name: str                 # "Caixa"
    opening_balance: Decimal  # Previous month
    debits: Decimal           # Month transactions (debit side)
    credits: Decimal          # Month transactions (credit side)
    closing_balance: Decimal  # Current balance
    file_checksum: str        # SHA-256 of input file
    parsed_at: datetime       # Timestamp
```

#### xlsx_parser.py

**Purpose:** Fall back to XLSX if XML unavailable

**Function signature:**
```python
def parse_xlsx(filepath: str, sheet: str = "Balancete") -> list[AccountEntry]:
    """Parse Excel export from ERP."""
```

**Expected structure:** Columns: Code, Name, OpeningBalance, Debits, Credits, ClosingBalance

#### account_mapper.py

**Purpose:** Map accounts to 4 Chapters using YAML config

**Main function:**
```python
def map_accounts(
    entries: list[AccountEntry],
    config: CompanyConfig
) -> MappedData:
    """
    Reclassify and organize accounts into 4 Chapters.
    
    Handles:
    - Wildcard matching ("3.1.*" → all revenue accounts)
    - Reclassifications (move from one chapter to another)
    - Exclusions (ignore already-processed accounts)
    - Validation (balance sheet check)
    
    Returns:
        MappedData with all accounts organized
    
    Raises:
        ValueError: If balance sheet doesn't balance (>0.1%)
        ValidationError: If required accounts missing
    """
```

**Output:** `MappedData` (Pydantic model):
```python
class MappedData(BaseModel):
    company: str
    period: str                      # "2025-02"
    
    # Chapter 1: Profitability
    revenue: list[ChapterAccount]
    cogs: list[ChapterAccount]
    operating_expenses: list[ChapterAccount]
    
    # Chapter 2: Working Capital
    ar: list[ChapterAccount]
    inventory: list[ChapterAccount]
    ap: list[ChapterAccount]
    
    # Chapter 3: Other Capital
    fixed_assets: list[ChapterAccount]
    
    # Chapter 4: Funding
    short_term_debt: list[ChapterAccount]
    long_term_debt: list[ChapterAccount]
    equity: list[ChapterAccount]
    cash: list[ChapterAccount]
    
    # Audit trail
    unmapped_accounts: list[UnmappedAccount]
    reclassifications_applied: list[Reclassification]
    validation_checks: ValidationResult
```

---

### 3.2 Models Layer

**Path:** `src/models/`

#### financial_data.py

Core Pydantic models:

```python
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ChapterAccount(BaseModel):
    """Single account in a chapter."""
    code: str
    name: str
    amount: Decimal
    
class UnmappedAccount(BaseModel):
    """Account not matched to any chapter."""
    code: str
    name: str
    amount: Decimal
    
class Reclassification(BaseModel):
    """Audit trail of account movements."""
    from_account: str
    to_chapter: str
    amount: Decimal
    reason: str
    applied_at: datetime

class ChapterResults(BaseModel):
    """Single chapter calculations."""
    revenue: Decimal | None = None
    cogs: Decimal | None = None
    gross_profit: Decimal | None = None
    # ... more fields

class PeriodResult(BaseModel):
    """Complete financial calculations for one period."""
    company: str
    period: str                    # "2025-02"
    
    # Raw amounts
    chapter1: ChapterResults       # Profitability
    chapter2: WorkingCapitalResult # WC
    chapter3: OtherCapitalResult   # Fixed assets
    chapter4: FundingResult        # Debt & equity
    
    # Calculated metrics
    profitability: ProfitabilityMetrics
    working_capital: WorkingCapitalMetrics
    cash_quality: CashQualityGrades
    power_of_one: PowerOfOneTable
    marginal_cf: MarginalCashFlow
    
    # Metadata
    input_checksum: str            # SHA-256 of source data
    config_version_hash: str       # Config hash
    calculated_at: datetime
    
class AnalysisResult(BaseModel):
    """Final analysis with AI insights."""
    period_result: PeriodResult
    ai_narrative: str | None       # AI-generated insights
    ai_model: str | None           # "claude-sonnet-4-20250514"
    ai_tokens_used: int | None
    ai_cost: Decimal | None
    variance_analysis: VarianceAnalysis
```

#### cashflow_story.py

CashFlow Story-specific models:

```python
class CashQualityGrade(BaseModel):
    """G/A/B grade for a single metric."""
    metric: str                    # "gross_margin_pct"
    value: Decimal                 # 52.3
    good_threshold: Decimal        # 50
    average_threshold: Decimal     # 45
    grade: Literal["G", "A", "B"]  # Based on thresholds
    direction: Literal["higher_is_better", "lower_is_better"]
    label_pt: str                  # Portuguese label

class CashQualityGrades(BaseModel):
    """Dashboard of all G/A/B grades."""
    profitability: list[CashQualityGrade]
    working_capital: list[CashQualityGrade]
    other_capital: list[CashQualityGrade]
    funding: list[CashQualityGrade]

class LeverImpact(BaseModel):
    """Impact of one Power of One lever."""
    lever_name: str                # "Price", "Volume", "COGS", etc.
    change_magnitude: str          # "+1%", "-1%", "-1 day"
    impact_profit: Decimal         # R$ impact on net income
    impact_cash: Decimal           # R$ impact on operating CF
    impact_value: Decimal          # Enterprise value impact (6x multiple)

class PowerOfOneTable(BaseModel):
    """All 7 levers with impacts."""
    levers: list[LeverImpact]      # 7 items
    base_scenario: PeriodResult    # Baseline for comparison

class MarginalCashFlow(BaseModel):
    """GM% - WC% analysis."""
    gross_margin_pct: Decimal      # Chapter 1 output
    wc_as_pct_revenue: Decimal     # Chapter 2 output
    marginal_cf_pct: Decimal       # GM% - WC%
    interpretation: str            # "Positive: growth generates cash"
    recommendation: str            # "Target: > 5% for sustainable growth"
```

---

### 3.3 Calculation Layer

**Path:** `src/calc/`

All modules are pure functions (no side effects, no state).

#### profitability.py

```python
def calculate_profitability(mapped: MappedData) -> ProfitabilityMetrics:
    """
    Chapter 1: Profitability
    
    Gross Revenue
      - Deductions (taxes, returns)
      = Net Revenue
      - COGS
      = Gross Profit
      Gross Margin % = Gross Profit / Net Revenue
      
      - Operating Expenses (overhead)
      = EBIT
      EBIT Margin % = EBIT / Net Revenue
      Overhead % = Operating Expenses / Net Revenue
    
    Returns all metrics as Decimal (not float for accuracy)
    """
```

**Exported metrics:**
- Net Revenue (Receita Líquida)
- Gross Profit
- Gross Margin %
- Operating Expenses (Overhead)
- Overhead %
- EBIT (Operating Profit)
- EBIT Margin %

#### working_capital.py

```python
def calculate_working_capital(mapped: MappedData) -> WorkingCapitalMetrics:
    """
    Chapter 2: Working Capital
    
    AR Days = (Accounts Receivable / Daily Revenue)
    Inventory Days = (Inventory / Daily COGS)
    AP Days = (Accounts Payable / Daily COGS)
    CCC = AR Days + Inventory Days - AP Days
    WC Increase = (Current AR + Inv - AP) - (Prior AR + Inv - AP)
    WC as % Revenue = WC / Annual Revenue
    """
```

**Exported metrics:**
- Accounts Receivable (R$)
- AR Days
- Inventory (R$)
- Inventory Days
- Accounts Payable (R$)
- AP Days
- Cash Conversion Cycle
- Working Capital Investment
- WC as % Revenue

#### other_capital.py

```python
def calculate_other_capital(mapped: MappedData) -> OtherCapitalMetrics:
    """
    Chapter 3: Other Capital
    
    Fixed Assets (net of depreciation)
    Asset Turnover = Revenue / Total Assets
    """
```

#### funding.py

```python
def calculate_funding(mapped: MappedData) -> FundingMetrics:
    """
    Chapter 4: Funding
    
    Short-term debt, Long-term debt, Total debt
    Equity (book value)
    Debt-to-Equity Ratio = Total Debt / Equity
    Interest Coverage = EBIT / Interest Expense
    """
```

#### power_of_one.py

```python
def calculate_power_of_one(
    base: PeriodResult,
    config: CompanyConfig
) -> PowerOfOneTable:
    """
    7 Levers sensitivity analysis.
    
    For each lever (Price, Volume, COGS, Overhead, AR Days, Inventory Days, AP Days):
    - Calculate new financials with ±1% (or ±1 day for WC)
    - Impact on Operating Profit
    - Impact on Operating Cash Flow
    - Impact on Enterprise Value (using valuation_multiple from config)
    
    Valuation Multiple = 6.0x EBIT (default for healthcare)
    Enterprise Value = EBIT * Multiple
    """
    
    levers = {
        "Price": price_lever(base, config),           # +1%
        "Volume": volume_lever(base, config),         # +1%
        "COGS": cogs_lever(base, config),             # -1%
        "Overhead": overhead_lever(base, config),     # -1%
        "AR Days": ar_days_lever(base, config),       # -1 day
        "Inventory Days": inventory_lever(base, config), # -1 day
        "AP Days": ap_days_lever(base, config),       # +1 day
    }
    
    return PowerOfOneTable(levers=levers, base_scenario=base)
```

#### cash_quality.py

```python
def assign_grades(
    metrics: dict[str, Decimal],
    config: CompanyConfig
) -> CashQualityGrades:
    """
    Assign G/A/B grades to all metrics.
    
    For metric = "gross_margin_pct" with value 52%:
    - Config: good=50, average=45, direction=higher_is_better
    - Grade: G (52 >= 50)
    
    Returns dashboard of all grades.
    """
```

#### marginal_cashflow.py

```python
def calculate_marginal_cf(
    profitability: ProfitabilityMetrics,
    wc: WorkingCapitalMetrics
) -> MarginalCashFlow:
    """
    Marginal Cash Flow % = Gross Margin % - (WC as % Revenue)
    
    Interpretation:
    - > 0%: Growth generates cash (ideal)
    - = 0%: Growth is cash-neutral
    - < 0%: Growth consumes cash ("40% Rule trap")
    """
```

#### taxes.py

```python
def calculate_brazilian_taxes(
    ebit: Decimal,
    revenue: Decimal,
    config: CompanyConfig
) -> TaxCalculation:
    """
    Brazilian tax rules (v1: simplified, can refine later).
    
    IRPJ (Corporate Tax):
    - Base rate: 15%
    - Surtax: 10% on income > R$20K/month
    
    CSLL (Social Tax): 9% on EBIT
    
    Returns:
    - Effective tax rate
    - IRPJ amount
    - CSLL amount
    - Net income (EBIT - taxes)
    """
```

---

### 3.4 AI Layer

**Path:** `src/ai/`

#### analyst.py

```python
from anthropic import Anthropic

class CashFlowAnalyst:
    """Claude-based financial analyst."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    def analyze(
        self,
        period_result: PeriodResult,
        config: CompanyConfig,
        language: str = "pt-BR"
    ) -> AnalysisResult:
        """
        Generate AI-powered narrative analysis.
        
        Inputs:
        - All calculated metrics from period_result
        - Company context from config
        
        Outputs:
        - Narrative insights (Portuguese)
        - Structured recommendations
        - Risk identification
        
        Graceful fallback: If API unavailable, returns empty narrative
        """
        
        prompt = self._build_prompt(period_result, config, language)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            narrative = response.content[0].text
            return AnalysisResult(
                period_result=period_result,
                ai_narrative=narrative,
                ai_model=self.model,
                ai_tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                ai_cost=Decimal(str(response.usage.output_tokens)) * Decimal("0.003") / 1000
            )
        except Exception as e:
            # Graceful fallback
            logger.warning(f"AI analysis failed: {e}, continuing without narrative")
            return AnalysisResult(
                period_result=period_result,
                ai_narrative=None
            )
```

#### prompts.py

**CashFlow Story Analysis Prompt (Portuguese):**

```python
CASHFLOW_ANALYSIS_PROMPT = """
Você é um analista financeiro especializado em "CashFlow Story" 
(metodologia de Alan Miltz).

Analise os dados abaixo e forneça insights em 3 partes:

1. **Diagnóstico**: Qual dos 4 Capítulos é o maior problema?
   - Capítulo 1 (Lucratividade): Gross Margin, Overhead, EBIT
   - Capítulo 2 (Working Capital): AR Days, Inventory, AP Days
   - Capítulo 3 (Outros Ativos): Fixed Assets, Asset Turnover
   - Capítulo 4 (Funding): Debt ratios, Interest Coverage

2. **Oportunidades**: Dos 7 Alavancadores (Power of One), qual 3 têm 
   maior impacto no caixa?
   - Price +1% impact
   - Volume +1% impact
   - COGS -1% impact
   - Overhead -1% impact
   - AR Days -1 dia
   - Inventory Days -1 dia
   - AP Days +1 dia

3. **Recomendações**: Cite 3 ações concretas (com valores em R$).

Dados financeiros:
{financial_data}

Responda em JSON estruturado.
"""
```

---

### 3.5 Output Layer

**Path:** `src/output/`

#### excel_report.py

```python
def generate_excel(
    analysis: AnalysisResult,
    config: CompanyConfig,
    output_path: str
) -> str:
    """
    Generate multi-sheet XLSX workbook.
    
    Sheets:
    1. Summary (4 Chapters overview, KPIs)
    2. Power of One (sensitivity table)
    3. Cash Quality (G/A/B dashboard)
    4. Accounts (detailed mapping, before/after reclassifications)
    5. Trend (YoY comparison if available)
    
    Formatting:
    - Conditional formatting (traffic lights: red/amber/green)
    - Currency formatting (R$ with 2 decimals)
    - Charts: Revenue trend, CF trend, Margin trend
    - Frozen headers
    
    Returns: Path to generated file
    """
```

#### html_dashboard.py

```python
def generate_html(
    analysis: AnalysisResult,
    config: CompanyConfig,
    output_path: str
) -> str:
    """
    Generate self-contained HTML dashboard.
    
    Features:
    - Responsive design (mobile-friendly)
    - Chart.js visualizations
    - Dark/light mode toggle
    - Single file (no external resources)
    - Embeddable in email
    
    Returns: Path to generated file
    """
```

#### pdf_report.py

```python
def generate_pdf(
    analysis: AnalysisResult,
    config: CompanyConfig,
    output_path: str
) -> str:
    """
    Generate Module 7 Board Report (2-3 pages).
    
    Content:
    - Executive summary (key metrics)
    - 4 Chapters visual summary
    - Power of One top 3 recommendations
    - AI narrative insights
    
    Generation:
    - Render HTML template
    - WeasyPrint HTML→PDF
    - Result: Print-ready PDF
    
    Returns: Path to generated file
    """
```

#### json_export.py

```python
def export_json(
    analysis: AnalysisResult,
    config: CompanyConfig,
    output_path: str
) -> str:
    """
    Export complete analysis as JSON.
    
    Includes:
    - All metrics and calculations
    - Audit trail (input hash, config hash, timestamps)
    - AI model info and cost
    - Schema version (for compatibility)
    
    Schema:
    {
        "schema_version": "1.0.0",
        "company": "austa",
        "period": "2025-02",
        "generated_at": "2025-02-23T15:30:00Z",
        "audit_trail": {
            "input_checksum": "sha256...",
            "config_hash": "sha256...",
            "python_version": "3.11.2",
            "dependencies": {...}
        },
        "results": {...all metrics...},
        "ai_analysis": {...}
    }
    
    Returns: Path to generated file
    """
```

---

### 3.6 Pipeline Orchestrator

**Path:** `src/pipeline.py`

```python
class CashFlowPipeline:
    """Orchestrate entire analysis workflow."""
    
    def __init__(self, config_path: str, api_key: str | None = None):
        self.company_config = load_config(config_path)
        self.analyst = CashFlowAnalyst(api_key) if api_key else None
    
    def run(
        self,
        input_file: str,
        output_dir: str,
        run_ai: bool = True
    ) -> tuple[MappedData, PeriodResult, AnalysisResult]:
        """
        Execute complete pipeline.
        
        Flow:
        1. Ingest (XML → AccountEntry list)
        2. Map (→ MappedData with 4 Chapters)
        3. Calculate (→ PeriodResult with all metrics)
        4. Analyze (→ AnalysisResult with AI, if enabled)
        5. Render (→ XLSX, HTML, PDF, JSON files)
        
        Graceful degradation:
        - Ingest error → Stop pipeline, clear error
        - Mapping error → Stop pipeline, report unmapped accounts
        - Calc error → Unlikely (pure functions), fail loudly
        - AI error → Continue without narrative (run_ai=False)
        - Render error → Report which format failed
        
        Returns tuple of all stages for introspection
        """
        
        # 1. Ingest
        entries = parse_xml(input_file)
        
        # 2. Map
        mapped = map_accounts(entries, self.company_config)
        
        # 3. Calculate
        period_result = self._calculate_all(mapped)
        
        # 4. Analyze
        if run_ai and self.analyst:
            analysis = self.analyst.analyze(period_result, self.company_config)
        else:
            analysis = AnalysisResult(period_result=period_result)
        
        # 5. Render
        self._render_all(analysis, output_dir)
        
        return mapped, period_result, analysis
    
    def _calculate_all(self, mapped: MappedData) -> PeriodResult:
        """Run all calculation modules."""
        # Call each calc/*.py module
        prof = calculate_profitability(mapped)
        wc = calculate_working_capital(mapped)
        other = calculate_other_capital(mapped)
        funding = calculate_funding(mapped)
        quality = assign_grades({...metrics...}, self.company_config)
        poo = calculate_power_of_one(period_result, self.company_config)
        mcf = calculate_marginal_cf(prof, wc)
        
        return PeriodResult(
            company=mapped.company,
            period=mapped.period,
            chapter1=prof,
            chapter2=wc,
            chapter3=other,
            chapter4=funding,
            profitability=prof,
            working_capital=wc,
            cash_quality=quality,
            power_of_one=poo,
            marginal_cf=mcf,
            calculated_at=datetime.now()
        )
    
    def _render_all(self, analysis: AnalysisResult, output_dir: str):
        """Generate all output formats."""
        generate_excel(analysis, self.company_config, output_dir)
        generate_html(analysis, self.company_config, output_dir)
        generate_pdf(analysis, self.company_config, output_dir)
        export_json(analysis, self.company_config, output_dir)
```

---

## 4. Configuration Schema

### default.yaml

```yaml
pipeline:
  log_level: INFO
  output_formats: [xlsx, html, pdf, json]
  locale: pt-BR
  currency: BRL

ai:
  provider: claude
  model: claude-sonnet-4-20250514
  max_tokens: 2000
  temperature: 0.3
  enabled: true
  fallback_on_error: true

tax:
  country: BR
  irpj_base_rate: 0.15
  irpj_surtax_rate: 0.10
  csll_rate: 0.09

defaults:
  asset_turnover: 2.5
  depreciation_rate: 0.02
  capex_rate: 0.05
```

### Company Config (companies/austa.yaml)

```yaml
company:
  name: AUSTA Group
  industry: healthcare
  currency: BRL

account_mapping:
  revenue:
    accounts: ["3.1"]
    label: "Receita Bruta"
  # ... (detailed mapping per company)

thresholds:
  # Override defaults
  gross_margin_pct:
    good: 15
    average: 10

power_of_one:
  valuation_multiple: 6.0
  sensitivity:
    price_change_pct: 1.0
    # ... (sensitivity assumptions)
```

---

## 5. Error Handling & Validation

| Stage | Error Type | Handling | Recovery |
|-------|-----------|----------|----------|
| Ingest | File not found | Log error, exit(1) | User provides correct path |
| Ingest | Malformed XML | Parse partial, log unmapped | Continue with available data |
| Mapping | Account mismatch | Log unmapped accounts, warn | CFO reviews, adjusts config |
| Mapping | Balance sheet ±>1% | Log discrepancy, warn | Check source ERP data |
| Calc | Division by zero | Default to 0, log | Rare (revenue should exist) |
| AI | API timeout | Fallback: skip narrative | Continue with calculations |
| AI | Rate limit | Backoff & retry | Graceful degrade |
| Render | Disk full | Clear logs, fail render | Free disk space |

---

## 6. Testing Strategy

### Unit Tests (70% coverage)

**test_models.py:** Pydantic model validation, type checking

**test_profitability.py:** Calculation accuracy
- Sample: revenue R$1M, COGS R$400K, overhead R$400K
- Expected: Gross profit R$600K, EBIT R$200K, EBIT% 20%

**test_working_capital.py:** AR/Inventory/AP calculations
- Sample: AR R$100K (45 days), Inventory R$50K (10 days), AP R$40K (20 days)
- Expected: CCC = 45 + 10 - 20 = 35 days

**test_power_of_one.py:** Leverage sensitivity
- Base: EBIT R$10M, Cash R$20M
- Price +1%: EBIT +R$1.2M, Cash +R$1.5M
- Expected matches configured sensitivity

**test_cash_quality.py:** G/A/B grading logic
- Input: gross_margin_pct=52%, thresholds good=50, average=45, direction=higher
- Expected: Grade=G

**test_mapping.py:** Account reclassification, balance sheet validation

### Integration Tests (20% coverage)

**test_end_to_end.py:** Full pipeline with fixtures
- Input: sample AUSTA XML file
- Expected output: all 4 formats generated
- Validation: checksum matches fixture

**test_ingest_to_render.py:** XLSX output validation
- Expected: multi-sheet workbook with correct values
- Charts embedded, conditional formatting applied

### Validation Tests (10% coverage)

**fixtures/austa_202501.xml:** Real AUSTA financials (anonymized)
- Revenue R$13.3M, EBIT R$2M, Cash R$2.9M (historical)
- Expected calculations must match CFO-verified manual reports

**fixtures/expected_outputs/:** Pre-calculated results
- XLSX: known cell values
- JSON: known metric values
- Used to catch regressions during refactoring

---

## 7. Deployment & Operations

### Local Development

```bash
git clone <repo>
cd cashflow-story-pipeline
make install
cp .env.example .env
# Edit .env with ANTHROPIC_API_KEY
make run
```

### Production Server (Linux)

```bash
# 1. Clone to /opt/cashflow/
# 2. Install in venv
# 3. Create systemd timer for cron-like execution
# 4. Create file watcher service for auto-triggering
# 5. Logs → /var/log/cashflow/
# 6. Reports → /data/reports/
```

### Docker (future v1.1)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN make install
CMD ["cashflow", "watch", "--folder", "/erp/exports"]
```

---

## 8. Performance Characteristics

| Operation | Target | Typical | Notes |
|-----------|--------|---------|-------|
| XML parsing (50MB file) | <3s | 1.2s | lxml is C-accelerated |
| Account mapping | <1s | 0.3s | 500 accounts |
| All calculations | <2s | 0.8s | Pure Python, 20+ metrics |
| AI analysis (Claude) | <30s | 15s | Network latency, token cost |
| XLSX generation | <2s | 1.1s | openpyxl with formatting |
| HTML generation | <1s | 0.4s | Jinja2 template |
| PDF generation | <3s | 2.5s | WeasyPrint HTML→PDF |
| JSON export | <1s | 0.2s | pydantic.model_dump_json() |
| **Total (with AI)** | <5 min | 2.5 min | For 1 company, 1 period |

Memory usage: ~200MB for 50MB ERP file (pandas overhead)

---

## 9. Security Considerations

1. **API Keys:** Stored in .env, never logged
2. **Data:** No persistence after reports generated
3. **Audit Trail:** All transformations logged (immutable)
4. **File Permissions:** OS handles (not application-level)
5. **Dependencies:** Pinned versions, no arbitrary package downloads

