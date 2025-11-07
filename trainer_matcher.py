"""
Trainer Matcher

This module matches and analyzes trainer performance.
"""

from typing import List, Dict
from collections import defaultdict


class TrainerMatcher:
    """Match and analyze trainer statistics."""
    
    def __init__(self):
        self.trainer_stats = defaultdict(lambda: {'wins': 0, 'races': 0, 'dogs': []})
    
    def analyze_trainers(self, dogs: List[Dict]) -> Dict:
        """
        Analyze trainer performance from dog data.
        
        Args:
            dogs: List of dog dictionaries
            
        Returns:
            Dictionary of trainer statistics
        """
        self.trainer_stats.clear()
        
        for dog in dogs:
            trainer = dog.get('trainer', 'Unknown')
            self.trainer_stats[trainer]['races'] += 1
            self.trainer_stats[trainer]['dogs'].append(dog['dog_name'])
            
            # Check if dog has winning form
            form = dog.get('form', '')
            if form and form.split('-')[0] == '1':
                self.trainer_stats[trainer]['wins'] += 1
        
        # Calculate win rates
        for trainer in self.trainer_stats:
            races = self.trainer_stats[trainer]['races']
            wins = self.trainer_stats[trainer]['wins']
            self.trainer_stats[trainer]['win_rate'] = (
                round(wins / races * 100, 2) if races > 0 else 0.0
            )
        
        return dict(self.trainer_stats)
    
    def get_trainer_score(self, trainer: str) -> float:
        """
        Get a score for a trainer based on their statistics.
        
        Args:
            trainer: Trainer name
            
        Returns:
            Trainer score
        """
        if trainer not in self.trainer_stats:
            return 0.0
        
        win_rate = self.trainer_stats[trainer]['win_rate']
        races = self.trainer_stats[trainer]['races']
        
        # Score based on win rate with confidence from race count
        base_score = win_rate / 10  # 100% win rate = 10 points
        confidence = min(races / 10, 1.0)  # More races = higher confidence
        
        return round(base_score * confidence, 2)
    
    def enhance_dogs_with_trainer_scores(self, dogs: List[Dict]) -> List[Dict]:
        """
        Add trainer scores to dog data.
        
        Args:
            dogs: List of dog dictionaries
            
        Returns:
            List of dogs with trainer_score added
        """
        if not self.trainer_stats:
            self.analyze_trainers(dogs)
        
        enhanced = []
        for dog in dogs:
            trainer = dog.get('trainer', 'Unknown')
            trainer_score = self.get_trainer_score(trainer)
            enhanced.append({
                **dog,
                'trainer_score': trainer_score
            })
        
        return enhanced
    
    def get_top_trainers(self, limit: int = 5) -> List[Dict]:
        """
        Get top trainers by win rate.
        
        Args:
            limit: Number of top trainers to return
            
        Returns:
            List of trainer dictionaries
        """
        trainers = [
            {
                'trainer': name,
                'wins': stats['wins'],
                'races': stats['races'],
                'win_rate': stats['win_rate']
            }
            for name, stats in self.trainer_stats.items()
        ]
        
        return sorted(trainers, key=lambda x: x['win_rate'], reverse=True)[:limit]
