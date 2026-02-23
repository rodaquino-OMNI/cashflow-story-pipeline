# Product Requirements Document: CashFlow Story Pipeline

**Version:** 1.0  
**Date:** 2026-02-23  
**Product Manager:** Rodrigo Aquino  
**Status:** Approved

---

## 1. Problem Statement

### The Fundamental Challenge: The 40% Rule

Companies achieving 40% revenue growth often experience negative cash flow growth or collapse in absolute cash balances. This happens because:

- **Revenue growth consumes working capital** (more AR, more inventory, extended payment terms)
- **Manual analysis takes 5-10 days**, so CFOs are always analyzing history, never making real-time decisions
- **Current tools are reactive**, not predictive (we find the problem after the quarter closes)

### AUSTA Group Case Study

AUSTA Group (R$160M annual revenue, 8 hospitals) grew revenue 15% YoY but cash collapsed:
- Cash position: R$2.9M (Jan 2025) → R$394K (Jul 2025)
- Root cause: Not profitability (EBIT improved) but working capital (AR Days increased from 45→75)
- Time to diagnosis: 5-7 business days (manual process)
- CFO spent 2-3 days/month building reports from ERP exports

This is not unique to healthcare. Manufacturing, professional services, and retail companies hit this wall constantly.

### Current State: Manual Process

1. Finance downloads XML from ERP (TOTVS)
2. Exports to CSV, opens in Excel
3. Manually reconciles to 4 Chapters structure (Profitability, Working Capital, Other Capital, Funding)
4. Calculates 20+ metrics (gross margin, AR days, EBIT, debt ratios, etc.)
5. Applies Cash Quality grading (G/A/B per metric)
6. Generates Power of One sensitivity table (7 levers, 3 impacts each = 21 calculations)
7. Writes narrative analysis, builds board presentation
8. **Total time: 20-40 hours over 5-10 days**

### Why Current Dashboards Fail

- Built for interactive exploration, not batch automation
- Cannot access local ERP files directly (require manual upload)
- Require cloud infrastructure and user authentication
- Change every feature → must redeploy entire app
- Expensive to host and maintain

---

## 2. Solution: CashFlow Story Pipeline

**Transform ERP data into board-ready insights in under 5 minutes.**

```
ERP XML → [Automated Processing] → 4 Financial Reports
                                  ├── XLSX (for CFO review)
                                  ├── HTML (for board)
                                  ├── PDF (for filing)
                                  └── JSON (for integrations)
```

### Core Value Proposition

| Metric | Current | With Pipeline | Improvement |
|--------|---------|----------------|-------------|
| Time to analysis | 5-10 days | 5 minutes | 48-96x faster |
| Cost per analysis | ~$1,000 (labor) | ~$0.50 (AI) | 2000x cheaper |
| Frequency | Monthly/Quarterly | Daily/On-demand | Continuous |
| Accuracy | Variable (manual) | Reproducible | Elimination of errors |
| Board readiness | Manual deck building | Auto-generated PDF | 2-3 hours saved |

### Implementation

- **Pipeline:** Python 3.11+ batch processor
- **AI Analysis:** Claude for narrative insights (optional layer)
- **Outputs:** XLSX, HTML, PDF, JSON
- **Deployment:** Local CLI, file watcher, cron scheduling
- **Configuration:** YAML per company (no code changes)

---

## 3. Users & Personas

### Primary Users

#### CFO / Financial Controller
**Goal:** Understand cash position and identify improvement levers  
**Frequency:** Daily/Weekly review, Monthly deep dive  
**Pain points:** Current 5-10 day lag, manual reconciliation errors  
**Success metric:** Time from ERP close to board-ready report <2 hours

#### CEO / Board Member
**Goal:** Quarterly board presentation with strategic recommendations  
**Frequency:** Quarterly (+ ad-hoc for board meetings)  
**Pain points:** Outdated analysis, manual deck updates  
**Success metric:** Board package ready 24 hours after month close

#### Financial Analyst
**Goal:** Ad-hoc "what-if" analysis and scenario planning  
**Frequency:** Weekly for forecasting, daily during issues  
**Pain points:** No easy way to test scenarios, slow calculation  
**Success metric:** Run same analysis for different periods <1 minute

#### IT / DevOps
**Goal:** Automate financial reporting, integrate with existing systems  
**Frequency:** One-time setup, then monitoring  
**Pain points:** No API, can't automate, manual file handling  
**Success metric:** Fully autonomous scheduled pipeline, zero manual touches

### Secondary Users

- **Investors/Board Observers:** Read PDF/HTML reports (not users of pipeline)
- **External Auditors:** Verify calculations via JSON audit trail (future)

