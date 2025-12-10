"""
Portfolio optimization using Modern Portfolio Theory (MPT) and Genetic Algorithms.
Implements efficient frontier calculation and multi-objective optimization.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path
import sys
from scipy.optimize import minimize
from deap import base, creator, tools, algorithms
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import Config
from src.utils.database import get_database

logger = logging.getLogger(__name__)


class ModernPortfolioTheory:
    """
    Modern Portfolio Theory (MPT) implementation for portfolio optimization.
    Calculates efficient frontier, optimal portfolios, and Sharpe ratios.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize MPT optimizer.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.risk_free_rate = risk_free_rate
        self.db = get_database()
    
    def calculate_returns_covariance(
        self, 
        tickers: List[str], 
        start_date: str = None,
        end_date: str = None
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Calculate expected returns and covariance matrix for assets.
        
        Args:
            tickers: List of stock tickers
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            Tuple of (expected_returns, covariance_matrix)
        """
        # Load historical prices
        prices_data = []
        for ticker in tickers:
            prices_df = self.db.load_daily_prices(ticker=ticker)
            if not prices_df.empty:
                prices_df = prices_df[['date', 'close']].copy()
                prices_df.columns = ['date', ticker]
                prices_data.append(prices_df)
        
        if not prices_data:
            raise ValueError("No price data available")
        
        # Merge all price data
        prices = prices_data[0]
        for df in prices_data[1:]:
            prices = prices.merge(df, on='date', how='outer')
        
        prices = prices.sort_values('date').set_index('date')
        
        # Filter by date range if provided
        if start_date:
            prices = prices[prices.index >= pd.to_datetime(start_date)]
        if end_date:
            prices = prices[prices.index <= pd.to_datetime(end_date)]
        
        # Calculate daily returns
        returns = prices.pct_change().dropna()
        
        # Expected annual returns (mean daily return * 252 trading days)
        expected_returns = returns.mean() * 252
        
        # Covariance matrix (annualized)
        cov_matrix = returns.cov() * 252
        
        return expected_returns, cov_matrix
    
    def portfolio_performance(
        self, 
        weights: np.ndarray,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> Tuple[float, float, float]:
        """
        Calculate portfolio return, volatility, and Sharpe ratio.
        
        Args:
            weights: Portfolio weights
            expected_returns: Expected returns for each asset
            cov_matrix: Covariance matrix
            
        Returns:
            Tuple of (return, volatility, sharpe_ratio)
        """
        portfolio_return = np.sum(weights * expected_returns)
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std
        
        return portfolio_return, portfolio_std, sharpe_ratio
    
    def optimize_portfolio(
        self,
        tickers: List[str],
        objective: str = 'max_sharpe',
        target_return: float = None,
        constraints: Dict = None
    ) -> Dict:
        """
        Optimize portfolio allocation.
        
        Args:
            tickers: List of stock tickers
            objective: Optimization objective ('max_sharpe', 'min_volatility', 'target_return')
            target_return: Target return for 'target_return' objective
            constraints: Additional constraints (e.g., max_weight, min_weight)
            
        Returns:
            Dictionary with optimal weights and performance metrics
        """
        expected_returns, cov_matrix = self.calculate_returns_covariance(tickers)
        
        n_assets = len(tickers)
        
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        # Constraints: weights sum to 1
        constraints_list = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        # Add target return constraint if specified
        if objective == 'target_return' and target_return is not None:
            constraints_list.append({
                'type': 'eq',
                'fun': lambda x: np.sum(x * expected_returns) - target_return
            })
        
        # Bounds: weights between 0 and 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Apply custom constraints if provided
        if constraints:
            if 'max_weight' in constraints:
                bounds = tuple((0, constraints['max_weight']) for _ in range(n_assets))
            if 'min_weight' in constraints:
                min_w = constraints['min_weight']
                bounds = tuple((min_w, bounds[i][1]) for i in range(n_assets))
        
        # Objective function
        if objective == 'max_sharpe':
            # Minimize negative Sharpe ratio
            def objective_func(weights):
                return -self.portfolio_performance(weights, expected_returns, cov_matrix)[2]
        elif objective == 'min_volatility' or objective == 'target_return':
            # Minimize volatility
            def objective_func(weights):
                return self.portfolio_performance(weights, expected_returns, cov_matrix)[1]
        else:
            raise ValueError(f"Unknown objective: {objective}")
        
        # Optimize
        result = minimize(
            objective_func,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        optimal_weights = result.x
        port_return, port_vol, sharpe = self.portfolio_performance(
            optimal_weights, expected_returns, cov_matrix
        )
        
        return {
            'tickers': tickers,
            'weights': {ticker: float(weight) for ticker, weight in zip(tickers, optimal_weights)},
            'expected_return': float(port_return),
            'volatility': float(port_vol),
            'sharpe_ratio': float(sharpe),
            'objective': objective
        }
    
    def efficient_frontier(
        self,
        tickers: List[str],
        n_portfolios: int = 100
    ) -> pd.DataFrame:
        """
        Calculate efficient frontier portfolios.
        
        Args:
            tickers: List of stock tickers
            n_portfolios: Number of portfolios to calculate
            
        Returns:
            DataFrame with portfolio returns, volatilities, and Sharpe ratios
        """
        expected_returns, cov_matrix = self.calculate_returns_covariance(tickers)
        
        # Calculate range of target returns
        min_ret = expected_returns.min()
        max_ret = expected_returns.max()
        target_returns = np.linspace(min_ret, max_ret, n_portfolios)
        
        frontier_portfolios = []
        
        for target_ret in target_returns:
            try:
                portfolio = self.optimize_portfolio(
                    tickers,
                    objective='target_return',
                    target_return=target_ret
                )
                frontier_portfolios.append({
                    'return': portfolio['expected_return'],
                    'volatility': portfolio['volatility'],
                    'sharpe_ratio': portfolio['sharpe_ratio'],
                    'weights': portfolio['weights']
                })
            except Exception as e:
                logger.warning(f"Failed to optimize for target return {target_ret}: {e}")
                continue
        
        return pd.DataFrame(frontier_portfolios)


class GeneticAlgorithmOptimizer:
    """
    Portfolio optimization using Genetic Algorithms.
    Supports multi-objective optimization (risk vs. return).
    """
    
    def __init__(
        self,
        population_size: int = 100,
        generations: int = 50,
        crossover_prob: float = 0.7,
        mutation_prob: float = 0.2
    ):
        """
        Initialize GA optimizer.
        
        Args:
            population_size: Number of individuals in population
            generations: Number of generations to evolve
            crossover_prob: Probability of crossover
            mutation_prob: Probability of mutation
        """
        self.population_size = population_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.mpt = ModernPortfolioTheory()
    
    def setup_genetic_algorithm(self, n_assets: int):
        """
        Setup DEAP genetic algorithm framework.
        
        Args:
            n_assets: Number of assets in portfolio
        """
        # Create fitness and individual classes
        if hasattr(creator, "FitnessMulti"):
            del creator.FitnessMulti
        if hasattr(creator, "Individual"):
            del creator.Individual
            
        creator.create("FitnessMulti", base.Fitness, weights=(1.0, -1.0))  # Max return, Min volatility
        creator.create("Individual", list, fitness=creator.FitnessMulti)
        
        self.toolbox = base.Toolbox()
        
        # Attribute generator: random weight between 0 and 1
        self.toolbox.register("attr_float", random.random)
        
        # Individual generator: n_assets weights
        self.toolbox.register(
            "individual",
            tools.initRepeat,
            creator.Individual,
            self.toolbox.attr_float,
            n=n_assets
        )
        
        # Population generator
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
    
    def normalize_weights(self, individual):
        """Normalize weights to sum to 1 and ensure all are positive (no short selling)."""
        # Ensure all weights are positive
        individual = [max(0, w) for w in individual]
        
        total = sum(individual)
        if total > 0:
            return [w / total for w in individual]
        return [1.0 / len(individual)] * len(individual)
    
    def evaluate_portfolio(
        self,
        individual,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ):
        """
        Evaluate portfolio fitness (return and volatility).
        
        Args:
            individual: Portfolio weights
            expected_returns: Expected returns
            cov_matrix: Covariance matrix
            
        Returns:
            Tuple of (return, volatility)
        """
        # Normalize weights
        weights = np.array(self.normalize_weights(individual))
        
        # Calculate performance
        port_return, port_vol, _ = self.mpt.portfolio_performance(
            weights, expected_returns, cov_matrix
        )
        
        return port_return, port_vol
    
    def optimize(
        self,
        tickers: List[str],
        constraints: Dict = None
    ) -> List[Dict]:
        """
        Optimize portfolio using genetic algorithm.
        
        Args:
            tickers: List of stock tickers
            constraints: Additional constraints
            
        Returns:
            List of Pareto-optimal portfolios
        """
        n_assets = len(tickers)
        
        # Get returns and covariance
        expected_returns, cov_matrix = self.mpt.calculate_returns_covariance(tickers)
        
        # Setup GA
        self.setup_genetic_algorithm(n_assets)
        
        # Register genetic operators
        self.toolbox.register(
            "evaluate",
            self.evaluate_portfolio,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix
        )
        self.toolbox.register("mate", tools.cxBlend, alpha=0.5)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
        self.toolbox.register("select", tools.selNSGA2)
        
        # Create initial population
        population = self.toolbox.population(n=self.population_size)
        
        # Statistics
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)
        
        # Run evolution
        population, logbook = algorithms.eaMuPlusLambda(
            population,
            self.toolbox,
            mu=self.population_size,
            lambda_=self.population_size,
            cxpb=self.crossover_prob,
            mutpb=self.mutation_prob,
            ngen=self.generations,
            stats=stats,
            verbose=False
        )
        
        # Extract Pareto front
        pareto_front = tools.sortNondominated(population, len(population), first_front_only=True)[0]
        
        # Convert to portfolio format
        portfolios = []
        for individual in pareto_front:
            weights = self.normalize_weights(individual)
            port_return, port_vol, sharpe = self.mpt.portfolio_performance(
                np.array(weights), expected_returns, cov_matrix
            )
            
            portfolios.append({
                'tickers': tickers,
                'weights': {ticker: float(weight) for ticker, weight in zip(tickers, weights)},
                'expected_return': float(port_return),
                'volatility': float(port_vol),
                'sharpe_ratio': float(sharpe),
                'method': 'genetic_algorithm'
            })
        
        # Sort by Sharpe ratio
        portfolios.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        return portfolios


def optimize_client_portfolio(client_id: str, method: str = 'mpt', **kwargs) -> Dict:
    """
    Optimize portfolio for a specific client based on their holdings.
    
    Args:
        client_id: Client identifier
        method: Optimization method ('mpt' or 'genetic')
        **kwargs: Additional arguments for optimizer
        
    Returns:
        Optimized portfolio allocation
    """
    db = get_database()
    
    # Load client holdings
    holdings_df = db.load_portfolio_holdings(client_id=client_id)
    
    if holdings_df.empty:
        raise ValueError(f"No holdings found for client {client_id}")
    
    # Get unique tickers
    tickers = holdings_df['ticker'].unique().tolist()
    
    if len(tickers) < 2:
        raise ValueError("Need at least 2 assets for optimization")
    
    # Choose optimizer
    if method == 'mpt':
        optimizer = ModernPortfolioTheory()
        result = optimizer.optimize_portfolio(tickers, **kwargs)
    elif method == 'genetic':
        optimizer = GeneticAlgorithmOptimizer()
        results = optimizer.optimize(tickers, **kwargs)
        result = results[0] if results else {}  # Return best portfolio
    else:
        raise ValueError(f"Unknown method: {method}")
    
    result['client_id'] = client_id
    result['optimization_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    return result


def main():
    """Demo portfolio optimization."""
    import logging
    from src.utils.helpers import setup_logging
    
    setup_logging()
    
    # Test tickers
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    
    print("\n" + "="*60)
    print("MODERN PORTFOLIO THEORY OPTIMIZATION")
    print("="*60 + "\n")
    
    mpt = ModernPortfolioTheory()
    
    # Max Sharpe portfolio
    print("1. Maximum Sharpe Ratio Portfolio:")
    max_sharpe = mpt.optimize_portfolio(tickers, objective='max_sharpe')
    print(f"   Expected Return: {max_sharpe['expected_return']:.2%}")
    print(f"   Volatility: {max_sharpe['volatility']:.2%}")
    print(f"   Sharpe Ratio: {max_sharpe['sharpe_ratio']:.2f}")
    print("   Weights:")
    for ticker, weight in max_sharpe['weights'].items():
        print(f"     {ticker}: {weight:.2%}")
    
    # Min volatility portfolio
    print("\n2. Minimum Volatility Portfolio:")
    min_vol = mpt.optimize_portfolio(tickers, objective='min_volatility')
    print(f"   Expected Return: {min_vol['expected_return']:.2%}")
    print(f"   Volatility: {min_vol['volatility']:.2%}")
    print(f"   Sharpe Ratio: {min_vol['sharpe_ratio']:.2f}")
    print("   Weights:")
    for ticker, weight in min_vol['weights'].items():
        print(f"     {ticker}: {weight:.2%}")
    
    print("\n" + "="*60)
    print("GENETIC ALGORITHM OPTIMIZATION")
    print("="*60 + "\n")
    
    ga = GeneticAlgorithmOptimizer(population_size=50, generations=30)
    pareto_portfolios = ga.optimize(tickers)
    
    print(f"Found {len(pareto_portfolios)} Pareto-optimal portfolios\n")
    print("Top 3 by Sharpe Ratio:")
    for i, portfolio in enumerate(pareto_portfolios[:3], 1):
        print(f"\n{i}. Portfolio:")
        print(f"   Expected Return: {portfolio['expected_return']:.2%}")
        print(f"   Volatility: {portfolio['volatility']:.2%}")
        print(f"   Sharpe Ratio: {portfolio['sharpe_ratio']:.2f}")
        print("   Weights:")
        for ticker, weight in portfolio['weights'].items():
            print(f"     {ticker}: {weight:.2%}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
