import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime

class EarningsTranscriptScraper:
    def __init__(self, base_url, target_dir="data/transcripts"):
        self.base_url = base_url
        self.target_dir = target_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        os.makedirs(target_dir, exist_ok=True)
    
    def get_transcript_links(self):
        """Extract all transcript links from the earnings page"""
        print(f"Fetching transcript links from {self.base_url}")
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            transcript_links = []
            
            link_patterns = [
                'a[href*="earnings-call-transcript"]',
                'a[href*="transcript"]',
                'a[title*="transcript"]',
                'a[title*="Transcript"]'
            ]
            
            for pattern in link_patterns:
                links = soup.select(pattern)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        title = link.get('title') or link.get_text(strip=True)
                        transcript_links.append({
                            'url': full_url,
                            'title': title,
                            'date': self.extract_date_from_title(title)
                        })
            
            seen_urls = set()
            unique_links = []
            for link in transcript_links:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            
            print(f"Found {len(unique_links)} transcript links")
            return unique_links
            
        except Exception as e:
            print(f"Error fetching transcript links: {e}")
            return []
    
    def extract_date_from_title(self, title):
        """Extract date from transcript title"""
        date_patterns = [
            r'Q[1-4]\s+\d{4}',  # Q1 2024
            r'\d{4}',           # 2024
            r'\w+\s+\d{1,2},\s+\d{4}',  # January 1, 2024
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, title)
            if match:
                return match.group()
        return "unknown"
    
    def scrape_transcript(self, transcript_info):
        """Scrape individual transcript content"""
        url = transcript_info['url']
        title = transcript_info['title']
        date = transcript_info['date']
        
        print(f"Scraping: {title}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            content = self.extract_transcript_content(soup)
            
            if content:
                safe_title = re.sub(r'[^\w\s-]', '', title)
                safe_title = re.sub(r'[-\s]+', '_', safe_title)
                filename = f"{date}_{safe_title}.txt"
                filepath = os.path.join(self.target_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {title}\n")
                    f.write(f"Date: {date}\n")
                    f.write(f"URL: {url}\n")
                    f.write(f"Scraped: {datetime.now().isoformat()}\n")
                    f.write("="*80 + "\n\n")
                    f.write(content)
                
                print(f"Saved: {filename}")
                return filepath
            else:
                print(f"No content found for: {title}")
                return None
                
        except Exception as e:
            print(f"Error scraping {title}: {e}")
            return None
    
    def extract_transcript_content(self, soup):
        """Extract the main transcript content from the page"""
        content_selectors = [
            'div[class*="transcript"]',
            'div[class*="content"]',
            'article',
            'div[class*="article"]',
            'div[class*="body"]'
        ]

        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator='\n', strip=True)
                if len(text) > 5000:  
                    return text

        paragraphs = soup.find_all('p')
        if paragraphs:
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
            if len(content) > 500:
                return content
        
        return None
    
    def scrape_all(self, delay=2):
        """Scrape all available transcripts"""
        transcript_links = self.get_transcript_links()
        
        if not transcript_links:
            print("No transcript links found")
            return
        
        successful_downloads = []
        
        for i, transcript_info in enumerate(transcript_links):
            print(f"\nProgress: {i+1}/{len(transcript_links)}")
            
            filepath = self.scrape_transcript(transcript_info)
            if filepath:
                successful_downloads.append(filepath)

            if i < len(transcript_links) - 1:
                print(f"Waiting {delay} seconds...")
                time.sleep(delay)
        
        summary = {
            'total_links': len(transcript_links),
            'successful_downloads': len(successful_downloads),
            'files': successful_downloads,
            'scraped_at': datetime.now().isoformat()
        }
        
        summary_path = os.path.join(self.target_dir, 'scrape_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nScraping complete!")
        print(f"Successfully downloaded: {len(successful_downloads)}/{len(transcript_links)} transcripts")
        print(f"Files saved to: {self.target_dir}")

def main():
    url = "https://www.fool.com/quote/nasdaq/nvda/#quote-earnings-transcripts"
    target_directory = "data/transcripts"
    scraper = EarningsTranscriptScraper(url, target_directory)
    scraper.scrape_all(delay=2)

if __name__ == "__main__":
    main()