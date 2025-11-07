# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection

## Usage
1. Place your `.txt` form file in the `data/` folder.
2. Run `main.py`
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data
- `ranked.csv`: Scored dogs
- `picks.csv`: Top 5 betting picks

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

```bash
python main.py
```

## Input Format

The pipeline expects race form data in the following text format:

```
Race 1
Dog: FastRunner, Trap: 1, Trainer: John Smith, Age: 3, Weight: 30.5
Form: 1-2-1-3-2

Dog: SpeedyDog, Trap: 2, Trainer: Jane Doe, Age: 4, Weight: 32.0
Form: 2-1-3-1-1

Race 2
Dog: QuickPaws, Trap: 1, Trainer: John Smith, Age: 2, Weight: 29.0
Form: 1-1-2-1-3
...
```

## Scoring System

The pipeline scores dogs based on:
- **Form Score**: Recent race performance (most recent races weighted higher)
- **Trap Score**: Starting position advantage
- **Age Score**: Prime racing age (2-4 years)
- **Weight Score**: Optimal racing weight (28-35 kg)
- **Trainer Score**: Trainer's historical win rate

Dogs are ranked by total score, and the top 5 are selected as betting picks.
