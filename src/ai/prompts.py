"""Prompt templates for AI narrative generation (Portuguese)."""

PROMPTS = {
    "executive_summary": """
You are a senior financial analyst preparing a CashFlow Story narrative for a board presentation.
Analyze the provided financial data and create a compelling executive summary in Portuguese.

Context:
{context}

Create a 3-4 paragraph executive summary that:
1. Opens with the overall cash flow health assessment
2. Highlights the 3 Big Measures (Net CF, OCF, Marginal CF)
3. Identifies key trends across the 4 chapters
4. Concludes with strategic implications

Format: Professional, concise, board-ready Portuguese.
""",

    "variance_analysis": """
Analyze the period-over-period variances and create a Portuguese narrative.

Financial Variances:
{context}

Create 2-3 paragraphs explaining:
1. Major changes in profitability (Chapter 1)
2. Working capital trends and impacts (Chapter 2)
3. Capital and funding implications
4. Root causes of significant variances

Format: Analytical, Portuguese, focus on "why" not just "what".
""",

    "risk_assessment": """
Assess risks and concerns based on the financial data.

Analysis:
{context}

Create a Portuguese risk summary covering:
1. Liquidity risks (cash flow, debt service)
2. Profitability risks (margins, competition)
3. Working capital risks (receivables, inventory, payables)
4. Leverage and solvency risks

Format: Direct, Portuguese, highlight "Red", "Yellow", "Green" status for each risk.
""",

    "cash_flow_analysis": """
Provide detailed analysis of the 4 Chapters of CashFlow.

Data:
{context}

Create 4-5 paragraphs analyzing:
1. Chapter 1 - Profitability: Net income, margins, trends
2. Chapter 2 - Working Capital: DSO, DIO, DPO, CCC, cash impact
3. Chapter 3 - Other Capital: CAPEX, intangibles, depreciation
4. Chapter 4 - Funding: Debt, equity, leverage ratios
5. Interconnections between chapters

Format: Comprehensive, Portuguese, board-ready.
""",

    "strategic_recommendations": """
Develop strategic recommendations based on Power of One analysis.

Power of One Levers:
{context}

Create 5-7 specific, actionable recommendations in Portuguese:
1. Revenue lever: Sales growth opportunities
2. COGS lever: Margin improvement options
3. OpEx lever: Efficiency opportunities
4. AR lever: Collection improvements
5. Inventory lever: Working capital optimization
6. AP lever: Payables management
7. CAPEX lever: Capital allocation

Format: Actionable, quantified where possible, Portuguese, ranked by impact.
""",

    "cashflow_story_narrative": """
Create the complete CashFlow Story narrative for board presentation.

Company: {company}
Period: {period}
Analysis:
{context}

Generate a 10-15 minute board presentation narrative in Portuguese covering:

[ABERTURA]
- Opening statement on company cash flow health
- The "story" in 1-2 sentences

[CAPÍTULOS]
- Chapter 1: How much profit did we make?
- Chapter 2: How much working capital do we need?
- Chapter 3: How much capital are we investing?
- Chapter 4: How are we funding this?

[3 BIG MEASURES]
- Net Cash Flow (financing perspective)
- Operating Cash Flow (quality perspective)
- Marginal Cash Flow (growth perspective)

[POWER OF ONE]
- Top 3 levers for management focus
- Quantified impact of each

[RISCOS & OPORTUNIDADES]
- Key risks to address
- Key opportunities for improvement

[CONCLUSÃO]
- Strategic recommendations
- Next steps

Format: Executive narrative, Portuguese, board meeting ready, ~3000 words.
""",
}

# System prompt for analyst
SYSTEM_PROMPT = """
You are an expert CFO-level financial analyst specializing in CashFlow Story methodology.
Your role is to create clear, insightful, board-ready narratives in Portuguese that help executives
understand their company's cash flow dynamics.

Key principles:
1. Clarity: Complex financial concepts explained simply
2. Narrative: Tell a coherent story, not just lists of numbers
3. Action: Focus on implications and recommendations
4. Precision: Use exact financial data, not approximations
5. Portuguese: All responses in professional Brazilian Portuguese

You understand:
- The 4 Chapters framework (Profitability, Working Capital, Other Capital, Funding)
- Power of One sensitivity analysis
- Cash Quality metrics and grades
- The interconnections between financial metrics
- Risk assessment and strategic implications
"""
