import requests
from ddgs import DDGS

from app.config import get_secret, log

GITHUB_TOKEN = get_secret("GITHUB_TOKEN")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")


# All three searches return the same kind of list:
#   [{"source": ..., "title": ..., "url": ..., "snippet": ...}, ...]
# Empty list on failure - no crash, so the caller can try another search.

def search_github(query, how_many=3):
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        response = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "per_page": how_many},
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
    except Exception as error:
        print(f"      [github] fail: {error}")
        return []

    return [
        {
            "source": "github",
            "title": item["full_name"],
            "url": item["html_url"],
            "snippet": item.get("description") or "",
        }
        for item in response.json().get("items", [])
    ]


def search_tavily(query, how_many=3):
    if not TAVILY_API_KEY:
        return []

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"query": query, "max_results": how_many},
            headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
            timeout=20,
        )
        response.raise_for_status()
    except Exception as error:
        print(f"      [tavily] fail: {error}")
        return []

    return [
        {
            "source": "tavily",
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        }
        for item in response.json().get("results", [])
    ]


def search_web(query, how_many=3):
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=how_many))
    except Exception as error:
        print(f"      [web] fail: {type(error).__name__} - probably a rate limit")
        return []

    return [
        {
            "source": "web",
            "title": hit.get("title", ""),
            "url": hit.get("href", ""),
            "snippet": hit.get("body", ""),
        }
        for hit in hits
    ]


def make_query(lane, skill, role_summary):
    if lane == "technical":
        # GitHub returns 0 results for a long query, so only the first 3 words.
        #first_three_words + " interview" = Fastapi interview for technical
        return " ".join(skill.split()[:3]) + " interview"

    if lane == "soft":
        return f"{skill} behavioural interview questions software engineer"

    return f"{role_summary} {skill} interview process"


def run_search(lane, query, skill):
    # "a or b" means: if a is an empty list, run b.
    if lane == "technical":
        return search_github(query) or search_web(f"{skill} interview questions")

    if lane == "soft":
        return search_tavily(query) or search_web(query)

    return search_web(query)


def do_research(state, lane):
    round_number = state.get("round", 0)
    role_summary = state.get("role_summary", "")

    skills = [
        req["skill"]
        for req in state.get("requirements", [])
        if req["lane"] == lane
    ]

    # In a retry round search the gaps review reported, not the skills.
    # This is needed to give the missing lanes priority.
    gaps = state.get("missing_by_lane", {}).get(lane, [])
    if gaps:
        skills = gaps

    if not skills and lane == "technical":
        log(lane, "lane is empty - not a single API call")
        return {"evidence": []}

    if not skills:
        log(lane, "lane empty - baseline query")
        skills = ["general interview preparation"]

    evidence = []

    # skills = ["FastAPI", "PostgreSQL"] is how the skills list looks, and it builds a query for each skill.
    for skill in skills:
        query = make_query(lane, skill, role_summary)

        for hit in run_search(lane, query, skill):
            evidence.append({
                "lane": lane,
                "skill": skill,
                "source": hit["source"],
                "title": hit["title"],
                "url": hit["url"],
                "snippet": hit["snippet"][:300],
            })

    log(lane, f"round={round_number} | {len(skills)} search -> {len(evidence)} results")

    return {"evidence": evidence}


def tech_research(state):
    return do_research(state, "technical")


def soft_research(state):
    return do_research(state, "soft")


def general_research(state):
    return do_research(state, "general")
