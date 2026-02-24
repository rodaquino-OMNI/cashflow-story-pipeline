"""Main pipeline orchestrator for CashFlow Story analysis."""

import logging
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.ai.analyst import CashFlowStoryAnalyst
from src.calc import (
    calculate_cash_flow,
    calculate_income_statement,
    calculate_marginal_cash_flow,
    calculate_power_of_one,
    calculate_ratios,
    calculate_working_capital,
    classify_cash_quality,
    estimate_balance_sheet,
)
from src.ingest.account_mapper import AccountMapper
from src.ingest.xml_parser import ERPXMLParser
from src.models import (
    AccountEntry,
    AnalysisResult,
    MappedData,
    PeriodResult,
    ThreeBigMeasures,
)
from src.output.excel_report import ExcelReportGenerator
from src.output.html_dashboard import HTMLDashboardGenerator
from src.output.json_export import JSONExporter
from src.output.pdf_report import PDFReportGenerator


class CashFlowStoryPipeline:
    """
    Orchestrates the complete CashFlow Story analysis pipeline.

    Workflow:
    1. Ingest: Parse ERP XML/Excel files
    2. Map: Map accounts to financial categories
    3. Calculate: Compute all financial metrics
    4. Analyze: Generate Power of One, Cash Quality, variances
    5. Synthesize: Create board narrative (with AI if enabled)
    6. Export: Generate Excel, HTML, PDF reports

    Attributes:
        config_name: Configuration profile name
        config_path: Path to configuration file
        logger: Structured logger instance
        audit_trail: Dictionary tracking all processing steps
    """

    def __init__(self, config_name: str = "default", config_path: str | None = None) -> None:
        """
        Initialize the CashFlow Story pipeline.

        Args:
            config_name: Configuration profile to use
            config_path: Optional path to custom config file
        """
        self.config_name = config_name
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.audit_trail: dict[str, Any] = {}

    def _resolve_config_path(self) -> str:
        """Resolve the account-mapping config path.

        Returns:
            str: Absolute path to the YAML config file.

        Raises:
            FileNotFoundError: If the resolved path does not exist.
        """
        if self.config_path:
            p = Path(self.config_path)
            if not p.exists():
                raise FileNotFoundError(f"Config file not found: {p}")
            return str(p)

        candidate = Path("config") / "companies" / f"{self.config_name}.yaml"
        if not candidate.exists():
            raise FileNotFoundError(
                f"Config file not found: {candidate}. "
                f"Set config_path or place a YAML file at {candidate}"
            )
        return str(candidate)

    def _run_calc_chain(self, mapped: MappedData) -> PeriodResult:
        """Run the full calculation chain on a single MappedData.

        The chain merges the income-statement result with working-capital
        fields, then feeds the merged result through balance sheet,
        cash flow, and ratio calculators.

        Args:
            mapped: Mapped financial data for one period.

        Returns:
            PeriodResult: Fully-calculated period result.
        """
        is_result = calculate_income_statement(mapped)
        wc_result = calculate_working_capital(mapped, days_in_period=mapped.days_in_period)

        merged = is_result.model_copy(update={
            "days_sales_outstanding": wc_result.days_sales_outstanding,
            "days_inventory_outstanding": wc_result.days_inventory_outstanding,
            "days_payable_outstanding": wc_result.days_payable_outstanding,
            "cash_conversion_cycle": wc_result.cash_conversion_cycle,
            "working_capital": wc_result.working_capital,
            "working_capital_investment": wc_result.working_capital_investment,
        })

        bs_result = estimate_balance_sheet(merged)
        cf_result = calculate_cash_flow(bs_result)
        ratios_result = calculate_ratios(cf_result)
        return ratios_result

    def run(
        self,
        input_path: str,
        output_path: str,
        options: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        """
        Execute the complete CashFlow Story pipeline.

        Args:
            input_path: Path to ERP data file (XML) or directory of XML files.
            output_path: Path for output reports directory.
            options: Pipeline options dict
                - no_ai: Skip AI analysis if True
                - format: Output formats list (excel, html, pdf, json)
                - verbose: Enable verbose logging

        Returns:
            AnalysisResult: Complete analysis with all calculations and insights.

        Raises:
            FileNotFoundError: If input file/directory not found.
            ValueError: If data validation fails.
        """
        load_dotenv()
        options = options or {}
        self.audit_trail = {
            "started_at": datetime.utcnow().isoformat(),
            "input": str(input_path),
            "stages": {},
        }

        try:
            # ----------------------------------------------------------
            # Stage 1: Ingest
            # ----------------------------------------------------------
            self.logger.info("Stage 1: Ingesting ERP data", extra={"stage": 1})
            try:
                t0 = time.monotonic()
                input_p = Path(input_path)

                all_entries: list[list[AccountEntry]] = []

                if input_p.is_dir():
                    xml_files = sorted(input_p.glob("*.xml"))
                    if not xml_files:
                        raise FileNotFoundError(
                            f"No XML files found in directory: {input_p}"
                        )
                    for xml_file in xml_files:
                        parser = ERPXMLParser(str(xml_file))
                        entries = parser.parse_balancete()
                        all_entries.append(entries)
                elif input_p.is_file():
                    parser = ERPXMLParser(str(input_p))
                    entries = parser.parse_balancete()
                    all_entries.append(entries)
                else:
                    raise FileNotFoundError(f"Input path not found: {input_p}")

                total_entries = sum(len(e) for e in all_entries)
                duration_ms = round((time.monotonic() - t0) * 1000, 2)
                self.audit_trail["stages"]["ingest"] = {
                    "entries_count": total_entries,
                    "files_count": len(all_entries),
                    "duration_ms": duration_ms,
                }
                self.logger.info(
                    "Ingest complete: %d entries from %d file(s)",
                    total_entries,
                    len(all_entries),
                )
            except Exception as e:
                self.logger.error(f"Ingest failed: {e}", extra={"stage": 1})
                raise

            # ----------------------------------------------------------
            # Stage 2: Map
            # ----------------------------------------------------------
            self.logger.info("Stage 2: Mapping accounts", extra={"stage": 2})
            try:
                t0 = time.monotonic()
                config_path_resolved = self._resolve_config_path()
                mapper = AccountMapper(config_path_resolved)

                mapped_list: list[MappedData] = []
                for entry_set in all_entries:
                    period = entry_set[0].period if entry_set else "unknown"
                    mapped = mapper.map_accounts(entry_set, period)
                    mapped_list.append(mapped)

                duration_ms = round((time.monotonic() - t0) * 1000, 2)
                self.audit_trail["stages"]["map"] = {
                    "periods_count": len(mapped_list),
                    "duration_ms": duration_ms,
                }
                self.logger.info(
                    "Map complete: %d period(s) mapped", len(mapped_list)
                )
            except Exception as e:
                self.logger.error(f"Map failed: {e}", extra={"stage": 2})
                raise

            # ----------------------------------------------------------
            # Stage 3: Calculate
            # ----------------------------------------------------------
            self.logger.info("Stage 3: Calculating metrics", extra={"stage": 3})
            try:
                t0 = time.monotonic()
                period_results: list[PeriodResult] = []
                for mapped in mapped_list:
                    pr = self._run_calc_chain(mapped)
                    period_results.append(pr)

                duration_ms = round((time.monotonic() - t0) * 1000, 2)
                self.audit_trail["stages"]["calculate"] = {
                    "periods_calculated": len(period_results),
                    "duration_ms": duration_ms,
                }
                self.logger.info(
                    "Calculate complete: %d period(s)", len(period_results)
                )
            except Exception as e:
                self.logger.error(f"Calculate failed: {e}", extra={"stage": 3})
                raise

            # ----------------------------------------------------------
            # Stage 4: Analyze
            # ----------------------------------------------------------
            self.logger.info("Stage 4: Analyzing cash flow story", extra={"stage": 4})
            try:
                t0 = time.monotonic()
                latest = period_results[-1] if period_results else None

                # Power of One (from latest period)
                power_of_one = calculate_power_of_one(latest) if latest else []

                # Cash Quality (from latest period)
                cash_quality = classify_cash_quality(latest) if latest else []

                # Marginal Cash Flow (from latest period)
                marginal_cf: dict[str, Decimal] | None = None
                if latest:
                    marginal_cf = calculate_marginal_cash_flow(latest)

                # Three Big Measures (from latest period)
                three_big: ThreeBigMeasures | None = None
                if latest:
                    mcf_pct = marginal_cf.get("mcf_percent", Decimal("0")) if marginal_cf else Decimal("0")
                    three_big = ThreeBigMeasures(
                        net_cash_flow=latest.net_cash_flow,
                        operating_cash_flow=latest.operating_cash_flow,
                        marginal_cash_flow=mcf_pct,
                        interpretations={
                            "net_cash_flow": (
                                "Positivo: a empresa gerou caixa no periodo."
                                if latest.net_cash_flow >= Decimal("0")
                                else "Negativo: a empresa consumiu caixa no periodo."
                            ),
                            "operating_cash_flow": (
                                "Positivo: operacoes geraram caixa."
                                if latest.operating_cash_flow >= Decimal("0")
                                else "Negativo: operacoes consumiram caixa."
                            ),
                            "marginal_cash_flow": (
                                "Positivo: crescimento gera caixa."
                                if mcf_pct >= Decimal("0")
                                else "Negativo: crescimento consome caixa."
                            ),
                        },
                    )

                # Variances across periods
                variances: dict[str, dict[str, Any]] = {}
                if len(period_results) >= 2:
                    prev = period_results[-2]
                    curr = period_results[-1]
                    for field in [
                        "gross_revenue", "net_revenue", "gross_profit",
                        "ebitda", "ebit", "net_income",
                        "operating_cash_flow", "free_cash_flow",
                        "working_capital",
                    ]:
                        prev_val = getattr(prev, field)
                        curr_val = getattr(curr, field)
                        abs_change = curr_val - prev_val
                        pct_change = (
                            (abs_change / prev_val * Decimal("100"))
                            if prev_val != Decimal("0")
                            else Decimal("0")
                        )
                        variances[field] = {
                            "previous": float(prev_val),
                            "current": float(curr_val),
                            "absolute_change": float(abs_change),
                            "percent_change": float(pct_change),
                        }

                duration_ms = round((time.monotonic() - t0) * 1000, 2)
                self.audit_trail["stages"]["analyze"] = {
                    "power_of_one_levers": len(power_of_one),
                    "cash_quality_metrics": len(cash_quality),
                    "has_marginal_cf": marginal_cf is not None,
                    "has_variances": len(variances) > 0,
                    "duration_ms": duration_ms,
                }
                self.logger.info("Analyze complete")
            except Exception as e:
                self.logger.error(f"Analyze failed: {e}", extra={"stage": 4})
                raise

            # ----------------------------------------------------------
            # Stage 5: Synthesize (AI narrative)
            # ----------------------------------------------------------
            ai_insights: str | None = None
            if not options.get("no_ai"):
                self.logger.info("Stage 5: Synthesizing AI narrative", extra={"stage": 5})
                try:
                    t0 = time.monotonic()
                    company_name = mapped_list[0].company if mapped_list else "unknown"

                    temp_result = AnalysisResult(
                        company=company_name,
                        periods=period_results,
                        variances=variances,
                        power_of_one=power_of_one,
                        cash_quality=cash_quality,
                        marginal_cash_flow=marginal_cf,
                        three_big_measures=three_big,
                        audit_trail=self.audit_trail,
                    )
                    analyst = CashFlowStoryAnalyst()
                    ai_insights = analyst.analyze(temp_result)

                    duration_ms = round((time.monotonic() - t0) * 1000, 2)
                    self.audit_trail["stages"]["synthesize"] = {
                        "ai_insights_length": len(ai_insights) if ai_insights else 0,
                        "duration_ms": duration_ms,
                    }
                    self.logger.info("Synthesize complete")
                except Exception as e:
                    self.logger.warning(f"Synthesize skipped: {e}", extra={"stage": 5})
                    ai_insights = None
                    self.audit_trail["stages"]["synthesize"] = {
                        "skipped": True,
                        "reason": str(e),
                    }
            else:
                self.logger.info("Stage 5: Skipped (no_ai=True)", extra={"stage": 5})
                self.audit_trail["stages"]["synthesize"] = {"skipped": True, "reason": "no_ai"}

            # ----------------------------------------------------------
            # Stage 6: Export
            # ----------------------------------------------------------
            self.logger.info("Stage 6: Exporting reports", extra={"stage": 6})
            try:
                t0 = time.monotonic()
                company_name = mapped_list[0].company if mapped_list else "unknown"

                analysis_result = AnalysisResult(
                    company=company_name,
                    periods=period_results,
                    variances=variances,
                    power_of_one=power_of_one,
                    cash_quality=cash_quality,
                    marginal_cash_flow=marginal_cf,
                    three_big_measures=three_big,
                    ai_insights=ai_insights,
                    audit_trail=self.audit_trail,
                )

                out_dir = Path(output_path)
                out_dir.mkdir(parents=True, exist_ok=True)

                formats = options.get("format", ["excel", "html", "pdf", "json"])
                output_files: dict[str, str] = {}

                if "excel" in formats:
                    excel_path = out_dir / "cashflow_story.xlsx"
                    result_path = ExcelReportGenerator(str(excel_path)).generate(analysis_result)
                    output_files["excel"] = str(result_path)

                if "html" in formats:
                    html_path = out_dir / "cashflow_story.html"
                    result_path = HTMLDashboardGenerator(str(html_path)).generate(analysis_result)
                    output_files["html"] = str(result_path)

                if "pdf" in formats:
                    pdf_path = out_dir / "cashflow_story.pdf"
                    result_path = PDFReportGenerator(
                        str(pdf_path), company_name=company_name
                    ).generate(analysis_result)
                    output_files["pdf"] = str(result_path)

                if "json" in formats:
                    json_path = out_dir / "cashflow_story.json"
                    result_path = JSONExporter(str(json_path)).export(analysis_result)
                    output_files["json"] = str(result_path)

                duration_ms = round((time.monotonic() - t0) * 1000, 2)
                self.audit_trail["stages"]["export"] = {
                    "formats": formats,
                    "output_files": output_files,
                    "duration_ms": duration_ms,
                }
                self.logger.info(
                    "Export complete: %s", ", ".join(output_files.keys())
                )
            except Exception as e:
                self.logger.error(f"Export failed: {e}", extra={"stage": 6})
                raise

            self.audit_trail["completed_at"] = datetime.utcnow().isoformat()

            # Update the final audit trail in the result
            analysis_result.audit_trail = self.audit_trail
            return analysis_result

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            self.audit_trail["error"] = str(e)
            raise
