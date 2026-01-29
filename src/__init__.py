"""
Core modules for the iTREDS healthcare data scraper.
"""

from .config import STATE_NAME, CALIFORNIA_COUNTIES, HEALTH_DEPT_URLS, DATA_COLLECTOR_NAME
from .utils import save_to_csv

__all__ = [
    "STATE_NAME",
    "CALIFORNIA_COUNTIES",
    "DATA_COLLECTOR_NAME",
    "save_to_csv",
]

