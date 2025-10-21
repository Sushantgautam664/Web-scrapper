import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_url_path='', static_folder='.')

# ---------- SEO ANALYSIS FUNCTION ----------
def analyze_seo(soup, url):
    """Analyze SEO factors of the webpage"""
    seo_data = {
        "title": "",
        "meta_description": "",
        "meta_keywords": "",
        "headings": {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []},
        "images_without_alt": [],
        "images_with_alt": [],
        "internal_links": [],
        "external_links": [],
        "canonical_url": "",
        "robots_meta": "",
        "viewport_meta": "",
        "language": "",
        "schema_markup": [],
        "issues": [],
        "recommendations": []
    }
    
    try:
        # Title tag
        title_tag = soup.find('title')
        if title_tag:
            seo_data["title"] = title_tag.get_text(strip=True)
            if len(seo_data["title"]) > 60:
                seo_data["issues"].append("Title tag is too long (>60 characters)")
            elif len(seo_data["title"]) < 30:
                seo_data["issues"].append("Title tag is too short (<30 characters)")
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            seo_data["meta_description"] = meta_desc.get('content', '')
            if len(seo_data["meta_description"]) > 160:
                seo_data["issues"].append("Meta description is too long (>160 characters)")
            elif len(seo_data["meta_description"]) < 120:
                seo_data["issues"].append("Meta description is too short (<120 characters)")
        else:
            seo_data["issues"].append("Missing meta description")
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            seo_data["meta_keywords"] = meta_keywords.get('content', '')
        
        # Headings structure
        for i in range(1, 7):
            headings = soup.find_all(f'h{i}')
            seo_data["headings"][f"h{i}"] = [h.get_text(strip=True) for h in headings]
        
        # Check for multiple H1 tags
        h1_count = len(seo_data["headings"]["h1"])
        if h1_count > 1:
            seo_data["issues"].append(f"Multiple H1 tags found ({h1_count}). Should have only one.")
        elif h1_count == 0:
            seo_data["issues"].append("No H1 tag found")
        
        # Images analysis
        images = soup.find_all('img')
        for img in images:
            alt_text = img.get('alt', '')
            src = img.get('src', '')
            if alt_text:
                seo_data["images_with_alt"].append({"src": src, "alt": alt_text})
            else:
                seo_data["images_without_alt"].append(src)
        
        if seo_data["images_without_alt"]:
            seo_data["issues"].append(f"{len(seo_data['images_without_alt'])} images without alt text")
        
        # Links analysis
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href:
                if href.startswith('http') and not href.startswith(url):
                    seo_data["external_links"].append(href)
                else:
                    seo_data["internal_links"].append(href)
        
        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            seo_data["canonical_url"] = canonical.get('href', '')
        else:
            seo_data["issues"].append("No canonical URL found")
        
        # Robots meta
        robots = soup.find('meta', attrs={'name': 'robots'})
        if robots:
            seo_data["robots_meta"] = robots.get('content', '')
        
        # Viewport meta
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            seo_data["viewport_meta"] = viewport.get('content', '')
        else:
            seo_data["issues"].append("No viewport meta tag found")
        
        # Language
        html_tag = soup.find('html')
        if html_tag:
            seo_data["language"] = html_tag.get('lang', '')
        
        # Schema markup
        schema_scripts = soup.find_all('script', type='application/ld+json')
        for script in schema_scripts:
            seo_data["schema_markup"].append(script.get_text(strip=True))
        
        # Generate recommendations
        if not seo_data["title"]:
            seo_data["recommendations"].append("Add a title tag")
        if not seo_data["meta_description"]:
            seo_data["recommendations"].append("Add a meta description")
        if not seo_data["canonical_url"]:
            seo_data["recommendations"].append("Add a canonical URL")
        if not seo_data["viewport_meta"]:
            seo_data["recommendations"].append("Add viewport meta tag for mobile responsiveness")
        if seo_data["images_without_alt"]:
            seo_data["recommendations"].append("Add alt text to all images")
        if not seo_data["schema_markup"]:
            seo_data["recommendations"].append("Consider adding structured data (Schema.org)")
        
    except Exception as e:
        seo_data["issues"].append(f"Error analyzing SEO: {str(e)}")
    
    return seo_data

# ---------- SCRAPER FUNCTION ----------
def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        links = soup.find_all('a')

        paragraph_texts = [p.get_text(strip=True) for p in paragraphs[:5]]
        all_paragraph_texts = [p.get_text(strip=True) for p in paragraphs]
        
        link_items = []
        all_link_items = []
        for a in links[:10]:
            href = a.get('href')
            text = a.get_text(strip=True)
            if href:
                link_items.append({"text": text, "url": href})
        
        for a in links:
            href = a.get('href')
            text = a.get_text(strip=True)
            if href:
                all_link_items.append({"text": text, "url": href})

        # SEO Analysis
        seo_data = analyze_seo(soup, url)

        return {
            "ok": True,
            "paragraphCount": len(paragraphs),
            "linkCount": len(links),
            "sampleParagraphs": paragraph_texts,
            "sampleLinks": link_items,
            "allParagraphs": all_paragraph_texts,
            "allLinks": all_link_items,
            "seo": seo_data,
        }
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error fetching the URL: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"An error occurred during scraping: {e}"}

# ---------- API ROUTE ----------
@app.post('/scrape')
def scrape_route():
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({"ok": False, "error": "Missing 'url' in JSON body"}), 400
    result = scrape_website(url)
    status = 200 if result.get('ok') else 500
    message = "Scrape complete: " + (
        f"{result.get('paragraphCount', 0)} paragraphs, {result.get('linkCount', 0)} links"
        if result.get('ok') else result.get('error', 'Unknown error')
    )
    result.update({"message": message})
    return jsonify(result), status

# ---------- FRONTEND ROUTES ----------
@app.get('/')
def index():
    return send_from_directory('.', 'index.html')

@app.get('/assest/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assest', filename)


@app.get('/<path:filename>')
def serve_root_files(filename):
    # Serve files like style.css placed at project root
    return send_from_directory('.', filename)

# ---------- MAIN ENTRY --------
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
