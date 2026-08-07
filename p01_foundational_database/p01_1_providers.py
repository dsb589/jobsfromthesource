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
    # put offset & select provider_params into params dict that 
    # gets passed into requests
    params = {
        "$offset": offset,
        "$order": provider_params["id_col"],
        "$limit": provider_params["batch_size"],    
    }
    # The CT API includes inactive records; we can filter them
    # out if we specify in our provider_params where condition
    if provider_params.get("where_cond"):
        params["$where"] = provider_params["where_cond"]
    # The CT API returns more fields than it needs to; we can
    # pull specific fields and rename them in our provider_params
    # select condition
    if provider_params.get("select_cond"):
        params["$select"] = provider_params["select_cond"]

def iter_massachusetts_entities(provider_params):
    return

def iter_new_york_entities(provider_params):
    return

def iter_entities():
    return