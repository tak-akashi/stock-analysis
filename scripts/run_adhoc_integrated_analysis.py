import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.analysis.integrated_analysis2 import main  # noqa: E402


if __name__ == "__main__":
    main()