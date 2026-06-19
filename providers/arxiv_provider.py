# providers/arxiv_provider.py
import requests
import xml.etree.ElementTree as ET

def search_arxiv(query: str):
    """
    جستجو در arXiv برای یافتن نسخه Open Access مقاله
    
    Args:
        query (str): عنوان مقاله یا شناسه arXiv
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    # ساخت URL جستجو
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=1"
    
    try:
        print(f"📡 Sending request to arXiv API...")
        r = requests.get(url, timeout=30)
        
        if r.status_code != 200:
            print(f"❌ arXiv API returned status: {r.status_code}")
            return None
        
        # پردازش پاسخ XML
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        
        if not entries:
            print("❌ No entries found in arXiv response")
            return None
        
        # استخراج اطلاعات مقاله اول
        entry = entries[0]
        title = entry.find("atom:title", ns)
        article_id = entry.find("atom:id", ns)
        
        if title is None or article_id is None:
            print("❌ Missing title or ID in arXiv response")
            return None
        
        title_text = title.text.strip()
        article_id_text = article_id.text.strip()
        
        # ساخت URL PDF
        pdf_url = article_id_text.replace("/abs/", "/pdf/") + ".pdf"
        
        print(f"✅ Found arXiv paper: {title_text}")
        
        return {
            "title": title_text,
            "pdf_url": pdf_url,
            "source": "arxiv"
        }
        
    except requests.exceptions.Timeout:
        print("❌ arXiv API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ arXiv API request error: {e}")
        return None
    except ET.ParseError as e:
        print(f"❌ arXiv XML parse error: {e}")
        return None
    except Exception as e:
        print(f"❌ arXiv search error: {e}")
        return None
