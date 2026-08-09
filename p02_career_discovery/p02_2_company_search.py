import time
import subprocess
import shutil
import pandas as pd
from urllib.parse import urlparse
import re
from cd1_searxng_client import search_searxng
from concurrent.futures import ThreadPoolExecutor, as_completed

def ensure_docker_running(timeout=120, check_interval=2):
    """
    In order for SearXNG to work, a Docker instance must be running.
    This function confirms wether Docker is running, and if it isn't running,
    it starts it.
    """