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
    
    # Parse dog entries and details
    # Pattern: "1. 13575Paradise Flyer" or "Box. TabDogName"
    # Tab number is 5 digits followed by dog name (letters, spaces, apostrophes, hyphens)
    dog_pattern = re.compile(r'(\d+)\.\s+(\d+)([A-Za-z][A-Za-z\s\'\-]+?)(?=\s+\d+\.|$)')
    
    # Build lookup: dog_name -> {trainer, sire, dam, owner, career, etc}
    dog_details = {}
    
    i = 0
    while i < len(paragraphs):
        para = paragraphs[i]
        
        # Find dog number: "1.", "2.", etc. as standalone paragraph
        if re.match(r'^\d+\.$', para.strip()):
            box_num = para.strip().rstrip('.')
            
            # Next para should be dog name
            if i + 1 < len(paragraphs):
                dog_name_para = paragraphs[i + 1].strip()
                
                # Extract trainer, sire, dam, owner, career stats from following paragraphs
                trainer = ""
                sire = ""
                dam = ""
                owner = ""
                career_wps = ""
                
                # Check next 10 paragraphs for details
                for offset in range(2, min(12, len(paragraphs) - i)):
                    detail_para = paragraphs[i + offset]
                    
                    # Trainer pattern: "0kg (1) bl 2 B\tCOLLEEN PIERSON Horse: 3-5-28 11%-29%"
                    trainer_match = re.search(r'kg\s+\(\d+\)\s+[a-z]+\s+\d+\s+[A-Z]\s+([A-Z][A-Z\s]+?)\s+(?:Horse|Dog):', detail_para)
                    if trainer_match:
                        trainer = trainer_match.group(1).strip()
                    
                    # Sire/Dam pattern: "ALLEN DEED (AUS) - BLUE GLITTER (AUS)"
                    sire_dam_match = re.search(r'([A-Z][A-Z\s]+?)\s+\([A-Z]+\)\s*-\s*([A-Z][A-Z\s]+?)\s+\([A-Z]+\)', detail_para)
                    if sire_dam_match:
                        sire = sire_dam_match.group(1).strip()
                        dam = sire_dam_match.group(2).strip()
                    
                    # Owner pattern: "Owner: Pierson Marsigalia Synd S Marsigalia,C Pierson"
                    owner_match = re.search(r'Owner:\s+(.+)', detail_para)
                    if owner_match:
                        owner = owner_match.group(1).strip()
                    
                    # Career pattern: "3-5-28" or similar (W-P-S format)
                    if not career_wps and re.search(r'\b\d+-\d+-\d+\b', detail_para):
                        career_match = re.search(r'\b(\d+-\d+-\d+)\b', detail_para)
                        if career_match:
                            career_wps = career_match.group(1)
                
                # Store dog details by name for later lookup
                dog_details[dog_name_para.upper()] = {
                    'trainer': trainer,
                    'sire': sire,
                    'dam': dam,
                    'owner': owner,
                    'career_wps': career_wps,
                }
        
        i += 1
    
    # Now parse numbered dog entries and match with details
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
                
                # Look up details
                details = dog_details.get(dog_name.upper(), {})
                
                # Create summary row for this dog with all fields (empty by default)
                summary_row = {
                    'Track': track,
                    'Race_Date': race_date,
                    'Race_No': race_no,
                    'Box': box,
                    'Dog_Name': dog_name,
                    'Tab_No': tab_no,
                    'Trainer': details.get('trainer', ''),
                    'Sire': details.get('sire', ''),
                    'Dam': details.get('dam', ''),
                    'Owner': details.get('owner', ''),
                    'Career_W-P-S': details.get('career_wps', ''),
                    'Prize_Money': '',
                    'RTC': '',
                    'DLR': '',
                    'DLW': '',
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
