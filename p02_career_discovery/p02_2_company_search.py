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
    # Start by looking for Docker on your machine.
    docker_path = shutil.which("docker")
    # Raise an error if Docker isn't installed. 
    if docker_path is None:
        raise RuntimeError("Docker CLI was not found. \
                           Make sure Docker Desktop is installed and Docker \
                           is available on PATH.")
    # assuming Docker exists on machine, check if it's running.
    result = subprocess.run([docker_path, "info"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=1)
    # If Docker is running already, nothing else to do.
    if result.returncode == 0:
        print("Docker is already running.")
        return