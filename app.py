import re
import requests
import urllib.parse as parse
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime
from reppy.robots import Robots
from settings import URLS


class Crawler:

    urls = set()
    regex_url = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    home_url = None
    user_agent = "*"

    def __init__(self, domain, website, scripts_tag=False):
        self.domain = domain
        self.website = website
        self.search_in_scripts_tag = scripts_tag
        self.robots_url = parse.urljoin(self.website, "/robots.txt")
        self.start_time = datetime.now()
        self.start_time_str = self.start_time.strftime("%m%d%Y%H%M%S")

    def save_data(self):
        with open(f"{self.domain}_{self.start_time_str}.txt", "w") as file:
            for url in self.urls:
                file.write(f'{url}\n')

    def crawl(self, url, first=False):

        if (datetime.now() - self.start_time).seconds >= 200:
            self.save_data()
            self.start_time = datetime.now()

        robots = Robots.fetch(self.robots_url)
        if not robots.allowed(url, self.user_agent):
            return
        try:
            response = requests.get(url)
        except Exception as e:
            print(e)
            return

        if response.status_code != 200:
            return

        if first:
            for h in response.history:
                self.urls.add(h.url)
                self.home_url = h.url

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        if self.search_in_scripts_tag:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.attrs.get("type") == 'text/javascript':
                    lines = list(map(lambda x: "".join(x.split()), script.text.split("\n")))
                    for line in lines:
                        new_urls = re.findall(self.regex_url, line)
                        for url in new_urls:
                            if ";" not in url:
                                self.urls.add(url)
                                print(url)
                                self.crawl(url)

        links = soup.find_all('a')
        for link in links:
            url = link.get('href')
            if url and isinstance(url, str):
                if (
                    re.match(self.regex_url, url) and (self.domain in url) or
                    url.startswith("/") or
                    url.startswith("#") or
                    url.startswith("./") or
                    url.startswith(".#")
                ):
                    if (
                        url.startswith("/") or url.startswith("./") or
                        url.startswith("#") or url.startswith(".#")
                    ):
                        url = parse.urljoin(self.home_url, url)
                    if (url not in list(self.urls)):
                        print(url)
                        self.urls.add(url)
                        self.crawl(url)
        return

    def main(self):
        robots = Robots.fetch(self.robots_url)
        if not robots.allowed(self.website, self.user_agent):
            return

        self.crawl(self.website, first=True)
        self.save_data()


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor() as executor:
        crawler_proccess = {}
        for url in URLS:
            print(f"starting {url['domain']}")
            crawler = Crawler(domain=url["domain"], website=url["website"])
            crawler_proccess[executor.submit(crawler.main)] = url["domain"]

        for future in concurrent.futures.as_completed(crawler_proccess):
            domain = crawler_proccess[future]
            try:
                future.result()
            except Exception as exc:
                print(f'{domain} generated an exception: {exc}')
            else:
                print(f'finished {domain}')
