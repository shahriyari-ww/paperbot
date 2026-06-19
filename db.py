from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_cached(query: str):
    result = supabase.table("papers").select("*").eq("query", query).execute()
    if result.data:
        return result.data[0]
    return None

def save_paper(query, title, file_id, source):
    supabase.table("papers").insert({
        "query": query,
        "title": title,
        "file_id": file_id,
        "source": source
    }).execute()