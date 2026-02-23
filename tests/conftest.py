"""Shared pytest fixtures with realistic AUSTA data."""
import pytest
from decimal import Decimal
from datetime import date
from typing import Dict, Any


@pytest.fixture
def sample_mapped_data_q1() -> Dict[str, Any]:
    """
    Q1 2025 AUSTA financial data.
    
    Revenue: R$40.1M
    COGS: R$30.65M
    AR: R$18.5M
    Cash: R$2.9M → R$1.2M (deterioration)
    """
    return {
        'period': 'Q1_2025',
        'period_start': date(2025, 1, 1),
        'period_end': date(2025, 3, 31),
        'empresa': {
            'nome': 'AUSTA Manufacturing',
            'cnpj': '12.345.678/0001-90',
        },
        'balance_sheet': {
            'current_assets': {
                'cash': Decimal('1200000.00'),  # R$1.2M (end of period)
                'cash_beginning': Decimal('2900000.00'),  # R$2.9M (beginning)
                'accounts_receivable': Decimal('18500000.00'),  # R$18.5M
                'inventory': Decimal('3200000.00'),  # R$3.2M
            },
            'fixed_assets': {
                'ppe': Decimal('45000000.00'),  # R$45M (Imobilizado)
            },
            'current_liabilities': {
                'accounts_payable': Decimal('8900000.00'),  # R$8.9M
                'short_term_debt': Decimal('12000000.00'),  # R$12M
            },
            'long_term_liabilities': {
                'long_term_debt': Decimal('25000000.00'),  # R$25M
            },
            'equity': {
                'patrimonio_liquido': Decimal('35000000.00'),  # R$35M
            },
        },
        'income_statement': {
            'revenue': Decimal('40100000.00'),  # R$40.1M
            'deductions': Decimal('2500000.00'),  # R$2.5M (ICMS, ISS, PIS, COFINS)
            'financial_income': Decimal('150000.00'),  # R$150K
            'cogs': Decimal('30650000.00'),  # R$30.65M (from 4.1 Custos R$22.4M + reclassified R$8.25M)
            'operating_expenses': Decimal('19650000.00'),  # R$19.65M (from 4.2 excluding reclassified)
            'financial_expenses': Decimal('1200000.00'),  # R$1.2M
        },
        'mapped_accounts': {
            '1.1.01': {'description': 'Caixa', 'value': Decimal('1200000.00')},
            '1.1.03': {'description': 'Contas a Receber', 'value': Decimal('18500000.00')},
            '1.1.04': {'description': 'Estoque', 'value': Decimal('3200000.00')},
            '1.2.03': {'description': 'Imobilizado', 'value': Decimal('45000000.00')},
            '2.1.01': {'description': 'Fornecedores', 'value': Decimal('8900000.00')},
            '2.1.02': {'description': 'Empréstimos CP', 'value': Decimal('12000000.00')},
            '2.2.01': {'description': 'Empréstimos LP', 'value': Decimal('25000000.00')},
            '2.3': {'description': 'Patrimônio Líquido', 'value': Decimal('35000000.00')},
            '3.1': {'description': 'Receita', 'value': Decimal('40100000.00')},
            '3.2': {'description': 'Deduções', 'value': Decimal('2500000.00')},
            '3.3': {'description': 'Receitas Financeiras', 'value': Decimal('150000.00')},
            '4.1': {'description': 'Custos', 'value': Decimal('22400000.00')},
            '4.2': {'description': 'Despesas Operacionais', 'value': Decimal('19650000.00')},
            '4.2.01': {'description': 'Pessoal e Serviços', 'value': Decimal('6500000.00')},
            '4.2.02': {'description': 'Materiais e Serviços', 'value': Decimal('1750000.00')},
            '4.3': {'description': 'Despesas Financeiras', 'value': Decimal('1200000.00')},
        },
    }


