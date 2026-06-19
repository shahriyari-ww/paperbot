import requests

def search_pubmed(query):
    try:
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=1&retmode=json"
        search_resp = requests.get(search_url, timeout=30)
        
        if search_resp.status_code != 200:
            return None
        
        search_data = search_resp.json()
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return None
        
        pmid = id_list[0]
        
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        summary_resp = requests.get(summary_url, timeout=30)
        
        if summary_resp.status_code != 200:
            return None
        
        summary_data = summary_resp.json()
        article_info = summary_data.get("result", {}).get(pmid, {})
        title = article_info.get("title", "Unknown Title")
        
        pmc_id = article_info.get("pmcid", "")
        if pmc_id:
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
            return {
                "title": title,
                "pdf_url": pdf_url,
                "source": "pubmed"
            }
        
        return None
        
    except Exception:
        return None


def search_pubmed_advanced(query):
    """
    نسخه پیشرفته جستجوی PubMed با فیلتر Open Access
    """
    try:
        # جستجو در PubMed Central با فیلتر Open Access
        pmc_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pmc&term={query}+AND+open+access[filter]&retmax=1&retmode=json"
        )
        
        pmc_resp = requests.get(pmc_url, timeout=30)
        if pmc_resp.status_code != 200:
            return None
        
        pmc_data = pmc_resp.json()
        id_list = pmc_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return None
        
        pmc_id = id_list[0]
        
        # دریافت اطلاعات مقاله
        summary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            f"?db=pmc&id={pmc_id}&retmode=json"
        )
        
        summary_resp = requests.get(summary_url, timeout=30)
        if summary_resp.status_code != 200:
            return None
        
        summary_data = summary_resp.json()
        article_info = summary_data.get("result", {}).get(pmc_id, {})
        
        title = article_info.get("title", "Unknown Title")
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "pubmed_advanced",
            "pmc_id": pmc_id
        }
        
    except Exception as e:
        print(f"PubMed Advanced search error: {e}")
        return None
