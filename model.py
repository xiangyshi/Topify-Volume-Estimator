import math
import numpy as np
import pandas as pd
from util.hf_client import get_similarities
from typing import Callable, List, Optional, Dict, Any


class ChatGPTVolumeEstimator:
    """
    A class for estimating ChatGPT query volume potential using SERP data and logit modeling.
    
    This class encapsulates the entire pipeline from SERP data to domain share estimation
    using visibility, semantic relevance, authority, SERP features, and estimated clicks.
    """
    
    # Class constants
    CTR_MAP = {1: 0.30, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05, 
               6: 0.04, 7: 0.03, 8: 0.02, 9: 0.01, 10: 0.01}
    DEFAULT_CTR_AFTER_10 = 0.005
    
    def __init__(self, 
                 lambdas: List[float] = [1.0, 1.0, 1.0, 1.0, 1.0],
                 alpha: float = 0.15,
                 similarity_func: Callable = get_similarities):
        """
        Initialize the ChatGPT Volume Estimator.
        
        Args:
            lambdas: Weight vector [λ1, λ2, λ3, λ4, λ5] for [vis, sem, auth, feat, est_clicks]
            alpha: Decay parameter for visibility calculation
            similarity_func: Function for semantic similarity calculation
        """
        self.lambdas = lambdas
        self.alpha = alpha
        self.similarity_func = similarity_func
        self.feature_columns = ['vis', 'sem', 'auth', 'feat', 'est_clicks']
    
    def _compute_visibility(self, rank: float) -> float:
        """Compute visibility score based on rank position."""
        if rank is None or (isinstance(rank, float) and np.isnan(rank)):
            return 0.0
        r = max(1.0, float(rank))
        return float(np.exp(-self.alpha * (r - 1)))
    
    def _compute_authority(self, rank: float, max_rank: float) -> float:
        """Compute authority score based on rank position."""
        if rank is None or (isinstance(rank, float) and np.isnan(rank)):
            return 0.0
        r = float(rank)
        return float(max(0.0, 1.0 - (r - 1.0) / max(1.0, max_rank - 1.0)))
    
    def _compute_feature_score(self, row: pd.Series) -> float:
        """Compute SERP feature score based on various signals."""
        score = 0.0
        # Featured snippet strong boost
        if 'is_featured_snippet' in row and row.get('is_featured_snippet'):
            score += 0.6
        # People also ask presence
        if 'in_people_also_ask' in row and row.get('in_people_also_ask'):
            score += 0.4
        return float(min(1.0, score))
    
    def _compute_logit(self, vis: float, sem: float, auth: float, feat: float, est_clicks: float) -> float:
        """Compute logit score from scaled features."""
        return (
            self.lambdas[0] * vis +
            self.lambdas[1] * sem +
            self.lambdas[2] * auth +
            self.lambdas[3] * feat +
            self.lambdas[4] * np.log(est_clicks + 1)
        )
    
    def _compute_domain_share(self, logits: np.ndarray) -> np.ndarray:
        """Compute domain shares using softmax."""
        exps = np.exp(logits - np.max(logits))  # Subtract max for numerical stability
        return exps / (exps.sum() + 1e-12)  # Add small epsilon to prevent division by zero
    
    def fit_transform(self, serp_df: pd.DataFrame, keyword: str) -> pd.DataFrame:
        """
        Map SERP dataframe rows to logit components and compute domain shares.
        
        Args:
            serp_df: DataFrame with columns ['rank_absolute', 'page', 'domain', 'title', 'description', 
                    'is_featured_snippet', 'in_people_also_ask', ...]
            keyword: The search keyword (e.g., "faceless video ai")
        
        Returns:
            DataFrame with original columns plus logit components and domain shares
        """
        # Check if DataFrame is empty
        if serp_df is None or serp_df.empty:
            raise ValueError("SERP DataFrame is empty or None")
        
        # Check required columns
        required_columns = ['rank_absolute', 'title', 'description']
        missing_columns = [col for col in required_columns if col not in serp_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Create a copy to avoid modifying original
        result_df = serp_df.copy()
        
        # 1. Compute Visibility (Vis) - based on rank_absolute
        result_df['vis'] = result_df['rank_absolute'].apply(self._compute_visibility)
        
        # 2. Compute Semantic Score
        # Handle NaN values in title and description
        result_df['title'] = result_df['title'].fillna('')
        result_df['description'] = result_df['description'].fillna('')
        result_df["text_for_semantics"] = result_df['title'] + " " + result_df['description']
        result_df["sem"] = self.similarity_func(keyword, result_df['text_for_semantics'].tolist())[0]
        
        # 3. Compute Authority (Auth) - For Future Implementation
        result_df['auth'] = result_df['rank_absolute'].apply(lambda x: 0)
        
        # 4. Compute SERP Features (Feat)
        result_df['feat'] = result_df.apply(self._compute_feature_score, axis=1)
        
        # 5. Compute Estimated clicks (Est_clicks) - placeholder for future implementation
        result_df['est_clicks'] = result_df['rank_absolute'].apply(lambda x: 0)
        
        # 6. Scale features to [0, 1] range with min-max per column
        for col in self.feature_columns:
            col_min = float(result_df[col].min())
            col_max = float(result_df[col].max())
            denom = (col_max - col_min) if (col_max - col_min) != 0 else 1.0
            result_df[f'{col}_scaled'] = (result_df[col] - col_min) / denom
        
        # 7. Compute final logit score with scaled features
        result_df['logit'] = result_df.apply(
            lambda row: self._compute_logit(
                row['vis_scaled'], 
                row['sem_scaled'], 
                row['auth_scaled'], 
                row['feat_scaled'], 
                row['est_clicks_scaled']
            ), axis=1
        )

        # 8. Compute Domain Share using softmax
        result_df['domain_share'] = self._compute_domain_share(result_df['logit'].values)
        
        return result_df
    
    def transform(self, serp_df: pd.DataFrame, keyword: str) -> pd.DataFrame:
        """
        Transform new SERP data using fitted scaler.
        
        Args:
            serp_df: New SERP DataFrame
            keyword: The search keyword
        
        Returns:
            DataFrame with logit components and domain shares
        """
        # Create a copy to avoid modifying original
        result_df = serp_df.copy()
        
        # Compute all features (same as fit_transform)
        result_df['vis'] = result_df['rank_absolute'].apply(self._compute_visibility)
        # Handle NaN values in title and description
        result_df['title'] = result_df['title'].fillna('')
        result_df['description'] = result_df['description'].fillna('')
        result_df["text_for_semantics"] = result_df['title'] + " " + result_df['description']
        result_df["sem"] = self.similarity_func(keyword, result_df['text_for_semantics'].tolist())[0]
        result_df['auth'] = result_df['rank_absolute'].apply(lambda x: 0)
        result_df['feat'] = result_df.apply(self._compute_feature_score, axis=1)
        result_df['est_clicks'] = result_df['rank_absolute'].apply(lambda x: 0)
        
        # Scale features to [0, 1] using min-max per column (no persistent state)
        for col in self.feature_columns:
            col_min = float(result_df[col].min())
            col_max = float(result_df[col].max())
            denom = (col_max - col_min) if (col_max - col_min) != 0 else 1.0
            result_df[f'{col}_scaled'] = (result_df[col] - col_min) / denom
        
        # Compute logit and domain share
        result_df['logit'] = result_df.apply(
            lambda row: self._compute_logit(
                row['vis_scaled'], 
                row['sem_scaled'], 
                row['auth_scaled'], 
                row['feat_scaled'], 
                row['est_clicks_scaled']
            ), axis=1
        )
        result_df['domain_share'] = self._compute_domain_share(result_df['logit'].values)
        
        return result_df
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get the current lambda weights as feature importance scores."""
        return dict(zip(['visibility', 'semantic', 'authority', 'features', 'estimated_clicks'], self.lambdas))
    
    def set_lambdas(self, lambdas: List[float]):
        """Update the lambda weights."""
        if len(lambdas) != 5:
            raise ValueError("Lambdas must be a list of 5 values")
        self.lambdas = lambdas
    
    def set_alpha(self, alpha: float):
        """Update the visibility decay parameter."""
        self.alpha = alpha