@pytest.fixture
def sample_mapped_data_q2() -> Dict[str, Any]:
    """
    Q2 2025 AUSTA financial data.
    
    Revenue: R$42.5M
    Shows severe cash deterioration to R$394K
    """
    return {
        'period': 'Q2_2025',
        'period_start': date(2025, 4, 1),
        'period_end': date(2025, 6, 30),
        'empresa': {
            'nome': 'AUSTA Manufacturing',
            'cnpj': '12.345.678/0001-90',
        },
        'balance_sheet': {
            'current_assets': {
                'cash': Decimal('394000.00'),  # R$394K (critical level)
                'cash_beginning': Decimal('1200000.00'),  # R$1.2M (from Q1)
                'accounts_receivable': Decimal('19800000.00'),  # R$19.8M (increase)
                'inventory': Decimal('3500000.00'),  # R$3.5M (slight increase)
            },
            'fixed_assets': {
                'ppe': Decimal('45000000.00'),  # R$45M (unchanged)
            },
            'current_liabilities': {
                'accounts_payable': Decimal('9200000.00'),  # R$9.2M (increase)
                'short_term_debt': Decimal('12500000.00'),  # R$12.5M (increase)
            },
            'long_term_liabilities': {
                'long_term_debt': Decimal('25000000.00'),  # R$25M (unchanged)
            },
            'equity': {
                'patrimonio_liquido': Decimal('35900000.00'),  # R$35.9M (increased by Q2 profit)
            },
        },
        'income_statement': {
            'revenue': Decimal('42500000.00'),  # R$42.5M
            'deductions': Decimal('2650000.00'),  # R$2.65M
            'financial_income': Decimal('175000.00'),  # R$175K
            'cogs': Decimal('31875000.00'),  # R$31.875M
            'operating_expenses': Decimal('20500000.00'),  # R$20.5M
            'financial_expenses': Decimal('1400000.00'),  # R$1.4M
        },
        'mapped_accounts': {
            '1.1.01': {'description': 'Caixa', 'value': Decimal('394000.00')},
            '1.1.03': {'description': 'Contas a Receber', 'value': Decimal('19800000.00')},
            '1.1.04': {'description': 'Estoque', 'value': Decimal('3500000.00')},
            '1.2.03': {'description': 'Imobilizado', 'value': Decimal('45000000.00')},
            '2.1.01': {'description': 'Fornecedores', 'value': Decimal('9200000.00')},
            '2.1.02': {'description': 'Empréstimos CP', 'value': Decimal('12500000.00')},
            '2.2.01': {'description': 'Empréstimos LP', 'value': Decimal('25000000.00')},
            '2.3': {'description': 'Patrimônio Líquido', 'value': Decimal('35900000.00')},
            '3.1': {'description': 'Receita', 'value': Decimal('42500000.00')},
            '3.2': {'description': 'Deduções', 'value': Decimal('2650000.00')},
            '3.3': {'description': 'Receitas Financeiras', 'value': Decimal('175000.00')},
            '4.1': {'description': 'Custos', 'value': Decimal('23625000.00')},
            '4.2': {'description': 'Despesas Operacionais', 'value': Decimal('20500000.00')},
            '4.3': {'description': 'Despesas Financeiras', 'value': Decimal('1400000.00')},
        },
    }


@pytest.fixture
def sample_period_result() -> Dict[str, Any]:
    """Pre-calculated PeriodResult for downstream testing."""
    return {
        'period': 'Q1_2025',
        'period_start': date(2025, 1, 1),
        'period_end': date(2025, 3, 31),
        'empresa': {
            'nome': 'AUSTA Manufacturing',
            'cnpj': '12.345.678/0001-90',
        },
        'metrics': {
            'profitability': {
                'gross_margin': Decimal('0.2360'),  # (40.1M - 30.65M) / 40.1M
                'operating_margin': Decimal('0.0140'),
                'net_margin': Decimal('-0.0070'),
            },
            'liquidity': {
                'current_ratio': Decimal('1.1234'),  # Current assets / Current liabilities
                'quick_ratio': Decimal('1.0534'),
                'cash_ratio': Decimal('0.0485'),
            },
            'efficiency': {
                'asset_turnover': Decimal('0.8500'),
                'inventory_turnover': Decimal('9.5781'),
                'days_inventory': Decimal('38.06'),
                'days_sales_outstanding': Decimal('168.38'),
                'days_payable_outstanding': Decimal('133.27'),
            },
            'leverage': {
                'debt_to_equity': Decimal('1.0557'),
                'debt_to_assets': Decimal('0.5140'),
                'equity_ratio': Decimal('0.4860'),
            },
        },
        'cash_flow': {
            'beginning_cash': Decimal('2900000.00'),
            'ending_cash': Decimal('1200000.00'),
            'cash_change': Decimal('-1700000.00'),
            'operating_cash_flow': Decimal('1500000.00'),
            'investing_cash_flow': Decimal('-500000.00'),
            'financing_cash_flow': Decimal('-2700000.00'),
        },
        'tax_calculations': {
            'irpj_base': Decimal('281500.00'),
            'irpj_rate': Decimal('0.15'),
            'irpj_standard': Decimal('42225.00'),
            'irpj_surcharge': Decimal('0.00'),
            'irpj_total': Decimal('42225.00'),
            'csll_base': Decimal('281500.00'),
            'csll_rate': Decimal('0.09'),
            'csll_total': Decimal('25335.00'),
        },
    }
