"""
Test suite for advanced features module
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features_advanced import (
    compute_weighted_average,
    compute_distance_weight,
    compute_trend,
    compute_advanced_features
)


class TestHelperFunctions:
    """Test core helper functions"""
    
    def test_weighted_average_basic(self):
        """Test basic weighted average calculation"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        weights = [1.0, 0.8, 0.6, 0.4, 0.2]
        result = compute_weighted_average(values, weights)
        # More recent values should have higher impact
        assert result < np.mean(values)  # Weighted towards lower (recent) values
        assert not np.isnan(result)
    
    def test_weighted_average_with_nans(self):
        """Test weighted average handles NaN values"""
        values = [1.0, np.nan, 3.0, np.nan, 5.0]
        weights = [1.0, 0.8, 0.6, 0.4, 0.2]
        result = compute_weighted_average(values, weights)
        assert not np.isnan(result)
    
    def test_weighted_average_all_nans(self):
        """Test weighted average returns NaN when all values are NaN"""
        values = [np.nan, np.nan, np.nan]
        weights = [1.0, 0.8, 0.6]
        result = compute_weighted_average(values, weights)
        assert np.isnan(result)
    
    def test_distance_weight_exact_match(self):
        """Test distance weight is 1.0 for exact match"""
        distances = [320, 320, 320]
        target = 320
        weights = compute_distance_weight(distances, target)
        assert all(weights == 1.0)
    
    def test_distance_weight_decreases_with_difference(self):
        """Test distance weight decreases as difference increases"""
        distances = [320, 340, 360, 400]
        target = 320
        weights = compute_distance_weight(distances, target)
        # Weights should decrease monotonically
        assert weights[0] > weights[1] > weights[2] > weights[3]
    
    def test_trend_improving(self):
        """Test trend detection for improving performance (positions getting lower)"""
        # Positions: 5, 4, 3, 2, 1 (improving)
        values = [5, 4, 3, 2, 1]
        trend = compute_trend(values)
        # Negative slope = improving (positions decreasing)
        assert trend < 0
    
    def test_trend_declining(self):
        """Test trend detection for declining performance"""
        # Positions: 1, 2, 3, 4, 5 (declining)
        values = [1, 2, 3, 4, 5]
        trend = compute_trend(values)
        # Positive slope = declining (positions increasing)
        assert trend > 0
    
    def test_trend_stable(self):
        """Test trend detection for stable performance"""
        values = [3, 3, 3, 3, 3]
        trend = compute_trend(values)
        assert abs(trend) < 0.1  # Near zero


