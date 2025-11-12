import re
import statistics
from typing import List, Dict

def parse_greyhound_data(text: str) -> List[Dict]:
    """
    Advanced parser for greyhound racing DOCX text.
    Extracts Group A (Identification), Group B (Career Stats),
    and Group C (Historical Race Detail) into a single unified structure.
    """

    # --- Regex anchors for Race + Dog blocks ---
    race_header_re = re.compile(r"Race No\s*(\d+).*?([A-Za-z]+)\s*(\d{3,4})m", re.DOTALL)
    dog_start_re   = re.compile(r"(\d+)\.\s*([A-Za-z'\- ]+)", re.MULTILINE)

    # --- Pattern fragments for details ---
    trainer_re  = re.compile(r"Trainer[:\s]*([A-Z][A-Za-z ]+)")
    career_re   = re.compile(r"Career[:\s]+(\d+\s*-\s*\d+\s*-\s*\d+)")
    prize_re    = re.compile(r"Prize\s*\$?([\d,]+)")
    hist_line_re = re.compile(
        r"(\d{1,2}/\d{1,2}/\d{4}).*?([A-Za-z]+).*?Distance\s*(\d{3,4})m.*?"
        r"Race Time\s*([\d:.]+).*?Sec Time\s*([\d:.]+)?.*?BP\s*(\d).*?"
        r"Odds\s*(\S+).*?Winner\s*([A-Za-z' ]+)", re.DOTALL)

    # --- Initialise ---
    all_dogs: List[Dict] = []

    # --- Iterate over races ---
    for race_match in race_header_re.finditer(text):
        race_no, track, distance = race_match.groups()
        race_start = race_match.end()
        
        # Find next race or end of text
        next_race = race_header_re.search(text, race_start)
        race_end = next_race.start() if next_race else len(text)
        race_segment = text[race_start:race_end]

        # Find all dogs in this race
        dog_matches = list(dog_start_re.finditer(race_segment))
        
        for i, dog_match in enumerate(dog_matches):
            box_num = dog_match.group(1)
            name = dog_match.group(2).strip()
            
            # Extract dog section (from this dog to next dog or end of race)
            dog_start = dog_match.start()
            if i + 1 < len(dog_matches):
                dog_end = dog_matches[i + 1].start()
            else:
                dog_end = len(race_segment)
            
            dog_section = race_segment[dog_start:dog_end]

            record = {
                # === Group A ===
                "Track": track,
                "Race_No": race_no,
                "Box": box_num,
                "Dog_Name": name,
                "Max_Speed_km/h": "",

                "Tab_No": "",
                "FF_Form": "",
                "A/S": "",
                "WT (kg)": "",
                "Trainer": trainer_re.search(dog_section).group(1).strip()
                    if trainer_re.search(dog_section) else "",
                "Sire": "",
                "Dam": "",
                "Owner": "",

                # === Group B ===
                "Career_W-P-S": career_re.search(dog_section).group(1).replace(" ", "")
                    if career_re.search(dog_section) else "",
                "Prize_Money": prize_re.search(dog_section).group(1)
                    if prize_re.search(dog_section) else "",
                "RTC": "",
                "DLR": "",
                "DLW": "",
                "Car_PM/s (G1)": "",
                "12m_PM/s (G2)": "",
                "API (G3)": "",
                "RTC/km": "",
                "Trainer_Win_%": "",
                "Trainer_Place_%": "",
                "Raced_Dist_W-P-S": "",
                "Crs_W-P-S": "",
                "Dist_W-P-S": "",
                "FU_W-P-S": "",
                "2U_W-P-S": "",
                "DOD": "",
                "Avg_Speed_km/h": "",
                "Min_Speed_km/h": "",
                "Max_Speed_km/h": "",

                # === Group C ===
                "Hist_Date": "",
                "Hist_Track": "",
                "Hist_Distance": "",
                "Hist_Finish_Pos": "",
                "Hist_Margin_L": "",
                "Hist_Race_Time": "",
                "Hist_Sec_Time": "",
                "Hist_Sec_Time_Adj": "",
                "Hist_Speed_km/h": "",
                "Hist_SOT": "",
                "Hist_RST": "",
                "Hist_BP": "",
                "Hist_Odds": "",
                "Hist_API": "",
                "Hist_Prize_Won": "",
                "Hist_Winner": "",
                "Hist_2nd_Place": "",
                "Hist_3rd_Place": "",
                "Hist_Settled_Turn": "",
                "Hist_Ongoing_Winners": "",
                "Hist_Track_Direction": ""
            }

            # --- Historical extraction (multiple possible per dog) ---
            # Extract all historical race entries found in dog section
            hist_entries = []
            for hm in hist_line_re.finditer(dog_section):
                hist_entries.append({
                    "Hist_Date": hm.group(1),
                    "Hist_Track": hm.group(2),
                    "Hist_Distance": hm.group(3),
                    "Hist_Race_Time": hm.group(4),
                    "Hist_Sec_Time": hm.group(5) or "",
                    "Hist_BP": hm.group(6),
                    "Hist_Odds": hm.group(7),
                    "Hist_Winner": hm.group(8).strip(),
                })
            # If historical data found, use the first entry's values
            if hist_entries:
                last = hist_entries[0]
                for k, v in last.items():
                    record[k] = v

            all_dogs.append(record)

    return all_dogs
