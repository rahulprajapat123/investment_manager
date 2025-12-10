"""
Clustering algorithms for portfolio diversification analysis.
Groups similar assets to improve risk management and asset allocation.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
import sys
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import Config
from src.utils.database import get_database

logger = logging.getLogger(__name__)


class AssetClustering:
    """
    Asset clustering for diversification analysis.
    Groups similar assets based on price correlations, returns, and volatility.
    """
    
    def __init__(self, method: str = 'kmeans'):
        """
        Initialize clustering analyzer.
        
        Args:
            method: Clustering method ('kmeans', 'hierarchical', 'dbscan')
        """
        self.method = method
        self.db = get_database()
        self.scaler = StandardScaler()
        self.model = None
        self.cluster_labels = None
    
    def calculate_asset_features(
        self,
        tickers: List[str],
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Calculate clustering features for assets.
        
        Args:
            tickers: List of stock tickers
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            DataFrame with asset features
        """
        features = []
        
        for ticker in tickers:
            # Load price data
            prices_df = self.db.load_daily_prices(ticker=ticker)
            
            if prices_df.empty:
                logger.warning(f"No data for {ticker}")
                continue
            
            # Filter by date
            if start_date:
                prices_df = prices_df[prices_df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                prices_df = prices_df[prices_df['date'] <= pd.to_datetime(end_date)]
            
            if len(prices_df) < 20:
                continue
            
            # Calculate features
            returns = prices_df['close'].pct_change().dropna()
            
            feature_dict = {
                'ticker': ticker,
                'mean_return': returns.mean() * 252,  # Annualized
                'volatility': returns.std() * np.sqrt(252),  # Annualized
                'sharpe_ratio': (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0,
                'max_drawdown': self._calculate_max_drawdown(prices_df['close']),
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis(),
                'avg_volume': prices_df['volume'].mean(),
                'price_range': (prices_df['high'] - prices_df['low']).mean() / prices_df['close'].mean()
            }
            
            features.append(feature_dict)
        
        features_df = pd.DataFrame(features)
        
        # Add correlation-based features
        if len(features_df) > 1:
            corr_features = self._calculate_correlation_features(tickers, start_date, end_date)
            features_df = features_df.merge(corr_features, on='ticker', how='left')
        
        return features_df
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _calculate_correlation_features(
        self,
        tickers: List[str],
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Calculate correlation-based features for each asset.
        
        Args:
            tickers: List of tickers
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with correlation features
        """
        # Build returns matrix
        returns_data = []
        
        for ticker in tickers:
            prices_df = self.db.load_daily_prices(ticker=ticker)
            if prices_df.empty:
                continue
            
            if start_date:
                prices_df = prices_df[prices_df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                prices_df = prices_df[prices_df['date'] <= pd.to_datetime(end_date)]
            
            returns = prices_df[['date', 'close']].copy()
            returns['return'] = returns['close'].pct_change()
            returns = returns[['date', 'return']]
            returns.columns = ['date', ticker]
            
            returns_data.append(returns)
        
        # Merge all returns
        if len(returns_data) < 2:
            return pd.DataFrame({'ticker': tickers, 'avg_correlation': 0})
        
        merged_returns = returns_data[0]
        for df in returns_data[1:]:
            merged_returns = merged_returns.merge(df, on='date', how='outer')
        
        merged_returns = merged_returns.set_index('date').dropna()
        
        # Calculate correlation matrix
        corr_matrix = merged_returns.corr()
        
        # Calculate average correlation for each asset
        corr_features = []
        for ticker in corr_matrix.columns:
            # Average correlation with other assets (excluding self)
            other_corrs = corr_matrix[ticker].drop(ticker)
            avg_corr = other_corrs.mean() if len(other_corrs) > 0 else 0
            
            corr_features.append({
                'ticker': ticker,
                'avg_correlation': avg_corr,
                'max_correlation': other_corrs.max() if len(other_corrs) > 0 else 0,
                'min_correlation': other_corrs.min() if len(other_corrs) > 0 else 0
            })
        
        return pd.DataFrame(corr_features)
    
    def fit_predict(
        self,
        tickers: List[str],
        n_clusters: int = 3,
        **kwargs
    ) -> Dict:
        """
        Perform clustering on assets.
        
        Args:
            tickers: List of stock tickers
            n_clusters: Number of clusters (for kmeans/hierarchical)
            **kwargs: Additional parameters for clustering algorithm
            
        Returns:
            Clustering results with labels and metrics
        """
        # Calculate features
        features_df = self.calculate_asset_features(tickers)
        
        if features_df.empty or len(features_df) < 2:
            raise ValueError("Insufficient data for clustering")
        
        # Prepare feature matrix
        feature_cols = [col for col in features_df.columns if col != 'ticker']
        X = features_df[feature_cols].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform clustering
        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=n_clusters, random_state=42, **kwargs)
            labels = self.model.fit_predict(X_scaled)
        
        elif self.method == 'hierarchical':
            self.model = AgglomerativeClustering(n_clusters=n_clusters, **kwargs)
            labels = self.model.fit_predict(X_scaled)
        
        elif self.method == 'dbscan':
            eps = kwargs.get('eps', 0.5)
            min_samples = kwargs.get('min_samples', 2)
            self.model = DBSCAN(eps=eps, min_samples=min_samples)
            labels = self.model.fit_predict(X_scaled)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        self.cluster_labels = labels
        
        # Calculate clustering quality metrics
        if n_clusters > 1 and len(set(labels)) > 1:
            silhouette = silhouette_score(X_scaled, labels)
            davies_bouldin = davies_bouldin_score(X_scaled, labels)
        else:
            silhouette = 0
            davies_bouldin = 0
        
        # Create results
        features_df['cluster'] = labels
        
        # Cluster statistics
        cluster_stats = []
        for cluster_id in sorted(set(labels)):
            if cluster_id == -1:  # Noise in DBSCAN
                continue
            
            cluster_data = features_df[features_df['cluster'] == cluster_id]
            
            cluster_stats.append({
                'cluster_id': int(cluster_id),
                'size': len(cluster_data),
                'tickers': cluster_data['ticker'].tolist(),
                'avg_return': float(cluster_data['mean_return'].mean()),
                'avg_volatility': float(cluster_data['volatility'].mean()),
                'avg_sharpe': float(cluster_data['sharpe_ratio'].mean()),
                'avg_correlation': float(cluster_data.get('avg_correlation', pd.Series([0])).mean())
            })
        
        return {
            'method': self.method,
            'n_clusters': n_clusters,
            'cluster_assignments': features_df[['ticker', 'cluster']].to_dict('records'),
            'cluster_stats': cluster_stats,
            'metrics': {
                'silhouette_score': float(silhouette),
                'davies_bouldin_score': float(davies_bouldin)
            },
            'features': features_df.to_dict('records')
        }
    
    def get_diversified_portfolio(
        self,
        tickers: List[str],
        n_assets: int = None,
        method: str = 'one_per_cluster'
    ) -> List[str]:
        """
        Select diversified portfolio based on clustering.
        
        Args:
            tickers: List of available tickers
            n_assets: Number of assets to select
            method: Selection method ('one_per_cluster', 'proportional')
            
        Returns:
            List of selected tickers
        """
        if self.cluster_labels is None:
            # Perform clustering first
            self.fit_predict(tickers)
        
        features_df = self.calculate_asset_features(tickers)
        features_df['cluster'] = self.cluster_labels
        
        selected = []
        
        if method == 'one_per_cluster':
            # Select best asset from each cluster
            for cluster_id in sorted(set(self.cluster_labels)):
                if cluster_id == -1:
                    continue
                
                cluster_data = features_df[features_df['cluster'] == cluster_id]
                
                # Select asset with highest Sharpe ratio
                best_asset = cluster_data.loc[cluster_data['sharpe_ratio'].idxmax()]
                selected.append(best_asset['ticker'])
        
        elif method == 'proportional':
            # Select proportionally from each cluster
            if n_assets is None:
                n_assets = len(tickers) // 2
            
            cluster_sizes = features_df['cluster'].value_counts()
            
            for cluster_id in sorted(set(self.cluster_labels)):
                if cluster_id == -1:
                    continue
                
                # Number to select from this cluster
                n_from_cluster = max(1, int(n_assets * cluster_sizes[cluster_id] / len(features_df)))
                
                cluster_data = features_df[features_df['cluster'] == cluster_id]
                cluster_data = cluster_data.sort_values('sharpe_ratio', ascending=False)
                
                selected.extend(cluster_data.head(n_from_cluster)['ticker'].tolist())
        
        # Limit to n_assets if specified
        if n_assets and len(selected) > n_assets:
            selected = selected[:n_assets]
        
        return selected


def analyze_portfolio_diversification(client_id: str) -> Dict:
    """
    Analyze portfolio diversification using clustering.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Diversification analysis results
    """
    db = get_database()
    
    # Load client holdings
    holdings_df = db.load_portfolio_holdings(client_id=client_id)
    
    if holdings_df.empty:
        raise ValueError(f"No holdings for client {client_id}")
    
    tickers = holdings_df['ticker'].unique().tolist()
    
    if len(tickers) < 3:
        return {
            'client_id': client_id,
            'message': 'Insufficient assets for clustering analysis',
            'tickers': tickers
        }
    
    # Perform clustering
    clusterer = AssetClustering(method='kmeans')
    n_clusters = min(3, len(tickers) // 2)  # Reasonable number of clusters
    
    results = clusterer.fit_predict(tickers, n_clusters=n_clusters)
    
    # Add diversification recommendations
    current_clusters = len(set(results['cluster_assignments'][i]['cluster'] 
                                for i in range(len(results['cluster_assignments']))))
    
    recommendations = []
    
    if current_clusters < n_clusters:
        recommendations.append("Portfolio is concentrated in few asset types. Consider diversifying across more sectors.")
    
    # Check cluster balance
    cluster_counts = {}
    for assignment in results['cluster_assignments']:
        cluster_id = assignment['cluster']
        cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
    
    max_cluster_size = max(cluster_counts.values())
    if max_cluster_size > len(tickers) * 0.6:
        recommendations.append("Portfolio is heavily weighted in one cluster. Rebalance across clusters for better diversification.")
    
    results['client_id'] = client_id
    results['recommendations'] = recommendations
    
    return results


def main():
    """Demo clustering analysis."""
    from src.utils.helpers import setup_logging
    
    setup_logging()
    
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'JPM', 'BAC', 'GS', 'XOM', 'CVX']
    
    print("\n" + "="*60)
    print("ASSET CLUSTERING ANALYSIS")
    print("="*60 + "\n")
    
    # K-Means clustering
    print("1. K-Means Clustering (3 clusters):")
    kmeans = AssetClustering(method='kmeans')
    results = kmeans.fit_predict(tickers, n_clusters=3)
    
    print(f"   Silhouette Score: {results['metrics']['silhouette_score']:.3f}")
    print(f"   Davies-Bouldin Score: {results['metrics']['davies_bouldin_score']:.3f}")
    print("\n   Cluster Statistics:")
    
    for cluster in results['cluster_stats']:
        print(f"\n   Cluster {cluster['cluster_id']} ({cluster['size']} assets):")
        print(f"     Tickers: {', '.join(cluster['tickers'])}")
        print(f"     Avg Return: {cluster['avg_return']:.2%}")
        print(f"     Avg Volatility: {cluster['avg_volatility']:.2%}")
        print(f"     Avg Sharpe: {cluster['avg_sharpe']:.2f}")
    
    # Diversified portfolio selection
    print("\n2. Diversified Portfolio Selection:")
    diversified = kmeans.get_diversified_portfolio(tickers, method='one_per_cluster')
    print(f"   Selected Assets: {', '.join(diversified)}")
    
    # Hierarchical clustering
    print("\n3. Hierarchical Clustering:")
    hierarchical = AssetClustering(method='hierarchical')
    hier_results = hierarchical.fit_predict(tickers, n_clusters=3)
    
    print(f"   Silhouette Score: {hier_results['metrics']['silhouette_score']:.3f}")
    print("\n   Cluster Assignments:")
    for assignment in hier_results['cluster_assignments']:
        print(f"     {assignment['ticker']}: Cluster {assignment['cluster']}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
