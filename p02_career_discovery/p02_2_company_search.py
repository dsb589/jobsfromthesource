import time
import subprocess
import shutil
import pandas as pd
from urllib.parse import urlparse
import re
from cd1_searxng_client import search_searxng
from concurrent.futures import ThreadPoolExecutor, as_completed