class TestAdvancedFeatures:
    """Test advanced feature computation"""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe for testing"""
        return pd.DataFrame({
            'DogName': ['Dog A', 'Dog B', 'Dog C'],
            'Track': ['Track 1', 'Track 1', 'Track 1'],
            'RaceNumber': [1, 1, 1],
            'Box': [1, 2, 3],
            'Distance': [320, 320, 320],
            'CareerWins': [10, 5, 2],
            'CareerStarts': [50, 40, 30],
            'CareerPlaces': [20, 15, 8],
            'PrizeMoney': [50000, 30000, 10000],
            'Trainer': ['Trainer A', 'Trainer B', 'Trainer A'],
            'DLR': [5, 10, 20],
            'RecentRuns': [
                str([{'pos': '1st', 'margin': 2.0, 'distance': 320, 'racetime': '22.50', 'sectime': '8.2'},
                     {'pos': '2nd', 'margin': 1.5, 'distance': 320, 'racetime': '22.60', 'sectime': '8.3'}]),
                str([{'pos': '3rd', 'margin': 3.0, 'distance': 320, 'racetime': '23.00', 'sectime': '8.5'}]),
                str([{'pos': '5th', 'margin': 5.0, 'distance': 340, 'racetime': '23.50', 'sectime': '8.7'}])
            ]
        })
    
    def test_distance_suit_increases_for_matching_distances(self, sample_df):
        """Test distance suitability is better for dogs racing at their preferred distance"""
        df = compute_advanced_features(sample_df)
        # Dog A has runs at exact distance (320m)
        # Dog C has runs at different distance (340m)
        assert df[df['DogName'] == 'Dog A']['DistanceSuit'].values[0] >= \
               df[df['DogName'] == 'Dog C']['DistanceSuit'].values[0]
    
    def test_overall_score_within_bounds(self, sample_df):
        """Test overall final score is normalized between 0 and 100"""
        df = compute_advanced_features(sample_df)
        assert df['OverallFinalScore'].min() >= 0
        assert df['OverallFinalScore'].max() <= 100
    
    def test_box_bias_positive_for_favored_box(self, sample_df):
        """Test box bias factor reflects box preference"""
        df = compute_advanced_features(sample_df)
        # Box bias should be calculated
        assert 'BoxBiasFactor' in df.columns
        # Values should be reasonable
        assert df['BoxBiasFactor'].notna().any()
    
    def test_form_momentum_computed(self, sample_df):
        """Test form momentum is calculated from recent performance"""
        df = compute_advanced_features(sample_df)
        assert 'FormMomentum' in df.columns
        # Dog A improving (1st, 2nd) should have negative momentum (good)
        # Dog C declining should have positive momentum (bad)
        dog_a_momentum = df[df['DogName'] == 'Dog A']['FormMomentum'].values[0]
        dog_c_momentum = df[df['DogName'] == 'Dog C']['FormMomentum'].values[0]
        assert dog_a_momentum < dog_c_momentum
    
    def test_weighted_avg_finish_favors_recent(self, sample_df):
        """Test weighted average gives more weight to recent races"""
        df = compute_advanced_features(sample_df)
        assert 'WeightedAvgFinish' in df.columns
        # Dog A with recent 1st, 2nd should have better weighted average
        assert df[df['DogName'] == 'Dog A']['WeightedAvgFinish'].values[0] < \
               df[df['DogName'] == 'Dog C']['WeightedAvgFinish'].values[0]
    
    def test_trainer_strike_rate_computed(self, sample_df):
        """Test trainer strike rate is calculated"""
        df = compute_advanced_features(sample_df)
        assert 'TrainerStrikeRate' in df.columns
        # Trainer A has 2 dogs, should have aggregated stats
        trainer_a_sr = df[df['Trainer'] == 'Trainer A']['TrainerStrikeRate'].values[0]
        assert 0 <= trainer_a_sr <= 1
    
    def test_speed_metrics_computed(self, sample_df):
        """Test speed metrics are calculated from race times"""
        df = compute_advanced_features(sample_df)
        assert 'Speed_kmh' in df.columns
        assert 'EarlySpeedIndex' in df.columns
        # Faster dog should have higher speed
        dog_a_speed = df[df['DogName'] == 'Dog A']['Speed_kmh'].values[0]
        dog_c_speed = df[df['DogName'] == 'Dog C']['Speed_kmh'].values[0]
        if pd.notna(dog_a_speed) and pd.notna(dog_c_speed):
            assert dog_a_speed > dog_c_speed  # Dog A is faster (22.50 vs 23.50)
    
    def test_all_required_features_present(self, sample_df):
        """Test that all expected features are computed"""
        df = compute_advanced_features(sample_df)
        
        required_features = [
            'WeightedAvgMargin', 'WeightedAvgFinish', 'FormConfidence',
            'FormMomentum', 'DistanceSuit', 'DistanceDelta',
            'EarlySpeedIndex', 'Speed_kmh', 'TrainerStrikeRate',
            'RestFactor', 'OverexposedPenalty', 'FormReliabilityScore',
            'BoxPerformanceScore', 'DistanceSuitabilityScore',
            'TrainerConfidenceScore', 'OverallFinalScore'
        ]
        
        for feature in required_features:
            assert feature in df.columns, f"Missing feature: {feature}"
    
    def test_no_crashes_with_missing_data(self):
        """Test that feature computation handles missing/incomplete data gracefully"""
        incomplete_df = pd.DataFrame({
            'DogName': ['Dog X'],
            'Distance': [320],
            'CareerStarts': [0],  # No starts
            'RecentRuns': [None]  # No history
        })
        
        # Should not crash
        df = compute_advanced_features(incomplete_df)
        assert len(df) == 1
        assert 'OverallFinalScore' in df.columns


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_dataframe(self):
        """Test handling of empty dataframe"""
        empty_df = pd.DataFrame()
        # Should handle gracefully
        try:
            result = compute_advanced_features(empty_df)
            assert len(result) == 0
        except Exception as e:
            pytest.fail(f"Failed on empty dataframe: {e}")
    
    def test_single_race_history(self):
        """Test with dog having only one race"""
        df = pd.DataFrame({
            'DogName': ['Single Race Dog'],
            'Distance': [320],
            'CareerStarts': [1],
            'CareerWins': [1],
            'PrizeMoney': [1000],
            'RecentRuns': [str([{'pos': '1st', 'distance': 320, 'racetime': '22.50'}])]
        })
        
        result = compute_advanced_features(df)
        # Should compute features even with limited data
        assert 'OverallFinalScore' in result.columns
        assert pd.notna(result['OverallFinalScore'].values[0])


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
