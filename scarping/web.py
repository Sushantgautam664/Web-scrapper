import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_url_path='', static_folder='.')

# ---------- SCRAPER FUNCTION ----------
def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        links = soup.find_all('a')

        paragraph_texts = [p.get_text(strip=True) for p in paragraphs[:5]]
        link_items = []
        for a in links[:10]:
            href = a.get('href')
            text = a.get_text(strip=True)
            if href:
                link_items.append({"text": text, "url": href})

        return {
            "ok": True,
            "paragraphCount": len(paragraphs),
            "linkCount": len(links),
            "sampleParagraphs": paragraph_texts,
            "sampleLinks": link_items,
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
    return send_from_directory('.', 'web.html')

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
