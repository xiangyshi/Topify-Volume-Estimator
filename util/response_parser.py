import json
import pandas as pd

def parse_ai_keyword_volume(task_result, endpoint):
    keyword, volume = [], []
    
    # Check if task failed
    if task_result.get("status_code") != 20000:
        print(f"Warning: AI keyword search volume task failed with status {task_result.get('status_code')}: {task_result.get('status_message')}")
        return keyword, volume
    
    for result in task_result.get("result", []):
        for item in result.get("items", []):
            keyword.append(item["keyword"])
            volume.append(item["ai_search_volume"])
    return keyword, volume

def parse_serp_organic(task_result, endpoint=None):
    """
    Parse SERP task result, keeping only organic results.
    Returns a DataFrame with rank, page, position, domain, title, description, and text_for_semantics.
    """
    records = []
    domains_in_people_also_ask = []
    
    # Check if task failed
    if task_result.get("status_code") != 20000:
        print(f"Warning: SERP task failed with status {task_result.get('status_code')}: {task_result.get('status_message')}")
        return pd.DataFrame()
    
    for result in task_result.get("result", []):
        for item in result.get("items", []):
            if item.get("type") == "organic":
                title = item.get("title", "")
                description = item.get("description", "")
                text_for_semantics = f"{title} {description}".strip()
                records.append({
                    "rank_absolute": item.get("rank_absolute"),
                    "page": item.get("page"),
                    "domain": item.get("domain"),
                    "title": title,
                    "description": description,
                    "text_for_semantics": text_for_semantics,
                    "is_featured_snippet": item.get("is_featured_snippet"),
                })
            if item.get("type") == "people_also_ask":
                for item in item.get("items", []):
                    for expanded_item in item.get("expanded_element", []):
                        domains_in_people_also_ask.append(expanded_item.get("domain"))
    df = pd.DataFrame(records)
    df["in_people_also_ask"] = df["domain"].isin(domains_in_people_also_ask)
    return df

def parse_api_responses(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        responses = json.load(f)

    keyword, volume = [], []
    serp_df = None
    for resp in responses:
        endpoint = resp.get("endpoint")
        data = resp.get("data", {})
        tasks = data.get("tasks", [])
        for task in tasks:
            if endpoint == "ai_keyword_search_volume":
                keyword, volume = parse_ai_keyword_volume(task, endpoint)
            elif endpoint == "serp_google_organic_live_advanced":
                serp_df = parse_serp_organic(task, endpoint)
            elif endpoint == "keyword_search_volume":
                pass

    return {
        "keyword": keyword[0],
        "volume": volume[0],
        "serp_df": serp_df
    }

def parse_api_responses_from_dict(responses):
    """
    Parse API responses from a dictionary/list instead of a file.
    
    Args:
        responses: List of response dictionaries with 'endpoint' and 'data' keys
        
    Returns:
        Dictionary with 'keyword', 'volume', and 'serp_df' keys
    """
    keyword, volume = [], []
    serp_df = None
    
    if not responses:
        return {
            "keyword": None,
            "volume": 0,
            "serp_df": None
        }
    
    for resp in responses:
        if not isinstance(resp, dict):
            continue
            
        endpoint = resp.get("endpoint")
        data = resp.get("data", {})
        tasks = data.get("tasks", [])
        
        for task in tasks:
            if endpoint == "ai_keyword_search_volume":
                keyword, volume = parse_ai_keyword_volume(task, endpoint)
            elif endpoint == "serp_google_organic_live_advanced":
                serp_df = parse_serp_organic(task, endpoint)
            elif endpoint == "keyword_search_volume":
                pass

    return {
        "keyword": keyword[0] if keyword else None,
        "volume": volume[0] if volume else 0,
        "serp_df": serp_df
    }