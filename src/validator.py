"""
Data validation module with comprehensive quality checks.
Generates error reports for failed validations.
"""
import pandas as pd
from decimal import Decimal
from typing import List, Dict, Tuple
from decimal_utils import to_decimal


class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, row_index: int, column: str, error_type: str, 
                 message: str, value=None):
        self.row_index = row_index
        self.column = column
        self.error_type = error_type
        self.message = message
        self.value = value
    
    def to_dict(self) -> Dict:
        return {
            'row_index': self.row_index,
            'column': self.column,
            'error_type': self.error_type,
            'message': self.message,
            'value': str(self.value) if self.value is not None else None
        }


class DataValidator:
    """Validates normalized trade and capital gains data."""
    
    def __init__(self, tolerance: Decimal = Decimal("0.01")):
        """
        Initialize validator.
        
        Args:
            tolerance: Tolerance for value comparisons (default: 0.01)
        """
        self.tolerance = tolerance
        self.errors: List[ValidationError] = []
    
    def validate_trades(self, trades_df: pd.DataFrame) -> Tuple[bool, List[ValidationError]]:
        """
        Validate trades DataFrame.
        
        Args:
            trades_df: Normalized trades DataFrame
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.errors = []
        
        if trades_df.empty:
            return True, []
        
        for idx, row in trades_df.iterrows():
            # Validate qty is numeric and non-null
            self._validate_numeric_non_null(idx, row, 'qty')
            
            # Validate action is in {Buy, Sell}
            self._validate_action(idx, row)
            
            # Validate trade value matches qty * price
            self._validate_trade_value(idx, row)
            
            # Validate date is parseable
            self._validate_date(idx, row, 'date')
            
            # Validate symbol is not empty
            self._validate_not_empty(idx, row, 'symbol')
        
        # Check for exact duplicate rows
        self._check_duplicates(trades_df, 'trades')
        
        return len(self.errors) == 0, self.errors
    
    def validate_capital_gains(self, cg_df: pd.DataFrame) -> Tuple[bool, List[ValidationError]]:
        """
        Validate capital gains DataFrame.
        
        Args:
            cg_df: Normalized capital gains DataFrame
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.errors = []
        
        if cg_df.empty:
            return True, []
        
        for idx, row in cg_df.iterrows():
            # Validate qty is numeric and non-null
            self._validate_numeric_non_null(idx, row, 'qty')
            
            # Validate symbol is not empty
            self._validate_not_empty(idx, row, 'symbol')
            
            # Validate dates
            self._validate_date(idx, row, 'sale_date')
            self._validate_date(idx, row, 'purchase_date')
            
            # Validate section is ST or LT
            self._validate_section(idx, row)
            
            # Validate P&L calculation (approximately)
            self._validate_pnl(idx, row)
        
        # Check for duplicates
        self._check_duplicates(cg_df, 'capital_gains')
        
        return len(self.errors) == 0, self.errors
    
    def _validate_numeric_non_null(self, idx: int, row: pd.Series, column: str):
        """Validate that a column is numeric and non-null."""
        value = row.get(column)
        
        if value is None or pd.isna(value):
            self.errors.append(ValidationError(
                idx, column, 'null_value',
                f'{column} is null or missing',
                value
            ))
            return
        
        if not isinstance(value, (int, float, Decimal)):
            try:
                to_decimal(value)
            except:
                self.errors.append(ValidationError(
                    idx, column, 'invalid_numeric',
                    f'{column} is not a valid number',
                    value
                ))
    
    def _validate_action(self, idx: int, row: pd.Series):
        """Validate that action is 'Buy' or 'Sell'."""
        action = row.get('action', '')
        
        if action not in ['Buy', 'Sell']:
            self.errors.append(ValidationError(
                idx, 'action', 'invalid_action',
                f'Action must be Buy or Sell, got: {action}',
                action
            ))
    
    def _validate_trade_value(self, idx: int, row: pd.Series):
        """Validate that trade value ≈ qty * price."""
        try:
            qty = to_decimal(row.get('qty', 0))
            price = to_decimal(row.get('price', 0))
            trade_value = to_decimal(row.get('trade_value', 0))
            
            expected_value = qty * price
            diff = abs(trade_value - expected_value)
            
            # Allow small tolerance
            if diff > self.tolerance:
                self.errors.append(ValidationError(
                    idx, 'trade_value', 'value_mismatch',
                    f'Trade value {trade_value} does not match qty*price {expected_value} (diff: {diff})',
                    trade_value
                ))
        except Exception as e:
            self.errors.append(ValidationError(
                idx, 'trade_value', 'validation_error',
                f'Error validating trade value: {e}',
                None
            ))
    
    def _validate_date(self, idx: int, row: pd.Series, column: str):
        """Validate that a date column is parseable."""
        date_val = row.get(column)
        
        if date_val is None or pd.isna(date_val):
            # Date can be null in some cases
            return
        
        if not isinstance(date_val, (pd.Timestamp, pd.DatetimeIndex)):
            try:
                pd.to_datetime(date_val)
            except:
                self.errors.append(ValidationError(
                    idx, column, 'invalid_date',
                    f'{column} is not a valid date',
                    date_val
                ))
    
    def _validate_not_empty(self, idx: int, row: pd.Series, column: str):
        """Validate that a column is not empty."""
        value = row.get(column)
        
        if not value or (isinstance(value, str) and value.strip() == ''):
            self.errors.append(ValidationError(
                idx, column, 'empty_value',
                f'{column} is empty',
                value
            ))
    
    def _validate_section(self, idx: int, row: pd.Series):
        """Validate that section is ST or LT."""
        section = row.get('section', '')
        
        if section not in ['ST', 'LT']:
            self.errors.append(ValidationError(
                idx, 'section', 'invalid_section',
                f'Section must be ST or LT, got: {section}',
                section
            ))
    
    def _validate_pnl(self, idx: int, row: pd.Series):
        """Validate P&L calculation."""
        try:
            sale_value = to_decimal(row.get('sale_value', 0))
            sale_expenses = to_decimal(row.get('sale_expenses', 0))
            purchase_value = to_decimal(row.get('purchase_value', 0))
            purchase_expenses = to_decimal(row.get('purchase_expenses', 0))
            pnl = to_decimal(row.get('pnl', 0))
            
            # P&L = (Sale Value - Sale Expenses) - (Purchase Value + Purchase Expenses)
            expected_pnl = (sale_value - sale_expenses) - (purchase_value + purchase_expenses)
            diff = abs(pnl - expected_pnl)
            
            # Allow tolerance for rounding
            if diff > self.tolerance:
                self.errors.append(ValidationError(
                    idx, 'pnl', 'pnl_mismatch',
                    f'P&L {pnl} does not match calculated {expected_pnl} (diff: {diff})',
                    pnl
                ))
        except Exception as e:
            self.errors.append(ValidationError(
                idx, 'pnl', 'validation_error',
                f'Error validating P&L: {e}',
                None
            ))
    
    def _check_duplicates(self, df: pd.DataFrame, table_name: str):
        """Check for exact duplicate rows."""
        duplicates = df[df.duplicated(keep=False)]
        
        if not duplicates.empty:
            for idx in duplicates.index:
                self.errors.append(ValidationError(
                    idx, 'row', 'duplicate_row',
                    f'Duplicate row found in {table_name}',
                    None
                ))
    
    def get_error_report(self) -> pd.DataFrame:
        """
        Get error report as DataFrame.
        
        Returns:
            DataFrame with error details
        """
        if not self.errors:
            return pd.DataFrame()
        
        return pd.DataFrame([err.to_dict() for err in self.errors])


def validate_all_data(trades_df: pd.DataFrame, cg_df: pd.DataFrame) -> Dict[str, any]:
    """
    Validate all normalized data.
    
    Args:
        trades_df: Normalized trades DataFrame
        cg_df: Normalized capital gains DataFrame
    
    Returns:
        Dictionary with validation results and error reports
    """
    validator = DataValidator()
    
    # Validate trades
    trades_valid, trades_errors = validator.validate_trades(trades_df)
    trades_error_report = pd.DataFrame([e.to_dict() for e in trades_errors]) if trades_errors else pd.DataFrame()
    
    # Validate capital gains
    validator.errors = []  # Reset errors
    cg_valid, cg_errors = validator.validate_capital_gains(cg_df)
    cg_error_report = pd.DataFrame([e.to_dict() for e in cg_errors]) if cg_errors else pd.DataFrame()
    
    is_valid = trades_valid and cg_valid
    
    return {
        'is_valid': is_valid,
        'trades_valid': trades_valid,
        'capital_gains_valid': cg_valid,
        'trades_errors': trades_error_report,
        'capital_gains_errors': cg_error_report,
        'total_errors': len(trades_errors) + len(cg_errors)
    }
