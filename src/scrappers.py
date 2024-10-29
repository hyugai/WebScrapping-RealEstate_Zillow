# libs
from libs import *

# URLsCollector
class URLScrapper(TableTracker):
    def __init__(self,
                 path: str, name: str, 
                 headers: dict):
        super().__init__(path, name)
        self.headers = headers

    def extract(self) -> str:
        with requests.Session() as s:
            self.headers['User-Agent'] = UserAgent().random 
            r = s.get(ZILLOW, headers=self.headers) 

            if r.status_code == 200:
                return r.text
            else:
                raise ValueError(f'Failed fetching (error code: {r.status_code})')

    def transform(self):
        content = self.extract() 

    def load(self):
        pass