"""
Parse DOCX content into structured summary and history rows.
"""
import re
from datetime import datetime


def parse_docx_content(extraction_result):
    """
    Parse extracted DOCX content into summary_rows and history_rows.
    
    Args:
        extraction_result: Dict with 'filename' and 'paragraphs'
        
    Returns:
        Tuple of (summary_rows, history_rows, unparsed_lines)
    """
    filename = extraction_result['filename']
    paragraphs = extraction_result['paragraphs']
    
    summary_rows = []
    history_rows = []
    unparsed_lines = []
    
    # Extract race metadata from header
    track = ""
    race_date = ""
    race_no = ""
    distance = ""
    
    for para in paragraphs[:10]:  # Check first 10 paragraphs for race info
        # Pattern: "Race No	12 Nov 25 06:35PM Cannington 275m FREE ENTRY..."
        # Format: Day Month Year Time Track Distance
        # Example: 12 Nov 25 06:35PM Cannington 275m
        race_match = re.search(r'Race\s+No\s+(\d{1,2})\s+(\w+)\s+(\d{2})\s+\d{1,2}:\d{2}[AP]M\s+([\w\s]+?)\s+(\d+)m', para)
        if race_match:
            day = race_match.group(1)
            month = race_match.group(2)
            year = race_match.group(3)
            track_raw = race_match.group(4).strip()
            distance = race_match.group(5)
            
            # Clean track name (remove FREE, ENTRY, TAB, PARK, etc.)
            track = track_raw.split(' FREE')[0].split(' ENTRY')[0].split(' TAB')[0].strip()
            
            # Parse date: day=12, month=Nov, year=25 -> "2025-11-12"
            try:
                date_str = f"{day} {month} {year}"
                date_obj = datetime.strptime(date_str, "%d %b %y")
                race_date = date_obj.strftime("%Y-%m-%d")
            except:
                race_date = ""
            
            # Race number not in DOCX - leave empty for now
            race_no = ""
            break
    
    # Parse dog entries
    # Pattern: "1. 13575Paradise Flyer" or "Box. TabDogName"
    # Tab number is 5 digits followed by dog name (letters, spaces, apostrophes, hyphens)
    dog_pattern = re.compile(r'(\d+)\.\s+(\d+)([A-Za-z][A-Za-z\s\'\-]+?)(?=\s+\d+\.|$)')
    
    for para in paragraphs:
        # Skip header/metadata lines
        if 'Race No' in para or 'Prizemoney' in para or 'Tab\tFF Horse' in para:
            continue
        
        # Find all dog entries in this paragraph
        matches = dog_pattern.findall(para)
        
        if matches:
            for match in matches:
                box = match[0]
                tab_no = match[1]
                dog_name = match[2].strip()
                
                # Create summary row for this dog
                summary_row = {
                    'Track': track,
                    'Race_Date': race_date,
                    'Race_No': race_no,
                    'Box': box,
                    'Dog_Name': dog_name,
                    'Tab_No': tab_no,
                    'Data_Source_File': filename,
                }
                summary_rows.append(summary_row)
        elif len(para) > 10 and not para.startswith('Feature') and not para.startswith('Y '):
            # Log as unparsed if it looks like it might contain data
            unparsed_lines.append(para)
    
    return summary_rows, history_rows, unparsed_lines


def parse_all_docx(extraction_results):
    """
    Parse all extracted DOCX results.
    
    Args:
        extraction_results: List of extraction result dicts
        
    Returns:
        Tuple of (all_summary_rows, all_history_rows, unparsed_by_file)
    """
    all_summary = []
    all_history = []
    unparsed_by_file = {}
    
    for result in extraction_results:
        summary, history, unparsed = parse_docx_content(result)
        all_summary.extend(summary)
        all_history.extend(history)
        
        if unparsed:
            unparsed_by_file[result['filename']] = unparsed
    
    return all_summary, all_history, unparsed_by_file
