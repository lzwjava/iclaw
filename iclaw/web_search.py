from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document

from iclaw import http

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def search_ddg(query, num_results=10):
    """Using DuckDuckGo's html version which is easier to scrape"""
    url = f"https://html.duckduckgo.com/html/?q={query}"

    try:
        res = http.get_session().get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"[web search] Error searching DDG: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    results = []

    for item in soup.select(".result__title .result__a"):
        href = item["href"]
        if href.startswith("//"):
            href = "https:" + href

        if "duckduckgo.com/l/?uddg=" in href:
            parsed = urlparse(href)
            query_params = parse_qs(parsed.query)
            if "uddg" in query_params:
                href = query_params["uddg"][0]

        results.append({"title": item.text.strip(), "url": href})

    return results[:num_results]


def search_startpage(query, num_results=20):
    """Using Startpage search"""
    url = "https://www.startpage.com/sp/search"
    params = {
        "query": query,
        "cat": "web",
        "language": "english",
    }

    try:
        res = http.get_session().get(url, params=params, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"[web search] Error searching Startpage: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    results = []

    search_items = soup.select(".result")

    for item in search_items:
        link_tag = item.select_one("a.result-link")
        title_tag = item.select_one(".wgl-title")

        if link_tag and link_tag.has_attr("href") and title_tag:
            href = link_tag["href"]
            title = title_tag.get_text(strip=True)
            # Ensure it's an external link
            if isinstance(href, str) and href.startswith("http"):
                results.append({"title": title, "url": href})

    return results[:num_results]


def search_bing(query, num_results=20):
    """Using Bing's search which is a good alternative"""
    # Use international URL and parameters to bypass country redirection
    url = f"https://www.bing.com/search?q={query}&setmkt=en-US&setlang=en-US&cc=US"

    try:
        shared = http.get_session()
        session = requests.Session()
        session.proxies = dict(shared.proxies)
        session.verify = shared.verify
        session.cookies.set("SRCHHPGUSR", "SRCHLANG=EN&WLS=2", domain=".bing.com")
        session.cookies.set("_EDGE_S", "mkt=en-us", domain=".bing.com")

        res = session.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"[web search] Error searching Bing: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    results = []

    for item in soup.select("li.b_algo"):
        title_link = item.select_one("h2 a")
        if not title_link:
            continue

        href = title_link["href"]
        if href.startswith("//"):
            href = "https:" + href

        results.append({"title": title_link.text.strip(), "url": href})

    return results[:num_results]


def extract_text_from_url(url):
    try:
        res = http.get_session().get(url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding

        if res.status_code != 200:
            return f"Error: Received status code {res.status_code}"

        soup = BeautifulSoup(res.text, "html.parser")

        # Remove irrelevant elements
        for element in soup(
            ["script", "style", "header", "footer", "nav", "aside", "form"]
        ):
            element.decompose()

        content_blocks = []

        # Site-specific selectors
        if "zhihu.com" in url:
            targets = soup.select(
                ".QuestionHeader-title, .RichContent-inner, .Post-RichTextContainer"
            )
        elif "zhidao.baidu.com" in url:
            targets = soup.select(
                ".wgt-best-mask, .wgt-best-content, .wgt-answers, .line.content, .best-text"
            )
        elif "wikipedia.org" in url:
            targets = soup.select("#firstHeading, .mw-parser-output p")
        elif "github.com" in url:
            targets = soup.select(".repository-content, article.markdown-body")
        else:
            # Generic extraction using readability-lxml
            try:
                doc = Document(res.text)
                summary_html = doc.summary()
                if summary_html:
                    summary_soup = BeautifulSoup(summary_html, "html.parser")
                    text = summary_soup.get_text(separator=" ", strip=True)
                    if len(text) > 100:  # Ensure it extracted meaningful content
                        return text
            except Exception:
                pass

            # Fallback to generic heuristics
            targets = soup.select("article, main, .main-content, #content, .content")
            if not targets:
                targets = [soup.find("body")]

        for t in targets:
            if t:
                text = t.get_text(separator=" ", strip=True)
                if text:
                    content_blocks.append(text)

        if content_blocks:
            full_text = "\n\n".join(content_blocks)
            return full_text[:3000]  # Truncate for LLM window

        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Error fetching {url}: {e}"


def format_llm_output(results):
    """Formats findings into a structured, LLM-friendly Markdown format."""
    blocks = []
    for i, res in enumerate(results):
        block = (
            f"### Source {i + 1}\n"
            f"**Title:** {res['title']}\n"
            f"**URL:** {res['url']}\n\n"
            f"**Content:**\n{res.get('content', 'No content extracted.')}\n"
            f"{'-' * 40}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def search_tavily(query, num_results=5):
    """Using Tavily API for search"""
    import os

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("[web search] Error: TAVILY_API_KEY not set.")
        return []

    from tavily import TavilyClient

    try:
        client = TavilyClient(api_key=api_key)
        # Tavily's search already includes content/context if requested
        response = client.search(
            query, search_depth="advanced", max_results=num_results
        )

        results = []
        for res in response.get("results", []):
            results.append(
                {
                    "title": res.get("title", "No Title"),
                    "url": res.get("url"),
                    "content": res.get("content", "No content available."),
                }
            )
        return results
    except Exception as e:
        print(f"[web search] Error searching Tavily: {e}")
        return []


def web_search(query, num_results=5, provider="duckduckgo"):
    """Function to be called as a tool."""
    print(f"[web search] Searching ({provider}): {query}")

    if provider == "tavily":
        search_results = search_tavily(query, num_results=num_results)
        if not search_results:
            return "No results found."
        return format_llm_output(search_results)

    if provider == "startpage":
        search_results = search_startpage(query, num_results=num_results)
    elif provider == "bing":
        search_results = search_bing(query, num_results=num_results)
    else:
        search_results = search_ddg(query, num_results=num_results)

    processed_results = []

    if not search_results:
        return "No results found."

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_info = {
            executor.submit(extract_text_from_url, r["url"]): r for r in search_results
        }

        for future in as_completed(future_to_info):
            info = future_to_info[future]
            try:
                content = future.result()
                processed_results.append({**info, "content": content})
                print(f"[web search] Fetched: {info['url']}")
            except Exception:
                processed_results.append(
                    {**info, "content": "Failed to extract content."}
                )

    # Sort results to match original search order
    url_order = {res["url"]: i for i, res in enumerate(search_results)}
    processed_results.sort(key=lambda x: url_order.get(x["url"], 999))

    return format_llm_output(processed_results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimized DDG Search & Extract for LLMs."
    )
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "-n",
        "--num_results",
        type=int,
        default=5,
        help="Number of results (default: 5)",
    )
    args = parser.parse_args()

    print(web_search(args.query, num_results=args.num_results))
