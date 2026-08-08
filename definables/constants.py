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