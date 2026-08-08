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
    # start by making a copy of input df
    employer_df = df.copy()
    # get names series 
    name = employer_df["name_to_search"].fillna("").str.lower()
    # initialize employer and website scores as zero
    employer_df["employer_quality_score"] = 0
    employer_df["website_priority_score"] = 0
    # loop through negative terms and assign points where they appear
    for term, points in dfn.NEGATIVE_TERMS_SCORES.items():
        # look for names containing negative terms
        matches = name.str.contains(term, na=False)
        # add points for matches in the org's name
        employer_df.loc[matches, "employer_quality_score"] += points
    # loop through legal terms and assign points where they appear
    for term, points in dfn.LEGAL_TERMS_SCORES.items():
        # look for names containing legal terms
        matches = name.str.contains(term, regex=True, na=False)
        # add points for matches in the org's name
        employer_df.loc[matches, "employer_quality_score"] += points
    # Initialize FALSE series noting whether employer has a business signal
    has_business_signal = pd.Series(False, index=employer_df.index)
    # loop through business terms and assign points where they appear
    for term, points in dfn.BUSINESS_TERMS_SCORES.items():
        # look for names containing business terms
        matches = name.str.contains(term, na=False)
        # amend employer quality score if business matches found
        employer_df.loc[matches, "employer_quality_score"] += points
        has_business_signal |= matches
    # overwrite has business signal column
    employer_df["has_business_signal"] = has_business_signal
    # get word count per entry in a series
    word_count = employer_df["name_to_search"].fillna("").str.split().str.len()
    # amend website priority scoring depending on # of words
    employer_df.loc[word_count <= 2, "website_priority_score"] += 3
    employer_df.loc[word_count == 3, "website_priority_score"] += 2
    employer_df.loc[word_count >= 5, "website_priority_score"] -= 2
    # Get length of first word
    first_word = employer_df["name_to_search"].fillna("").str.split().str[0].str.len()
    # Amend website priority scoring depending on length of first word
    employer_df.loc[first_word >= 7, "website_priority_score"] += 2
    employer_df.loc[has_business_signal, "website_priority_score"] += 2
    employer_df.loc[name.str.len() < 5,"employer_quality_score"] -= 2
    # get overall employer score by adding component scores.
    employer_df["employer_score"] = employer_df["employer_quality_score"] + employer_df["website_priority_score"]
    # by default, rate the confidence that each row is an employer as 'low'
    employer_df["employer_category"] = "low_confidence"
    # Define high confidence
    employer_df.loc[employer_df["employer_quality_score"] >= 5, "employer_category"] = "high_confidence"
    # Define medium confidence
    employer_df.loc[(employer_df["employer_quality_score"] >= 2) &
                    (employer_df["employer_quality_score"] < 5),
                    "employer_category"] = "medium_confidence"
    return employer_df
    

def create_website_queue(df, registry_size_cutoff=100000, apply_filters=True):
    """
    Function to remove additional entities from df that are unlikely to be true
    employers.
    returns df
    """
    # start by making a copy of input df
    employer_df = df.copy()
    # by default give websites a tier 3 priority
    employer_df["website_priority_tier"] = "tier_3"
    if len(employer_df) > registry_size_cutoff:
        # Define tier 1 orgs for large registries
        employer_df.loc[(employer_df["employer_quality_score"] >= 7) |
                        (employer_df["website_priority_score"] >= 6),
                        "website_priority_tier"] = "tier_1"
        # define tier 2 orgs for large registries
        employer_df.loc[(employer_df["employer_quality_score"] >= 4) &
                        (employer_df["has_business_signal"]),
                        "website_priority_tier"] = "tier_2"
    else:
        # Define tier 1 orgs
        employer_df.loc[(employer_df["employer_quality_score"] >= 6) |
                        (employer_df["website_priority_score"] >= 5),
                        "website_priority_tier"] = "tier_1"
        # define tier 2 orgs
        employer_df.loc[(employer_df["employer_quality_score"] >= 3) &
                        (employer_df["has_business_signal"]),
                        "website_priority_tier"] = "tier_2"
    if apply_filters:
        # filter out tier 3's
        employer_df = employer_df[employer_df["website_priority_tier"].isin(["tier_1", "tier_2"])]
    return employer_df

def deduplicate_employers(df, apply_filters=True):
    """
    Function to normalize names in the df and deduplicate them
    returns df
    """
    # start by making a copy of input df
    employer_df = df.copy()
    before = len(df)
    # get normalized names for the employers in the df
    employer_df["dedupe_name"] = employer_df["name_to_search"].fillna("").str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
    if apply_filters:
        # deduplicate based on normalized name + state
        employer_df = employer_df.drop_duplicates(subset=["dedupe_name", "state"], keep="first")
    # drop the new deduplicator column
    employer_df = employer_df.drop(columns=["dedupe_name"])
    after = len(df)
    print("Before:", before)
    print("After:", after)
    print("Removed:", before - after)
    return employer_df
    
def analyze_website_queue(df):
    "Function to print basic analysis of cleaned df"
    print("Total queued:", len(df))
    if "employer_category" in df.columns:
        print("Employer categories:")
        print(df["employer_category"].value_counts())
    if "employer_quality_score" in df.columns:
        print("Quality score distribution:")
        print(df["employer_quality_score"].describe())
    if "website_priority_score" in df.columns:
        print("Website priority distribution:")
        print(df["website_priority_score"].describe())
    if "has_business_signal" in df.columns:
        print("Business signal count:")
        print(df["has_business_signal"].value_counts())
    print("Top website discovery candidates:")
    columns = [
        column
        for column in [
            "name_to_search",
            "employer_quality_score",
            "website_priority_score",
            "employer_category"
        ]
        if column in df.columns
    ]
    print(df[columns].head(25).to_string(index=False))
    
def run_first_cleaning_pass(df, apply_filters=True):
    """
    Master function that runs through all other functions in file
    """
    print("Starting with raw DF from source.")
    clean_employer_df = clean_employer_dataframe(df, apply_filters=apply_filters)
    print("SHAPE AFTER clean_employer_dataframe().", clean_employer_df.shape)
    remove_financial_entities_df = remove_financial_entities(clean_employer_df, apply_filters=apply_filters)
    print("SHAPE AFTER remove_financial_entities().", remove_financial_entities_df.shape)
    employer_filters_df = apply_employer_filters(remove_financial_entities_df, apply_filters=apply_filters)
    print("SHAPE AFTER apply_employer_filters().", employer_filters_df.shape)
    employer_priority_df = employer_priority_score(employer_filters_df)
    print("SHAPE AFTER employer_priority_score().", employer_priority_df.shape)
    website_queue = create_website_queue(employer_priority_df, apply_filters=apply_filters)
    print("SHAPE AFTER create_website_queue().", website_queue.shape)
    analyze_website_queue(website_queue)
    deduplicated_df = deduplicate_employers(website_queue, apply_filters=apply_filters)
    print("SHAPE AFTER deduplicate_employers().", deduplicated_df.shape)
    return deduplicated_df