import requests # type: ignore
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github+json"
        }

    def get(self, endpoint, params=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        merged_headers = {**self.headers, **(headers or {})}
        response = requests.get(url, headers=merged_headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_text(self, endpoint, params=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        merged_headers = {**self.headers, **(headers or {})}
        response = requests.get(url, headers=merged_headers, params=params)
        response.raise_for_status()
        return response.text