---

## 4. Core Use Cases

### UC-01: Monthly Automated Analysis

**Actor:** CFO  
**Trigger:** Month close (e.g., last day of month)  
**Steps:**

1. Finance downloads ERP balancete XML to /erp/exports/
2. File watcher detects new file
3. Pipeline automatically processes: XML → accounts mapping → calculations → AI analysis → reports
4. Reports generated: XLSX (in /reports/), email notification sent

**Output:** Board-ready XLSX with conditional formatting, narrative insights  
**Time:** <5 minutes

### UC-02: Quarterly Board Meeting Preparation

**Actor:** CFO / Board Secretary  
**Trigger:** Board meeting scheduled (Q end + 2 weeks)  
**Steps:**

1. CFO runs: `cashflow run --input /path/to/q3.xml --config austa --output ./reports/`
2. Generates XLSX (detailed analysis) + PDF (2-page executive summary)
3. CFO copies PDF into board deck template
4. Optional: regenerate AI narrative with different model/temperature

**Output:** PDF ready for printing, XLSX for reference  
**Time:** 10 minutes (including review)

### UC-03: Ad-Hoc Scenario Analysis

**Actor:** Financial Analyst  
**Trigger:** CEO asks "what if we reduce AR Days by 10?"  
**Steps:**

1. Analyst creates variant config: `cp config/companies/austa.yaml config/scenario_ar.yaml`
2. Updates thresholds/assumptions in YAML
3. Runs: `cashflow run --input /same/data --config scenario_ar --output ./scenarios/`
4. Compares JSON outputs: baseline vs scenario (Power of One impact table)

**Output:** Side-by-side comparison showing cash impact, value impact  
**Time:** 2-3 minutes

### UC-04: New Company Onboarding

**Actor:** CFO / IT  
**Trigger:** New acquisition or client wants pipeline  
**Steps:**

1. New company provides chart of accounts (Excel)
2. IT creates config: `cp config/companies/austa.yaml config/companies/newclient.yaml`
3. Maps chart of accounts to 4 Chapters in YAML
4. Validates mapping: `cashflow validate --config newclient`
5. Runs test with sample balancete: `cashflow run --input /sample/newclient/ --config newclient`
6. CFO reviews output, approves thresholds
7. Production deployment via cron

**Output:** Fully configured, tested pipeline  
**Time:** 1-2 hours (one-time setup)

---

## 5. Functional Requirements

### FR-01: XML/XLSX Ingestion

**Description:** Parse ERP export files and extract financial data  

**Requirements:**
- Parse TOTVS XML export (balancete format)
- Fall back to XLSX if XML unavailable
- Extract: account code, account name, debit/credit amounts, periods
- Handle multiple periods in single file (monthly trends)
- Validate structure and reject malformed inputs with clear error messages
- Support UTF-8 and Latin1 encoding
- Log all parsed accounts with materiality filter (ignore <R$1K)

**Acceptance criteria:**
- Parses AUSTA sample XML file in <1 second
- Handles missing periods gracefully
- Reports unmapped accounts for CFO review

### FR-02: Account Mapping to 4 Chapters

**Description:** Map ERP accounts to CashFlow Story structure  

**Requirements:**
- Load config from YAML (per company)
- Support account wildcards: "3.1.*" matches all sub-accounts
- Support reclassifications: move amount from account A to account B with audit trail
- Validation: all material accounts mapped, balance sheet equation holds
- Output: MappedData with all accounts organized by chapter
- Log all unmapped accounts and amounts for audit

**Acceptance criteria:**
- AUSTA: R$33M reclassification from 4.2.01→4.1 is applied and logged
- Balance sheet validation: Assets = Liabilities + Equity ±0.01%
- Unmapped accounts <0.5% of total revenue

### FR-03: CashFlow Story Calculations

**Description:** Implement all CashFlow Story financial metrics  

**Calculations required:**

**Chapter 1: Profitability**
- Gross Revenue
- Deductions (taxes, returns)
- Net Revenue
- Cost of Goods Sold (COGS) / Cost of Services (COCS)
- Gross Profit & Gross Margin %
- Operating Expenses (overhead)
- Overhead % of Revenue
- EBIT (Earnings Before Interest and Tax)
- EBIT Margin %

**Chapter 2: Working Capital**
- Accounts Receivable (AR) Days = (AR / Daily Revenue)
- Inventory Days = (Inventory / Daily COGS)
- Accounts Payable (AP) Days = (AP / Daily COGS)
- Cash Conversion Cycle = AR Days + Inventory Days - AP Days
- Working Capital Investment = (AR + Inventory - AP)
- Working Capital as % Revenue

