import logging
import os

# --- Log Directory Setup ---
LOG_DIR = "logs"  # Directory to store log files
os.makedirs(LOG_DIR, exist_ok=True)  # Create directory if it doesn't exist

# --- Log File Path ---
LOG_FILE = os.path.join(LOG_DIR, "trend_analyzer.log")  # Path to log file

# --- Logger Configuration ---
logging.basicConfig(
    level=logging.INFO,  # Minimum logging level (INFO and above will be captured)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format: timestamp - level - message
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),  # Save logs to file with Unicode support
        # logging.StreamHandler(),  print logs to terminal (currently disabled)
    ]
)

# --- Create Logger Instance ---
logger = logging.getLogger(__name__)  # Module-specific logger to be imported and used in other files
