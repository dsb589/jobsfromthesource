PROVIDER_PARAMS = {
    "Connecticut": {
        "endpoint_url": "https://data.ct.gov/resource/n7gp-d28j.json",
        "where_cond": "lower(status)='active'",
        "select_cond": """
            id as source_id,
            name as legal_name,
            status as entity_status,
            date_registration
        """,
        "batch_size": 5000,
        "source": "CT_BUSINESS_REGISTRY",
        "state": "CT",
        "source_type": "socrata_api",
        "id_col": "id"},
    "Massachusetts": {
        "endpoint_url": "https://corp.sec.state.ma.us/corpweb/CorpSearch/CorpSearch.aspx",
        "source": "MA_BUSINESS_REGISTRY",
        "state": "MA",
        "source_type": "selenium",
        "search_terms": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        "batch_size": 100},
    "New York": {
        "endpoint_url": "https://data.ny.gov/resource/n9v6-gdp6.json",
        "select_cond": """
            dos_id as source_id,
            current_entity_name as legal_name
        """,
        "batch_size": 5000,
        "source": "NY_BUSINESS_REGISTRY",
        "state": "NY",
        "id_col": "dos_id"
        },
    "Nonprofits": {}
}