#!/usr/bin/env python3
"""
Greyhound Analytics Pipeline

Main entry point for automated parsing and scoring of greyhound racing forms.
"""

import os
import sys
import pandas as pd
from pathlib import Path

from parser import FormParser
from scorer import FeatureScorer
from trainer_matcher import TrainerMatcher
from pdf_converter import PDFConverter


def find_input_file(data_dir: str = 'data') -> str:
    """
    Find the first .txt or .pdf file in the data directory.
    
    Args:
        data_dir: Directory to search for input files
        
    Returns:
        Path to the input file
        
    Raises:
        FileNotFoundError: If no suitable file is found
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Look for .txt files first
    txt_files = list(data_path.glob('*.txt'))
    if txt_files:
        return str(txt_files[0])
    
    # Then look for .pdf files
    pdf_files = list(data_path.glob('*.pdf'))
    if pdf_files:
        return str(pdf_files[0])
    
    raise FileNotFoundError(f"No .txt or .pdf files found in {data_dir}")


def main():
    """Main pipeline execution."""
    
    print("=" * 60)
    print("Greyhound Analytics Pipeline")
    print("=" * 60)
    
    # Setup paths
    data_dir = 'data'
    output_dir = 'outputs'
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Find and load input file
    print("\n[1/6] Loading input file...")
    try:
        input_file = find_input_file(data_dir)
        print(f"    Found: {input_file}")
    except FileNotFoundError as e:
        print(f"    ERROR: {e}")
        print("\n    Please place a .txt or .pdf form file in the 'data/' folder.")
        return 1
    
    # Step 2: Convert PDF if needed
    text_file = input_file
    if input_file.lower().endswith('.pdf'):
        print("\n[2/6] Converting PDF to text...")
        converter = PDFConverter()
        text_file = os.path.join(data_dir, 'converted_form.txt')
        converter.convert_pdf_to_text(input_file, text_file)
        print(f"    Converted to: {text_file}")
    else:
        print("\n[2/6] Skipping PDF conversion (text file provided)")
    
    # Step 3: Parse race form
    print("\n[3/6] Parsing race form...")
    parser = FormParser()
    try:
        races = parser.parse_text_file(text_file)
        print(f"    Parsed {len(races)} dogs")
    except Exception as e:
        print(f"    ERROR: Failed to parse file: {e}")
        return 1
    
    if not races:
        print("    ERROR: No race data found in file")
        print("    Please ensure your file follows the expected format.")
        return 1
    
    # Save parsed form data
    todays_form_path = os.path.join(output_dir, 'todays_form.csv')
    df_form = pd.DataFrame(races)
    df_form.to_csv(todays_form_path, index=False)
    print(f"    Saved: {todays_form_path}")
    
    # Step 4: Match trainers
    print("\n[4/6] Analyzing trainers...")
    trainer_matcher = TrainerMatcher()
    trainer_stats = trainer_matcher.analyze_trainers(races)
    print(f"    Analyzed {len(trainer_stats)} trainers")
    
    # Build trainer score mapping
    trainer_scores = {
        trainer: trainer_matcher.get_trainer_score(trainer)
        for trainer in trainer_stats
    }
    
    # Step 5: Score features
    print("\n[5/6] Scoring features...")
    scorer = FeatureScorer()
    scored_races = scorer.score_all(races, trainer_scores)
    ranked_races = scorer.rank_dogs(scored_races)
    print(f"    Scored and ranked {len(ranked_races)} dogs")
    
    # Save ranked data
    ranked_path = os.path.join(output_dir, 'ranked.csv')
    df_ranked = pd.DataFrame(ranked_races)
    # Reorder columns for better readability
    col_order = ['race', 'dog_name', 'trap', 'trainer', 'total_score', 
                 'form_score', 'trap_score', 'age_score', 'weight_score', 
                 'trainer_score', 'age', 'weight', 'form']
    existing_cols = [c for c in col_order if c in df_ranked.columns]
    df_ranked = df_ranked[existing_cols]
    df_ranked.to_csv(ranked_path, index=False)
    print(f"    Saved: {ranked_path}")
    
    # Step 6: Select top picks
    print("\n[6/6] Selecting top picks...")
    top_picks = ranked_races[:5]
    
    picks_path = os.path.join(output_dir, 'picks.csv')
    df_picks = pd.DataFrame(top_picks)
    if not df_picks.empty:
        df_picks = df_picks[existing_cols]
    df_picks.to_csv(picks_path, index=False)
    print(f"    Selected {len(top_picks)} top picks")
    print(f"    Saved: {picks_path}")
    
    # Display results
    print("\n" + "=" * 60)
    print("TOP 5 BETTING PICKS")
    print("=" * 60)
    for i, pick in enumerate(top_picks, 1):
        print(f"\n#{i} - {pick['dog_name']}")
        print(f"    Race: {pick['race']} | Trap: {pick['trap']} | Score: {pick['total_score']}")
        print(f"    Trainer: {pick['trainer']}")
        print(f"    Form: {pick['form']}")
    
    print("\n" + "=" * 60)
    print("Pipeline completed successfully!")
    print("=" * 60)
    print(f"\nOutput files generated in '{output_dir}/':")
    print(f"  - todays_form.csv  : Parsed race data")
    print(f"  - ranked.csv       : All dogs scored and ranked")
    print(f"  - picks.csv        : Top 5 betting picks")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
