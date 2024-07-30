import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os

# Constants
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1  # Delay between requests in seconds
NUM_THREADS = 4  # Number of parallel threads
INTERIM_FILE = 'output/interim_data.csv'  # Intermediate output file
FINAL_FILE = 'output/final_data.csv'  # Final sorted output file

# Load configuration from JSON file
def load_config():
    """Load configuration from a JSON file."""
    with open('config.json', 'r') as file:
        config = json.load(file)
    return config

def fetch_page(url, headers, retries=MAX_RETRIES):
    """Fetch a page and return the response or None if it fails."""
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response
    except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
        if retries > 0:
            print(f"Retrying {url} ({MAX_RETRIES - retries + 1}/{MAX_RETRIES}) due to {e}")
            time.sleep(DELAY_BETWEEN_REQUESTS)
            return fetch_page(url, headers, retries - 1)
        else:
            print(f"Failed to retrieve {url}: {e}")
            return None

def normalize_url(url):
    """Remove query parameters and fragments from a URL."""
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))

def get_all_links(url, domain, visited):
    """Extract and return all valid links from a page."""
    response = fetch_page(url, headers)
    if not response:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.attrs['href']
        full_url = urljoin(url, href)
        normalized_url = normalize_url(full_url)
        parsed_url = urlparse(normalized_url)

        if domain in parsed_url.netloc and normalized_url not in visited:
            visited.add(normalized_url)
            links.append(normalized_url)
    return links

def fetch_title_and_status(url):
    """Get page title and status code for a URL."""
    response = fetch_page(url, headers)
    if not response:
        return 'Failed to retrieve title', 'Failed to retrieve status'

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string if soup.title else 'No Title'
    status_code = response.status_code
    return title, status_code

def write_to_csv(file, data):
    """Write data to a CSV file."""
    with open(file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['url', 'title', 'status_code'])
        writer.writerow(data)

def crawl_website(start_url):
    """Crawl a website and save URL, title, and status code to CSV."""
    domain = urlparse(start_url).netloc
    visited = set()
    to_visit = [normalize_url(start_url)]  # Queue of URLs to visit

    # Create interim CSV file and write header
    if not os.path.exists(INTERIM_FILE):
        with open(INTERIM_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['url', 'title', 'status_code'])
            writer.writeheader()

    while to_visit:
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = {executor.submit(get_all_links, current_url, domain, visited): current_url for current_url in to_visit}
            to_visit = []

            for future in as_completed(futures):
                current_url = futures[future]
                print(f"Crawling: {current_url}")
                links = future.result()
                to_visit.extend(links)

                title, status_code = fetch_title_and_status(current_url)
                write_to_csv(INTERIM_FILE, {'url': current_url, 'title': title, 'status_code': status_code})

                time.sleep(DELAY_BETWEEN_REQUESTS)

    # Sort and move to final CSV file
    with open(INTERIM_FILE, mode='r', encoding='utf-8') as infile, open(FINAL_FILE, mode='w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=['url', 'title', 'status_code'])
        writer.writeheader()
        sorted_rows = sorted(reader, key=lambda row: row['url'])
        writer.writerows(sorted_rows)

    print(f"Crawling completed. Results saved to '{FINAL_FILE}'.")

if __name__ == "__main__":
    config = load_config()
    start_url = config.get('start_url')
    user_agent = config.get('user_agent')
    headers = {'User-Agent': user_agent}
    crawl_website(start_url)