**Chapter 3: Other Capital**
- Fixed Assets (net of depreciation)
- Depreciation Expense
- CapEx (capital expenditure) estimate
- Asset Turnover = Revenue / Total Assets

**Chapter 4: Funding**
- Short-term Debt
- Long-term Debt
- Total Debt
- Equity (book value)
- Debt-to-Equity Ratio
- Interest Expense
- Interest Coverage Ratio = EBIT / Interest

**Power of One: 7 Levers (sensitivity analysis)**
For each lever, calculate impact on:
1. Operating profit (pre-tax)
2. Operating cash flow
3. Enterprise value (valuation)

Levers:
1. Price: +1% impact (volume constant)
2. Volume: +1% impact (price constant)
3. COGS: -1% impact (% of revenue)
4. Overhead: -1% impact
5. AR Days: -1 day improvement
6. Inventory Days: -1 day improvement
7. AP Days: +1 day (longer terms from suppliers)

**Cash Quality: G/A/B Grading**
- Each metric assigned grade based on thresholds
- Configurable per company/industry
- Supports direction: "higher is better" vs "lower is better"
- Visual: Red (Below), Amber (Average), Green (Good)

**Marginal Cash Flow**
- GM% (Gross Margin %) - WC% (Working Capital % of Revenue) = Marginal CF%
- Interpretation:
  - \>0%: Growth generates cash (ideal)
  - ~0%: Growth is cash neutral
  - <0%: Growth consumes cash (the 40% Rule trap)

**Acceptance criteria:**
- All calculations match calculations.js (ported from existing code)
- Test fixtures with known outputs (from AUSTA historical data)
- >95% accuracy vs manual calculations
- Handles edge cases: zero revenue, zero inventory, negative equity

### FR-04: AI Analysis (Optional)

**Description:** Generate narrative insights using Claude AI  

**Requirements:**
- Integrate Anthropic Claude API (v1 uses single provider)
- Structured prompts: "Analyze this CashFlow Story and identify top 3 cash risks"
- Input: PeriodResult (all calculated metrics)
- Output: Narrative text in Portuguese, structured as JSON
- Optional: fallback gracefully if API unavailable
- Temperature: 0.3 (consistent output)
- Max tokens: 2,000 per analysis
- Log: model version, prompt, token usage, cost

**Features:**
- Identify which chapter is weakest (Profitability? Working Capital?)
- Highlight G/A/B grades below target
- Recommend top 3 actions from Power of One (e.g., "Reducing AR Days by 5 would improve cash by R$5M")
- Contextualize: compare vs industry benchmarks if available

**Acceptance criteria:**
- Cost <$0.50 per analysis
- Latency <30 seconds
- Output valid JSON structure
- Falls back gracefully (returns "Analysis unavailable" if API down)

### FR-05: Report Generation

**Description:** Generate output files in XLSX, HTML, PDF, JSON formats  

**Requirements:**

**XLSX Workbook:**
- Sheet 1: 4 Chapters summary (profitability, WC, other capital, funding)
- Sheet 2: Power of One sensitivity table
- Sheet 3: Cash Quality dashboard (metrics with G/A/B grades)
- Sheet 4: Detailed accounts (mapped, before/after reclassifications)
- Conditional formatting: traffic lights (red/amber/green)
- Charts: Revenue trend, Cash Flow trend, Margin trend

**HTML Report:**
- Single-file (self-contained, no external resources)
- Responsive (mobile-friendly)
- Charts: Chart.js visualizations
- Embeddable in email or Slack
- Dark/light mode toggle

**PDF Report:**
- Module 7 Board Report template (2-3 pages)
- Executive summary, key metrics, top 3 recommendations
- Generated via WeasyPrint (HTML→PDF)
- Print-ready (no background colors, proper page breaks)

**JSON Export:**
- Complete data export: all metrics, audit trail, metadata
- Schema version included
- Supports downstream integration (future web UI, BI tools)
- Includes input file hash, config version, timestamp

**Acceptance criteria:**
- All outputs generated in parallel <5 seconds
- XLSX with 50+ rows of data renders in Excel without lag
- PDF renders correctly on all browsers
- JSON schema is stable (backward-compatible)

### FR-06: Automation & Scheduling

**Description:** Enable headless, scheduled pipeline execution  

**Requirements:**
- CLI interface: `cashflow run`, `cashflow validate`, `cashflow watch`
- File watcher: monitors folder, auto-triggers on new XML
- Cron integration: can be scheduled via crontab or systemd timer
- Environment-driven config: API keys from .env
- Idempotent: running same input twice produces identical output
- Logging: structured logs (JSON format) for debugging

