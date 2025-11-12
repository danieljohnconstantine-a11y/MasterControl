import re
from typing import List, Dict

def parse_greyhound_data(text: str) -> List[Dict]:
    """
    Extract structured greyhound racing data (Groups A+B+C) from DOCX text.
    Returns list of dictionaries ready for DataFrame merge/export.
    """

    # Regex patterns for core fields
    race_header_pattern = re.compile(
        r"Race No\s*(\d+).*?([A-Za-z]+)\s*(\d{3,4})m", re.DOTALL)
    dog_block_pattern = re.compile(
        r"(\d+)\.\s*([A-Za-z'\- ]+).*?(\d+\-\d+\-\d+).*?Trainer\s*([A-Za-z ]+)",
        re.DOTALL)

    hist_pattern = re.compile(
        r"(\d+(?:st|nd|rd|th)) of \d+.*?(\d{1,2}/\d{1,2}/\d{4}).*?([A-Za-z]+).*?Distance (\d{3,4})m.*?Race Time ([\d:.]+).*?BP (\d).*?Odds (\S+).*?Winner ([A-Za-z' ]+)",
        re.DOTALL)

    records = []
    current_track, current_race = None, None

    for race_match in race_header_pattern.finditer(text):
        current_race = race_match.group(1)
        current_track = race_match.group(2).capitalize()

        race_text = text[race_match.end():]
        for dog_match in dog_block_pattern.finditer(race_text):
            dog = {
                "Track": current_track,
                "Race_No": current_race,
                "Box": dog_match.group(1),
                "Dog_Name": dog_match.group(2).strip(),
                "Career_W-P-S": dog_match.group(3),
                "Trainer": dog_match.group(4).strip(),
            }

            # Try to extract historical speeds
            hist_match = hist_pattern.search(race_text)
            if hist_match:
                dog["Hist_Date"] = hist_match.group(2)
                dog["Hist_Track"] = hist_match.group(3)
                dog["Hist_Distance"] = hist_match.group(4)
                dog["Hist_Race_Time"] = hist_match.group(5)
                dog["Hist_BP"] = hist_match.group(6)
                dog["Hist_Odds"] = hist_match.group(7)
                dog["Hist_Winner"] = hist_match.group(8)
            else:
                dog["Hist_Date"] = ""
                dog["Hist_Track"] = ""
                dog["Hist_Distance"] = ""
                dog["Hist_Race_Time"] = ""
                dog["Hist_BP"] = ""
                dog["Hist_Odds"] = ""
                dog["Hist_Winner"] = ""

            # Placeholder for calculated fields (e.g., speed)
            dog["Max_Speed_km/h"] = ""
            records.append(dog)

    return records
