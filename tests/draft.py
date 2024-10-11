# libs
import os, sys
cwd = os.getcwd()
os.chdir('src/'); path_to_src = os.getcwd()
os.chdir(cwd)
if path_to_src not in sys.path:
    sys.path.append(path_to_src)
from _libs import *
from _usr_libs import *

# exp 
test_url = "https://www.zillow.com/homedetails/1611-Los-Alamos-Ave-SW-Albuquerque-NM-87104/6710669_zpid/"
headers = {'User-Agent': USER_AGENT, 'Accept-Language': ACCEPT_LANGUAGE, 
           'Accept-Encoding': ACCEPT_ENCODING}
with requests.Session() as s:
    r = s.get(test_url, headers=headers)
    if r.status_code == 200:
        print(r.content.decode('utf-8'))
    else:
        print(r.status_code)