#!/bin/bash
echo "==============================================="
echo " GREYHOUND RACING DOCX → EXCEL/CSV PIPELINE"
echo "==============================================="
echo

# --- 1️⃣ Setup virtual environment ---
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate

# --- 2️⃣ Install requirements ---
if ! python3 -c "import docx" &>/dev/null; then
  echo "Installing dependencies..."
  pip install -r requirements.txt
fi

# --- 3️⃣ Run main pipeline ---
echo
echo "Running DOCX extraction pipeline..."
python3 main.py
echo
echo "✅ Pipeline complete!"
echo "Outputs:"
echo "  outputs/all_dogs_master.xlsx"
echo "  outputs/all_dogs_master.csv"
echo "Logs:"
echo "  outputs/logs/"
echo
read -p "Press Enter to close..."
