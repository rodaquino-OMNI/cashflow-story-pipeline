"""HTML dashboard generation with inline CSS and Chart.js."""

from decimal import Decimal
from pathlib import Path
from typing import Any

from src.models import AnalysisResult


class HTMLDashboardGenerator:
    """
    Generates interactive HTML dashboard for CashFlow Story.

    Features:
    - Responsive design (mobile-friendly)
    - Interactive charts using Chart.js
    - 4 Chapters sections with expandable details
    - Power of One visualization
    - Cash Quality gauge charts
    - Key metrics cards
    - Drill-down capabilities

    Uses f-string templates for rendering (no Jinja2 dependency).

    Attributes:
        output_path: Path for HTML file
        template_dir: Path to Jinja2 template directory (kept for compatibility)
    """

    def __init__(
        self,
        output_path: str,
        template_dir: str | None = None
    ) -> None:
        """
        Initialize HTML dashboard generator.

        Args:
            output_path: Path for output HTML file
            template_dir: Path to templates (kept for API compatibility, unused)
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.template_dir = Path(template_dir) if template_dir else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, analysis_result: AnalysisResult) -> Path:
        """
        Generate interactive HTML dashboard.

        Args:
            analysis_result: Complete analysis results

        Returns:
            Path: Path to generated HTML file

        Raises:
            IOError: If file write fails
        """
        ctx = self._prepare_context(analysis_result)
        html = self._build_html(ctx, analysis_result)
        self.output_path.write_text(html, encoding="utf-8")
        return self.output_path

    # ------------------------------------------------------------------
    # Context preparation
    # ------------------------------------------------------------------

    def _prepare_context(self, analysis_result: AnalysisResult) -> dict[str, Any]:
        """
        Prepare context dictionary for rendering.

        Args:
            analysis_result: Analysis results

        Returns:
            Dict[str, Any]: Context for template rendering
        """
        periods = analysis_result.periods
        latest = periods[-1] if periods else None

        def _f(val: Any) -> float:
            """Convert Decimal or None to float."""
            if val is None:
                return 0.0
            if isinstance(val, Decimal):
                return float(val)
            return float(val)

        # KPI data from latest period
        kpis: dict[str, float] = {}
        if latest:
            kpis = {
                "net_revenue": _f(latest.net_revenue),
                "ebitda": _f(latest.ebitda),
                "ebitda_margin_pct": _f(latest.ebitda_margin_pct),
                "net_income": _f(latest.net_income),
                "net_margin_pct": _f(latest.net_margin_pct),
                "free_cash_flow": _f(latest.free_cash_flow),
                "operating_cash_flow": _f(latest.operating_cash_flow),
                "gross_margin_pct": _f(latest.gross_margin_pct),
                "current_ratio": _f(latest.current_ratio),
                "quick_ratio": _f(latest.quick_ratio),
                "debt_to_equity": _f(latest.debt_to_equity),
                "roe_pct": _f(latest.roe_pct),
                "roa_pct": _f(latest.roa_pct),
                "roce_pct": _f(latest.roce_pct),
                "days_sales_outstanding": _f(latest.days_sales_outstanding),
                "days_inventory_outstanding": _f(latest.days_inventory_outstanding),
                "days_payable_outstanding": _f(latest.days_payable_outstanding),
                "cash_conversion_cycle": _f(latest.cash_conversion_cycle),
                "working_capital": _f(latest.working_capital),
                "ppe_net": _f(latest.ppe_net),
                "intangibles_net": _f(latest.intangibles_net),
                "total_debt": _f(latest.total_debt),
                "net_debt": _f(latest.net_debt),
                "shareholders_equity": _f(latest.shareholders_equity),
                "investing_cash_flow": _f(latest.investing_cash_flow),
                "financing_cash_flow": _f(latest.financing_cash_flow),
                "net_cash_flow": _f(latest.net_cash_flow),
            }

        # Revenue trend data (all periods)
        period_labels: list[str] = [p.period for p in periods]
        revenue_data: list[float] = [_f(p.net_revenue) for p in periods]
        ebitda_data: list[float] = [_f(p.ebitda) for p in periods]
        net_income_data: list[float] = [_f(p.net_income) for p in periods]

        # Cash flow data for latest period waterfall
        cf_labels = ["FCO", "FCI", "FCF", "Fluxo Líquido"]
        cf_data: list[float] = []
        if latest:
            cf_data = [
                _f(latest.operating_cash_flow),
                _f(latest.investing_cash_flow),
                _f(latest.financing_cash_flow),
                _f(latest.net_cash_flow),
            ]
        else:
            cf_data = [0.0, 0.0, 0.0, 0.0]

        # Power of One data
        po1_labels: list[str] = []
        po1_cash_data: list[float] = []
        po1_profit_data: list[float] = []
        for lever in analysis_result.power_of_one:
            po1_labels.append(lever.label_pt)
            po1_cash_data.append(_f(lever.cash_impact))
            po1_profit_data.append(_f(lever.profit_impact))

        # Cash Quality data
        cq_items = []
        for cq in analysis_result.cash_quality:
            cq_items.append({
                "label": cq.label_pt,
                "value": _f(cq.value),
                "grade": cq.grade,
            })

        # Three Big Measures
        tbm: dict[str, Any] = {}
        if analysis_result.three_big_measures:
            tbm_obj = analysis_result.three_big_measures
            tbm = {
                "net_cash_flow": _f(tbm_obj.net_cash_flow),
                "operating_cash_flow": _f(tbm_obj.operating_cash_flow),
                "marginal_cash_flow": _f(tbm_obj.marginal_cash_flow),
                "interp_ncf": tbm_obj.interpretations.get(
                    "net_cash_flow", "Variação total de caixa no período."
                ),
                "interp_ocf": tbm_obj.interpretations.get(
                    "operating_cash_flow", "Caixa gerado pelas operações."
                ),
                "interp_mcf": tbm_obj.interpretations.get(
                    "marginal_cash_flow", "Diferença entre FCF% e variação de Capital de Giro%."
                ),
            }

        # Overall status based on latest net_cash_flow
        if latest:
            ncf = _f(latest.net_cash_flow)
            if ncf > 0:
                overall_status = "Positivo"
                status_color = "#27AE60"
            elif ncf < 0:
                overall_status = "Negativo"
                status_color = "#E74C3C"
            else:
                overall_status = "Neutro"
                status_color = "#F39C12"
        else:
            overall_status = "N/D"
            status_color = "#95A5A6"

        return {
            "company": analysis_result.company,
            "generated_at": analysis_result.generated_at.strftime("%d/%m/%Y %H:%M"),
            "overall_status": overall_status,
            "status_color": status_color,
            "kpis": kpis,
            "latest_period": latest.period if latest else "N/D",
            "period_labels": period_labels,
            "revenue_data": revenue_data,
            "ebitda_data": ebitda_data,
            "net_income_data": net_income_data,
            "cf_labels": cf_labels,
            "cf_data": cf_data,
            "po1_labels": po1_labels,
            "po1_cash_data": po1_cash_data,
            "po1_profit_data": po1_profit_data,
            "cq_items": cq_items,
            "tbm": tbm,
            "ai_insights": analysis_result.ai_insights,
            "multiple_periods": len(periods) > 1,
            "analysis_result": analysis_result,
        }

    # ------------------------------------------------------------------
    # Chapter cards
    # ------------------------------------------------------------------

    def _generate_chapter_cards(self, analysis_result: AnalysisResult) -> str:
        """
        Generate HTML for 4 Chapters expandable cards.

        Returns:
            str: HTML markup for chapter cards
        """
        periods = analysis_result.periods
        latest = periods[-1] if periods else None

        def _f(val: Any) -> float:
            if val is None:
                return 0.0
            if isinstance(val, Decimal):
                return float(val)
            return float(val)

        # ---- Chapter 1: Rentabilidade ----
        if latest:
            c1_rows = [
                ("Receita Bruta", _f(latest.gross_revenue), False),
                ("Receita Líquida", _f(latest.net_revenue), False),
                ("COGS", _f(latest.cogs), False),
                ("Lucro Bruto", _f(latest.gross_profit), False),
                ("Margem Bruta (%)", _f(latest.gross_margin_pct), True),
                ("EBITDA", _f(latest.ebitda), False),
                ("Margem EBITDA (%)", _f(latest.ebitda_margin_pct), True),
                ("EBIT", _f(latest.ebit), False),
                ("Lucro Líquido", _f(latest.net_income), False),
                ("Margem Líquida (%)", _f(latest.net_margin_pct), True),
            ]
            c1_metric = f"Margem EBITDA: {_f(latest.ebitda_margin_pct):.1f}%"
        else:
            c1_rows = []
            c1_metric = "N/D"

        # ---- Chapter 2: Capital de Giro ----
        if latest:
            c2_rows = [
                ("Contas a Receber", _f(latest.accounts_receivable), False),
                ("Estoques", _f(latest.inventory), False),
                ("Contas a Pagar", _f(latest.accounts_payable), False),
                ("DSO (dias)", _f(latest.days_sales_outstanding), True),
                ("DIO (dias)", _f(latest.days_inventory_outstanding), True),
                ("DPO (dias)", _f(latest.days_payable_outstanding), True),
                ("CCC (dias)", _f(latest.cash_conversion_cycle), True),
                ("Capital de Giro", _f(latest.working_capital), False),
            ]
            c2_metric = f"CCC: {_f(latest.cash_conversion_cycle):.0f} dias"
        else:
            c2_rows = []
            c2_metric = "N/D"

        # ---- Chapter 3: Outros Capitais ----
        if latest:
            c3_rows = [
                ("Imobilizado Líquido (PPE)", _f(latest.ppe_net), False),
                ("Intangível Líquido", _f(latest.intangibles_net), False),
                ("Outros Ativos Não Circulantes", _f(latest.other_capital_net), False),
                ("Investimento em Outros Capitais", _f(latest.other_capital_investment), False),
            ]
            c3_metric = f"PPE Líquido: {_f(latest.ppe_net):,.0f}"
        else:
            c3_rows = []
            c3_metric = "N/D"

        # ---- Chapter 4: Financiamento ----
        if latest:
            c4_rows = [
                ("Dívida Total", _f(latest.total_debt), False),
                ("Dívida Líquida", _f(latest.net_debt), False),
                ("Patrimônio Líquido", _f(latest.shareholders_equity), False),
                ("Índice Corrente", _f(latest.current_ratio), True),
                ("Índice Rápido", _f(latest.quick_ratio), True),
                ("Dívida / PL", _f(latest.debt_to_equity), True),
                ("ROE (%)", _f(latest.roe_pct), True),
                ("ROA (%)", _f(latest.roa_pct), True),
                ("ROCE (%)", _f(latest.roce_pct), True),
            ]
            c4_metric = f"D/E: {_f(latest.debt_to_equity):.2f}x"
        else:
            c4_rows = []
            c4_metric = "N/D"

        def build_table(rows: list) -> str:
            if not rows:
                return "<p>Dados não disponíveis.</p>"
            rows_html = ""
            for label, value, is_pct in rows:
                if is_pct:
                    val_str = f"{value:.1f}%"
                    val_class = "value-pct"
                else:
                    val_str = _fmt_brl_html(value)
                    positive = value >= 0
                    val_class = "value-positive" if positive else "value-negative"
                rows_html += (
                    f'<tr>'
                    f'<td class="td-label">{label}</td>'
                    f'<td class="td-value {val_class}">{val_str}</td>'
                    f'</tr>'
                )
            return f'<table class="detail-table"><tbody>{rows_html}</tbody></table>'

        chapters = [
            {
                "id": "cap1",
                "number": "1",
                "title": "Rentabilidade",
                "icon": "&#128200;",
                "metric": c1_metric,
                "table": build_table(c1_rows),
                "color": "#2980B9",
            },
            {
                "id": "cap2",
                "number": "2",
                "title": "Capital de Giro",
                "icon": "&#9851;",
                "metric": c2_metric,
                "table": build_table(c2_rows),
                "color": "#27AE60",
            },
            {
                "id": "cap3",
                "number": "3",
                "title": "Outros Capitais",
                "icon": "&#127981;",
                "metric": c3_metric,
                "table": build_table(c3_rows),
                "color": "#8E44AD",
            },
            {
                "id": "cap4",
                "number": "4",
                "title": "Financiamento",
                "icon": "&#127968;",
                "metric": c4_metric,
                "table": build_table(c4_rows),
                "color": "#E67E22",
            },
        ]

        cards_html = ""
        for ch in chapters:
            cards_html += f"""
            <div class="chapter-card" id="card-{ch['id']}">
                <div class="chapter-header" onclick="toggleChapter('{ch['id']}')"
                     style="border-left: 5px solid {ch['color']};">
                    <div class="chapter-title-group">
                        <span class="chapter-icon">{ch['icon']}</span>
                        <div>
                            <div class="chapter-label">Capítulo {ch['number']}</div>
                            <div class="chapter-title">{ch['title']}</div>
                        </div>
                    </div>
                    <div class="chapter-meta">
                        <span class="chapter-metric">{ch['metric']}</span>
                        <span class="chapter-toggle" id="toggle-{ch['id']}">&#9660;</span>
                    </div>
                </div>
                <div class="chapter-body" id="body-{ch['id']}">
                    {ch['table']}
                </div>
            </div>"""

        return cards_html

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    def _generate_charts(self, analysis_result: AnalysisResult) -> str:
        """
        Generate Chart.js scripts for visualizations.

        Returns:
            str: JavaScript code for all charts
        """
        ctx = self._prepare_context(analysis_result)

        period_labels_json = _to_js_str_array(ctx["period_labels"])
        revenue_json = _to_js_num_array(ctx["revenue_data"])
        ebitda_json = _to_js_num_array(ctx["ebitda_data"])
        net_income_json = _to_js_num_array(ctx["net_income_data"])
        cf_labels_json = _to_js_str_array(ctx["cf_labels"])
        cf_data_json = _to_js_num_array(ctx["cf_data"])

        cf_colors = []
        for v in ctx["cf_data"]:
            if v >= 0:
                cf_colors.append("rgba(39, 174, 96, 0.85)")
            else:
                cf_colors.append("rgba(231, 76, 60, 0.85)")
        cf_colors_json = "[" + ", ".join(f'"{c}"' for c in cf_colors) + "]"

        # Revenue trend chart (only if multiple periods)
        revenue_chart_js = ""
        if ctx["multiple_periods"]:
            revenue_chart_js = f"""
            // Revenue Trend Chart
            (function() {{
                const ctx = document.getElementById('revenueChart');
                if (!ctx) return;
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {period_labels_json},
                        datasets: [
                            {{
                                label: 'Receita Líquida',
                                data: {revenue_json},
                                borderColor: '#2980B9',
                                backgroundColor: 'rgba(41, 128, 185, 0.1)',
                                borderWidth: 2,
                                fill: true,
                                tension: 0.3,
                                pointRadius: 4,
                            }},
                            {{
                                label: 'EBITDA',
                                data: {ebitda_json},
                                borderColor: '#27AE60',
                                backgroundColor: 'rgba(39, 174, 96, 0.1)',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.3,
                                pointRadius: 4,
                            }},
                            {{
                                label: 'Lucro Líquido',
                                data: {net_income_json},
                                borderColor: '#E74C3C',
                                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.3,
                                pointRadius: 4,
                            }},
                        ]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{ position: 'top' }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(ctx) {{
                                        return ctx.dataset.label + ': ' + formatBRL(ctx.parsed.y);
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                ticks: {{
                                    callback: function(val) {{ return formatBRL(val); }}
                                }}
                            }}
                        }}
                    }}
                }});
            }})();
