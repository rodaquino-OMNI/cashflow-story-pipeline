# ADR-006: Output-First Design

## Status
Accepted

## Date
2026-02-23

## Context
The current React app focuses on building an interactive dashboard. In practice, the primary consumers want static deliverables: an Excel file for the CFO to review locally, a PDF for the board meeting deck, an HTML page to share via email or Slack. The dashboard is used once (to view the latest numbers); the reports are circulated to 5-20 people, filed in the accounting system, and referenced repeatedly over months.

Interactive features (drill-down, filtering, custom date ranges) are rarely used in practice. The constraints of a web UI actually hurt: no local copy, requires specific browsers, cannot be edited/annotated, must be online.

## Decision
Design the system around output formats, not interactive UI.

**Primary outputs (in order of importance):**
1. **XLSX:** Multi-sheet workbook with traffic-light conditional formatting
   - 4 Chapters summary with G/A/B grades
   - Power of One leverage table
   - Detailed account mapping and reclassifications
   - Year-over-year comparison
   - Editable for CFO annotations
   - Opens in Excel, Google Sheets, LibreOffice

2. **HTML:** Self-contained single-file dashboard
   - Chart.js visualizations (revenue, cash flow, margins)
   - Responsive design for mobile
   - Embeddable in email as attachment or link
   - Requires no server

3. **PDF:** Module 7 board meeting template
   - 2-3 page executive summary
   - Generated via WeasyPrint (HTML→PDF)
   - Print-ready, no dependency on viewers
   - Easy to include in board packets

4. **JSON:** Structured data for downstream systems
   - Integration with accounting software (future)
   - Feed to web dashboard (future)
   - Machine-readable for analysis tools
   - Version-stable schema for compatibility

## Consequences

### Positive
- Reports are the actual deliverable — not a side feature or "nice to have"
- XLSX with traffic lights is immediately useful for CFOs (they live in Excel)
- PDF board report replaces manual preparation (saves 2-3 hours per quarter)
- JSON enables future web dashboard without redesigning pipeline
- All outputs are archivable and auditable (can be stored in Confluence, email, filing system)
- Users can edit/annotate XLSX locally
- No session state to manage, no "lost work" because user navigated away
- Dramatically lower hosting costs: no server, no session DB

### Negative
- No real-time interaction or drill-down within the dashboard
- Charts are static (no hover for exact values, no zoom, no panning)
- Users cannot customize views ad-hoc (column reordering must happen in XLSX)
- No ability to track who viewed what (offline files don't report telemetry)

### Risks
- Report templates may not match exact client expectations → mitigated by:
  1. Jinja2 templating that allows easy customization without code changes
  2. Early review and approval of templates with CFO
  3. Version 2 can introduce interactive web UI that consumes JSON output

## Implementation
- templates/report.xlsx (Jinja2 + openpyxl)
- templates/dashboard.html (Chart.js, responsive)
- templates/board_report.html (tailored for PDF generation)
- output/ module orchestrates generation
- Audit trail embedded in JSON includes input hash, config version, timestamp, model version

## Future Migration Path
If interactive features are needed:
1. Pipeline continues to generate JSON (no changes)
2. New React/Vue dashboard consumes JSON API (or static JSON files)
3. Users can choose: reports (fast, portable) or dashboard (interactive)
