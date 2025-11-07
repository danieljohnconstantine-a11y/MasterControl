"""
Advanced Feature Engineering for Greyhound Racing Analysis
Implements weighted metrics, trend analysis, and comprehensive scoring
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime
import ast


# ==================== CORE HELPER FUNCTIONS (UTILITY LAYER) ====================

def compute_weighted_average(values, weights):
    """
    Compute weighted average with handling for NaNs and mismatched lengths.
    Recent races should have higher weight (e.g. [1.0, 0.8, 0.6, 0.4, 0.2]).
    
    Args:
        values: Array-like of numeric values
        weights: Array-like of weights (most recent first)
    
    Returns:
        float: Weighted average or NaN if no valid values
    """
    values = np.array(values, dtype=float)
    weights = np.array(weights[:len(values)], dtype=float)
    mask = ~np.isnan(values)
    if not np.any(mask):
        return np.nan
    return np.average(values[mask], weights=weights[:np.sum(mask)])


def compute_distance_weight(distances, target_distance):
    """
    Returns distance similarity weights: closer = higher weight.
    Example: if current distance is 320m and dog ran 324m, weight ≈ 0.99.
    
    Args:
        distances: Array of past race distances
        target_distance: Current race distance
    
    Returns:
        Array of weights (0-1 scale)
    """
    distances = np.array(distances, dtype=float)
    return 1 - np.minimum(np.abs(distances - target_distance) / target_distance, 1)


def compute_trend(values):
    """
    Returns slope (trend) of a numeric series — negative slope = improving form.
    Used for FormMomentum, SpeedImprovementRate, TrainerFormTrend, etc.
    
    Args:
        values: Array-like of numeric values (most recent first)
    
    Returns:
        float: Slope coefficient (negative = improving)
    """
    values = np.array(values, dtype=float)
    if len(values) < 2 or np.all(np.isnan(values)):
        return 0.0
    x = np.arange(len(values))
    mask = ~np.isnan(values)
    if np.sum(mask) < 2:
        return 0.0
    slope, _, _, _, _ = linregress(x[mask], values[mask])
    return slope


def extract_recent_runs_data(recent_runs_str, limit=10):
    """
    Parse RecentRuns string into structured data
    
    Returns:
        dict with lists of positions, margins, times, distances, etc.
    """
    if pd.isna(recent_runs_str):
        return None
    
    try:
        runs = ast.literal_eval(recent_runs_str)
    except:
        return None
    
    if not runs:
        return None
    
    data = {
        'positions': [],
        'margins': [],
        'race_times': [],
        'sectional_times': [],
        'distances': [],
        'tracks': [],
        'dates': [],
        'prizes': []
    }
    
    for run in runs[:limit]:
        # Position
        if run.get('pos'):
            try:
                pos_num = int(''.join(filter(str.isdigit, run['pos'])))
                data['positions'].append(pos_num)
            except:
                data['positions'].append(np.nan)
        else:
            data['positions'].append(np.nan)
        
        # Margin
        if run.get('margin'):
            try:
                data['margins'].append(float(run['margin']))
            except:
                data['margins'].append(np.nan)
        else:
            data['margins'].append(np.nan)
        
        # Race time
        if run.get('racetime'):
            try:
                time_str = run['racetime']
                if ':' in time_str:
                    parts = time_str.split(':')
                    seconds = float(parts[0]) * 60 + float(parts[1])
                else:
                    seconds = float(time_str)
                data['race_times'].append(seconds)
            except:
                data['race_times'].append(np.nan)
        else:
            data['race_times'].append(np.nan)
        
        # Sectional time
        if run.get('sectime'):
            try:
                data['sectional_times'].append(float(run['sectime']))
            except:
                data['sectional_times'].append(np.nan)
        else:
            data['sectional_times'].append(np.nan)
        
        # Distance
        if run.get('distance'):
            try:
                data['distances'].append(int(run['distance']))
            except:
                data['distances'].append(np.nan)
        else:
            data['distances'].append(np.nan)
        
        # Track
        data['tracks'].append(run.get('track', ''))
        
        # Date
        data['dates'].append(run.get('date', ''))
        
        # Prize
        if run.get('prize'):
            try:
                data['prizes'].append(float(run['prize']))
            except:
                data['prizes'].append(np.nan)
        else:
            data['prizes'].append(np.nan)
    
    return data


# ==================== ADVANCED FEATURE COMPUTATION ====================

def compute_advanced_features(df):
    """
    Main function to compute all advanced features
    """
    df = df.copy()
    
    # Ensure numeric types
    numeric_cols = ['DLR', 'CareerStarts', 'Distance', 'CareerWins', 'CareerPlaces', 'PrizeMoney']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print("🧮 Computing advanced features...")
    
    # Extract structured data from RecentRuns
    print("   Parsing race history...")
    df['_recent_data'] = df['RecentRuns'].apply(extract_recent_runs_data)
    
    # Extract individual components
    df['FinishPositions'] = df['_recent_data'].apply(lambda x: x['positions'] if x else [])
    df['Margins'] = df['_recent_data'].apply(lambda x: x['margins'] if x else [])
    df['PastTimes'] = df['_recent_data'].apply(lambda x: x['race_times'] if x else [])
    df['PastSectionals'] = df['_recent_data'].apply(lambda x: x['sectional_times'] if x else [])
    df['PastDistances'] = df['_recent_data'].apply(lambda x: x['distances'] if x else [])
    df['PastTracks'] = df['_recent_data'].apply(lambda x: x['tracks'] if x else [])
    df['NumRaces'] = df['FinishPositions'].apply(len)
    
    # ==================== FORM AND CONSISTENCY ====================
    print("   Computing form metrics...")
    
    df['WeightedAvgMargin'] = df['Margins'].apply(
        lambda x: compute_weighted_average(x, [1.0, 0.8, 0.6, 0.4, 0.2])
    )
    
    df['WeightedAvgFinish'] = df['FinishPositions'].apply(
        lambda x: compute_weighted_average(x, [1.0, 0.8, 0.6, 0.4, 0.2])
    )
    
    df['FormConfidence'] = np.minimum(1.0, df['NumRaces'] / 5)
    
    df['FormMomentum'] = df['FinishPositions'].apply(compute_trend)
    
    df['FinishConsistency'] = df['FinishPositions'].apply(
        lambda x: np.std(x) if len(x) > 1 else np.nan
    )
    
    # ==================== DISTANCE SUITABILITY ====================
    print("   Computing distance suitability...")
    
    df['CurrentDistance'] = df['Distance']
    
    df['DistanceWeights'] = df.apply(
        lambda r: compute_distance_weight(r['PastDistances'], r['CurrentDistance']) 
        if len(r['PastDistances']) > 0 else [],
        axis=1
    )
    
    def avg_time_same_dist(row):
        times = []
        for d, t in zip(row['PastDistances'], row['PastTimes']):
            if not np.isnan(d) and not np.isnan(t) and abs(d - row['CurrentDistance']) <= 20:
                times.append(t)
        return np.nanmean(times) if times else np.nan
    
    df['AvgTimeSameDist'] = df.apply(avg_time_same_dist, axis=1)
    
    def best_time_same_dist(row):
        times = []
        for d, t in zip(row['PastDistances'], row['PastTimes']):
            if not np.isnan(d) and not np.isnan(t) and abs(d - row['CurrentDistance']) <= 20:
                times.append(t)
        return np.nanmin(times) if times else np.nan
    
    df['BestTimeSameDist'] = df.apply(best_time_same_dist, axis=1)
    
    df['AvgTimeAll'] = df['PastTimes'].apply(lambda x: np.nanmean(x) if len(x) > 0 else np.nan)
    
    df['DistanceSuit'] = df.apply(
        lambda r: r['AvgTimeAll'] / r['AvgTimeSameDist'] 
        if pd.notna(r['AvgTimeSameDist']) and r['AvgTimeSameDist'] > 0 else 1.0,
        axis=1
    )
    
    df['DogAvgDistance'] = df['PastDistances'].apply(lambda x: np.nanmean(x) if len(x) > 0 else np.nan)
    df['DistanceDelta'] = np.abs(df['CurrentDistance'] - df['DogAvgDistance'])
    
    # ==================== SPEED AND SECTIONALS ====================
    print("   Computing speed metrics...")
    
    df['FirstSectional'] = df['PastSectionals'].apply(lambda x: x[0] if len(x) > 0 else np.nan)
    df['EarlySpeedIndex'] = df.apply(
        lambda r: r['FirstSectional'] / r['CurrentDistance'] * 1000
        if pd.notna(r['FirstSectional']) and r['CurrentDistance'] > 0 else np.nan,
        axis=1
    )
    
    df['RaceTime'] = df['PastTimes'].apply(lambda x: x[0] if len(x) > 0 else np.nan)
    df['SectionalDistance'] = 100  # Assume first 100m for sectional
    
    df['FinishSpeedIndex'] = df.apply(
        lambda r: ((r['RaceTime'] - r['FirstSectional']) / (r['CurrentDistance'] - r['SectionalDistance']))
        if pd.notna(r['RaceTime']) and pd.notna(r['FirstSectional']) and r['CurrentDistance'] > r['SectionalDistance']
        else np.nan,
        axis=1
    )
    
    df['Speed_kmh'] = df.apply(
        lambda r: (r['CurrentDistance'] / r['RaceTime']) * 3.6
        if pd.notna(r['RaceTime']) and r['RaceTime'] > 0 else np.nan,
        axis=1
    )
    
    df['PastSpeeds'] = df.apply(
        lambda r: [(d / t) * 3.6 for d, t in zip(r['PastDistances'], r['PastTimes']) 
                   if not np.isnan(d) and not np.isnan(t) and t > 0],
        axis=1
    )
    
    df['SpeedImprovementRate'] = df['PastSpeeds'].apply(compute_trend)
    
    # ==================== TRAINER AND KENNEL ====================
    print("   Computing trainer metrics...")
    
    # Trainer strike rate (aggregated)
    if 'Trainer' in df.columns:
        trainer_wins = df.groupby('Trainer')['CareerWins'].sum()
        trainer_starts = df.groupby('Trainer')['CareerStarts'].sum()
        trainer_sr = (trainer_wins / trainer_starts).fillna(0)
        df['TrainerStrikeRate'] = df['Trainer'].map(trainer_sr)
    else:
        df['TrainerStrikeRate'] = 0.15
    
    # Track-specific trainer performance
    if 'Trainer' in df.columns and 'Track' in df.columns:
        track_trainer_wins = df.groupby(['Trainer', 'Track'])['CareerWins'].sum()
        track_trainer_starts = df.groupby(['Trainer', 'Track'])['CareerStarts'].sum()
        track_trainer_sr = (track_trainer_wins / track_trainer_starts).fillna(0)
        df['TrainerTrackSR'] = df.apply(
            lambda r: track_trainer_sr.get((r['Trainer'], r['Track']), 0),
            axis=1
        )
    else:
        df['TrainerTrackSR'] = df['TrainerStrikeRate']
    
    # ==================== FATIGUE AND EXPOSURE ====================
    print("   Computing rest and fatigue metrics...")
    
    # Estimate days since last race (simplified - would need actual dates)
    df['DaysSinceLastRun'] = 10  # Placeholder
    
    df['RestFactor'] = df['DaysSinceLastRun'].apply(
        lambda d: 1.0 if 7 <= d <= 14 else max(0, 1 - abs(d - 10) / 20)
    )
    
    df['OverexposedPenalty'] = df['DaysSinceLastRun'].apply(
        lambda d: -0.1 if d <= 3 else 0
    )
    
    df['DistanceRangeAdaptability'] = df['PastDistances'].apply(
        lambda x: np.std(x) if len(x) > 1 else 0
    )
    
    # ==================== PRIZE AND COMPETITION ====================
    print("   Computing prize and competition metrics...")
    
    df['AvgPrizeMoneyPerStart'] = df.apply(
        lambda r: r['PrizeMoney'] / r['CareerStarts'] 
        if r['CareerStarts'] > 0 else 0,
        axis=1
    )
    
    # Grade weighting (if grade data available)
    grade_weights = {"G1": 1.0, "G2": 0.8, "G3": 0.6, "LR": 0.5, "MDN": 0.3}
    if 'Grade' in df.columns:
        df['PrizeGradeWeighting'] = df['Grade'].map(grade_weights).fillna(0.5)
    else:
        df['PrizeGradeWeighting'] = 0.5
    
    # ==================== BOX PERFORMANCE ====================
    print("   Computing box performance...")
    
    if 'Box' in df.columns and 'DogName' in df.columns:
        # Simulate win data (would come from race history in production)
        df['_Win'] = (df['FinishPositions'].apply(lambda x: x[0] if len(x) > 0 else np.nan) == 1).astype(float)
        
        box_stats = df.groupby(['DogName', 'Box']).agg({
            '_Win': 'mean',
            'WeightedAvgMargin': 'mean'
        }).reset_index()
        box_stats.columns = ['DogName', 'Box', 'Win_BoxAvg', 'Margin_BoxAvg']
        
        df = df.merge(box_stats, on=['DogName', 'Box'], how='left', suffixes=('', '_dup'))
        
        overall_win_rate = df['_Win'].mean()
        overall_margin = df['WeightedAvgMargin'].mean()
        
        df['BoxBiasFactor'] = df.apply(
            lambda r: (r.get('Win_BoxAvg', overall_win_rate) - overall_win_rate) * 
                     (1 - (r.get('Margin_BoxAvg', overall_margin) / overall_margin))
            if pd.notna(r.get('Margin_BoxAvg')) and overall_margin > 0 else 0,
            axis=1
        )
        
        df['BoxSuitability'] = df.apply(
            lambda r: (r.get('Win_BoxAvg', 0) * 0.6 + 
                      (1 / (1 + r.get('Margin_BoxAvg', 1))) * 0.4),
            axis=1
        )
    else:
        df['BoxBiasFactor'] = 0.1
        df['BoxSuitability'] = 0.5
    
    # Track win rate
    if 'Track' in df.columns and 'DogName' in df.columns and '_Win' in df.columns:
        track_wins = df.groupby(['DogName', 'Track'])['_Win'].mean()
        df['TrackWinRate'] = df.apply(
            lambda r: track_wins.get((r['DogName'], r['Track']), 0),
            axis=1
        )
    else:
        df['TrackWinRate'] = 0.15
    
    # ==================== COMPOSITE SCORES ====================
    print("   Computing composite scores...")
    
    df['FormReliabilityScore'] = df.apply(
        lambda r: (10 - r['FinishConsistency']) * r['FormConfidence']
        if pd.notna(r['FinishConsistency']) else r['FormConfidence'] * 5,
        axis=1
    )
    
    df['BoxPerformanceScore'] = df['BoxSuitability'] * (1 + df['BoxBiasFactor'])
    
    df['DistanceSuitabilityScore'] = df['DistanceSuit'] - (df['DistanceDelta'] / 1000)
    
    df['TrainerConfidenceScore'] = df['TrainerStrikeRate'] * (1 + df['TrainerTrackSR'])
    
    # ==================== OVERALL FINAL SCORE ====================
    print("   Computing overall final score...")
    
    df['OverallFinalScoreRaw'] = (
        0.25 * df['FormMomentum'].fillna(0) +
        0.20 * df['DistanceSuitabilityScore'].fillna(0) +
        0.15 * df['BoxPerformanceScore'].fillna(0) +
        0.15 * df['TrainerConfidenceScore'].fillna(0) +
        0.10 * df['FormReliabilityScore'].fillna(0) +
        0.10 * df['RestFactor'].fillna(0.8) +
        0.05 * df['SpeedImprovementRate'].fillna(0) +
        df['OverexposedPenalty'].fillna(0)
    )
    
    # Normalize to 0-100 scale
    raw_min = df['OverallFinalScoreRaw'].min()
    raw_max = df['OverallFinalScoreRaw'].max()
    
    if raw_max > raw_min:
        df['OverallFinalScore'] = 100 * (df['OverallFinalScoreRaw'] - raw_min) / (raw_max - raw_min)
    else:
        df['OverallFinalScore'] = 50.0
    
    # Clean up temporary columns
    cols_to_drop = ['_recent_data', '_Win']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    print("✅ Advanced features computed successfully")
    
    return df


def save_advanced_features(df, output_dir='outputs'):
    """Save the advanced features to CSV"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{output_dir}/greyhound_features_extended_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"📊 Saved extended features: {filename}")
    
    # Show top 10 dogs
    print("\n🏆 Top 10 Dogs by OverallFinalScore:")
    print("=" * 80)
    top10 = df.sort_values('OverallFinalScore', ascending=False).head(10)
    display_cols = ['DogName', 'Trainer', 'Track', 'RaceNumber', 'OverallFinalScore', 
                    'FormMomentum', 'DistanceSuitabilityScore', 'BoxPerformanceScore']
    available_cols = [c for c in display_cols if c in top10.columns]
    print(top10[available_cols].to_string(index=False))
    
    return filename


if __name__ == '__main__':
    # Test with sample data
    print("Testing advanced features module...")
    df = pd.read_csv('outputs/todays_form.csv')
    df_advanced = compute_advanced_features(df)
    save_advanced_features(df_advanced)
