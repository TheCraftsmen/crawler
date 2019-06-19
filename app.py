import re
import requests
import urllib.parse as parse
from bs4 import BeautifulSoup


class Crawler:

    urls = set()
    regex_url = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    domain = "ripio.com"
    website = "https://www.ripio.com/"
    home_url = None

    def crawl(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            return
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

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
        response = requests.get(self.website)
        if response.status_code != 200:
            return
        for h in response.history:
            self.urls.add(h.url)
            self.home_url = h.url
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
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
            if url and isinstance(url, str) and (url not in list(self.urls)):
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

        print(list(self.urls))


if __name__ == '__main__':
    crawler = Crawler()
    crawler.main()
