"""Test Brazilian tax calculations (IRPJ and CSLL)."""
import pytest
from decimal import Decimal
from src.calc.brazilian_tax import calculate_brazilian_tax


class TestBrazilianTax:
    """Test suite for Brazilian income tax calculations."""

    def test_zero_profit(self):
        """Test tax calculation with zero profit."""
        irpj, csll = calculate_brazilian_tax(Decimal("0"), period_months=1)
        assert irpj == Decimal("0")
        assert csll == Decimal("0")

    def test_below_surtax_threshold(self):
        """Test profit below quarterly R$60K surtax threshold.

        EBT=30000 over 3 months → monthly=10000 < 20000, no surtax.
        IRPJ = 30000 * 15% = 4500
        CSLL  = 30000 *  9% = 2700
        """
        irpj, csll = calculate_brazilian_tax(Decimal("30000"), period_months=3)
        assert irpj == Decimal("4500.00")
        assert csll == Decimal("2700.00")

    def test_above_surtax_threshold(self):
        """Test prompt example: EBT=281500 over 3 months.

        Monthly = 93833.33 > 20000 → surtax applies.
        IRPJ base  = 281500 * 15%                          = 42225.00
        Surtax base= 281500 - (20000*3) = 221500
        IRPJ surtax= 221500 * 10%                          = 22150.00
        IRPJ total                                          = 64375.00
        CSLL       = 281500 *  9%                          = 25335.00
        """
        irpj, csll = calculate_brazilian_tax(Decimal("281500"), period_months=3)
        assert irpj == Decimal("64375.00")
        assert csll == Decimal("25335.00")

    def test_monthly_threshold(self):
        """Test exactly at monthly threshold (no surtax when monthly profit = R$20,000).

        EBT=60000, 3 months → monthly=20000, not above threshold.
        IRPJ = 60000 * 15% = 9000
        CSLL = 60000 *  9% = 5400
        """
        irpj, csll = calculate_brazilian_tax(Decimal("60000"), period_months=3)
        assert irpj == Decimal("9000.00")
        assert csll == Decimal("5400.00")

    def test_yearly_threshold(self):
        """Test annual profit with surtax on 12-month period.

        EBT=3000000, 12 months → monthly=250000 > 20000
        IRPJ base   = 3000000 * 15%                          = 450000
        Surtax base = 3000000 - (20000*12) = 2760000
        IRPJ surtax = 2760000 * 10%                          = 276000
        IRPJ total                                            = 726000
        CSLL        = 3000000 *  9%                          = 270000
        """
        irpj, csll = calculate_brazilian_tax(Decimal("3000000"), period_months=12)
        assert irpj == Decimal("726000.00")
        assert csll == Decimal("270000.00")

    def test_negative_profit(self):
        """Test tax calculation with negative profit (loss)."""
        irpj, csll = calculate_brazilian_tax(Decimal("-500000"), period_months=3)
        assert irpj == Decimal("0")
        assert csll == Decimal("0")

    def test_large_profit_approaching_34_percent(self):
        """Test large profit: effective rate approaches 34% maximum.

        EBT=10_000_000, 1 month → monthly=10M > 20000
        IRPJ base   = 10000000 * 15% = 1500000
        Surtax base = 10000000 - 20000 = 9980000
        IRPJ surtax = 9980000 * 10%   =  998000
        IRPJ total                     = 2498000
        CSLL        = 10000000 * 9%   =  900000
        Total       = 3398000 → eff. rate = 33.98%
        """
        irpj, csll = calculate_brazilian_tax(Decimal("10000000"), period_months=1)
        assert irpj == Decimal("2498000.00")
        assert csll == Decimal("900000.00")
        total = irpj + csll
        eff_rate = total / Decimal("10000000")
        # Effective rate should be close to 34%
        assert eff_rate < Decimal("0.34")
        assert eff_rate > Decimal("0.339")

    def test_component_breakdown(self):
        """Test component breakdown matches known values from prompt example."""
        ebt = Decimal("281500")
        irpj, csll = calculate_brazilian_tax(ebt, period_months=3)

        # Verify total combined tax
        total_tax = irpj + csll
        assert total_tax == Decimal("89710.00")

        # Verify effective rate ~31.9%
        eff_rate = total_tax / ebt
        assert abs(eff_rate - Decimal("0.3186")) < Decimal("0.001")
