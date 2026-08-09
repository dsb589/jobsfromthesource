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
    """
    Function to strip out words like LLC, Inc., etc. from company names before 
    searching
    """
    # get lowercase name
    name = name.lower()
    # remove unnecessary business suffixes like LLC from the name
    for suffix in dfn.SEARXNG_EXTRA_SUFFIXES:
        name = name.replace(suffix, "")
    # return cleaned name 
    return re.sub(r"[^a-z0-9 ]", "", name).strip()

def extract_domain(url):
    """
    Function to get the base domain of the selected website
    """
    try:
        # get base domain
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""
    
def domain_penalty(url):
    """
    Function to apply a scoring penalty to websites if the domain is blocked
    """
    # Get base domain
    domain = extract_domain(url)
    # Check if domain is blocked and if it is, apply a penalty
    for blocked in dfn.SEARXNG_BLOCKED_DOMAINS:
        if blocked in domain:
            return -100
    return 0

def score_candidate(company_name, title, url, content):
    """
    Function to score candidate websites for an employer to determine
    most likely fit.
    """
    # by default, give candidates a score of 0
    score = 0
    # apply basic cleaning to company name
    company = clean_company_name(company_name)
    # Check to see if the company name is in the website name
    text = " ".join([title or "", content or "", url or ""]).lower()
    # if its present, increase the score of the candidate site
    if company in text:
        score += 50
    # check to see if individual words in the company name are in the website name
    words = [w for w in company.split() if len(w) > 2]
    # get count of matches of words shared between company name and website
    matches = sum(word in text for word in words)
    # treat each matching word as worth 10 points
    score += matches * 10
    # get base domain of company
    domain = extract_domain(url)
    # check similarity between domain text and company name
    if domain:
        # get unique words for the company (ignoring smaller words)
        company_words = [w for w in company.split() if len(w) > 3]
        # check presence of company words in domain
        domain_match = any(word in domain for word in company_words)
        # score a candidate higher if the domain and company are close
        if domain_match:
            score += 30
    # Finally, slightly increase the score if the website indicates that
    # its an employer, based on presence of predefined employer keywords
    for term in dfn.SEARXNG_EMPLOYER_SIGNALS:
        if term in text:
            score += 5
    # apply domain penalty, if applicable
    score += domain_penalty(url)
    return

def search_company(company_name, state=None, results_per_query=3):
    """
    Function to find and assess candidates for each company website
    """
    # initialize blank query dict
    candidates = {}
    # generate queries for each organisation
    queries = generate_queries(
        company_name,
        state
    )
    # loop through the results from each query
    for query in queries:
        # Check if we already have a very strong candidate.
        # If we do, choose it and stop.
        if candidates:
            best_score = max(c["score"]for c in candidates.values())
            if best_score >= 90:
                break
        # if we are still deciding, run query through searxng
        try:
            results = search_searxng(query, num_results=results_per_query)
        # handle errors if search fails
        except Exception as e:
            print("Search failed:", company_name, e)
            continue
        # loop through the search results and find the best one
        for rank, result in enumerate(results, start=1):
            # store url from search result
            url = result.get("url", "")
            # stop if there aren't any urls
            if not url:
                continue
            # get domain; if it's a blocked domain, stop.
            domain = extract_domain(url)
            if any(blocked in domain for blocked in dfn.SEARXNG_BLOCKED_DOMAINS):
                continue   
            # score the strenght of the url
            score = score_candidate(company_name, 
                                    result.get("title", ""),
                                    url,
                                    result.get("content", ""))
            # generate a normalized row
            row = {"company_name": company_name,
                   "state": state,
                   "query": query,
                   "query_rank": rank,
                   "title": result.get("title", ""),
                   "url": url,
                   "domain": extract_domain(url),
                   "content": result.get("content", ""),
                   "score": score}
            # keep best version of duplicate URLs
            if url not in candidates:
                candidates[url] = row
            else:
                if score > candidates[url]["score"]:
                    candidates[url] = row
        # put candidate urls into df
        df = pd.DataFrame(candidates.values())
        if len(df):
            df = df.sort_values("score", ascending=False)
        # keep only plausible company websites
        df = df[df["score"] >= 50]
    return df

def process_company(row):
    """
    Caller function to store results from search_company
    """
    # run search company function
    results = search_company(row.name_to_search, row.state)
    return row.name_to_search, results
    