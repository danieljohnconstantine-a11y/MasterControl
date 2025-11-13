import re
from datetime import datetime
from typing import List, Dict, Tuple

def parse_greyhound_data(text: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Advanced parser for greyhound racing DOCX text.
    Extracts Group A (Identification), Group B (Career Stats) into summary_rows,
    and Group C (Historical Race Detail) into history_rows.
    
    Returns:
        Tuple of (summary_rows, history_rows)
    """

    # --- Regex patterns ---
    # Race header with date: "Race No	12 Nov 25 06:35PM Cannington 275m FREE..."
    # Format after tab: <day> <month> <year> <time> <track> <distance>m
    # Note: The day number may coincidentally match a race number
    race_header_re = re.compile(
        r"Race No\t(\d+)\s+(\w+)\s+(\d+)\s+\d+:\d+[AP]M\s+([A-Za-z]+)\s+(\d{3,4})m"
    )
    # Dog pattern: "1. Paradise Flyer" or "1. 13575Paradise Flyer"
    # Format: box_number. optional_tab_number + dog_name
    dog_re = re.compile(r"(\d+)\.\s+(?:\d+)?([A-Za-z][A-Za-z\s'\-]+?)(?=\s+\d+\.|$)")
    
    # Dog detail patterns - expanded for full coverage
    trainer_re = re.compile(r"Trainer[:\s]*([A-Z][A-Za-z ]+)")
    career_re = re.compile(r"Career[:\s]+(\d+\s*-\s*\d+\s*-\s*\d+)")
    prize_re = re.compile(r"Prize\s*\$?([\d,]+)")
    tab_no_re = re.compile(r"(\d{4,5})[A-Za-z]")  # Tab number before dog name
    ff_form_re = re.compile(r"FF[:\s]+([A-Z0-9\-]+)")
    bp_re = re.compile(r"BP[:\s]+(\d+)")
    age_sex_re = re.compile(r"([BDMT])[/\s]+([KF])")  # B/D/M/T for age, K/F for sex
    weight_re = re.compile(r"(\d{2}(?:\.\d)?)\s*kg")
    sire_re = re.compile(r"Sire[:\s]*([A-Z][A-Za-z\s]+?)(?=\s+Dam|\s+Owner|$)")
    dam_re = re.compile(r"Dam[:\s]*([A-Z][A-Za-z\s]+?)(?=\s+Owner|$)")
    owner_re = re.compile(r"Owner[:\s]*([A-Z][A-Za-z\s&]+?)(?=\s+[A-Z][a-z]+:|$)")
    
    # Group B patterns - career statistics
    rtc_re = re.compile(r"RTC[:\s]+([\d.]+)")
    dlr_re = re.compile(r"DLR[:\s]+([\d.]+)")
    dlw_re = re.compile(r"DLW[:\s]+([\d.]+)")
    api_re = re.compile(r"API[:\s]+(\d+)")
    trainer_win_re = re.compile(r"Trainer Win %[:\s]+([\d.]+)")
    trainer_place_re = re.compile(r"Trainer Place %[:\s]+([\d.]+)")
    dod_re = re.compile(r"DOD[:\s]+([\d.]+)")
    
    # Historical race pattern (with margin and position)
    hist_line_re = re.compile(
        r"(\d+(?:st|nd|rd|th))\s+of\s+\d+\s+(\d{1,2}/\d{1,2}/\d{4})\s+([A-Za-z]+)\s+"
        r"Margin\s+([\d.]+)\s+Lengths\s+Distance\s+(\d{3,4})m.*?"
        r"(?:SOT|Race Time)\s+([A-Za-z\d:.]+)",
        re.DOTALL
    )
    
    # --- Initialize output lists ---
    summary_rows: List[Dict] = []
    history_rows: List[Dict] = []

    # --- Parse races ---
    for race_match in race_header_re.finditer(text):
        race_day = race_match.group(1)
        race_month = race_match.group(2)
        race_year = race_match.group(3)
        track = race_match.group(4)
        distance = race_match.group(5)
        
        # Use the day as race_no (they coincide in this format)
        race_no = race_day
        
        # Parse race date to YYYY-MM-DD format
        race_date_str = f"{race_day} {race_month} {race_year}"
        try:
            race_date_dt = datetime.strptime(race_date_str, "%d %b %y")
            race_date = race_date_dt.strftime("%Y-%m-%d")
        except:
            race_date = ""
        
        race_start = race_match.end()
        
        # Find next race or end of text
        next_race = race_header_re.search(text, race_start)
        race_end = next_race.start() if next_race else len(text)
        race_segment = text[race_start:race_end]

        # Find all dogs in this race - use the new dog_re pattern
        dog_matches = list(dog_re.finditer(race_segment))
        
        for i, dog_match in enumerate(dog_matches):
            box_num = dog_match.group(1)
            dog_name = dog_match.group(2).strip()
            
            # Extract dog section (from this dog to next dog or end of race)
            dog_start = dog_match.start()
            if i + 1 < len(dog_matches):
                dog_end = dog_matches[i + 1].start()
            else:
                dog_end = len(race_segment)
            
            dog_section = race_segment[dog_start:dog_end]

            # --- Extract Group A + B fields (summary) ---
            trainer_match = trainer_re.search(dog_section)
            career_match = career_re.search(dog_section)
            prize_match = prize_re.search(dog_section)
            
            summary_row = {
                # Core fields
                "Track": track,
                "Race_No": race_no,
                "Race_Date": race_date,
                "Distance": distance,
                "Box": box_num,
                "Dog_Name": dog_name,
                
                # Group A - Identification
                "Tab_No": "",
                "FF_Form": "",
                "A/S": "",
                "WT (kg)": "",
                "Trainer": trainer_match.group(1).strip() if trainer_match else "",
                "Sire": "",
                "Dam": "",
                "Owner": "",

                # Group B - Career Stats
                "Career_W-P-S": career_match.group(1).replace(" ", "") if career_match else "",
                "Prize_Money": prize_match.group(1) if prize_match else "",
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
                "Max_Speed_km/h": ""
            }
            
            summary_rows.append(summary_row)

            # --- Extract Group C historical races ---
            for hist_match in hist_line_re.finditer(dog_section):
                history_row = {
                    # Link to summary
                    "Dog_Name": dog_name,
                    "Tab_No": "",  # Will be populated if found
                    
                    # Group C - Historical Race Details
                    "Hist_Finish_Pos": hist_match.group(1),
                    "Hist_Date": hist_match.group(2),
                    "Hist_Track": hist_match.group(3),
                    "Hist_Margin_L": hist_match.group(4),
                    "Hist_Distance": hist_match.group(5),
                    "Hist_Race_Time": hist_match.group(6),
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
                
                history_rows.append(history_row)

    return summary_rows, history_rows
