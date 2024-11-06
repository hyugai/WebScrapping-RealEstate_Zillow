# libs
import sys
from pathlib import Path

src_path = (Path.cwd()/'src').as_posix()
if src_path not in sys.path:
    sys.path.append(src_path)
from libs import *

# exp
db_path = (Path.cwd()/'tests'/'resource'/'db'/'real_estate.db').as_posix()
with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    cur.execute('SELECT * FROM pages_hrefs')
    pages_hrefs = [row[0] for row in cur.fetchall()]

scrape_freeProxyList()
csv_path = (Path.cwd()/'tests'/'resource'/'proxies'/'free_proxy_list.csv').as_posix()
df_proxies = pd.read_csv(csv_path)
proxies_pool = [f"http://{ip}:{port}" for ip, port in zip(df_proxies['ip_address'], df_proxies['port'])]    

home_scraper = GeneralHomeScraper(ZILLOW_HEADERS, proxies_pool)
home_scraper.main(pages_hrefs)