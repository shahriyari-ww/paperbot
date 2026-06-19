import requests
import xml.etree.ElementTree as ET

def search_arxiv(query):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=1"
    
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return None
        
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        
        if not entries:
            return None
        
        entry = entries[0]
        title = entry.find("atom:title", ns).text.strip()
        article_id = entry.find("atom:id", ns).text.strip()
        pdf_url = article_id.replace("/abs/", "/pdf/") + ".pdf"
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "arxiv"
        }
    except Exception:
        return None