"""
Greyhound Feature Scorer

This module scores greyhound features for betting prediction.
"""

from typing import List, Dict
import re


class FeatureScorer:
    """Score greyhound racing features."""
    
    def __init__(self):
        self.form_scores = {
            '1': 10,  # Win
            '2': 7,   # Second
            '3': 5,   # Third
            '4': 3,   # Fourth
            '5': 1,   # Fifth
            '6': 0,   # Sixth or lower
            '0': 0,   # Did not finish/place
            '-': 0    # No data
        }
    
    def _get_position_score(self, position: str) -> int:
        """
        Get score for a single position.
        
        Args:
            position: Position string (e.g., '1', '2', '3')
            
        Returns:
            Position score
        """
        if position in self.form_scores:
            return self.form_scores[position]
        elif position.isdigit():
            # Handle positions beyond 6
            pos_num = int(position)
            if pos_num <= 5:
                return self.form_scores.get(str(pos_num), 0)
        return 0
    
    def score_form(self, form_string: str) -> float:
        """
        Score a dog's recent form.
        
        Form string example: "1-2-3-1" (most recent on left)
        
        Args:
            form_string: String representing recent race positions
            
        Returns:
            Form score (higher is better)
        """
        if not form_string:
            return 0.0
        
        positions = form_string.split('-')
        score = 0.0
        weight = 1.0
        
        for pos in positions[:5]:  # Consider last 5 races
            pos_clean = pos.strip()
            score += self._get_position_score(pos_clean) * weight
            weight *= 0.8  # Decay weight for older races
        
        return round(score, 2)
    
    def score_trap(self, trap: int) -> float:
        """
        Score based on trap position.
        
        Traps 1-3 often have slight advantages.
        
        Args:
            trap: Trap number (1-6 typically)
            
        Returns:
            Trap score
        """
        trap_scores = {
            1: 5,
            2: 4,
            3: 3,
            4: 2,
            5: 1,
            6: 1
        }
        return trap_scores.get(trap, 0)
    
    def score_age(self, age: int) -> float:
        """
        Score based on dog's age.
        
        Prime racing age is typically 2-4 years.
        
        Args:
            age: Dog's age in years
            
        Returns:
            Age score
        """
        if 2 <= age <= 4:
            return 5
        elif age < 2 or age == 5:
            return 3
        else:
            return 1
    
    def score_weight(self, weight: float) -> float:
        """
        Score based on dog's weight.
        
        Typical racing weight is 28-35kg.
        
        Args:
            weight: Dog's weight in kg
            
        Returns:
            Weight score
        """
        if 28 <= weight <= 35:
            return 5
        elif 26 <= weight < 28 or 35 < weight <= 37:
            return 3
        else:
            return 1
    
    def score_dog(self, dog: Dict, trainer_score: float = 0.0) -> Dict:
        """
        Calculate total score for a dog.
        
        Args:
            dog: Dictionary containing dog data
            trainer_score: Optional trainer score to include in total
            
        Returns:
            Dog dictionary with added scores
        """
        form_score = self.score_form(dog.get('form', ''))
        trap_score = self.score_trap(dog.get('trap', 0))
        age_score = self.score_age(dog.get('age', 0))
        weight_score = self.score_weight(dog.get('weight', 0))
        
        total_score = form_score + trap_score + age_score + weight_score + trainer_score
        
        result = {
            **dog,
            'form_score': form_score,
            'trap_score': trap_score,
            'age_score': age_score,
            'weight_score': weight_score,
            'total_score': round(total_score, 2)
        }
        
        if trainer_score > 0:
            result['trainer_score'] = trainer_score
        
        return result
    
    def score_all(self, dogs: List[Dict], trainer_scores: Dict[str, float] = None) -> List[Dict]:
        """
        Score all dogs in a list.
        
        Args:
            dogs: List of dog dictionaries
            trainer_scores: Optional dict mapping trainer names to scores
            
        Returns:
            List of scored dog dictionaries
        """
        if trainer_scores is None:
            trainer_scores = {}
        
        return [
            self.score_dog(dog, trainer_scores.get(dog.get('trainer', ''), 0.0))
            for dog in dogs
        ]
    
    def rank_dogs(self, dogs: List[Dict]) -> List[Dict]:
        """
        Rank dogs by total score.
        
        Args:
            dogs: List of scored dog dictionaries
            
        Returns:
            Sorted list of dogs (highest score first)
        """
        return sorted(dogs, key=lambda x: x.get('total_score', 0), reverse=True)
