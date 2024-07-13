import requests
import time
import urllib.request
import urllib.error
from bs4 import BeautifulSoup
from html.parser import HTMLParser
from urllib.parse import urlparse
import re
import openai
from dotenv import load_dotenv
import os
import json
import sys

HTTP_URL_PATTERN = re.compile(r"^https?://")

class HyperlinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hyperlinks = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            if "href" in attrs:
                self.hyperlinks.append(attrs["href"])

def get_text_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    return text

def get_domain_name(url):
    domain = re.search('https?://([A-Za-z_0-9.-]+).*', url)
    if domain:
        return domain.group(1)
    else:
        return ""

def get_hyperlinks(url):
    for retry in range(1):
        try:
            with urllib.request.urlopen(url) as response:
                if not response.info().get('Content-Type').startswith("text/html"):
                    return []

                html = response.read().decode('utf-8')
                break

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"HTTP Error 429: Too Many Requests. Retrying {retry + 1} of 1 attempts for {url}")
                time.sleep(3)
            else:
                print(e)
                return []
        except Exception as e:
            print(e)
            return []
    else:
        print(f"Failed to fetch {url} after 1 retries")
        return []

    parser = HyperlinkParser()
    parser.feed(html)

    return parser.hyperlinks

def get_domain_hyperlinks(local_domain, url):
    clean_links = []
    for link in set(get_hyperlinks(url)):
        clean_link = None

        if re.search(HTTP_URL_PATTERN, link):
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link

        else:
            if link.startswith("/"):
                link = link[1:]
            elif link.startswith("#") or link.startswith("mailto:"):
                continue
            clean_link = "https://" + local_domain + "/" + link

        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)

    return list(set(clean_links))

def crawl_website(url):
    domain_name = get_domain_name(url)
    visited_links = set()
    pending_links = {url}
    all_text = ""

    while pending_links:
        current_link = pending_links.pop()
        visited_links.add(current_link)

        try:
            page_text = get_text_from_url(current_link)
            all_text += page_text
            domain_links = get_domain_hyperlinks(domain_name, current_link)

            for link in domain_links:
                if link not in visited_links:
                    pending_links.add(link)

        except Exception as e:
            print(f"Error while processing {current_link}: {e}")

    return all_text

def remove_clutter(content):
    clutter_patterns = [
        r"Simple Slide \d",
        r"Slide \d \(current slide\) Slide \d",
        r"429 Too Many Requests.*GMT",
        r"SEC-60"
    ]

    for pattern in clutter_patterns:
        content = re.sub(pattern, '', content)

    return content

def generate_summary(unstructured_data):
    load_dotenv()

    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're an expert at summarizing a company's unstructured website data into a concise 150 to 200 word summary."},
            {"role": "user", "content": f"Summarize the company's unstructured data: {unstructured_data}"},
        ]
    )
    return response['choices'][0]['message']['content']

def save_summarized_to_file(filename, content):
    content = remove_clutter(content)
    content = re.sub(r'\s\s+', ' ', content)

    summarized_content = ""

    words = content.split()
    chunk_size = 1000
    num_chunks = len(words) // chunk_size + (1 if len(words) % chunk_size > 0 else 0)

    openai_call_count = 0
    max_openai_calls = 3

    for i in range(num_chunks):
        if openai_call_count >= max_openai_calls:
            break

        chunk = ' '.join(words[i * chunk_size: (i + 1) * chunk_size])
        
        for retry in range(3):  # Retry 3 times for failed requests
            try:
                summary = generate_summary(chunk)
                summarized_content += summary + '\n\n'
                openai_call_count += 1
                break
            except Exception as e:
                print(f"Error generating summary, retry {retry + 1}: {e}")
                time.sleep(3)
        else:
            print(f"Failed to generate summary after 3 retries")

    with open(filename, 'w') as file:
        file.write(summarized_content)


def main():
    print("Scraping")
    data_json = sys.argv[1]
    data = json.loads(data_json)
    url = data["url"]
    
    domain_name = get_domain_name(url)
    text_content = crawl_website(url)
    filename = f"{domain_name}.txt"
    save_summarized_to_file(filename, text_content)
    print("Complete")

if __name__ == "__main__":
    main()
