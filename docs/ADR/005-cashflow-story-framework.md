# ADR-005: CashFlow Story as First-Class Framework

## Status
Accepted

## Date
2026-02-23

## Context
The existing React codebase performs traditional financial statement analysis (P&L, Balance Sheet, Cash Flow, standard ratios) but does NOT implement the CashFlow Story methodology. There is no 4 Chapters framework, no Power of One sensitivity analysis, no Cash Quality G/A/B grading, and no Marginal Cash Flow calculation. These are the core analytical tools that differentiate this product from generic financial dashboards.

CashFlow Story (Alan Miltz / Verne Harnish's *Scaling Up*) is the competitive advantage. It answers the critical question: "How do we grow revenue while protecting/improving cash?"

## Decision
Implement CashFlow Story (Alan Miltz / Scaling Up) as a first-class framework, not an afterthought.

**Core components:**

### 1. **4 Chapters of Cash**
- Chapter 1: Profitability (Revenue - COGS - Overhead = EBIT)
- Chapter 2: Working Capital (AR Days - Inventory Days + AP Days)
- Chapter 3: Other Capital (Fixed assets, depreciation, capex)
- Chapter 4: Funding (Debt, equity, interest, dividends)

### 2. **Power of One: 7 Levers**
Each lever shows profit impact, cash impact, and value impact (enterprise value):
- Price: +1% on volume → impact on profit, cash, value
- Volume: +1% on price → impact on profit, cash, value
- COGS: -1% on revenue → impact on profit, cash, value
- Overhead: -1% → impact on profit, cash, value
- AR Days: -1 day → impact on profit, cash, value
- Inventory Days: -1 day → impact on profit, cash, value
- AP Days: +1 day → impact on profit, cash, value

### 3. **Cash Quality: G/A/B Grading**
For each metric (GM%, Overhead%, AR Days, etc.):
- Good (G): Above target threshold, strong execution
- Average (A): Between thresholds, acceptable
- Below (B): Below acceptable, needs improvement

### 4. **Marginal Cash Flow**
The fundamental insight: GM% - WC% = Marginal CF%
- If positive: growth generates cash (best case)
- If near zero: growth neutral on cash
- If negative: growth consumes cash (the "40% Rule" trap)

### 5. **3 Big Measures**
Dashboard focus on:
- Net Cash Flow (absolute)
- Operating Cash Flow (excludes financing)
- Marginal Cash Flow (per additional dollar of revenue)

### 6. **Module 7 Board Report**
Quarterly template matching Scaling Up / EOS playbooks

## Consequences

### Positive
- Fills the critical gap in the existing codebase
- Directly implements the methodology the business is built on
- Power of One provides actionable, quantified recommendations ("If we reduce AR Days by 5, cash improves by R$2.5M")
- Cash Quality gives instant visual health assessment (red/amber/green)
- Marginal CF answers the fundamental question: "Should we grow?"
- Differentiates from generic financial dashboards
- Matches board/investor expectations (they use Scaling Up methodology too)

### Negative
- More calculation modules to implement and test (9 modules vs 5)
- Requires deep understanding of the methodology
- Industry-specific thresholds need calibration per sector
- More training required for CFOs unfamiliar with methodology

### Risks
- Methodology interpretation differences → mitigated by:
  1. Referencing Scaling Up source material directly
  2. Validating calculations against Blue Consulting case studies
  3. CFO review and sign-off on thresholds
- Thresholds not appropriate for all industries → mitigated by healthcare-specific defaults in AUSTA config, with easy override per company

## Implementation Plan
- calc/profitability.py - Chapter 1 calculations
- calc/working_capital.py - Chapter 2 calculations
- calc/power_of_one.py - 7 levers sensitivity
- calc/cash_quality.py - G/A/B grading
- calc/marginal_cashflow.py - GM% - WC% analysis
- All tested against fixture data from real AUSTA financials

## Related Decisions
- ADR-006: Output-First Design (reports showcase 4 Chapters, Power of One, Cash Quality)