"""

        cash_flow_chart_js = f"""
            // Cash Flow Bar Chart
            (function() {{
                const ctx = document.getElementById('cashFlowChart');
                if (!ctx) return;
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {cf_labels_json},
                        datasets: [{{
                            label: 'Fluxo de Caixa',
                            data: {cf_data_json},
                            backgroundColor: {cf_colors_json},
                            borderColor: {cf_colors_json},
                            borderWidth: 1,
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(ctx) {{
                                        return 'Valor: ' + formatBRL(ctx.parsed.y);
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                ticks: {{
                                    callback: function(val) {{ return formatBRL(val); }}
                                }}
                            }}
                        }}
                    }}
                }});
            }})();
"""

        return revenue_chart_js + cash_flow_chart_js

    # ------------------------------------------------------------------
    # Power of One
    # ------------------------------------------------------------------

    def _generate_power_of_one_visualization(self, analysis_result: AnalysisResult) -> str:
        """
        Generate Power of One lever visualization HTML/JS.

        Returns:
            str: HTML/JS for Power of One display
        """
        levers = analysis_result.power_of_one
        if not levers:
            return '<p class="no-data">Nenhum dado de Power of One disponível.</p>'

        def _f(val: Any) -> float:
            if val is None:
                return 0.0
            if isinstance(val, Decimal):
                return float(val)
            return float(val)

        po1_labels = [lv.label_pt for lv in levers]
        po1_cash = [_f(lv.cash_impact) for lv in levers]
        po1_profit = [_f(lv.profit_impact) for lv in levers]

        labels_json = _to_js_str_array(po1_labels)
        cash_json = _to_js_num_array(po1_cash)
        profit_json = _to_js_num_array(po1_profit)

        cash_colors = [
            "rgba(39, 174, 96, 0.85)" if v >= 0 else "rgba(231, 76, 60, 0.85)"
            for v in po1_cash
        ]
        cash_colors_json = "[" + ", ".join(f'"{c}"' for c in cash_colors) + "]"

        html = """
        <div class="chart-container">
            <canvas id="po1Chart"></canvas>
        </div>
        <script>
        (function() {
            const ctx = document.getElementById('po1Chart');
            if (!ctx) return;
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: """ + labels_json + """,
                    datasets: [
                        {
                            label: 'Impacto no Caixa',
                            data: """ + cash_json + """,
                            backgroundColor: """ + cash_colors_json + """,
                            borderWidth: 1,
                        },
                        {
                            label: 'Impacto no Lucro',
                            data: """ + profit_json + """,
                            backgroundColor: 'rgba(41, 128, 185, 0.65)',
                            borderWidth: 1,
                        },
                    ]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.dataset.label + ': ' + formatBRL(ctx.parsed.x);
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                callback: function(val) { return formatBRL(val); }
                            }
                        }
                    }
                }
            });
        })();
        </script>
