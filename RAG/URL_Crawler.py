import requests
from bs4 import BeautifulSoup
import html2text
import os
import re
import argparse
from urllib.parse import urlparse, urljoin
import hashlib

def is_external_url(base_url, url):
    """
    Check if a URL is external to the base URL's domain.
    
    Args:
        base_url (str): The base URL to compare against
        url (str): The URL to check
        
    Returns:
        bool: True if the URL is external, False otherwise
    """
    base_domain = urlparse(base_url).netloc
    url_domain = urlparse(url).netloc
    return base_domain != url_domain and url_domain != ''

def get_page_links(soup, base_url, allow_external=False):
    """
    Extract links from the page.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        base_url (str): The base URL for resolving relative links
        allow_external (bool): Whether to include external links
        
    Returns:
        list: List of valid links
    """
    # Try to find main content, or use the whole body if not found
    main_content = soup.find('main') or soup.find('article') or soup.find('body')
    if not main_content:
        return []
    
    links = []
    for a_tag in main_content.find_all('a', href=True):
        href = a_tag['href']
        
        # Skip anchor links and javascript
        if href.startswith('#') or href.startswith('javascript:'):
            continue
            
        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        
        # Check if it's an external link
        if not allow_external and is_external_url(base_url, full_url):
            continue
            
        # Skip common non-content URLs
        skip_patterns = ['login', 'logout', 'signup', 'register', 'contact','browse','zip','download','pdf','doc','xls','ppt','docx','xlsx','pptx']
        if any(pattern in full_url.lower() for pattern in skip_patterns):
            continue
            
        links.append(full_url)
            
    return links

def get_safe_filename(url, suffix=""):
    """
    Create a safe filename from URL.
    
    Args:
        url (str): The URL to convert to filename
        suffix (str): Optional suffix to add to filename
        
    Returns:
        str: Safe filename
    """
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc.replace("www.", "")
    
    # Extract path and remove extension if present
    path = parsed_url.path.strip('/')
    path = os.path.splitext(path)[0] if path else ""
    
    # Create a base name from domain and path
    if path:
        base_name = f"{netloc}_{path}"
    else:
        base_name = netloc
        
    # Replace invalid filename characters
    base_name = re.sub(r'[\\/*?:"<>|]', "_", base_name)
    base_name = re.sub(r'[. ]', "-", base_name)
    
    # If the filename becomes too long, hash part of it
    if len(base_name) > 100:
        hash_part = hashlib.md5(url.encode()).hexdigest()[:10]
        base_name = f"{base_name[:50]}_{hash_part}"
    
    # Add suffix if provided
    if suffix:
        return f"{base_name}_{suffix}"
    return base_name

def crawl_to_markdown(url, output_dir="web_content", current_depth=0, max_depth=0, allow_external=False, visited=None):
    """
    Recursively crawl web pages and save content as markdown files.
    
    Args:
        url (str): URL of the web page to crawl
        output_dir (str): Directory to save markdown files
        current_depth (int): Current crawling depth
        max_depth (int): Maximum crawling depth (0 means only the initial page)
        allow_external (bool): Whether to follow external links
        visited (set): Set of already visited URLs
    """
    if visited is None:
        visited = set()
        
    if url in visited:
        return
        
    visited.add(url)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create safe filename base from URL
    filename_base = get_safe_filename(url)
    
    # Fetch the webpage
    print(f"Fetching {url}... (depth: {current_depth})")
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return
    
    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract main content (try different common content containers)
    main_content = (soup.find(id="content") or 
                   soup.find("main") or 
                   soup.find("article") or 
                   soup.find("div", class_="content") or
                   soup.body)
    
    if not main_content:
        print(f"Could not find content for {url}")
        return
    
    # Initialize HTML to Markdown converter
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.ignore_tables = False
    
    # Extract title
    title_element = soup.find('title') or soup.find('h1')
    title = title_element.get_text().strip() if title_element else "Untitled"
    
    # Save main content
    main_md = converter.handle(str(main_content))
    main_filename = f"{filename_base}.md"
    with open(os.path.join(output_dir, main_filename), "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\nSource: {url}\n\n{main_md}")
    
    print(f"  Saved main content: {main_filename}")
    
    # Extract sections (h2, h3 headers commonly define sections)
    sections = main_content.find_all(["h2", "h3"])
    
    # Process each major section
    for i, section in enumerate(sections):
        section_title_text = section.get_text().strip()
        if not section_title_text:
            continue
        
        # Skip common non-content sections
        skip_sections = ["References", "See also", "External links", "Notes", "Bibliography", 
                         "Comments", "Related", "Share", "Tags"]
        if any(section_title_text.startswith(skip) for skip in skip_sections):
            continue
        
        # Create section filename
        safe_section = re.sub(r'[\\/*?:"<>|]', "", section_title_text).strip()
        safe_section = re.sub(r'[. ]', "-", safe_section)
        if not safe_section:
            safe_section = f"section_{i}"
            
        section_filename = f"{filename_base}_{safe_section}.md"
        
        # Find content for this section
        section_content = []
        tag = section
        while tag := tag.find_next_sibling():
            if tag.name in ["h2", "h3"]:
                break
            section_content.append(str(tag))
        
        # Convert section content to markdown
        if section_content:
            section_md = converter.handle("".join(section_content))
            with open(os.path.join(output_dir, section_filename), "w", encoding="utf-8") as f:
                f.write(f"# {section_title_text}\n\nSource: {url}\n\n{section_md}")
            print(f"  Saved section: {section_filename}")
    
    print(f"Completed page: {url}")
    
    # Continue crawling if we haven't reached max depth
    if current_depth < max_depth:
        links = get_page_links(soup, url, allow_external)
        for link in links:
            if link not in visited:
                crawl_to_markdown(
                    link, 
                    output_dir, 
                    current_depth + 1,
                    max_depth,
                    allow_external,
                    visited
                )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl websites and save as markdown')
    parser.add_argument('url', help='URL of the page to start crawling from')
    parser.add_argument('--depth', type=int, default=0, help='Maximum crawling depth (0 = only initial page)')
    parser.add_argument('--output', default='web_content', help='Output directory for markdown files')
    parser.add_argument('--allow-external', action='store_true', help='Allow following external links')
    
    args = parser.parse_args()
    
    crawl_to_markdown(
        url=args.url,
        output_dir=args.output,
        max_depth=args.depth,
        allow_external=args.allow_external
    )
    
    print(f"Crawling completed. Content saved to {args.output} directory.")