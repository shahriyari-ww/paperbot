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