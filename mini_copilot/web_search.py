import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document

DEFAULT_PROXY = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
PROXY = {
    "http": os.environ.get("HTTP_PROXY", DEFAULT_PROXY["http"]),
    "https": os.environ.get("HTTPS_PROXY", DEFAULT_PROXY["https"]),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def search_ddg(query, num_results=10):
    url = f"https://html.duckduckgo.com/html/?q={query}"
    try:
        res = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"[web search] DDG error: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select(".result__title .result__a"):
        href = item["href"]
        if href.startswith("//"):
            href = "https:" + href
        if "duckduckgo.com/l/?uddg=" in href:
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            if "uddg" in params:
                href = params["uddg"][0]
        results.append({"title": item.text.strip(), "url": href})
    return results[:num_results]


def extract_text_from_url(url):
    try:
        session = requests.Session()
        res = session.get(url, headers=HEADERS, proxies=PROXY, timeout=15)
        res.encoding = res.apparent_encoding
        if res.status_code != 200:
            return f"Error: status {res.status_code}"

        soup = BeautifulSoup(res.text, "html.parser")
        for el in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            el.decompose()

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
            try:
                doc = Document(res.text)
                summary_html = doc.summary()
                if summary_html:
                    text = BeautifulSoup(summary_html, "html.parser").get_text(
                        separator=" ", strip=True
                    )
                    if len(text) > 100:
                        return text
            except Exception:
                pass
            targets = soup.select("article, main, .main-content, #content, .content")
            if not targets:
                targets = [soup.find("body")]

        blocks = [t.get_text(separator=" ", strip=True) for t in targets if t]
        return "\n\n".join(b for b in blocks if b) or soup.get_text(
            separator=" ", strip=True
        )
    except Exception as e:
        return f"Error fetching {url}: {e}"


def web_search(query, num_results=5):
    """Search DDG and extract content. Returns formatted string for LLM context."""
    print(f"[web search] Searching: {query}")
    search_results = search_ddg(query, num_results=num_results)
    if not search_results:
        return "No web search results found."

    processed = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_info = {
            executor.submit(extract_text_from_url, r["url"]): r for r in search_results
        }
        for future in as_completed(future_to_info):
            info = future_to_info[future]
            try:
                content = future.result()
            except Exception as e:
                content = f"Error: {e}"
            processed.append({**info, "content": content})
            print(f"[web search] Fetched: {info['url']}")

    url_order = {r["url"]: i for i, r in enumerate(search_results)}
    processed.sort(key=lambda x: url_order.get(x["url"], 999))

    blocks = []
    for i, r in enumerate(processed):
        content = r.get("content", "").strip()
        # Truncate very long content to avoid flooding context
        if len(content) > 2000:
            content = content[:2000] + "...[truncated]"
        blocks.append(
            f"### Source {i + 1}\n**Title:** {r['title']}\n**URL:** {r['url']}\n\n**Content:**\n{content}\n"
            + "-" * 40
        )
    return "\n\n".join(blocks)