"""
        return html

    # ------------------------------------------------------------------
    # Cash Quality
    # ------------------------------------------------------------------

    def _generate_cash_quality_gauges(self, analysis_result: AnalysisResult) -> str:
        """
        Generate Cash Quality grade badges/cards.

        Returns:
            str: HTML for cash quality display
        """
        cq_list = analysis_result.cash_quality
        if not cq_list:
            return '<p class="no-data">Nenhuma métrica de qualidade de caixa disponível.</p>'

        def _f(val: Any) -> float:
            if val is None:
                return 0.0
            if isinstance(val, Decimal):
                return float(val)
            return float(val)

        grade_color = {
            "G": "#27AE60",
            "A": "#F39C12",
            "B": "#E74C3C",
        }
        grade_label = {
            "G": "Bom",
            "A": "Regular",
            "B": "Abaixo",
        }

        html = '<div class="cq-grid">'
        for cq in cq_list:
            color = grade_color.get(cq.grade, "#95A5A6")
            label = grade_label.get(cq.grade, cq.grade)
            value = _f(cq.value)
            val_display = f"{value:.1f}"
            html += f"""
            <div class="cq-card">
                <div class="cq-badge" style="background-color: {color};">{cq.grade}</div>
                <div class="cq-label">{cq.label_pt}</div>
                <div class="cq-value">{val_display}</div>
                <div class="cq-grade-label" style="color: {color};">{label}</div>
            </div>"""

        html += "</div>"
        return html

    # ------------------------------------------------------------------
    # Full HTML builder
    # ------------------------------------------------------------------

    def _build_html(self, ctx: dict[str, Any], analysis_result: AnalysisResult) -> str:
        """Build the complete self-contained HTML document."""
        kpis = ctx["kpis"]
        tbm = ctx["tbm"]
        ai_insights = ctx["ai_insights"]
        company = ctx["company"]
        generated_at = ctx["generated_at"]
        overall_status = ctx["overall_status"]
        status_color = ctx["status_color"]

        def brl(val: float) -> str:
            """Format value as Brazilian currency in Python (for static rendering)."""
            negative = val < 0
            val = abs(val)
            integer_part = int(val)
            decimal_part = round((val - integer_part) * 100)
            # Group thousands
            s = str(integer_part)
            groups = []
            while len(s) > 3:
                groups.insert(0, s[-3:])
                s = s[:-3]
            groups.insert(0, s)
            formatted = ".".join(groups) + f",{decimal_part:02d}"
            return ("(R$ " + formatted + ")") if negative else ("R$ " + formatted)

        def pct(val: float, decimals: int = 1) -> str:
            return f"{val:.{decimals}f}%"

        # Three Big Measures HTML
        if tbm:
            three_big_html = f"""
            <section class="section" id="three-big">
                <h2 class="section-title">As 3 Grandes Medidas</h2>
                <div class="kpi-grid three-col">
                    <div class="kpi-card">
                        <div class="kpi-icon">&#128181;</div>
                        <div class="kpi-label">Fluxo de Caixa Líquido</div>
                        <div class="kpi-value {'kpi-positive' if tbm['net_cash_flow'] >= 0 else 'kpi-negative'}">{brl(tbm['net_cash_flow'])}</div>
                        <div class="kpi-interp">{tbm['interp_ncf']}</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon">&#9881;</div>
                        <div class="kpi-label">Fluxo de Caixa Operacional</div>
                        <div class="kpi-value {'kpi-positive' if tbm['operating_cash_flow'] >= 0 else 'kpi-negative'}">{brl(tbm['operating_cash_flow'])}</div>
                        <div class="kpi-interp">{tbm['interp_ocf']}</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon">&#128200;</div>
                        <div class="kpi-label">Fluxo de Caixa Marginal</div>
                        <div class="kpi-value {'kpi-positive' if tbm['marginal_cash_flow'] >= 0 else 'kpi-negative'}">{pct(tbm['marginal_cash_flow'])}</div>
                        <div class="kpi-interp">{tbm['interp_mcf']}</div>
                    </div>
                </div>
            </section>"""
        else:
            three_big_html = ""

        # Revenue trend chart section (only when multiple periods)
        if ctx["multiple_periods"]:
            revenue_chart_section = """
            <section class="section" id="trend-section">
                <h2 class="section-title">Tendência de Receita e Resultados</h2>
                <div class="chart-container">
                    <canvas id="revenueChart"></canvas>
                </div>
            </section>"""
        else:
            revenue_chart_section = ""

        # AI Insights section
        if ai_insights:
            ai_section = f"""
            <section class="section" id="ai-section">
                <h2 class="section-title">&#129504; Insights de IA</h2>
                <div class="ai-insights-box">
                    <div class="ai-insights-content">{ai_insights.replace(chr(10), '<br>')}</div>
                </div>
            </section>"""
        else:
            ai_section = ""

        # Chapter cards
        chapter_cards_html = self._generate_chapter_cards(analysis_result)

        # Cash quality
        cq_html = self._generate_cash_quality_gauges(analysis_result)

        # Power of One section
        po1_section_content = self._generate_power_of_one_visualization(analysis_result)

        # Chart scripts
        chart_scripts = self._generate_charts(analysis_result)
        # Power of One chart script is already embedded inside po1_section_content
        # but we strip the <script> from it and put it at bottom for clarity.
        # Actually keep it embedded for simpler structure — it is already inside a <script> tag.

        # KPI cards from latest period
        kpi_items = [
            ("Receita Líquida", brl(kpis.get("net_revenue", 0.0)), "&#128176;"),
            ("EBITDA", f"{brl(kpis.get('ebitda', 0.0))} ({pct(kpis.get('ebitda_margin_pct', 0.0))})", "&#128184;"),
            ("Lucro Líquido", f"{brl(kpis.get('net_income', 0.0))} ({pct(kpis.get('net_margin_pct', 0.0))})", "&#127381;"),
            ("Fluxo de Caixa Livre", brl(kpis.get("free_cash_flow", 0.0)), "&#128181;"),
        ] if kpis else []

        kpi_cards_html = ""
        for label, value, icon in kpi_items:
            kpi_cards_html += f"""
                <div class="kpi-card">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{ctx['latest_period']}</div>
                </div>"""

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CashFlow Story - {company}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* ========== Reset & Base ========== */
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #F5F5F5;
            color: #2C3E50;
            font-size: 14px;
            line-height: 1.5;
        }}
        a {{ color: #2980B9; text-decoration: none; }}

        /* ========== Header ========== */
        .site-header {{
            background: #1F4E79;
            color: #fff;
            padding: 24px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .header-left h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .header-left .subtitle {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 4px;
        }}
        .header-right {{
            text-align: right;
        }}
        .status-badge {{
            display: inline-block;
            padding: 6px 18px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1rem;
            background: {status_color};
            color: #fff;
            margin-bottom: 4px;
        }}
        .header-date {{
            font-size: 0.8rem;
            opacity: 0.75;
        }}

        /* ========== Layout ========== */
        .main-content {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 24px 16px 48px;
        }}
        .section {{
            margin-bottom: 32px;
        }}
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #1F4E79;
            border-bottom: 2px solid #1F4E79;
            padding-bottom: 6px;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* ========== KPI Grid ========== */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }}
        .kpi-grid.three-col {{
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        }}
        .kpi-card {{
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.15s;
        }}
        .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}
        .kpi-icon {{ font-size: 1.8rem; margin-bottom: 8px; }}
        .kpi-label {{ font-size: 0.78rem; color: #7F8C8D; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
        .kpi-value {{ font-size: 1.2rem; font-weight: 700; color: #1F4E79; word-break: break-word; }}
        .kpi-sub {{ font-size: 0.75rem; color: #95A5A6; margin-top: 4px; }}
        .kpi-interp {{ font-size: 0.8rem; color: #555; margin-top: 8px; font-style: italic; }}
        .kpi-positive {{ color: #27AE60 !important; }}
        .kpi-negative {{ color: #E74C3C !important; }}

        /* ========== Chapter Cards ========== */
        .chapters-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }}
        .chapter-card {{
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        .chapter-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 16px;
            cursor: pointer;
            user-select: none;
            background: #FAFAFA;
            transition: background 0.15s;
        }}
        .chapter-header:hover {{ background: #EAF2FB; }}
        .chapter-title-group {{ display: flex; align-items: center; gap: 10px; }}
        .chapter-icon {{ font-size: 1.4rem; }}
        .chapter-label {{ font-size: 0.7rem; color: #7F8C8D; text-transform: uppercase; letter-spacing: 0.5px; }}
        .chapter-title {{ font-size: 1rem; font-weight: 700; color: #2C3E50; }}
        .chapter-meta {{ display: flex; align-items: center; gap: 10px; }}
        .chapter-metric {{ font-size: 0.82rem; color: #555; font-weight: 600; }}
        .chapter-toggle {{ font-size: 0.9rem; color: #7F8C8D; transition: transform 0.2s; display: inline-block; }}
        .chapter-toggle.open {{ transform: rotate(180deg); }}
        .chapter-body {{ display: none; padding: 0 16px 16px; }}
        .chapter-body.open {{ display: block; }}

        /* ========== Detail Tables ========== */
        .detail-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        .detail-table td {{ padding: 7px 4px; border-bottom: 1px solid #ECF0F1; vertical-align: middle; }}
        .td-label {{ color: #555; font-size: 0.82rem; }}
        .td-value {{ text-align: right; font-weight: 600; font-size: 0.85rem; }}
        .value-positive {{ color: #27AE60; }}
        .value-negative {{ color: #E74C3C; }}
        .value-pct {{ color: #2980B9; }}

        /* ========== Charts ========== */
        .chart-container {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .chart-container canvas {{ max-height: 340px; }}

        /* ========== Cash Quality ========== */
        .cq-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 14px;
        }}
        .cq-card {{
            background: #fff;
            border-radius: 8px;
            padding: 16px 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
        }}
        .cq-badge {{
            display: inline-block;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            color: #fff;
            font-size: 1.3rem;
            font-weight: 700;
            line-height: 44px;
            margin-bottom: 8px;
        }}
        .cq-label {{ font-size: 0.78rem; color: #555; margin-bottom: 4px; font-weight: 600; }}
        .cq-value {{ font-size: 1rem; font-weight: 700; color: #2C3E50; }}
        .cq-grade-label {{ font-size: 0.75rem; font-weight: 600; margin-top: 4px; }}

        /* ========== AI Insights ========== */
        .ai-insights-box {{
            background: #EAF2FB;
            border-left: 4px solid #2980B9;
            border-radius: 0 8px 8px 0;
            padding: 20px 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .ai-insights-content {{ font-size: 0.9rem; color: #2C3E50; line-height: 1.7; white-space: pre-wrap; }}

        /* ========== Footer ========== */
        .site-footer {{
            background: #1F4E79;
            color: rgba(255,255,255,0.7);
            text-align: center;
            padding: 16px;
            font-size: 0.78rem;
        }}

        /* ========== Utility ========== */
        .no-data {{ color: #95A5A6; font-style: italic; padding: 12px 0; }}

        /* ========== Print ========== */
        @media print {{
            .site-header {{ background: #1F4E79 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .chapter-body {{ display: block !important; }}
            .chapter-toggle {{ display: none; }}
            .kpi-card, .chapter-card, .cq-card, .chart-container {{ box-shadow: none; border: 1px solid #ddd; }}
            body {{ background: #fff; }}
            .main-content {{ padding: 8px; }}
        }}

        /* ========== Responsive ========== */
        @media (max-width: 600px) {{
            .site-header {{ padding: 16px; }}
            .header-left h1 {{ font-size: 1.3rem; }}
            .kpi-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
</head>
<body>

<!-- ===== HEADER ===== -->
<header class="site-header">
    <div class="header-left">
        <h1>&#128200; CashFlow Story</h1>
        <div class="subtitle">{company}</div>
    </div>
    <div class="header-right">
        <div class="status-badge">{overall_status}</div>
        <div class="header-date">Gerado em: {generated_at}</div>
    </div>
</header>

<!-- ===== MAIN ===== -->
<main class="main-content">

    <!-- KPIs -->
    <section class="section" id="kpis">
        <h2 class="section-title">Indicadores Principais &mdash; {ctx['latest_period']}</h2>
        <div class="kpi-grid">
            {kpi_cards_html}
        </div>
    </section>

    <!-- 3 Big Measures -->
    {three_big_html}

    <!-- Revenue Trend -->
    {revenue_chart_section}

    <!-- Cash Flow Chart -->
    <section class="section" id="cashflow-section">
        <h2 class="section-title">Fluxo de Caixa &mdash; {ctx['latest_period']}</h2>
        <div class="chart-container">
            <canvas id="cashFlowChart"></canvas>
        </div>
    </section>

    <!-- 4 Chapters -->
    <section class="section" id="chapters">
        <h2 class="section-title">Os 4 Capítulos do Caixa</h2>
        <div class="chapters-grid">
            {chapter_cards_html}
        </div>
    </section>

    <!-- Power of One -->
    <section class="section" id="po1-section">
        <h2 class="section-title">&#128270; Power of One &mdash; Impacto de 1% em Cada Alavanca</h2>
        {po1_section_content}
    </section>

    <!-- Cash Quality -->
    <section class="section" id="cq-section">
        <h2 class="section-title">&#127919; Qualidade do Caixa</h2>
        {cq_html}
    </section>

    <!-- AI Insights -->
    {ai_section}

</main>

<!-- ===== FOOTER ===== -->
<footer class="site-footer">
    CashFlow Story Pipeline &mdash; Gerado em {generated_at} &mdash; {company}
</footer>

<!-- ===== SCRIPTS ===== -->
<script>
    // ---- Brazilian currency formatter ----
    function formatBRL(value) {{
        if (value === null || value === undefined) return 'R$ 0,00';
        var negative = value < 0;
        var abs = Math.abs(value);
        var intPart = Math.floor(abs);
        var decPart = Math.round((abs - intPart) * 100);
        var intStr = intPart.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '.');
        var formatted = 'R$ ' + intStr + ',' + String(decPart).padStart(2, '0');
        return negative ? '(' + formatted + ')' : formatted;
    }}

    // ---- Chapter toggle ----
    function toggleChapter(id) {{
        var body = document.getElementById('body-' + id);
        var toggle = document.getElementById('toggle-' + id);
        if (body && toggle) {{
            var isOpen = body.classList.contains('open');
            body.classList.toggle('open', !isOpen);
            toggle.classList.toggle('open', !isOpen);
        }}
    }}

    // Auto-open Chapter 1 on load
    document.addEventListener('DOMContentLoaded', function() {{
        toggleChapter('cap1');
    }});
</script>

<script>
{chart_scripts}
</script>

</body>
</html>"""
        return html


# ------------------------------------------------------------------
# Module-level helpers (private)
# ------------------------------------------------------------------

def _to_js_str_array(items: list[str]) -> str:
    """Convert a Python list of strings to a JS array literal."""
    escaped = [s.replace("\\", "\\\\").replace("'", "\\'") for s in items]
    inner = ", ".join(f"'{e}'" for e in escaped)
    return f"[{inner}]"


def _to_js_num_array(items: list[float]) -> str:
    """Convert a Python list of floats to a JS array literal."""
    inner = ", ".join(str(round(v, 2)) for v in items)
    return f"[{inner}]"


def _fmt_brl_html(value: float) -> str:
    """Format a float as Brazilian Real string for static HTML output."""
    negative = value < 0
    abs_val = abs(value)
    integer_part = int(abs_val)
    decimal_part = round((abs_val - integer_part) * 100)
    s = str(integer_part)
    groups: list[str] = []
    while len(s) > 3:
        groups.insert(0, s[-3:])
        s = s[:-3]
    groups.insert(0, s)
    formatted = "R$ " + ".".join(groups) + f",{decimal_part:02d}"
    return f"({formatted})" if negative else formatted
