import p01_1_providers
import p01_2_employer_tables
import gc
import traceback

# Change active to False to skip steps
PIPELINE = {
    "p01_1_providers": {
        "func": p01_1_providers,
        "active": True,
    },
    "p01_2_employer_tables": {
        "func": p01_2_employer_tables,
        "active": True,
    },
}

if __name__ == "__main__":
    try:
        for step_name, step in PIPELINE.items():
            if step["active"]:
                step["func"].main()
                gc.collect()
    except Exception:
        print(traceback.format_exc)