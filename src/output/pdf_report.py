"""PDF report generation for board presentations."""

import logging
import shutil
from pathlib import Path

from src.models import AnalysisResult

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Generates professional PDF report for board meetings.

    Content (Module 7 board meeting format):
    - Cover page with company and date
    - Executive Summary
    - 4 Chapters analysis with visualizations
    - 3 Big Measures highlight
    - Power of One levers (top 5)
    - Cash Quality Assessment
    - Risk/Opportunity Analysis
    - Financial statements (DRE, CF, BS)
    - Appendices with detailed tables

    Formatting:
    - Professional branding
    - Page breaks between sections
    - Embedded charts and tables
    - Interactive links (if PDF supports)
    - Portuguese language

    Uses reportlab or similar for PDF generation.

    Attributes:
        output_path: Path for PDF file
        company_name: Company name for report
    """

    def __init__(self, output_path: str, company_name: str = "Enterprise") -> None:
        """
        Initialize PDF report generator.

        Args:
            output_path: Path for output PDF file
            company_name: Company name for branding
        """
        self.output_path = Path(output_path)
        self.company_name = company_name
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self, analysis_result: AnalysisResult) -> Path:
        """
        Generate complete PDF report for board meeting.

        Delegates HTML generation to HTMLDashboardGenerator, then converts to
        PDF via weasyprint.  If weasyprint is not installed the method falls
        back to returning the HTML file and logs a warning.

        Args:
            analysis_result: Complete analysis results

        Returns:
            Path: Path to generated PDF (or HTML when weasyprint is absent)

        Raises:
            IOError: If file write fails
        """
        from src.output.html_dashboard import HTMLDashboardGenerator

        temp_html_path = self.output_path.with_suffix(".html")

        # Produce the HTML file that will be the source for the PDF.
        HTMLDashboardGenerator(str(temp_html_path)).generate(analysis_result)

        try:
            import weasyprint  # noqa: PLC0415

            try:
                weasyprint.HTML(filename=str(temp_html_path)).write_pdf(
                    str(self.output_path)
                )
                # Remove intermediate HTML only when PDF was successfully written.
                temp_html_path.unlink(missing_ok=True)
                return self.output_path
            except Exception as exc:
                logger.error(
                    "weasyprint falhou ao gerar PDF: %s. Retornando HTML.", exc
                )
                html_output = self.output_path.with_suffix(".html")
                if temp_html_path != html_output:
                    shutil.copy2(str(temp_html_path), str(html_output))
                return html_output

        except ImportError:
            logger.warning(
                "weasyprint não instalado. Gerando relatório em HTML. "
                "Instale com: pip install weasyprint"
            )
            html_output = self.output_path.with_suffix(".html")
            if temp_html_path != html_output:
                shutil.copy2(str(temp_html_path), str(html_output))
            return html_output

    # ------------------------------------------------------------------
    # Stub methods – not used in the HTML→PDF delegation approach but
    # retained as part of the public interface.
    # ------------------------------------------------------------------

    def _add_cover_page(self, analysis_result: AnalysisResult) -> None:
        """
        Add cover page with company info and date.

        Not used — HTML→PDF delegation handles this via HTMLDashboardGenerator.
        """
        pass

    def _add_executive_summary_section(self, analysis_result: AnalysisResult) -> None:
        """
        Add executive summary section.

        Not used — HTML→PDF delegation handles this via HTMLDashboardGenerator.
        """
        pass

    def _add_four_chapters_section(self, analysis_result: AnalysisResult) -> None:
        """
        Add detailed 4 Chapters analysis section.

        Each chapter on separate page with:
        - Chapter title and narrative
        - Key metrics table
        - Trend chart
        - Commentary

        Not used — HTML→PDF delegation handles this via HTMLDashboardGenerator.
        """
        pass

    def _add_power_of_one_section(self, analysis_result: AnalysisResult) -> None:
        """
        Add Power of One analysis section.

        Not used — HTML→PDF delegation handles this via HTMLDashboardGenerator.
        """
        pass

    def _add_financial_statements_appendix(
        self, analysis_result: AnalysisResult
    ) -> None:
        """
        Add appendix with detailed financial statements.

        Not used — HTML→PDF delegation handles this via HTMLDashboardGenerator.
        """
        pass
