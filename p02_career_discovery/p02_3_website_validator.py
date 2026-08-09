import os
import gc
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

# start session to check websites
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def ollama_available():
    """
    Check whether Ollama API is responding.
    """
    try:
        response = session.get("http://localhost:11434", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def wait_for_ollama():
    """
    Wait until Ollama is available. Do not start or restart Ollama.
    """

def ask_ollama():
    """
    Send one validation request. Unload after every response.
    """