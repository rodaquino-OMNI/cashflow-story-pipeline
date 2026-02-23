# ADR-007: Immutable Data Pipeline

## Status
Accepted

## Date
2026-02-23

## Context
Financial analysis for board meetings and regulatory compliance requires full auditability. Every number in a report must be traceable back to the source data. The pipeline must be reproducible: same input + same config = same output, bit-for-bit. This is especially important for controlled companies, PE-backed companies, and those in regulated industries.

## Decision
Each pipeline stage produces an immutable output artifact. No stage mutates its input.

**Pipeline stages (immutable flow):**

1. **Raw** → `list[AccountEntry]`
   - Parsed from XML/XLSX exactly as ingested
   - No normalization, no reclassification
   - Hash: SHA-256 of input file

2. **Mapped** → `MappedData` (Pydantic model)
   - Accounts organized by 4 Chapters
   - Reclassifications applied and logged
   - All unmapped accounts listed
   - Hash: hash of raw + hash of config

3. **Calculated** → `PeriodResult`
   - All financial metrics computed
   - Profitability, Working Capital, Other Capital, Funding chapters
   - Power of One table
   - Cash Quality grades
   - No changes to mapped data

4. **Analyzed** → `AnalysisResult`
   - Marginal Cash Flow calculation
   - Variance analysis (vs prior period, vs budget)
   - AI narrative generation (optional)
   - Structured insights

5. **Rendered** → Files
   - XLSX, HTML, PDF, JSON generated from analysis result
   - No feedback from rendering to earlier stages

**Audit trail includes:**
- Input file checksum (SHA-256) and metadata (size, timestamp)
- Config version hash and all overrides applied
- Timestamp of each stage completion
- Runtime (for performance tracking)
- Unmapped accounts and amounts (with materiality threshold)
- All reclassifications applied with business justification
- AI model version, prompt used, tokens consumed
- Python version, library versions (for reproducibility)

## Consequences

### Positive
- Full traceability from report number → calculated value → source account → ERP line
- Each stage independently testable with fixture data
- Reproducible: deterministic given same inputs (Python package versions matter)
- Compliance-friendly for auditors (can verify calculations backwards)
- Easy debugging: inspect intermediate stage outputs via JSON export
- Can replay analysis with different AI model version (AI is optional layer)
- Changes to AI don't require re-calculating financials

### Negative
- More data objects to maintain (AccountEntry, MappedData, etc.)
- Slightly higher memory usage (immutable copies vs in-place mutation)
- Cannot optimize by mutating in place (though Python is rarely bottlenecked here)
- More lines of code to pass data through stages

### Risks
- AI responses are non-deterministic (different narrative each time) → mitigated by:
  1. Logging full prompt, response, and temperature in audit trail
  2. Using temperature=0.3 for consistency
  3. Optional re-generation flag: keep existing AI analysis or regenerate
  4. AI is optional; financials are deterministic

- Backward compatibility when models change → mitigated by:
  1. Semantic versioning of data models
  2. Migration scripts if schema changes
  3. JSON schema validation on import

## Implementation
- src/models/financial_data.py - frozen Pydantic models
- src/pipeline.py - orchestrates stages, returns tuple of results
- Each calc/*.py module is pure function: no state mutation
- Audit trail stored in JSON alongside reports
- Test fixtures include expected audit trail output

## Related Decisions
- ADR-003: Single AI Provider (AI is optional layer on immutable calculations)
- ADR-007 enables compliance validation required by CFO/board
