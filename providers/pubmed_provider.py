# providers/pubmed_provider.py
import requests
import time
import random

def search_pubmed_advanced(query: str):
    """
    نسخه پیشرفته جستجوی PubMed با مدیریت خطای 429
    """
    try:
        # تأخیر تصادفی برای جلوگیری از خطای 429
        time.sleep(random.uniform(1.5, 3.0))
        
        print(f"📡 Searching PubMed Central (Advanced) for: {query}")
        
        # جستجو در PubMed Central با فیلتر Open Access
        pmc_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pmc&term={query}+AND+open+access[filter]&retmax=1&retmode=json"
        )
        
        pmc_resp = requests.get(pmc_url, timeout=30)
        
        if pmc_resp.status_code == 429:
            print("❌ Rate limit (429) from PubMed. Waiting 5 seconds...")
            time.sleep(5)  # منتظر بمان و دوباره تلاش کن
            # می‌توانید یک بار دیگر درخواست را تکرار کنید
            pmc_resp = requests.get(pmc_url, timeout=30)
            if pmc_resp.status_code != 200:
                return None
        
        if pmc_resp.status_code != 200:
            print(f"❌ PMC search returned: {pmc_resp.status_code}")
            return None
        
        # ... ادامه کد (همان کد قبلی)
        
    except Exception as e:
        print(f"❌ PubMed Advanced search error: {e}")
        return None
