import requests
from bs4 import BeautifulSoup
from typing import Optional, List

class WebCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def crawl(self, url: str) -> Optional[str]:
        """
        Fetches the content of a URL and extracts the text.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

    def get_sitemap_urls(self, sitemap_url: str) -> List[str]:
        """
        Fetches a sitemap and returns all URLs found in it.
        Handles nested sitemaps (sitemapindex).
        """
        urls = []
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            
            # Check for sitemap index
            sitemap_tags = soup.find_all("sitemap")
            if sitemap_tags:
                for sitemap in sitemap_tags:
                    loc = sitemap.find("loc")
                    if loc:
                        urls.extend(self.get_sitemap_urls(loc.text.strip()))
            else:
                # Regular sitemap
                url_tags = soup.find_all("url")
                for url_tag in url_tags:
                    loc = url_tag.find("loc")
                    if loc:
                        urls.append(loc.text.strip())
                        
            return urls
            
        except Exception as e:
            print(f"Error fetching sitemap {sitemap_url}: {e}")
            return []
