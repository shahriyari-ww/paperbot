# providers/nexus_provider.py
import requests
from bs4 import BeautifulSoup

def search_nexus(query: str):
    """
    جستجو در Nexus (Standard Template Construct)
    
    Args:
        query (str): DOI یا عنوان مقاله
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        # وب‌سایت Nexus
        url = f"https://nexus.odyssey.one/search?q={query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print(f"📡 Searching Nexus for: {query}")
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ Nexus returned status: {resp.status_code}")
            return None
        
        # پردازش HTML برای استخراج اطلاعات
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # پیدا کردن اولین نتیجه
        result = soup.find('div', class_='result')
        if not result:
            print("❌ No results found")
            return None
        
        # استخراج عنوان و لینک
        title_elem = result.find('h3')
        title = title_elem.text if title_elem else "Unknown Title"
        
        link_elem = result.find('a')
        pdf_url = link_elem.get('href') if link_elem else None
        
        if not pdf_url:
            print("❌ No PDF link found")
            return None
        
        print(f"✅ Found article: {title}")
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "nexus"
        }
        
    except Exception as e:
        print(f"❌ Nexus search error: {e}")
        return None
