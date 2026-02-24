"""Power of One analysis - sensitivity of 1% changes on profit and cash."""

from decimal import Decimal

from src.models import PeriodResult, PowerOfOneLever


def calculate_power_of_one(period_result: PeriodResult) -> list[PowerOfOneLever]:
    """
    Calculate Power of One analysis: impact of a 1-unit change on each lever.

    The 7 Key Levers:
      Chapter 1 (Profitability): Revenue +1%, COGS -1%, OpEx -1%
      Chapter 2 (Working Capital): AR -1 day, Inventory -1 day, AP +1 day
      Chapter 3 (Other Capital): CAPEX -1%

    Args:
        period_result: PeriodResult with all calculations for the period.

    Returns:
        List of 7 PowerOfOneLever objects sorted by abs(cash_impact) descending.
    """
    ZERO = Decimal("0")
    ONE_PCT = Decimal("0.01")
    VALUATION_MULTIPLE = Decimal("6.0")
    DAYS_IN_YEAR = Decimal("365")
    DEPRECIATION_FACTOR = Decimal("0.10")

    pr = period_result
    levers: list[PowerOfOneLever] = []

    # --- Chapter 1: Profitability levers ---

    # 1. REVENUE: 1% increase
    revenue_change = pr.net_revenue * ONE_PCT
    ebit_margin = (
        pr.ebit_margin_pct / Decimal("100")
        if pr.ebit_margin_pct != ZERO
        else ZERO
    )
    revenue_profit = revenue_change * ebit_margin
    levers.append(
        PowerOfOneLever(
            lever="revenue",
            label_pt="Receita",
            current_value=pr.net_revenue,
            change_amount=revenue_change,
            change_unit="%",
            profit_impact=revenue_profit,
            cash_impact=revenue_profit,
            value_impact=revenue_profit * VALUATION_MULTIPLE,
            category="Chapter 1",
        )
    )

    # 2. COGS: 1% reduction
    cogs_change = pr.cogs * ONE_PCT
    levers.append(
        PowerOfOneLever(
            lever="cogs",
            label_pt="Custo dos Produtos/Serviços",
            current_value=pr.cogs,
            change_amount=cogs_change,
            change_unit="%",
            profit_impact=cogs_change,
            cash_impact=cogs_change,
            value_impact=cogs_change * VALUATION_MULTIPLE,
            category="Chapter 1",
        )
    )

    # 3. OVERHEAD / OPEX: 1% reduction
    opex_change = pr.operating_expenses * ONE_PCT
    levers.append(
        PowerOfOneLever(
            lever="overhead",
            label_pt="Despesas Operacionais",
            current_value=pr.operating_expenses,
            change_amount=opex_change,
            change_unit="%",
            profit_impact=opex_change,
            cash_impact=opex_change,
            value_impact=opex_change * VALUATION_MULTIPLE,
            category="Chapter 1",
        )
    )

    # --- Chapter 2: Working Capital levers ---

    daily_revenue = (
        pr.net_revenue / DAYS_IN_YEAR if pr.net_revenue != ZERO else ZERO
    )
    daily_cogs = pr.cogs / DAYS_IN_YEAR if pr.cogs != ZERO else ZERO

    # 4. AR DAYS: 1-day reduction
    ar_cash_freed = daily_revenue
    levers.append(
        PowerOfOneLever(
            lever="ar_days",
            label_pt="Prazo de Recebimento",
            current_value=pr.days_sales_outstanding,
            change_amount=Decimal("1"),
            change_unit="dias",
            profit_impact=ZERO,
            cash_impact=ar_cash_freed,
            value_impact=ar_cash_freed,
            category="Chapter 2",
        )
    )

    # 5. INVENTORY DAYS: 1-day reduction
    inv_cash_freed = daily_cogs
    levers.append(
        PowerOfOneLever(
            lever="inventory_days",
            label_pt="Prazo de Estoque",
            current_value=pr.days_inventory_outstanding,
            change_amount=Decimal("1"),
            change_unit="dias",
            profit_impact=ZERO,
            cash_impact=inv_cash_freed,
            value_impact=inv_cash_freed,
            category="Chapter 2",
        )
    )

    # 6. AP DAYS: 1-day increase (extending payables frees cash)
    ap_cash_freed = daily_cogs
    levers.append(
        PowerOfOneLever(
            lever="ap_days",
            label_pt="Prazo de Pagamento",
            current_value=pr.days_payable_outstanding,
            change_amount=Decimal("1"),
            change_unit="dias",
            profit_impact=ZERO,
            cash_impact=ap_cash_freed,
            value_impact=ap_cash_freed,
            category="Chapter 2",
        )
    )

    # --- Chapter 3: Other Capital lever ---

    # 7. CAPEX: 1% reduction
    capex = abs(pr.other_capital_investment)
    capex_change = capex * ONE_PCT
    levers.append(
        PowerOfOneLever(
            lever="capex",
            label_pt="Investimentos (CAPEX)",
            current_value=capex,
            change_amount=capex_change,
            change_unit="%",
            profit_impact=capex_change * DEPRECIATION_FACTOR,
            cash_impact=capex_change,
            value_impact=capex_change,
            category="Chapter 3",
        )
    )

    # Sort by absolute cash impact, highest first
    levers.sort(key=lambda lv: abs(lv.cash_impact), reverse=True)

    return levers