**Execution modes:**

1. **One-time run:**
   ```bash
   cashflow run --input /path/to/file --config austa --output ./reports/
   ```

2. **File watcher:**
   ```bash
   cashflow watch --folder /erp/exports --config austa --output ./reports/
   ```

3. **Scheduled (cron):**
   ```bash
   0 2 * * * /usr/local/bin/cashflow run --input /data/latest --config austa --output /reports
   ```

**Acceptance criteria:**
- CLI runs without interactive prompts
- File watcher detects new files within 10 seconds
- Logs are JSON format, include timestamps and trace IDs
- Same input twice = identical output (reproducible)

---

## 6. Non-Functional Requirements

### Performance

| Metric | Target | Rationale |
|--------|--------|-----------|
| End-to-end latency (XML→reports) | <5 minutes | User expectation: analysis complete in one "sitting" |
| AI analysis latency | <30 seconds | Does not block report generation |
| File watcher detection | <10 seconds | Reasonable for automated workflows |
| XLSX generation | <2 seconds | Multiple sheets, charts, formatting |
| Cold start (with deps) | <30 seconds | Python import overhead |

### Cost

| Component | Target | Notes |
|-----------|--------|-------|
| AI cost per analysis | <$0.50 | 2,000 tokens at $0.003/1K token |
| Infrastructure | ~$0 | Local execution, no servers required |
| Total cost per company | <$50/month | 100 analyses @ $0.50 each |

### Reliability

- **Availability:** Graceful degradation: reports complete even if AI API fails
- **Error handling:** All errors caught and logged, with recovery suggestions
- **Validation:** Input/output validation at each stage, audit trail preserved
- **Idempotency:** Same input + config → identical output (deterministic)

### Scalability

- **Companies:** Support unlimited companies via configuration (no code changes)
- **Data size:** Handle files up to 100MB (typical ERP export is 10-50MB)
- **Historical data:** Supports multi-year lookback (for trend analysis)

### Security

- **API keys:** Stored in .env, never logged or printed
- **Data handling:** No persistence of financial data after report generation
- **Audit trail:** All transformations logged for compliance
- **Access control:** File-level (OS handles, not application)

### Maintainability

- **Code quality:** Ruff linting, mypy type checking, pytest coverage >90%
- **Documentation:** ADRs, technical spec, inline comments for complex logic
- **Dependencies:** Pinned versions, lock file, minimal external dependencies
- **Testing:** Unit tests, integration tests, fixture-based validation

### Deployment

- **Language:** Python 3.11+ (mature, stable)
- **Package manager:** pip with requirements.txt or Poetry
- **CI/CD:** GitHub Actions (optional, for v1.1)
- **Platforms:** macOS, Linux, Windows (tested on Linux)

---

## 7. Out of Scope (v1)

The following features are explicitly deferred to v1.1 or v2:

### ❌ Multi-User Web Dashboard
Rationale: Output files (XLSX, PDF) are primary deliverables. Dashboard adds complexity without solving core problem.

### ❌ User Authentication & Access Control
Rationale: Batch pipeline runs locally or on dedicated server. No multi-user login needed.

### ❌ Multiple AI Providers (Gemini, GPT-4, Ollama)
Rationale: Claude excels at financial analysis. Multi-provider adds complexity for marginal benefit. Easy to add later if needed.

### ❌ Real-time Data / Streaming
Rationale: ERP data is batch (monthly). Real-time would require API integration with ERP, not feasible with TOTVS XML export.

### ❌ Mobile Apps
Rationale: Reports are PDF/XLSX, already mobile-accessible. Native app adds development burden.

### ❌ Forecast / Budget Integration
Rationale: v1 analyzes actual data. Variance vs budget deferred to v1.1.

### ❌ Multi-currency / International Tax
Rationale: v1 focuses on Brazil (BRL). Can extend later.

---

## 8. Success Metrics

### Time Savings
- **Target:** 5-10 days → 5 minutes per analysis
- **Metric:** Time from ERP close to board-ready report
- **Measurement:** Track pipeline run time + CFO review time in logs

### Accuracy
- **Target:** >95% match to manual calculations
- **Metric:** Discrepancy between pipeline output and human-built reports
- **Measurement:** QA team validates 10 analyses vs manual versions

