import pandas as pd 
from definables import constants as dfn

def clean_employer_dataframe(df, apply_filters=True):
    """
    Function to remove employers from df that are unlikely to be true
    employers.
    returns df
    """
    # start by making a copy of input df
    employer_df = df.copy()
    # Check for name_to_search col; stop if not found.
    if "name_to_search" not in employer_df.columns:
        raise ValueError("DataFrame must contain 'name_to_search'.")
    # only apply filters if argument is True
    if apply_filters:
        # Get rid of rows with no name.
        employer_df = employer_df[employer_df["name_to_search"].notna()]
        employer_df = employer_df[employer_df["name_to_search"].str.strip() != ""]
        # get series of org names
        name = employer_df["name_to_search"].str.lower()
        # look for non-employer indicators
        bad_pattern = "|".join(dfn.NON_EMPLOYER_TERMS)
        # filter out orgs with non-employer indicators
        employer_df = employer_df[~name.str.contains(bad_pattern, na=False)]
    return employer_df
        
def remove_financial_entities(df, apply_filters=True):
    """
    Function to remove financial entities from df that are unlikely to be true
    employers.
    returns df
    """
    # start by making a copy of input df
    employer_df = df.copy()
    # only apply filters if argument is True
    if apply_filters:
        financial_patterns = "|".join(dfn.FINANCIAL_TERMS)
        # Get name series from df
        name = employer_df["name_to_search"].str.lower()
        employer_df = employer_df[~name.str.contains(financial_patterns, na=False)]
    return employer_df
    
def apply_employer_filters(df, apply_filters=True):
    """
    Function to remove additional entities from df that are unlikely to be true
    employers.
    returns df
    """
    # start by making a copy of input df
    employer_df = df.copy()
    # only apply filters if argument is True
    if apply_filters:
        # get proportion of entity name that's numeric. If high, filter.
        numeric_ratio = employer_df["name_to_search"].str.count(r"\d") / employer_df["name_to_search"].str.len()
        # filter out entities with a high % of numeric characters in the name
        employer_df = employer_df[numeric_ratio < 0.3]
        # get name series from df
        name = employer_df["name_to_search"].str.lower()
        # Apply additional filtering of passive terms.
        passive_pattern = "|".join(dfn.PASSIVE_TERMS)
        employer_df = employer_df[~name.str.contains(passive_pattern, na=False)]
    return employer_df

def employer_priority_score(df):
    """
    Function to assgn priority scores to employers based on key words in their
    name that indicate whether they are or are not employers
    """
    


def create_website_queue(df, registry_size_cutoff=100000, apply_filters=True):
    """
    Function to remove additional entities from df that are unlikely to be true
    employers.
    returns df
    """
    
def deduplicate_employers(df, apply_filters=True):
    """
    Function to normalize names in the df and deduplicate them
    returns df
    """
    
def analyze_website_queue(df):
    "Function to print basic analysis of cleaned df"
    
def run_first_cleaning_pass(df, apply_filters=True):
    """
    Master function that runs through all other functions in file
    """
