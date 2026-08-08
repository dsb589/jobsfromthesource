import sys
from definables import provider_params as pp
from definables import constants as dfn
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
                "source_id": str(row.get("source_id")),
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
    Results are yielded.
    """
    def parse_massachusetts_results(html):
        """
        Function to read rows of companies from MA corporations table
        """
        # Initialize empty list of entities
        entities = []
        # Initialize soup object
        soup = BeautifulSoup(html, "html.parser")
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
            # Find name link
            name_link = row.find("a")
            # Stop searching if there aren't entries 
            if len(cells) < 3:
                continue
            # Stop searching if no name link 
            if not name_link:
                continue
            # Get fields from individual row and add to entities list.
            entities.append(
                {
                    "legal_name": name_link.get_text(" ", strip=True).strip("; "),
                    "source_id": str(cells[0].get_text(strip=True)),
                    "entity_status": "Active",
                    "source": provider_params["source"],
                    "state": provider_params["state"]
                }
            )
        # Return populated entities list
        return entities
    
    def get_total_pages(html):
        """
        Helper function to determine total number of pages on webpage
        """
        # Get text items in html on page
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        # Look for number of pages in the html
        page_count_object = re.search(r"Number of pages:\s*(\d+)", text)
        # If object is found, get the total number
        if page_count_object:
            return int(page_count_object.group(1))
        return 1
    
    # Main Block of function; calls subfunctions.
    # Initialize options object for web scraping
    options = Options()
    # Initialize driver object. Headless does not work for this site currently.
    driver = webdriver.Chrome(options=options)
    try:
        # Minimalist search terms to enter into the search box on the landing page
        search_terms = string.ascii_uppercase + "0123456789"
        # Loop through the search terms.
        for search_term in search_terms:
            # Access the driver
            driver.get(
                provider_params["endpoint_url"]
            )
            # Minimize driver window for ease of use
            driver.minimize_window()
            # Wait for search page to load before proceeding
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.ID, "MainContent_txtEntityName")
                )
            )
            # There are different search types on the MA site; select the 
            # "Begins with" search.
            search_type = Select(
                driver.find_element(
                    By.ID, "MainContent_ddBeginsWithEntityName"
                )
            )
            # Enter the search term, e.g. A B C
            search_type.select_by_value(search_term)
            # Look for the dropdown on the page to enter count per page
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.ID, "MainContent_txtEntityName")
                )
            )
            # Select dropdown object
            records_dropdown = Select(
                driver.find_element(
                    By.ID, "MainContent_ddRecordsPerPage"
                )
            )
            # Set dropdown to 100 per page
            records_dropdown.select_by_value("100")
            # Return to search screen if needed
            if "CorpSearchResults" in driver.current_url:
                driver.find_element(
                    By.ID, "MainContent_btnNewSearch"
                ).click()
                # Wait for objects to appear
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.ID, "MainContent_txtEntityName")
                    )
                )
                # Wait for search box
                search_box = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.ID, "MainContent_txtEntityName")
                    )
                )
                # Empty search box
                search_box.clear()
                # Place search term in search box
                search_box.send_keys(search_term)
                # Press the search button
                driver.find_element(
                    By.ID, "MainContent_btnSearch"
                ).click()
                # Wait for results to appear
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.ID, "MainContent_SearchControl_grdSearchResultsEntity")
                    )
                )
                # Once search loads, determine # of pages
                html = driver.page_source
                total_pages = get_total_pages(html)
                # Loop through every page 
                for page in range(1, total_pages + 1):
                    # parse each entity
                    for entity in parse_massachusetts_results(html):
                        yield entity
                    # continue as long as we're not on last page
                    if page < total_pages:
                        # Execute search results
                        driver.execute_script(
                            """
                            __doPostBack(
                                'ctl00$MainContent$SearchControl$grdSearchResultsEntity',
                                arguments[0]
                            )
                            """,
                            f"Page${page+1}"
                        )
                        # SLeep for a second (safety measure)
                        time.sleep(1)
                        # Wait for the next page to load
                        WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located(
                                (By.ID, "MainContent_SearchControl_grdSearchResultsEntity")
                            )
                        )
                        # Re-access html after load
                        html = driver.page_source
    
    # Exception block
    finally:
        # Check if driver is still alive
        try:
            print("Driver alive:", driver.title)
        except Exception as e:
            print("Driver already dead:", e)
        # Close browser if it's dead
        driver.quit()
        print("Browser closed")
        
    

def iter_new_york_entities(provider_params):
    """
    Pull employers list from NY.gov.
    Callable via iter_entities, then passed into a dataframe.
    Results are yielded
    """
    # initialize offset to determine starting point for API call
    offset = 0
    # Initialize a continuous while loop
    while True:
        # set parameters as constants from provider_params + currnet offset
        params = {
            "$limit": provider_params["batch_size"],
            "$offset": offset,
            "$order": provider_params["id_col"],
            "$select": provider_params["select_cond"]
        }
        # Allow 5 attempts at API call
        retries = 5
        # Start loop that retries on failure
        for attempt in range(retries):
            try:
                response = requests.get(provider_params["endpoint_url"],
                                        params=params,
                                        timeout=30)
                response.raise_for_status()
                records = response.json()
                break
            except (Timeout,ConnectionError,RequestException) as e:
                print(f"Request failed attempt {attempt + 1}/{retries})")
                print(e)
                # If we're at the last attempt in the loop, stop
                if attempt == retries - 1:
                    raise
                sleep_time = 5 * (attempt + 1)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        # Check if any records have been populated. If not, stop.
        if not records:
            break
        # Put data for row extracted from API into normalized fields.
        for row in records:
            yield {
                "name_to_search": row.get("name_to_search"),
                "source_id": str(row.get("source_id")),
                "entity_status": "Active",
                "source": provider_params["source"],
                "state": provider_params["state"]
            }
        # Increase the offset by the batch size
        offset += provider_params["batch_size"]

def iter_propublica_nonprofits(provider_params):
    """
    Pull employers list from Propublica nonprofits API.
    Callable via iter_entities, then passed into a dataframe.
    Results are yielded
    """
    def make_request(params):
        """
        Make an API request
        """
        # try the request 5 times
        retries = 5
        # Loop through each attempt (of the allowed retries)
        for attempt in range(retries):
            try:
                # Make the request
                response = requests.get(
                    # pull url from provider_params
                    url=provider_params["endpoint_url"],
                    params=params,
                    timeout=30
                )
                # If we get an error 404, stop
                if response.status_code == 404:
                    print("ProPublica returned 404 for partition:")
                    print(params)
                    return None
                # Raise any other errors, if applicable
                response.raise_for_status()
                # Return json object
                return response.json()
            # Handle timeout and connection exceptions
            except (Timeout,ConnectionError) as e:
                print(f"ProPublica request failed (attempt {attempt + 1}/{retries})")
                print(e)
                # If we exceed number of allowed retries, stop
                if attempt == retries - 1:
                    raise
                # Retry after x seconds
                sleep_time = 5 * (attempt + 1)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            #  Handle all other errors the same way
            except RequestException as e:
                print(f"ProPublica request failed (attempt {attempt + 1}/{retries})")
                print(e)
                # If we exceed number of allowed retries, stop
                if attempt == retries - 1:
                    raise
                # Retry after x seconds
                sleep_time = 5 * (attempt + 1)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        return
    def get_partition_results(base_params):
        return
    return

def iter_entities():
    return