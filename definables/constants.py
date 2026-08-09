# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 10:03:10 2026

@author: danie
"""

STATES = ["CT", "MA", "NY"]

# ProPublica NTEE major groups
NONPROFIT_NTEE_CATEGORIES = list(range(1, 11))

# ProPublica 501(c) subsection codes
NONPROFIT_501C_CODES = [
    2, 3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 16, 17, 18,
    19, 21, 22, 23, 25, 26, 27, 28, 92
]

# NPI Limits
NPI_API_LIMIT = 1000

LETTER_STRING = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

ZIP_PREFIXES = {
    "CT": [f"{n:03d}" for n in range(60, 70)],
    "MA": [f"{n:03d}" for n in range(10, 28)],
    "NY":[f"{n:03d}" for n in range(100, 150)]
}

# Filtering Lists
NON_EMPLOYER_TERMS = [
    "foundation",
    "church",
    "temple",
    "lodge",
    "society",
    "club",
    "condominium",
    "trust",
    "realty",
    "properties",
    "holdings",
    "capital",
    "investments"
]

FINANCIAL_TERMS = [
    "fund",
    "funds",
    "equity",
    "investment",
    "investments",
    "asset management",
    "partners lp",
    "real estate investment"
]

PASSIVE_TERMS = [
    "nominee",
    "nominees",
    "trustee",
    "portfolio",
    "asset",
    "venture",
    "ventures"
]

NEGATIVE_TERMS_SCORES = {
    "church": -5,
    "foundation": -5,
    "association": -5,
    "lodge": -5,
    "society": -5,
    "club": -5,
    "trust": -4,
    "holdings": -4,
    "capital": -4,
    "realty": -4,
    "properties": -4,
    "investments": -4,
    "ventures": -3
}

LEGAL_TERMS_SCORES = {
    r"\binc\b": 1,
    r"\bincorporated\b": 1,
    r"\bcorporation\b": 1,
    r"\bcorp\b": 1,
    r"\bcompany\b": 1,
    r"\bco\b": 1,
    r"\bllc\b": 1,
    r"\bl\.l\.c\b": 1,
    r"\blp\b": 1,
    r"\bllp\b": 1
}

BUSINESS_TERMS_SCORES = {
    "manufacturing": 3,
    "technology": 3,
    "software": 3,
    "health": 3,
    "medical": 3,
    "engineering": 3,
    "services": 2,
    "solutions": 2,
    "systems": 2,
    "construction": 2,
    "restaurant": 2,
    "foods": 2,
    "logistics": 2,
    "transport": 2,
    "consulting": 2,
    "design": 2,
    "studio": 2,
    "retail": 2,
    "market": 2,
    "store": 2,
    "supply": 2
}


# SEARXNG CONSTANTS
SEARXNG_URL = "http://localhost:8080/search"
SEARXNG_BLOCKED_DOMAINS = {
    "indeed.com",
    "glassdoor.com",
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "reddit.com",
    "wikipedia.org",
    "bbc.co.uk",
    "commentcamarche.net",
    "ctcompanydir.com",
    "bizapedia.com",
    "opencorporates.com",
    "dnb.com",
    "zoominfo.com",
    "yellowpages.com",
    "manta.com",
    "dnb.com",
    "dnb.com",
    "crunchbase.com",
    "bbb.org",
    "mapquest.com",
    "trustpilot.com",
    "chamberofcommerce.com",
    "nextdoor.com",
    "waze.com",
}
SEARXNG_EXTRA_SUFFIXES = [
    " llc",
    " inc",
    " ltd",
    " corporation",
    " corp",
    " company",
    " co",
    " plc"
]
SEARXNG_EMPLOYER_SIGNALS = [
        "career",
        "careers",
        "jobs",
        "employment",
        "join our team",
        "work with us",
        "hiring",
        "we are hiring",
        "apply now",
        "opportunities",
        "resume",
        "send your resume"
    ]