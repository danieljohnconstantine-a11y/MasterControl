# Unified column order - 56 unique fields across Groups A, B, and C
COLUMN_ORDER = [
    # Core identification fields (first 5 - added Race_Date)
    "Track", "Race_No", "Race_Date", "Box", "Dog_Name",
    # Group A – Identification (9 more fields)
    "Tab_No", "FF_Form", "A/S", "WT (kg)", "Trainer", "Sire", "Dam", "Owner",
    # Group B – Career Stats (27 fields - added Hist_Count)
    "Career_W-P-S", "Prize_Money", "RTC", "DLR", "DLW",
    "Car_PM/s (G1)", "12m_PM/s (G2)", "API (G3)", "RTC/km",
    "Trainer_Win_%", "Trainer_Place_%",
    "Raced_Dist_W-P-S", "Crs_W-P-S", "Dist_W-P-S",
    "FU_W-P-S", "2U_W-P-S", "DOD",
    "Avg_Speed_km/h", "Min_Speed_km/h", "Max_Speed_km/h", "Hist_Count",
    # Group C – Historical Race Detail (21 fields)
    "Hist_Date", "Hist_Track", "Hist_Distance", "Hist_Finish_Pos", "Hist_Margin_L",
    "Hist_Race_Time", "Hist_Sec_Time", "Hist_Sec_Time_Adj", "Hist_Speed_km/h",
    "Hist_SOT", "Hist_RST", "Hist_BP", "Hist_Odds", "Hist_API", "Hist_Prize_Won",
    "Hist_Winner", "Hist_2nd_Place", "Hist_3rd_Place",
    "Hist_Settled_Turn", "Hist_Ongoing_Winners", "Hist_Track_Direction",
]
