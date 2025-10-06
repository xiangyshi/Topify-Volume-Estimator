from enum import Enum

class Endpoints(Enum):
    BASE_URL = "https://api.dataforseo.com/v3"

    # post_data[len(post_data)] = dict(
    #     language_name="English",
    #     location_code=2840,
    #     keywords=[
    #         "iphone",
    #         "seo"
    #     ]
    # )

    AI_KEYWORD_SEARCH_VOLUME = "ai_optimization/ai_keyword_data/keywords_search_volume/live"

    # login="login" 
    # password="password" 
    # cred="$(printf ${login}:${password} | base64)" 
    # curl --location --request POST 'https://api.dataforseo.com/v3/serp/google/organic/task_post' \
    # --header "Authorization: Basic ${cred}"  \
    # --header "Content-Type: application/json" \
    # --data-raw '[
    #     {
    #         "language_code": "en",
    #         "location_code": 2840,
    #         "keyword": "albert einstein"
    #     }
    # ]'
    
    SERP_GOOGLE_ORGANIC_LIVE_ADVANCED = "serp/google/organic/live/advanced"

    #
    #  payload=[
    #    {
    #       "keywords":["long-form video"], 
    #       "location_code":2840, 
    #       "language_code":"en", 
    #       "sort_by":"relevance"
    #    }
    # ]

    KEYWORD_SEARCH_VOLUME = "keywords_data/google_ads/search_volume/live"