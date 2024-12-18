# libs
import time
import json
import random
import aiohttp
import asyncio
from lxml import etree
from bs4 import BeautifulSoup
from zillow_conf import zillow

# class DetailedHomesScraper
"""
We will have 6 "parent compounds" (~ 6 nodes) including: "Interior", "Property", "Construction", "Utilities & green energy", "Community & HOA", "Financial & listing details"
Each node -> 2 sub-nodes: 
     -> the 1st one contains the PARENT COMPOUND'S NAME
     -> the 2nd one is the CONTENT ("free-text" & "sub-compound") of it 
 """
class ExtendedScraper():
    def __init__(self) -> None:
        self.zillow = zillow

    async def push_into_queue(self, 
                              href: tuple[int, str], queue: asyncio.Queue) -> None:
        await queue.put(href) 

    async def extract_detailedInfo(self, 
                                   s: aiohttp.ClientSession, queues: dict[str, asyncio.Queue]) -> None:
        #while not queues['href'].empty(): # using the .empty() method ONLY when we get the item out 
        while True:
            home_id, href = await queues['href'].get()
            print(href)
            headers = random.choice(zillow['headers'])
            # headers = zillow['headers'][-1]

            async with s.get(href, headers=headers) as r:
                if r.status == 200:
                    print('OK')

                    content = await r.text()
                    dom = etree.HTML(str(BeautifulSoup(content, features='lxml')))

                    xpath = "//h2[text()='Facts & features']/following-sibling::div/descendant::div[@data-testid='category-group']"
                    nodes_div = dom.xpath(xpath)

                    allCompounds: dict = {} # We will have 6 "parent compounds" (~ 6 nodes) including: "Interior", "Property", "Construction", "Utilities & green energy", "Community & HOA", "Financial & listing details"

                    for node in nodes_div:
                        parentCompound_Name: str = node.xpath("./descendant::h3")[0].text # PARENT COMPOUND'S NAME

                        parentCompound_Content= {} # PARENT COMPOUND'S CONTENT (iterate "ul"s to collect "free-text" and "sub-combound")
                        for node_ul in node.xpath("./descendant::ul"): # Each "ul" node is either a "sub-combound" or "free texts" (sub-combound without the title)
                            subCompound_Name: list[etree._Element] = node_ul.xpath("./preceding-sibling::h6") # If this is empty, this "ul" node will be "free texts"
                            
                            nodes_span: list[etree._Element] = node_ul.xpath("./descendant::span") # Each node "span" consits of either 3 seprated strings or 1 single string (noted as noKeyTexts)
                            unflattened_subCompound_Content: list[list[str]]= [[i.strip().replace('"', 'in').replace('\r\n', ' ').replace('\'', '')  for i in span.itertext()] 
                                                                                   for span in nodes_span] # replace '"' -> in, \r\n -> whitespace, ' -> null character

                            # Make it compatible with the others
                            noKeyTexts = ['{"Description": "%s"}' % unflattened_subCompound_Content.pop(i)[0] \
                                              for i, val in enumerate(unflattened_subCompound_Content) if (len(val) == 1)]

                            flattened_subCompound_Content: list[str] = ['{"' + '"'.join(i) + '"}' \
                                                                            for i in unflattened_subCompound_Content if (':' in i)] # len(i) != 2 -> remove "View virtual tour"
                            flattened_subCompound_Content.extend(noKeyTexts) # Add fixed noKeyTexts 

                            subCompound_Content = dict()
                            [subCompound_Content.update(eval(i)) for i in flattened_subCompound_Content]

                            if subCompound_Name: 
                                parentCompound_Content[subCompound_Name[0].text] = subCompound_Content # Collect sub-compound for PARENT COMPOUND
                            else:
                                parentCompound_Content.update(subCompound_Content) # Collect free-text for PARENT COMPOUND

                        allCompounds[parentCompound_Name] = parentCompound_Content
                    
                    await queues['home'].put((json.dumps(allCompounds), 1, home_id)) # convert to a JSON string
                else:
                    print(f'Failed (error code: {r.status})')

            queues['href'].task_done()

    async def transship(self,
                        queue: asyncio.Queue, results: list) -> None:
        while True:
            item = await queue.get() 
            results.append(item)

            queue.task_done()

    async def collect(self,
                      hrefs: list[tuple[int, str]], num_workers: int=5) -> dict[str, list]:
        queues = {'href': asyncio.Queue(), 'home': asyncio.Queue()}
        results = {'home': []}

        async with aiohttp.ClientSession() as s:
            tasks_push_hrefs_into_queue = [asyncio.create_task(self.push_into_queue(item, queues['href'])) for item in hrefs]
            tasks_extract_homeDetails = [asyncio.create_task(self.extract_detailedInfo(s, queues)) for _ in range(num_workers)]
            task_transship = asyncio.create_task(self.transship(queues['home'], results['home'])) 
            
            await asyncio.gather(*tasks_push_hrefs_into_queue) # use asyncio.gather specifically when the task is not in the "while True:..." loop, cause the program will hang forever to wait for that infinitive loop

            [await q.join() for q in queues.values()]
            [t.cancel() for t in tasks_extract_homeDetails]
            task_transship.cancel()

        return results

    def main(self, 
             hrefs: list[tuple[int, str]], num_workers: int=5) -> dict[str, list]:
        start = time.time()
        results = asyncio.run(self.collect(hrefs, num_workers)) 
        print(f"Finished in: {time.time() - start}s \
                \nSuccessful rate: {(len(results['home'])/len(hrefs))*100:.2f}%")

        return results
