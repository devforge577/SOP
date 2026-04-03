import sys
from pathlib import Path

# Add project root to sys.path so pytest can find database/, modules/, etc.
sys.path.insert(0, str(Path(__file__).resolve().parent))
