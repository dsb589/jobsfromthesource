import requests
from definables import constants as dfn

def search_searxng(query, num_results=10):
    """
    Query local SearXNG instance.
    Returns:
        list of search result dictionaries
    """
    # Set parameters + headers for searxng search
    params = {
        "q": query,
        "format": "json",
        "engines": "bing"
    }
    headers = {
        "User-Agent": "CareerDiscoveryBot/1.0"
    }
    # Submit request
    response = requests.get(
        dfn.SEARXNG_URL,
        params=params,
        headers=headers,
        timeout=30
    )
    # Get response & convert it to data from json
    response.raise_for_status()
    data = response.json()
    # Return results from data; if no results, return blank list.
    results = data.get("results", [])
    # Return number of search results for the search, pre-specified (10 by default)
    return results[:num_results]