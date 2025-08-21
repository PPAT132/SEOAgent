from bs4 import BeautifulSoup

def extract_context(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get ALL titles (not just first)
    all_titles = [title.get_text() for title in soup.find_all('title')]
    
    # Get ALL meta descriptions
    all_meta_descs = [meta.get('content') for meta in soup.find_all('meta', attrs={'name': 'description'})]
    
    # Get ALL headings
    all_headings = [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]

    # Get ALL main content
    main_content = soup.find('main') or soup.find('body') or soup
    
    if main_content:
        # Get text from main content only, limit length
        content_text = main_content.get_text(separator=' ', strip=True)
        # Limit to first 1000 characters (adjust as needed)
        content_text = content_text[:3000] + "..." if len(content_text) > 3000 else content_text
    else:
        content_text = ""
    
    return f"""
        ALL_TITLES: {' | '.join(all_titles)}
        ALL_META_DESCRIPTIONS: {' | '.join(all_meta_descs)}
        ALL_HEADINGS: {' | '.join(all_headings)}
        ALL_PAGE_TEXT: {content_text}
        """