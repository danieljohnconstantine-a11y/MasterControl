"""
Module for parsing greyhound data from extracted text.
"""
import re


def parse_greyhound_data(text):
    """
    Parse greyhound racing data from text content.
    
    Args:
        text (str): Raw text extracted from DOCX file
        
    Returns:
        list: List of dictionaries containing parsed greyhound data
    """
    dogs = []
    lines = text.split('\n')
    
    # Pattern to match dog entries - adjust based on actual DOCX format
    # This is a placeholder pattern that should be customized
    dog_pattern = re.compile(
        r'(\d+)\.\s+([A-Z][A-Za-z\s]+)\s+(\d+[a-z])\s+([\d.]+)kg'
    )
    
    current_race = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try to parse as dog entry
        match = dog_pattern.search(line)
        if match:
            box, name, sex_age, weight = match.groups()
            dog_entry = {
                'Box': int(box),
                'DogName': name.strip(),
                'SexAge': sex_age,
                'Weight': float(weight),
                **current_race
            }
            dogs.append(dog_entry)
    
    return dogs
