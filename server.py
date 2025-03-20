from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xml.etree.ElementTree as ET
import threading
import os
import time
import requests

DB_FILE = "database.xml"
LOCK = threading.Lock()

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def init_db():
    if not os.path.exists(DB_FILE):
        root = ET.Element("notebook")
        tree = ET.ElementTree(root)
        tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)

def add_note(topic, text, timestamp):
    with LOCK:
        tree = ET.parse(DB_FILE)
        root = tree.getroot()
        topic_el = None
        for t in root.findall("topic"):
            if t.get("name") == topic:
                topic_el = t
                break
        if topic_el is None:
            topic_el = ET.SubElement(root, "topic")
            topic_el.set("name", topic)
        note_el = ET.SubElement(topic_el, "note")
        note_el.set("timestamp", timestamp)
        note_el.text = text
        tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)
        return True

def get_topic_contents(topic):
    with LOCK:
        tree = ET.parse(DB_FILE)
        root = tree.getroot()
        for t in root.findall("topic"):
            if t.get("name") == topic:
                notes = t.findall("note")
                results = []
                for note in notes:
                    ts = note.get("timestamp", "")
                    tx = note.text if note.text else ""
                    results.append({"timestamp": ts, "text": tx})
                return results
        return []

def add_wikipedia_info(topic, keyword):
    open_search_url = "https://en.wikipedia.org/w/api.php"
    open_search_params = {
        'action': 'opensearch',
        'search': keyword,
        'limit': 1,
        'namespace': 0,
        'format': 'json'
    }
    try:
        r1 = requests.get(open_search_url, params=open_search_params, timeout=5)
        data1 = r1.json()
        if len(data1) != 4:
            return "Invalid OpenSearch response."
        titles = data1[1]
        links = data1[3]
        if not titles or not links:
            return "No Wikipedia pages found for that keyword."

        page_title = titles[0]
        page_link = links[0]

        summary_url = "https://en.wikipedia.org/w/api.php"
        summary_params = {
            'action': 'query',
            'prop': 'extracts',
            'explaintext': '1',
            'exintro': '1',
            'exsentences': '3',
            'redirects': '1',
            'titles': page_title,
            'format': 'json'
        }
        r2 = requests.get(summary_url, params=summary_params, timeout=5)
        data2 = r2.json()

        pages = data2.get("query", {}).get("pages", {})
        page_extract = ""
        for _, page_info in pages.items():
            if "extract" in page_info:
                page_extract = page_info["extract"].strip()
            break

        if not page_extract:
            page_extract = "No content available (page may be a disambiguation or has no intro)."

        text = (
            f"Title: {page_title}\n"
            f"Link: {page_link}\n"
            f"Relevant information:\n{page_extract}"
        )
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        add_note(topic, text, timestamp)

        return f"Added Wikipedia info to topic '{topic}': {page_link}"
    except Exception as e:
        return f"Error querying Wikipedia: {e}"


def run_server(host="localhost", port=9000):
    init_db()
    server = SimpleXMLRPCServer((host, port), requestHandler=RequestHandler, allow_none=True)
    server.register_introspection_functions()
    server.register_function(add_note, "add_note")
    server.register_function(get_topic_contents, "get_topic_contents")
    server.register_function(add_wikipedia_info, "add_wikipedia_info")

    print(f"Server started on {host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer interrupted. Shutting down gracefully...")


if __name__ == "__main__":
    run_server()
