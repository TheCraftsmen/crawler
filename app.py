import re
import logging
import requests
import urllib.parse as parse
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime
from reppy.robots import Robots
from settings import URLS
from time import sleep

logger = logging.getLogger()
file_handler = logging.FileHandler(filename='crawler.log')
stream_handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


class Crawler:

    urls = set()
    regex_url = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    home_url = None
    user_agent = "*"
    num_request = 0
    max_num_request = 2
    max_seconds_delay = 1

    def __init__(self, domain, website, scripts_tags=False):
        self.domain = domain
        self.website = website
        self.search_in_scripts_tags = scripts_tags
        self.robots_url = parse.urljoin(self.website, "/robots.txt")
        self.start_time = datetime.now()
        self.start_time_str = self.start_time.strftime("%m%d%Y%H%M%S")

    def ratelimit(self):
        self.num_request += 1
        time_pased = (datetime.now() - self.start_waiting_time).seconds
        if self.num_request >= self.max_num_request:
            if time_pased < self.max_seconds_delay:
                sleep(self.max_seconds_delay - time_pased)
            self.num_request = 0
            del self.start_waiting_time

    def save_data(self):
        with open(f"{self.domain}_{self.start_time_str}.txt", "w") as file:
            for url in self.urls:
                file.write(f'{url}\n')

    def autosave(self):
        if (datetime.now() - self.start_time).seconds >= 200:
            self.save_data()
            self.start_time = datetime.now()

    def set_home_url(self, history):
        if history:
            for h in history:
                self.urls.add(h.url)
                self.home_url = h.url
        else:
            self.home_url = self.website

    def search_links_in_script_tags(self, soup):
        new_urls = []
        scripts = soup.find_all('script')
        for script in scripts:
            if script.attrs.get("type") == 'text/javascript':
                lines = list(map(lambda x: "".join(x.split()), script.text.split("\n")))
                for line in lines:
                    new_urls = re.findall(self.regex_url, line)
                    for url in new_urls:
                        if ";" not in url:
                            logger.info(f'new url found: {url}')
                            self.urls.add(url)
                            new_urls.append(url)
        return new_urls

    def search_links_in_html(self, soup):
        new_urls = []
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
                        logger.info(f'new url found: {url}')
                        self.urls.add(url)
                        new_urls.append(url)
        return new_urls

    def crawl(self, url, first=False):
        new_urls = []
        self.autosave()

        robots = Robots.fetch(self.robots_url)
        if not robots.allowed(url, self.user_agent):
            return new_urls

        if not hasattr(self, "start_waiting_time"):
            self.start_waiting_time = datetime.now()

        try:
            response = requests.get(url)
        except Exception as e:
            logger.exception(e)
            return new_urls

        if response.status_code != 200:
            return new_urls

        self.ratelimit()

        if first:
            self.set_home_url(response.history)

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        if self.search_in_scripts_tags:
            new_urls += self.search_links_in_script_tags(soup)

        new_urls += self.search_links_in_html(soup)
        return list(set(new_urls))

    def main(self):
        robots = Robots.fetch(self.robots_url)
        if not robots.allowed(self.website, self.user_agent):
            return

        urls_valid = [self.website]
        while urls_valid:
            new_urls = []
            for url_valid in urls_valid:
                new_urls += self.crawl(url_valid, first=True)
            urls_valid = list(set(new_urls))
        self.save_data()


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor() as executor:
        crawler_proccess = {}
        for url in URLS:
            logger.info(f"starting {url['domain']}")
            crawler = Crawler(domain=url["domain"], website=url["website"])
            crawler_proccess[executor.submit(crawler.main)] = url["domain"]

        for future in concurrent.futures.as_completed(crawler_proccess):
            domain = crawler_proccess[future]
            try:
                future.result()
            except Exception as exc:
                logger.exception(f'{domain} generated an exception: {exc}')
            else:
                logger.info(f'finished {domain}')
