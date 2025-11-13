"""
Parse DOCX blocks into structured summary and history rows.
Replaces parse_data.py with clean implementation.
"""
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime


def parse_race_header(text: str) -> Dict[str, str]:
    """Extract race metadata from header text."""
    metadata = {}
    
    # Pattern: "Race No 12 Nov 25 06:35PM Cannington 275m"
    race_pattern = r'Race\s+No\.?\s*(\d+)\s+(\d{1,2}\s+\w+\s+\d{2})\s+.*?([A-Z][a-z]+)\s+(\d+)m'
    match = re.search(race_pattern, text, re.IGNORECASE)
    
    if match:
        metadata['Race_No'] = match.group(1)
        
        # Parse date
        date_str = match.group(2)
        try:
            # Try parsing "12 Nov 25" format
            date_obj = datetime.strptime(date_str, "%d %b %y")
            metadata['Race_Date'] = date_obj.strftime("%Y-%m-%d")
        except:
            metadata['Race_Date'] = ""
        
        metadata['Track'] = match.group(3)
        metadata['Distance_m'] = match.group(4)
    
    return metadata


def parse_dog_line(text: str, race_metadata: Dict[str, str]) -> Dict[str, Any]:
    """Parse a single dog entry line."""
    dog_data = race_metadata.copy()
    
    # Pattern for numbered dog entry: "1. DOG NAME ..."
    dog_pattern = r'^(\d+)\.\s+([A-Z][A-Z\s\'-]+)'
    match = re.match(dog_pattern, text)
    
    if match:
        dog_data['Box'] = match.group(1)
        dog_data['Dog_Name'] = match.group(2).strip()
    
    # Extract Tab_No
    tab_pattern = r'T(?:ab)?:?\s*(\d+)'
    tab_match = re.search(tab_pattern, text)
    if tab_match:
        dog_data['Tab_No'] = tab_match.group(1)
    
    # Extract Trainer
    trainer_pattern = r'(?:Trainer|Trnr):?\s*([A-Z][A-Za-z\s\'-]+?)(?:\s+\(|$|\s+[A-Z]{2})'
    trainer_match = re.search(trainer_pattern, text)
    if trainer_match:
        dog_data['Trainer'] = trainer_match.group(1).strip()
    
    # Extract Weight
    weight_pattern = r'(\d+\.?\d*)\s*kg'
    weight_match = re.search(weight_pattern, text, re.IGNORECASE)
    if weight_match:
        dog_data['WT (kg)'] = weight_match.group(1)
    
    # Extract A/S (Age/Sex)
    as_pattern = r'\b([BDR][DGM])\b'
    as_match = re.search(as_pattern, text)
    if as_match:
        dog_data['A/S'] = as_match.group(1)
    
    # Extract Prize Money
    prize_pattern = r'\$([0-9,]+)'
    prize_match = re.search(prize_pattern, text)
    if prize_match:
        dog_data['Prize_Money'] = prize_match.group(1).replace(',', '')
    
    return dog_data


def parse_history_line(text: str, dog_info: Dict[str, str]) -> Dict[str, Any]:
    """Parse a historical race line for a dog."""
    history = {
        'Dog_Name': dog_info.get('Dog_Name', ''),
        'Tab_No': dog_info.get('Tab_No', ''),
        'Race_Track': dog_info.get('Track', ''),
        'Race_Date': dog_info.get('Race_Date', ''),
        'Race_No': dog_info.get('Race_No', ''),
        'Box': dog_info.get('Box', ''),
    }
    
    # Extract historical date
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    date_match = re.search(date_pattern, text)
    if date_match:
        history['Hist_Date'] = date_match.group(1)
    
    # Extract track
    track_pattern = r'\b([A-Z][a-z]+(?:on)?)\b'
    track_match = re.search(track_pattern, text)
    if track_match:
        history['Hist_Track'] = track_match.group(1)
    
    # Extract distance
    dist_pattern = r'(\d+)m'
    dist_match = re.search(dist_pattern, text)
    if dist_match:
        history['Hist_Distance'] = dist_match.group(1)
    
    # Extract race time
    time_pattern = r'(\d{1,2}:\d{2}\.\d{2}|\d{2}\.\d{2})'
    time_match = re.search(time_pattern, text)
    if time_match:
        history['Hist_Race_Time'] = time_match.group(1)
    
    # Extract finish position
    pos_pattern = r'\b([1-8])(?:st|nd|rd|th)\b'
    pos_match = re.search(pos_pattern, text)
    if pos_match:
        history['Hist_Finish_Pos'] = pos_match.group(1)
    
    # Extract margin
    margin_pattern = r'(\d+\.?\d*)[LH]'
    margin_match = re.search(margin_pattern, text)
    if margin_match:
        history['Hist_Margin_L'] = margin_match.group(1)
    
    return history


def parse_docx_blocks(blocks: List[Dict[str, Any]], source_file: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Parse blocks into summary_rows and history_rows.
    
    Returns:
        - summary_rows: list of dog summary dicts
        - history_rows: list of historical race dicts
        - unparsed: list of unparsed text lines
    """
    summary_rows = []
    history_rows = []
    unparsed = []
    
    race_metadata = {}
    current_dog = None
    
    for block in blocks:
        block_type = block.get('type', '')
        raw_text = block.get('raw', '')
        
        # Check headers for race metadata
        if block_type == 'header' or block_type == 'paragraph':
            meta = parse_race_header(raw_text)
            if meta:
                race_metadata.update(meta)
        
        # Parse tables (main dog data)
        if block_type == 'table':
            table_data = block.get('table', [])
            
            for row in table_data:
                row_text = ' '.join(row)
                
                # Try to parse as dog entry
                if re.match(r'^\d+\.', row_text):
                    dog_info = parse_dog_line(row_text, race_metadata)
                    dog_info['Data_Source_File'] = source_file
                    
                    if dog_info.get('Dog_Name'):
                        summary_rows.append(dog_info)
                        current_dog = dog_info
                    else:
                        unparsed.append(f"Dog line unparsed: {row_text}")
                
                # Try to parse as history line
                elif current_dog and (re.search(r'\d{1,2}[/-]\d{1,2}', row_text) or re.search(r'\d+m', row_text)):
                    history = parse_history_line(row_text, current_dog)
                    history_rows.append(history)
        
        # Parse paragraphs
        elif block_type == 'paragraph':
            # Check if it's a dog line
            if re.match(r'^\d+\.', raw_text):
                dog_info = parse_dog_line(raw_text, race_metadata)
                dog_info['Data_Source_File'] = source_file
                
                if dog_info.get('Dog_Name'):
                    summary_rows.append(dog_info)
                    current_dog = dog_info
                else:
                    unparsed.append(f"Dog line unparsed: {raw_text}")
    
    return summary_rows, history_rows, unparsed


def parse_all_files(files_data: Dict[str, List[Dict[str, Any]]]) -> Tuple[List[Dict], List[Dict], Dict[str, List[str]]]:
    """
    Parse all DOCX files.
    
    Returns:
        - all_summary_rows
        - all_history_rows
        - unparsed_by_file
    """
    all_summary = []
    all_history = []
    unparsed_by_file = {}
    
    for filename, blocks in files_data.items():
        summary, history, unparsed = parse_docx_blocks(blocks, filename)
        all_summary.extend(summary)
        all_history.extend(history)
        
        if unparsed:
            unparsed_by_file[filename] = unparsed
    
    return all_summary, all_history, unparsed_by_file
