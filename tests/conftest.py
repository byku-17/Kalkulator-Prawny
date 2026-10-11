import sys
from pathlib import Path

# Udostępnia moduły z katalogu głównego (obliczenia, walidacja) testom.
sys.path.insert(0, str(Path(__file__).parent.parent))
