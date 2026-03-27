#!/usr/bin/env python3
"""
iCrawl — Lightweight Intelligent Scraper
Pulls clean text content from URLs without paid APIs.
Uses requests + BeautifulSoup. No firecrawl dependency.
"""

import requests
from bs4 import BeautifulSoup
import json, sys, os, re
from urllib.parse import urljoin, urlparse

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def scrape(url, timeout=15):
    """Scrape a URL and return clean markdown-ish text."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        return {"error": str(e), "url": url}
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Remove noise
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
        tag.decompose()
    
    # Try to find main content
    main = soup.find('main') or soup.find('article') or soup.find('div', {'role': 'main'})
    if not main:
        main = soup.find('body') or soup
    
    # Extract title
    title = soup.find('title')
    title_text = title.get_text(strip=True) if title else ''
    
    # Extract headings and paragraphs
    content_blocks = []
    for el in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'blockquote']):
        text = el.get_text(strip=True)
        if not text or len(text) < 10:
            continue
        if el.name.startswith('h'):
            level = int(el.name[1])
            content_blocks.append(f"{'#' * level} {text}")
        elif el.name == 'li':
            content_blocks.append(f"- {text}")
        elif el.name == 'blockquote':
            content_blocks.append(f"> {text}")
        else:
            content_blocks.append(text)
    
    return {
        "url": url,
        "title": title_text,
        "content": "\n\n".join(content_blocks),
        "word_count": sum(len(b.split()) for b in content_blocks)
    }

def search_and_scrape(query, num_results=5):
    """Search via DuckDuckGo HTML and scrape top results."""
    search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    try:
        r = requests.get(search_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        return {"error": str(e)}
    
    results = []
    for link in soup.find_all('a', class_='result__a')[:num_results]:
        href = link.get('href', '')
        title = link.get_text(strip=True)
        # DuckDuckGo wraps URLs in redirects
        if 'uddg=' in href:
            from urllib.parse import parse_qs
            parsed = parse_qs(urlparse(href).query)
            href = parsed.get('uddg', [href])[0]
        results.append({"title": title, "url": href})
    
    return results

def deep_search(query, num_results=3):
    """Search + scrape the top results for full content."""
    links = search_and_scrape(query, num_results)
    if isinstance(links, dict) and 'error' in links:
        return links
    
    full_results = []
    for link in links:
        print(f"  ↳ Scraping: {link['url'][:80]}...")
        result = scrape(link['url'])
        result['search_title'] = link['title']
        full_results.append(result)
    
    return full_results

# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 icrawl.py <url_or_search_query>")
        print("  URL mode:    python3 icrawl.py https://example.com")
        print("  Search mode: python3 icrawl.py 'how to edit interview videos'")
        sys.exit(1)
    
    target = " ".join(sys.argv[1:])
    
    if target.startswith('http'):
        result = scrape(target)
        print(f"\n# {result.get('title', 'No Title')}\n")
        print(result.get('content', 'No content extracted'))
        print(f"\n---\nWords: {result.get('word_count', 0)}")
    else:
        print(f"🔍 Searching: {target}\n")
        results = deep_search(target, num_results=3)
        for r in results:
            print(f"\n{'='*60}")
            print(f"# {r.get('search_title', r.get('title', 'No Title'))}")
            print(f"URL: {r.get('url', '')}")
            print(f"Words: {r.get('word_count', 0)}")
            print(f"{'='*60}")
            content = r.get('content', '')
            # Truncate if very long
            if len(content) > 3000:
                content = content[:3000] + "\n\n[...truncated...]"
            print(content)
