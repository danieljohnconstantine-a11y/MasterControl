"""
Greyhound Racing Form Parser

This module parses greyhound racing form data from text files.
"""

import re
from typing import List, Dict, Optional


class FormParser:
    """Parse greyhound racing form data from text."""
    
    def __init__(self):
        self.races = []
    
    def parse_text_file(self, filepath: str) -> List[Dict]:
        """
        Parse a text file containing race form data.
        
        Args:
            filepath: Path to the text file
            
        Returns:
            List of dictionaries containing race data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[Dict]:
        """
        Parse race form content.
        
        Expected format:
        Race [number]
        Dog: [name], Trap: [number], Trainer: [name], Age: [age], Weight: [weight]
        Form: [form string]
        
        Args:
            content: Raw text content
            
        Returns:
            List of dictionaries with parsed race data
        """
        races = []
        lines = content.strip().split('\n')
        
        current_race = None
        current_dog = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for race header
            race_match = re.match(r'Race\s+(\d+)', line, re.IGNORECASE)
            if race_match:
                current_race = int(race_match.group(1))
                continue
            
            # Check for dog information line
            dog_match = re.match(
                r'Dog:\s*(.+?),\s*Trap:\s*(\d+),\s*Trainer:\s*(.+?),\s*Age:\s*(\d+),\s*Weight:\s*(\d+\.?\d*)',
                line,
                re.IGNORECASE
            )
            if dog_match and current_race is not None:
                current_dog = {
                    'race': current_race,
                    'dog_name': dog_match.group(1).strip(),
                    'trap': int(dog_match.group(2)),
                    'trainer': dog_match.group(3).strip(),
                    'age': int(dog_match.group(4)),
                    'weight': float(dog_match.group(5))
                }
                continue
            
            # Check for form line
            form_match = re.match(r'Form:\s*(.+)', line, re.IGNORECASE)
            if form_match and current_dog:
                current_dog['form'] = form_match.group(1).strip()
                races.append(current_dog)
                current_dog = {}
        
        self.races = races
        return races
    
    def get_race_data(self, race_number: Optional[int] = None) -> List[Dict]:
        """
        Get parsed race data, optionally filtered by race number.
        
        Args:
            race_number: Optional race number to filter by
            
        Returns:
            List of race dictionaries
        """
        if race_number is None:
            return self.races
        return [r for r in self.races if r['race'] == race_number]
