import os
import gc
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

# start session to check websites
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