### Adoption
- **Target:** 20+ companies configured (unlimited in theory)
- **Metric:** Number of active company configs
- **Measurement:** Count config/companies/*.yaml files

### Cost Reduction
- **Target:** <$50/month total per company (AI + infrastructure)
- **Metric:** Actual cost per analysis
- **Measurement:** Track Anthropic API bill, log tokens used

### Report Quality
- **Target:** CFO approves output without modifications
- **Metric:** % reports used as-is (not edited)
- **Measurement:** Survey/feedback post-report

### Reliability
- **Target:** 99% success rate (1 failure per 100 runs tolerable)
- **Metric:** Pipeline completion rate
- **Measurement:** Log every execution, track success/failure

---

## 9. Implementation Roadmap

### Milestone 1: Foundation (Week 1)
- [ ] Pydantic models: financials.py, cashflow_story.py
- [ ] Config loading and validation (default.yaml, companies/*.yaml)
- [ ] Brazilian tax rules and entity calculations
- [ ] Unit tests for models

**Deliverable:** Core data structures tested, config system working

### Milestone 2: Calculations (Week 2)
- [ ] Port all calc/*.py modules from calculations.js
- [ ] Profitability, Working Capital, Other Capital, Funding chapters
- [ ] Power of One (7 levers, 3 impacts each)
- [ ] Cash Quality grading (G/A/B per metric)
- [ ] Fixture-based validation against known outputs

**Deliverable:** All calculations done, 90%+ test coverage

### Milestone 3: Ingestion (Week 3)
- [ ] XML parser (lxml, handles TOTVS balancete)
- [ ] XLSX parser (openpyxl fallback)
- [ ] Account mapping logic (wildcards, reclassifications)
- [ ] Validation: balance sheet equation, materiality filter
- [ ] Integration tests with AUSTA sample data

**Deliverable:** Can parse real ERP files, map to 4 Chapters

### Milestone 4: AI Analysis (Week 3)
- [ ] Claude SDK integration
- [ ] Structured prompts (Portuguese, CashFlow Story context)
- [ ] JSON output parsing and validation
- [ ] Fallback/error handling
- [ ] Cost logging and token tracking

**Deliverable:** AI analysis optional layer working, <$0.50/run

### Milestone 5: Report Generation (Week 4)
- [ ] XLSX generator (openpyxl, conditional formatting, charts)
- [ ] HTML generator (Jinja2, Chart.js, responsive)
- [ ] PDF generator (WeasyPrint, board report template)
- [ ] JSON exporter (complete audit trail)
- [ ] Integration: all outputs from single pipeline run

**Deliverable:** Four file formats generated, no manual post-processing

### Milestone 6: Automation (Week 4)
- [ ] CLI interface (Click framework)
- [ ] File watcher (watchdog library)
- [ ] Environment config (.env loading)
- [ ] Logging (structlog, JSON format)
- [ ] Cron/systemd integration docs

**Deliverable:** Can run via CLI, file watcher, or scheduled job

### Milestone 7: Validation & Deployment (Week 5)
- [ ] End-to-end tests with AUSTA real data
- [ ] CFO review and sign-off
- [ ] Documentation: PRD, technical spec, ADRs
- [ ] Docker build (optional, nice-to-have)
- [ ] Setup guide and README

**Deliverable:** Production-ready, deployed with AUSTA, documentation complete

---

## 10. Constraints & Assumptions

### Constraints
- Python 3.11+ (language choice locked in)
- TOTVS ERP (primary target, others via XML compatibility)
- Monthly/Quarterly frequency (not real-time)
- Claude AI (single provider for v1)
- Local execution or dedicated server (no SaaS hosting required)

### Assumptions
- CFO provides charts of accounts mapping (one-time setup)
- ERP exports valid XML/XLSX (ingestion handles but doesn't fix malformed files)
- Financial data is accurate at source (pipeline doesn't validate reasonableness)
- Company thresholds are calibrated (industry-specific G/A/B grades)
- Python environment available (development, not end-user facing)

---

## 11. Acceptance Criteria

The CashFlow Story Pipeline v1.0 is complete when:

1. **All 7 milestones delivered** and tested
2. **AUSTA Group analysis** runs end-to-end: XML → XLSX + PDF in <5 minutes
3. **>95% accuracy** on calculations vs manual AUSTA reports
4. **>90% test coverage** (pytest, all modules)
5. **4 output formats** generated: XLSX, HTML, PDF, JSON
6. **CFO sign-off** on output quality and usability
7. **Documentation complete** (PRD, Tech Spec, ADRs, README, setup guide)
8. **Production deployment** with AUSTA running monthly pipeline

**Definition of Done:** CFO runs `cashflow run` monthly without manual intervention, and board receives PDF report within 24 hours of month close.

