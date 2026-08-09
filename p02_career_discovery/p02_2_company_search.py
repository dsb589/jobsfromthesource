import time
import subprocess
import shutil
import pandas as pd
from urllib.parse import urlparse
import re
from p02_1_searxng_client import search_searxng
from concurrent.futures import ThreadPoolExecutor, as_completed
from definables import constants as dfn

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
    # If it's not running, we have to find it and start it.
    # Log
    print("Docker is not running.")
    # Search for common Docker paths on Windows
    docker_desktop_paths = [
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
        r"C:\Users\{}\AppData\Local\Programs\Docker\Docker\Docker Desktop.exe".format(
            __import__("getpass").getuser())]
    # Check these paths. 
    docker_desktop = None
    # See if docker exists in any of the common windows paths
    for path in docker_desktop_paths:
        if __import__("os").path.exists(path):
            docker_desktop = path
            break
    # If we still can't find it, throw an error.
    if docker_desktop is None:
        raise RuntimeError("Docker Desktop was not found.")
    # if we can find it, open it
    subprocess.Popen([docker_desktop],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
    # Finally, wait for the Docker daemon
    # log
    print("Waiting for Docker daemon...")
    start = time.time()
    while True:
        # wait for it to load for 10 seconds
        result = subprocess.run([docker_path, "info"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=10)
        # if it's successfully loaded, finish.
        if result.returncode == 0:
            elapsed = (time.time() - start)
            print("Docker is ready ({round(elapsed, 1)} seconds).")
            return
        
        # Otherwise, throw a timeout error.
        elapsed = time.time() - start
        if elapsed >= timeout:
            raise RuntimeError(
                    "Docker Desktop started, but the Docker daemon did not become \
                    ready within {timeout} seconds.")
        # sleep and try again
        time.sleep(check_interval)
        
def generate_queries(company_name, state=None):
    """
    Broad recall search - basic search variants to place in SearXNG query
    """
    queries = [company_name, f"{company_name} careers", f"{company_name} jobs"]
    # if state is specified then include it in the search
    if state:
        queries.append(f"{company_name} {state}")
    return list(dict.fromkeys(queries))

def clean_company_name(name):
    # get lowercase name
    name = name.lower()
    # remove unnecessary business suffixes like LLC from the name
    for suffix in dfn.SEARXNG_EXTRA_SUFFIXES:
        name = name.replace(suffix, "")
    # return cleaned name
    return re.sub(r"[^a-z0-9 ]", "", name).strip()

    