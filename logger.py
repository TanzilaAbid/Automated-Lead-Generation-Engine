"""
Structured logging shared by every module.
Console output for humans, a single run log file for the record.
 
All loggers created via get_logger() during one process run write to the
SAME timestamped file (logs/run_<timestamp>.log). The timestamp is computed
once, the first time this module is imported, and reused by every caller --
so a single `python main.py` or `streamlit run streamlit_app.py` invocation
produces exactly one run log, not one per module.
"""
import logging
import os
from datetime import datetime
 
LOG_DIR = "logs"
 
# Computed once per process, shared by every module that calls get_logger().
_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
_RUN_LOG_PATH = f"{LOG_DIR}/run_{_RUN_ID}.log"
 
_shared_file_handler: logging.Handler | None = None
 
 
def _get_shared_file_handler(formatter: logging.Formatter) -> logging.Handler:
    global _shared_file_handler
    if _shared_file_handler is None:
        os.makedirs(LOG_DIR, exist_ok=True)
        _shared_file_handler = logging.FileHandler(_RUN_LOG_PATH)
        _shared_file_handler.setFormatter(formatter)
    return _shared_file_handler
 
 
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
 
    if logger.handlers:
        return logger  # already configured, avoid duplicate handlers
 
    logger.setLevel(logging.INFO)
 
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
 
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
 
    logger.addHandler(_get_shared_file_handler(formatter))
 
    return logger