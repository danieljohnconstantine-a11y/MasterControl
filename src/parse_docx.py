"""
DOCX Parsing Module
Responsibility: Parse structured blocks into summary_rows and history_rows
No invented data - only extract what's clearly present
"""
import re
from datetime import datetime


def parse_docx_blocks(blocks):
    """
    Parse DOCX blocks into summary and history rows.
    
    Args:
        blocks: List of dicts from read_docx.extract_docx_content()
        
    Returns:
        tuple: (summary_rows, history_rows, unparsed_lines)
        - summary_rows: list of dicts (one per dog per meeting)
        - history_rows: list of dicts (one per historical race)
        - unparsed_lines: list of strings that couldn't be parsed
    """
    summary_rows = []
    history_rows = []
    unparsed_lines = []
    
    # Extract race metadata from headers/paragraphs
    race_metadata = extract_race_metadata(blocks)
    
    # Parse tables for dog data
    for block in blocks:
        if block["type"] == "table":
            dogs, histories, unparsed = parse_dog_table(block["table"], race_metadata, block["source_file"])
            summary_rows.extend(dogs)
            history_rows.extend(histories)
            unparsed_lines.extend(unparsed)
    
    return summary_rows, history_rows, unparsed_lines


def extract_race_metadata(blocks):
    """Extract Track, Race_No, Race_Date, Distance from headers/paragraphs."""
    metadata = {
        "Track": "",
        "Race_No": "",
        "Race_Date": "",
        "Distance": ""
    }
    
    # Look for race header pattern: "Race No 12 Nov 25 06:35PM Cannington 275m"
    for block in blocks:
        if block["type"] in ["header", "paragraph"]:
            text = block["text"] if isinstance(block["text"], str) else " ".join(block["text"])
            
            # Pattern: Race No <num> <date> <track> <distance>m
            match = re.search(r'Race\s+No\s+(\d+)\s+(\d{1,2}\s+\w+\s+\d{2})\s+\d{2}:\d{2}[AP]M\s+(\w+)\s+(\d+)m', text, re.IGNORECASE)
            if match:
                metadata["Race_No"] = match.group(1)
                date_str = match.group(2)
                metadata["Track"] = match.group(3)
                metadata["Distance"] = match.group(4)
                
                # Parse date to YYYY-MM-DD
                try:
                    parsed_date = datetime.strptime(date_str + " 2025", "%d %b %y %Y")
                    metadata["Race_Date"] = parsed_date.strftime("%Y-%m-%d")
                except:
                    metadata["Race_Date"] = date_str
    
    return metadata


def parse_dog_table(table_data, race_metadata, source_file):
    """Parse a table to extract dog summary and history data."""
    dogs = []
    histories = []
    unparsed = []
    
    if not table_data or len(table_data) < 2:
        return dogs, histories, unparsed
    
    # Try to identify dog rows (usually start with number + dog name)
    for i, row in enumerate(table_data):
        if not row or len(row) == 0:
            continue
        
        first_cell = row[0].strip()
        
        # Check if this looks like a dog entry (starts with number)
        if re.match(r'^\d+\.?\s', first_cell):
            dog_data = parse_dog_row(row, race_metadata, source_file)
            if dog_data:
                dogs.append(dog_data)
            else:
                unparsed.append(" | ".join(row))
        
        # Check for history data rows
        elif re.match(r'^\d{1,2}[/-]\d{1,2}', first_cell):  # Date pattern
            hist_data = parse_history_row(row, race_metadata, source_file)
            if hist_data:
                histories.append(hist_data)
            else:
                unparsed.append(" | ".join(row))
    
    return dogs, histories, unparsed


def parse_dog_row(row, race_metadata, source_file):
    """Parse a single dog row into a summary dict."""
    dog = {
        "Track": race_metadata.get("Track", ""),
        "Race_Date": race_metadata.get("Race_Date", ""),
        "Race_No": race_metadata.get("Race_No", ""),
        "Box": "",
        "Dog_Name": "",
        "Tab_No": "",
        "Data_Source_File": source_file,
        "Parse_Timestamp": datetime.now().isoformat()
    }
    
    # Extract box number and dog name from first cell
    # Pattern: "1. DOG NAME" or "1 DOG NAME"
    first_cell = row[0].strip()
    match = re.match(r'^(\d+)\.?\s+(.+)', first_cell)
    if match:
        dog["Box"] = match.group(1)
        dog["Dog_Name"] = match.group(2).strip()
    
    # Try to extract other fields from remaining cells
    for cell in row[1:]:
        cell_text = cell.strip()
        if not cell_text:
            continue
        
        # Tab number pattern
        if re.match(r'^\d{4,}$', cell_text):
            dog["Tab_No"] = cell_text
        
        # Trainer pattern (often has specific markers)
        if "Trainer" in cell_text or re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', cell_text):
            if not dog.get("Trainer"):
                dog["Trainer"] = cell_text
        
        # Weight pattern: "30.5kg" or "30.5"
        weight_match = re.search(r'(\d+\.?\d*)\s*kg', cell_text, re.IGNORECASE)
        if weight_match:
            dog["WT (kg)"] = weight_match.group(1)
        
        # Prize money pattern: "$" followed by number
        if "$" in cell_text:
            dog["Prize_Money"] = cell_text.replace("$", "").strip()
    
    return dog if dog["Dog_Name"] else None


def parse_history_row(row, race_metadata, source_file):
    """Parse a historical race row."""
    hist = {
        "Track": race_metadata.get("Track", ""),
        "Race_Date": race_metadata.get("Race_Date", ""),
        "Race_No": race_metadata.get("Race_No", ""),
        "Dog_Name": "",  # Will be linked later
        "Hist_Date": "",
        "Hist_Track": "",
        "Hist_Distance": "",
        "Hist_Race_Time": "",
        "Data_Source_File": source_file
    }
    
    # Parse date from first cell
    date_cell = row[0].strip()
    hist["Hist_Date"] = date_cell
    
    # Extract other history fields from remaining cells
    for i, cell in enumerate(row[1:], 1):
        cell_text = cell.strip()
        if not cell_text:
            continue
        
        # Track name
        if i == 1 and re.match(r'^[A-Z]{2,}', cell_text):
            hist["Hist_Track"] = cell_text
        
        # Distance pattern: "450m" or "450"
        dist_match = re.search(r'(\d+)\s*m?', cell_text)
        if dist_match and not hist["Hist_Distance"]:
            hist["Hist_Distance"] = dist_match.group(1)
        
        # Time pattern: "25.50" or "00:25.50"
        time_match = re.search(r'(\d{1,2}:\d{2}\.\d{2}|\d{2}\.\d{2})', cell_text)
        if time_match:
            hist["Hist_Race_Time"] = time_match.group(1)
    
    return hist if hist["Hist_Date"] else None
