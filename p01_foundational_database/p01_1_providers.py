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
        """
        Get all available results for a single partition
        """
        # Initialize first page as 0
        page = 0
        # Initialize loop
        while True:
            # Use a copy of parameters & add a "page" parameter to the copy
            params = base_params.copy()
            params["page"] = page
            # Use the make_request function to make a partitioned request
            data = make_request(
                params
            )
            # If no data is available for the partition, skip it.
            if data is None:
                print("Skipping unavailable partition:")
                print(base_params)
                break
            # Store # of total results for a partition
            total_results = data.get("total_results", 0)
            # Store # of pages for a partition
            num_pages = data.get("num_pages", 0)
            # Get number of organizations in partition
            organizations = data.get("organizations", [])
            # Prints to help with debugging
            print("Partition:", base_params, "|", "Page:", page, "|", "Total:", 
                  total_results, "|", "Pages:",num_pages)
            # Return normalized row of data for each organisation
            for row in organizations:
                yield {
                    "name_to_search": row.get("name"),
                    "source_id": str(row.get("ein")),
                    "entity_status": None,
                    "source": provider_params["source"],
                    "state": row.get("state"),
                    "date_registration": None
                }
            # if no organizations found, stop.
            if not organizations:
                break
            # Limitation: if there are more than 10,000 results in a given
            # partition, this will break. #TODO would be good to add a workaround.
            # For now, simply continue as if 10,000 is the true number of 
            # organisations in the partition, when this occurs.
            if page >= num_pages - 1:
                if total_results >= 10000:
                    print("Reached ProPublica's " "10,000-record limit for partition:")
                    print(base_params)
                break
            # Go to the next page.
            page += 1
    # main loop: run partitioned requests for each state.
    for state in dfn.STATES:
        print(f"Processing Propublica results for {state}")
        # Process each Propublica NTEE category.
        for ntee in dfn.NONPROFIT_NTEE_CATEGORIES:
            base_params = {
                "state[id]": state,
                "ntee[id]": ntee
            }
            # Make first request with updated base params
            first_params = base_params.copy()
            # Set page to 0
            first_params["page"] = 0
            # Access basic make request function
            data = make_request(first_params)
            # If this state/NTEE combination returns 404, skip.
            if data is None:
                print("Skipping unavailable partition:")
                print(base_params)
                continue
            # Find total # of results and total # of pages.
            total_results = data.get("total_results", 0)
            num_pages = data.get("num_pages", 0)
            print()
            # logging
            print(f"{state} / NTEE {ntee}: {total_results} results / {num_pages} pages")
            # Stop if we don't have any results.
            if total_results == 0:
                continue
            # If total_results > 0 and < 10000 we can paginate directly
            if total_results < 10000:
                yield from get_partition_results(
                    base_params
                )
                continue
            # Otherwise, if we exceed 10000 results, we need to partition further.
            # Logging.
            print("Partition exceeds 10,000 results:")
            print(base_params)
            print("Splitting partition using 501(c) subsection.")
            # process each 501c subsection
            for c_code in dfn.NONPROFIT_501C_CODES:
                sub_partition = {
                    "state[id]": state,
                    "ntee[id]": ntee,
                    "c_code[id]": c_code
                }
                # First request for this 501c subsection.
                first_sub_params = sub_partition.copy()
                # set page to 0
                first_sub_params["page"] = 0
                # Make request to API
                sub_data = make_request(first_sub_params)
                # If nothing found, skip
                if sub_data is None:
                    # Log
                    print("Skipping unavailable 501(c) partition:")
                    print(sub_partition)
                    continue
                # get total results and # pages for subsection
                sub_total = sub_data.get("total_results", 0)
                sub_pages = sub_data.get("num_pages", 0)
                # log 
                print(f"{state} / NTEE {ntee} / 501(c) {c_code}: {sub_total} results / "
                    f"{sub_pages} pages")
                # when no results return for the subsection, skip it.
                if sub_total == 0:
                    continue
                # If subsection has > 0 results and less than 10k, we can process it
                if sub_total < 10000:
                    yield from get_partition_results(sub_partition)
                    continue
                # Otherwise, if we still exceed 10K, we reach a limitation
                # and need to treat this like the subsection legitimately 
                # has only 10k results. Seeking workaround.
                # Log the occurrence:
                print()
                print("WARNING: 501(c) partition exceeds "
                    "ProPublica's 10,000-result limit.")
                print("Retrieving the maximum accessible 10,000 records.")
                print("Partition:")
                print(sub_partition)
                print(f"Total reported by API: {sub_total}")
                # Get partition results just for the available 10k, and move on.
                yield from get_partition_results(sub_partition)
                continue
                
def iter_medical_organizations(provider_params):
    """
    Pull employers list from NPI Registry API.
    Callable via iter_entities, then passed into a dataframe.
    Results are yielded
    """
    # Get all possible 2-letter taxonomy prefixes for taxonomy partition searches,
    # to use as needed
    taxonomy_prefixes = []
    for first in dfn.LETTER_STRING:
        for second in dfn.LETTER_STRING:
            taxonomy_prefixes.append(first + second + "*")

    def make_request(params):
        return
    def convert_organization(row):
        return
    def get_partition_results(state, partition_params, description):
        return
    def get_taxonomy_partitions(state, zip_code):
        return
    def get_exact_zip_results(state, zip_code):
        return
    def get_zip_partition(state, zip_prefix):
        return
    
    return


def iter_entities():
    return