# providers/pubmed_provider.py
import requests
import time
import random

def search_pubmed(query: str):
    """
    جستجو در PubMed برای یافتن نسخه Open Access مقاله
    """
    try:
        print(f"📡 Searching PubMed for: {query}")
        
        # ساخت URL جستجو
        search_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={query}&retmax=1&retmode=json"
        )
        
        search_resp = requests.get(search_url, timeout=30)
        
        if search_resp.status_code == 429:
            print("❌ Rate limit (429) from PubMed. Waiting 5 seconds...")
            time.sleep(5)
            search_resp = requests.get(search_url, timeout=30)
        
        if search_resp.status_code != 200:
            print(f"❌ PubMed search returned: {search_resp.status_code}")
            return None
        
        search_data = search_resp.json()
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            print("❌ No PubMed ID found")
            return None
        
        pmid = id_list[0]
        print(f"✅ Found PubMed ID: {pmid}")
        
        # دریافت اطلاعات کامل مقاله
        summary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            f"?db=pubmed&id={pmid}&retmode=json"
        )
        
        summary_resp = requests.get(summary_url, timeout=30)
        
        if summary_resp.status_code == 429:
            print("❌ Rate limit (429) from PubMed. Waiting 5 seconds...")
            time.sleep(5)
            summary_resp = requests.get(summary_url, timeout=30)
        
        if summary_resp.status_code != 200:
            print(f"❌ PubMed summary returned: {summary_resp.status_code}")
            return None
        
        summary_data = summary_resp.json()
        article_info = summary_data.get("result", {}).get(pmid, {})
        title = article_info.get("title", "Unknown Title")
        
        print(f"📄 Article title: {title}")
        
        # بررسی وجود نسخه Open Access در PubMed Central
        pmc_id = article_info.get("pmcid", "")
        if pmc_id:
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
            print(f"✅ Found PMC ID: {pmc_id}")
            return {
                "title": title,
                "pdf_url": pdf_url,
                "source": "pubmed",
                "pmid": pmid,
                "pmc_id": pmc_id
            }
        else:
            print("❌ No PMC ID found (article may not be Open Access)")
        
        return None
        
    except requests.exceptions.Timeout:
        print("❌ PubMed API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ PubMed request error: {e}")
        return None
    except Exception as e:
        print(f"❌ PubMed search error: {e}")
        return None


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
            time.sleep(5)
            pmc_resp = requests.get(pmc_url, timeout=30)
        
        if pmc_resp.status_code != 200:
            print(f"❌ PMC search returned: {pmc_resp.status_code}")
            return None
        
        pmc_data = pmc_resp.json()
        id_list = pmc_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            print("❌ No PMC ID found with Open Access filter")
            return None
        
        pmc_id = id_list[0]
        print(f"✅ Found PMC ID: {pmc_id}")
        
        # دریافت اطلاعات مقاله
        summary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            f"?db=pmc&id={pmc_id}&retmode=json"
        )
        
        summary_resp = requests.get(summary_url, timeout=30)
        
        if summary_resp.status_code == 429:
            print("❌ Rate limit (429) from PubMed. Waiting 5 seconds...")
            time.sleep(5)
            summary_resp = requests.get(summary_url, timeout=30)
        
        if summary_resp.status_code != 200:
            print(f"❌ PMC summary returned: {summary_resp.status_code}")
            return None
        
        summary_data = summary_resp.json()
        article_info = summary_data.get("result", {}).get(pmc_id, {})
        
        title = article_info.get("title", "Unknown Title")
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
        
        print(f"✅ Found Open Access article: {title}")
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "pubmed_advanced",
            "pmc_id": pmc_id
        }
        
    except requests.exceptions.Timeout:
        print("❌ PMC API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ PMC request error: {e}")
        return None
    except Exception as e:
        print(f"❌ PubMed Advanced search error: {e}")
        return None
