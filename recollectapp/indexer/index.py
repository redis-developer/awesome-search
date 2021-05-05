import re
from typing import Dict, List

from time import sleep
import requests
from config.settings import GH_ACCESS_TOKEN

MAX_THREADS = 4
DELAY = 0.5
URL_PATTERN = "(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"


class RepoScraperError(Exception):
    pass


class RepoScraper:
    """
    Uses Github API to return data for a repo.
    """

    def __init__(self, url: str):
        url = url.replace("https://github.com/", '')
        url = url.split('/')
        self.owner = url[0]
        self.repo = url[1].split(')', 1)[0]

    def get_repo_data(self) -> Dict:
        return requests.get(f"https://api.github.com/repos/{self.owner}/{self.repo}", headers={
            'Authorization': GH_ACCESS_TOKEN,
        }).json()

    def get_readme_text(self) -> str:
        data = requests.get(
            f"https://api.github.com/repos/{self.owner}/{self.repo}/readme", headers={
                'Authorization': GH_ACCESS_TOKEN,
            }).json()
        download = data['download_url']
        return requests.get(download).text


class AwesomeScrape:
    """
    Scrapes repositories found on an awsome list.

    Saves the repository data into a Redis instance.
    """

    def __init__(self, url: str):
        self.url = url
        self.repo_urls = self.__parse_urls()

    def __parse_urls(self) -> List[str]:
        """
        Parses all Github repo URLs found on awsome list.
        """
        raw_readme = RepoScraper(self.url).get_readme_text()
        urls = []
        for match in re.finditer(re.compile(URL_PATTERN), raw_readme):
            url = match.group()
            if url.startswith("https://github.com/"):
                urls.append(url)
        return urls

    def scrape(self, max_num: int = None) -> List[Dict]:
        """
        Scrapes data on all repositories found on awsome list.
        """

        repo_data = []

        def get_repo_data(url) -> Dict:
            return RepoScraper(url).get_repo_data()

        urls = self.repo_urls[:max_num] if max_num is not None else self.repo_urls
        for url in urls:
            try:
                repo_data.append(get_repo_data(url))
                sleep(DELAY)
            except RepoScraperError:
                pass

        return repo_data
