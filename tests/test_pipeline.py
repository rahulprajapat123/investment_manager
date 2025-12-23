"""
Test suite for portfolio analytics pipeline.
Validates against reference values for demo client "Rahul Demo".
"""
import pytest
import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion import ingest_all_files
from normalizer import normalize_all_files
from aggregator import compute_weighted_avg_buy_price, compute_realized_pnl_by_stock


# Reference weighted average buy prices for Rahul Demo (C001)
REFERENCE_WEIGHTED_AVG_PRICES = {
    'AAPL': Decimal('351.15'),
    'AMZN': Decimal('229.33'),
    'GOOGL': Decimal('317.58'),
    'JPM': Decimal('335.72'),
    'META': Decimal('223.73'),
    'MSFT': Decimal('189.79'),
    'NVDA': Decimal('198.25'),
    'SPY': Decimal('351.59'),
    'TSLA': Decimal('434.52'),
    'V': Decimal('243.43')
}

# Tolerance for decimal comparisons
TOLERANCE = Decimal('0.01')


@pytest.fixture(scope='module')
def normalized_data():
    """Load and normalize all data once for all tests."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        pytest.skip(f"Data directory not found: {data_dir}")
    
    ingested_files = ingest_all_files(str(data_dir))
    normalized = normalize_all_files(ingested_files)
    
    return normalized


@pytest.fixture(scope='module')
def c001_trades(normalized_data):
    """Filter trades for client C001."""
    trades_df = normalized_data['trades']
    return trades_df[trades_df['client_id'] == 'C001']


@pytest.fixture(scope='module')
def c001_capital_gains(normalized_data):
    """Filter capital gains for client C001."""
    cg_df = normalized_data['capital_gains']
    return cg_df[cg_df['client_id'] == 'C001']


def test_data_ingestion(normalized_data):
    """Test that data was successfully ingested and normalized."""
    assert not normalized_data['trades'].empty, "No trades data ingested"
    assert not normalized_data['capital_gains'].empty, "No capital gains data ingested"


def test_c001_exists(c001_trades, c001_capital_gains):
    """Test that client C001 (Rahul Demo) exists in the data."""
    assert not c001_trades.empty, "No trades found for C001"
    assert not c001_capital_gains.empty, "No capital gains found for C001"


def test_weighted_avg_buy_prices(c001_trades):
    """
    Test weighted average buy prices against reference values.
    This is the primary accuracy test for the pipeline.
    """
    # Compute weighted average buy prices
    trade_summary = compute_weighted_avg_buy_price(c001_trades, client_id='C001')
    
    assert not trade_summary.empty, "No trade summary computed for C001"
    
    # Check each stock against reference
    errors = []
    
    for _, row in trade_summary.iterrows():
        symbol = row['symbol']
        computed_price = row['weighted_avg_buy_price']
        
        if symbol in REFERENCE_WEIGHTED_AVG_PRICES:
            reference_price = REFERENCE_WEIGHTED_AVG_PRICES[symbol]
            diff = abs(computed_price - reference_price)
            
            if diff > TOLERANCE:
                errors.append(
                    f"{symbol}: Expected {reference_price}, got {computed_price}, "
                    f"diff = {diff}"
                )
    
    # Check that all reference stocks are present
    computed_symbols = set(trade_summary['symbol'].tolist())
    missing_symbols = set(REFERENCE_WEIGHTED_AVG_PRICES.keys()) - computed_symbols
    
    if missing_symbols:
        errors.append(f"Missing symbols in computed data: {missing_symbols}")
    
    # Assert no errors
    if errors:
        error_msg = "\n".join(errors)
        pytest.fail(f"Weighted average buy price validation failed:\n{error_msg}")


def test_individual_stock_aapl(c001_trades):
    """Test AAPL weighted average buy price specifically."""
    trade_summary = compute_weighted_avg_buy_price(c001_trades, client_id='C001', symbol='AAPL')
    
    assert not trade_summary.empty, "No AAPL trades found"
    
    aapl_row = trade_summary.iloc[0]
    computed = aapl_row['weighted_avg_buy_price']
    expected = REFERENCE_WEIGHTED_AVG_PRICES['AAPL']
    
    diff = abs(computed - expected)
    assert diff <= TOLERANCE, \
        f"AAPL: Expected {expected}, got {computed}, diff = {diff}"


def test_individual_stock_msft(c001_trades):
    """Test MSFT weighted average buy price specifically."""
    trade_summary = compute_weighted_avg_buy_price(c001_trades, client_id='C001', symbol='MSFT')
    
    assert not trade_summary.empty, "No MSFT trades found"
    
    msft_row = trade_summary.iloc[0]
    computed = msft_row['weighted_avg_buy_price']
    expected = REFERENCE_WEIGHTED_AVG_PRICES['MSFT']
    
    diff = abs(computed - expected)
    assert diff <= TOLERANCE, \
        f"MSFT: Expected {expected}, got {computed}, diff = {diff}"


def test_capital_gains_computation(c001_capital_gains):
    """Test that capital gains P&L is computed correctly."""
    cg_summary = compute_realized_pnl_by_stock(c001_capital_gains, client_id='C001')
    
    assert not cg_summary.empty, "No capital gains summary computed"
    
    # Check that total_pnl = stcg + ltcg for each stock
    errors = []
    
    for _, row in cg_summary.iterrows():
        symbol = row['symbol']
        total_pnl = row['total_pnl']
        stcg = row['stcg']
        ltcg = row['ltcg']
        
        computed_total = stcg + ltcg
        diff = abs(total_pnl - computed_total)
        
        if diff > TOLERANCE:
            errors.append(
                f"{symbol}: total_pnl {total_pnl} != stcg {stcg} + ltcg {ltcg} "
                f"(diff = {diff})"
            )
    
    if errors:
        error_msg = "\n".join(errors)
        pytest.fail(f"Capital gains computation validation failed:\n{error_msg}")


def test_no_null_quantities(c001_trades):
    """Test that all quantities are non-null."""
    null_qty = c001_trades['qty'].isna().sum()
    assert null_qty == 0, f"Found {null_qty} null quantities in trades"


def test_valid_actions(c001_trades):
    """Test that all actions are either Buy or Sell."""
    valid_actions = {'Buy', 'Sell'}
    invalid = c001_trades[~c001_trades['action'].isin(valid_actions)]
    
    assert len(invalid) == 0, \
        f"Found {len(invalid)} invalid actions: {invalid['action'].unique()}"


def test_decimal_precision(c001_trades):
    """Test that all monetary values use Decimal type."""
    # Check a sample row
    if not c001_trades.empty:
        row = c001_trades.iloc[0]
        
        assert isinstance(row['qty'], Decimal), "qty is not Decimal"
        assert isinstance(row['price'], Decimal), "price is not Decimal"
        assert isinstance(row['trade_value'], Decimal), "trade_value is not Decimal"


def test_all_stocks_present(c001_trades):
    """Test that all reference stocks are present in C001 trades."""
    computed_symbols = set(c001_trades['symbol'].unique())
    reference_symbols = set(REFERENCE_WEIGHTED_AVG_PRICES.keys())
    
    missing = reference_symbols - computed_symbols
    
    assert not missing, f"Missing symbols in C001 trades: {missing}"


def test_broker_coverage(c001_trades):
    """Test that multiple brokers are represented for C001."""
    brokers = c001_trades['broker'].unique()
    
    # Should have data from multiple brokers
    assert len(brokers) >= 2, \
        f"Expected multiple brokers for C001, found only: {brokers}"


def test_trade_value_consistency(c001_trades):
    """Test that trade_value approximately equals qty * price."""
    errors = []
    
    for idx, row in c001_trades.head(50).iterrows():  # Test first 50 rows
        expected_value = row['qty'] * row['price']
        diff = abs(row['trade_value'] - expected_value)
        
        if diff > TOLERANCE:
            errors.append(
                f"Row {idx}: trade_value {row['trade_value']} != "
                f"qty {row['qty']} * price {row['price']} = {expected_value}"
            )
    
    assert not errors, f"Trade value inconsistencies:\n" + "\n".join(errors[:5])


def test_no_negative_quantities(c001_trades, c001_capital_gains):
    """Test that quantities are always positive."""
    neg_trades = c001_trades[c001_trades['qty'] < 0]
    neg_cg = c001_capital_gains[c001_capital_gains['qty'] < 0]
    
    assert len(neg_trades) == 0, f"Found {len(neg_trades)} negative quantities in trades"
    assert len(neg_cg) == 0, f"Found {len(neg_cg)} negative quantities in capital gains"


def test_date_validity(c001_trades):
    """Test that dates are valid."""
    # Check for non-null dates in most rows
    date_col = c001_trades['date']
    non_null_dates = date_col.notna().sum()
    
    # At least 80% of rows should have valid dates
    assert non_null_dates >= len(c001_trades) * 0.8, \
        f"Only {non_null_dates}/{len(c001_trades)} rows have valid dates"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
