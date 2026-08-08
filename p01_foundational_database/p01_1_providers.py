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

def iter_connecticut_entities(provider_params) -> None:
    """
    Pull employers list from CT.gov.
    Callable via iter_entities, then passed into a dataframe.
    Results are yielded
    """
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
    
    # With finalized params, make API calls in a loop
    retries = 5
    # run through 5 attempts
    for attempt in range(retries):
        # Use try/except logic for each request
        try:
            # Make the request
            response = requests.get(
                provider_params["endpoint_url"],
                params=params,
                timeout=30
            )
            # Get response
            response.raise_for_status()
            # Get records as json
            records = response.json()
            break
        # Error handling if the try block doesn't work
        except (
            Timeout,
            ConnectionError,
            RequestException
        ) as e:
            print(
                f"Request failed "
                f"(attempt {attempt + 1}/{retries})"
            )
    
            print(e)
            # Stop the whole thing if we've exceeded our max retries
            if attempt == retries - 1:
                raise
            # Otherwise, wait a few seconds and try again
            sleep_time = 5 * (attempt + 1)
            print(
                f"Retrying in {sleep_time} seconds..."
            )
            time.sleep(
                sleep_time
            )
        # At this stage, records should be returned.
        # If they aren't, break the loop.
        if not records:
            break
        # Generate each row of data through yield
        for row in records:
            yield {
                "legal_name": row.get("legal_name"),
                "source_id": row.get("source_id"),
                "entity_status": row.get("entity_status"),
                "source": provider_params["source"],
                "state": provider_params["state"],
                "date_registration": row.get("date_registration")
            }
        # increase the offset by the batch size; get next batch.
        offset += provider_params["batch_size"]

def iter_massachusetts_entities(provider_params):
    """
    Pull employers list from Massachusetts Corp Search aspx.
    Callable via iter_entities, then passed into a dataframe.
    Results are yielded
    """
    def parse_massachusetts_results(html):
        # Initialize empty list of entities
        entities = []
        # Initialize soup object
        soup = BeautifulSoup(
            html,
            "html.parser"
        )
        # Find corporations search table 
        search_table = soup.find(
            "table",
            id="MainContent_SearchControl_grdSearchResultsEntity"
        )
        # If we dont find the corporations table, return nothing
        if not search_table:
            return []
        # Loop through the table looking for grid objects
        for row in search_table.find_all("tr", class_=["GridRow", "GridAltRow"]):
            # Find individual table cells
            cells = row.find_all("td")

        return entities
    return

def iter_new_york_entities(provider_params):
    """
    Pull employers list from NY.gov.
    Callable via iter_entities, then passed into a dataframe.
    Results are yielded
    """
    return

def iter_entities():
    return