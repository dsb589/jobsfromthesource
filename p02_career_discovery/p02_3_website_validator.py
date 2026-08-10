import os
import gc
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from definables import constants as dfn


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
    while True:
        if ollama_available():
            return True
        print("Waiting for Ollama...")
        time.sleep(dfn.OLLAMA_WAIT_SECONDS)

def ask_ollama(prompt):
    """
    Send one validation request. Unload after every response.
    """
    payload = {"model": dfn.OLLAMA_MODEL,
               "prompt": prompt,
               "stream": False,
                # unload model immediately
                # after response
                "keep_alive":"0s"}


    for attempt in range(1, dfn.OLLAMA_RETRIES + 1):
        try:
            wait_for_ollama()
            response = session.post(dfn.OLLAMA_URL,
                                    json=payload,
                                    timeout=300)
            response.raise_for_status()
            result = (response.json().get("response", "").strip())
            return result
        except Exception as e:
            print(f"Ollama attempt {attempt}/{dfn.OLLAMA_RETRIES} failed:", e)
            if attempt < dfn.OLLAMA_RETRIES:
                time.sleep(dfn.OLLAMA_WAIT_SECONDS * attempt)
            else:
                return ""
            
def clean_test(text, limit):
    """ 
    Remove excessive whitespace
    and limit size of the website content.
    """
    # return blank text if no text passed
    if not text:
        return ""
    
    # strip out unwanted characters
    text = str(text).replace("\n", " ").replace("\r", " ")
    # treat text as a list separated by blank space
    text = " ".join( text.split())
    # get first n words in text where n is limit
    return text[:limit]