import requests
import re
import time
import random
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from typing import List

app = FastAPI()

# 프론트엔드 통신을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NaverAiPrecision:
    def __init__(self):
        self.base_url = "https://search.naver.com/search.naver"
        self.headers = {
            "authority": "search.naver.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
        }

    def scrape_single(self, keyword: str):
        with requests.Session() as session:
            try:
                params = {"where": "nexearch", "query": keyword}
                resp = session.get(self.base_url, params=params, headers=self.headers, timeout=10)
                html = resp.text

                exposed = '"templateId":"aibAnswer' in html
                urls = []

                if exposed:
                    api_url_match = re.search(r'"apiURL":\s*"(https://aib-api\.naver\.com/[^"]+)"', html)
                    token_match = re.search(r'"X-NX-Query-Info":\s*"([^"]+)"', html)

                    all_found_urls = []
                    if api_url_match and token_match:
                        api_url = api_url_match.group(1).replace(r'\/', '/')
                        api_headers = self.headers.copy()
                        api_headers.update({
                            "authority": "aib-api.naver.com",
                            "x-nx-query-info": token_match.group(1),
                            "referer": resp.url
                        })
                        api_resp = session.get(api_url, headers=api_headers, timeout=10)
                        if api_resp.status_code == 200:
                            all_found_urls += re.findall(r'"url":"(https?://[^"]+)"', api_resp.text)

                    all_found_urls += re.findall(r'"url":"(https?://[^"]+)"', html)
                    
                    clean_urls = set()
                    for u in all_found_urls:
                        u_clean = u.replace(r'\/', '/')
                        valid_domains = ["premium.naver.com", "blog.naver", "cafe.naver", "namu.wiki", "news.naver", "kin.naver"]
                        if any(d in u_clean for d in valid_domains):
                            clean_urls.add(u_clean.split('?')[0])
                    urls = sorted(list(clean_urls))

                return {"keyword": keyword, "exposed": exposed, "urls": urls}
            except Exception:
                return {"keyword": keyword, "exposed": False, "urls": []}

@app.get("/api/scrape/stream")
async def stream_scrape(request: Request, keywords: str):
    scraper = NaverAiPrecision()
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

    async def event_generator():
        for kw in keyword_list:
            # 클라이언트 연결 끊김 확인
            if await request.is_disconnected():
                break

            result = scraper.scrape_single(kw)
            yield {
                "event": "message",
                "data": json.dumps(result)
            }
            # 요청 간 딜레이
            time.sleep(random.uniform(1.0, 2.0))

        yield {"event": "done", "data": "finished"}

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
