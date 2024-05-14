"""Entry point for module call."""

# Standard library
import gc

# First-party
from realtime_pollen_calibration.cli import main

if __name__ == "__main__":
    main()
    gc.collect()
