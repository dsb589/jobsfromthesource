import sys
from definables import provider_params as pp
import requests
from bs4 import BeautifulSoup
from requests.exceptions import (
    Timeout,
    ConnectionError,
    RequestException
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import string

def iter_connecticut_entities(provider_params):
    # start an offset counter to help with batched requests
    offset = 0

def iter_massachusetts_entities(provider_params):
    return

def iter_new_york_entities(provider_params):
    return

def iter_entities():
    return