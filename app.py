from flask import Flask, request, jsonify
import requests
import logging
from bs4 import BeautifulSoup

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

BASE_URL = "https://phasmophobia.fandom.com/api.php"

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/fandom', methods=['GET'])
def fetch_fandom_data():
    query = request.args.get('query')
    app.logger.debug(f'Received query: {query}')
    if query:
        try:
            # Search for the query first to get the exact title
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query
            }
            search_response = requests.get(BASE_URL, params=search_params)
            search_data = search_response.json()
            app.logger.debug(f'Search response data: {search_data}')
            search_results = search_data.get("query", {}).get("search", [])
            if search_results:
                # Use the first search result's title
                exact_title = search_results[0]['title']
                app.logger.debug(f'Exact title found: {exact_title}')

                # Now query the page using the exact title
                page_params = {
                    "action": "parse",
                    "format": "json",
                    "page": exact_title,
                    "prop": "text",
                    "section": 0
                }
                page_response = requests.get(BASE_URL, params=page_params)
                page_data = page_response.json()
                app.logger.debug(f'Page response data: {page_data}')
                page_html = page_data.get("parse", {}).get("text", {}).get("*", "")
                if page_html:
                    # Parse and clean the HTML content
                    soup = BeautifulSoup(page_html, 'lxml')
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    page_text = soup.get_text(separator=' ').strip()
                    # Further cleaning to remove excessive whitespace
                    page_text = ' '.join(page_text.split())
                    app.logger.debug(f'Page found: {exact_title}')
                    return jsonify({
                        "title": exact_title,
                        "url": f'https://phasmophobia.fandom.com/wiki/{exact_title.replace(" ", "_")}',
                        "text": page_text[:500]  # Limit text to the first 500 characters
                    })
                else:
                    app.logger.debug(f'No exact match for query: {query}')
                    return jsonify({"error": f'No results found for "{query}". Try another query!'}), 404
            else:
                app.logger.debug(f'No search results for query: {query}')
                return jsonify({"error": f'No results found for "{query}". Try another query!'}), 404
        except Exception as e:
            app.logger.error(f'Exception: {str(e)}')
            return jsonify({"error": str(e)}), 500
    app.logger.debug('No query provided')
    return jsonify({"error": "No query provided"}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

