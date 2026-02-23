# ADR-003: Single AI Provider (Claude) in v1

## Status
Accepted

## Date
2026-02-23

## Context
The existing codebase integrates 4 AI providers (Gemini, GPT-4, Claude, Ollama) through a complex abstraction layer with provider-specific adapters, error handling, and fallback logic. This multi-provider architecture contributed ~500 lines of orchestration code while providing marginal benefit — most users only need one provider. Additionally, financial analysis and Portuguese language support are Claude's strengths.

## Decision
Use Claude (Anthropic) as the sole AI provider in v1. The AI layer is optional — the pipeline produces complete calculations and reports without it.

**Rationale:**
- Claude excels at financial analysis and structured reasoning
- Native Portuguese language support without prompt engineering
- Structured output format for reliable parsing (JSON mode)
- Single SDK reduces dependency surface and maintenance burden
- Pipeline works offline; AI adds narrative layer and insights on top
- Stronger financial analysis performance compared to other models
- Best at understanding context and providing actionable recommendations

## Consequences

### Positive
- ~200 lines of AI code vs ~500 in multi-provider abstraction
- One SDK to maintain, one API to monitor, one rate limit to handle
- Consistent output quality (no provider variance)
- Simpler error handling and retry logic
- Easier testing: mock one provider instead of N
- Smaller security surface (fewer API keys, fewer integrations)

### Negative
- No provider failover in v1
- Locked to Anthropic pricing and availability
- Cannot leverage provider-specific strengths (e.g., real-time data from GPT-4)
- If Claude API changes, requires rework

### Risks
- API outage blocks AI narrative generation → mitigated by graceful degradation: pipeline completes without AI, reports show "AI analysis unavailable" and CFO can still see all calculations
- Rate limiting under load → mitigated by batch mode: multiple companies processed sequentially with backoff
- Token cost scaling → mitigated by temperature=0.3 for consistency and structured prompts for efficiency

## Migration Path
v2 can add provider abstraction if needed, but with single provider in v1 we avoid premature abstraction and maintain focus.
