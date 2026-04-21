import requests
import re
import time
import random
import json
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from playwright.async_api import async_playwright

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "static", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")

class NaverAiUltimate:
    def __init__(self):
        self.base_url = "https://search.naver.com/search.naver"
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

    async def scrape_and_capture(self, keyword, target_keywords, filename):
        print(f"🚀 [{keyword}] 초정밀 분석 시작...")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 2000},
                    user_agent=self.user_agent
                )
                page = await context.new_page()
                url = f"{self.base_url}?where=nexearch&query={keyword}"
                
                found_data = []
                seen_urls = set()
                is_exposed = False
                matched_targets = []
                full_text = ""

                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)
                
                # [속성 기반 단순화 판정 v32]
                # data-block-id 속성에 'ai-briefing'이 포함된 요소가 있으면 진짜 AI 브리핑으로 간주합니다.
                aib_container = await page.query_selector('[data-block-id*="ai-briefing"]')
                
                if aib_container:
                    is_exposed = True
                    print(f"  > [Confirmed] AI 브리핑(data-block-id) 감지됨")
                    
                    # 1. 내용 확장
                    expand_btn = await aib_container.query_selector('button:has-text("더보기"), .fds-aib-expand-button, .more')
                    if expand_btn:
                        await expand_btn.click(force=True)
                        await asyncio.sleep(5)

                    text_elements = await aib_container.query_selector_all('.fds-markdown-p')
                    for el in text_elements:
                        full_text += await el.inner_text()
                    
                    for tk in target_keywords:
                        if tk and tk.lower() in full_text.lower():
                            matched_targets.append(tk)

                    source_btn = await aib_container.query_selector('button:has-text("전체보기"), button:has-text("출처")')
                    if source_btn:
                        await source_btn.click(force=True)
                        await asyncio.sleep(3)

                    # 링크 수집 (상단 캐러셀 + 출처 패널)
                    multimedia_items = await aib_container.query_selector_all('.fds-multimedia-item a')
                    for link in multimedia_items:
                        href = await link.get_attribute("href")
                        if href and href.startswith("http"):
                            u_clean = href.split('?')[0].split('#')[0]
                            if u_clean not in seen_urls:
                                seen_urls.add(u_clean)
                                found_data.append({"url": u_clean, "location": "상단 캐러셀"})

                    source_panel = await page.query_selector('.fds-aib-multi-source-scroll-area')
                    if source_panel:
                        panel_links = await source_panel.query_selector_all('a')
                        for link in panel_links:
                            href = await link.get_attribute("href")
                            if href and href.startswith("http"):
                                u_clean = href.split('?')[0].split('#')[0]
                                if u_clean not in seen_urls:
                                    seen_urls.add(u_clean)
                                    found_data.append({"url": u_clean, "location": "출처 패널"})
                else:
                    print(f"  > [{keyword}] 광고 블록 또는 미노출 (판정 제외 완료)")
                
                save_path = os.path.join(SCREENSHOT_DIR, filename)
                await page.screenshot(path=save_path)
                await browser.close()
                return is_exposed, found_data, filename, matched_targets
            except Exception as e:
                print(f"  ❌ 오류 발생: {e}")
                return False, [], None, []

@app.get("/")
async def root():
    return {"status": "ok", "message": "v31 Attribute-based Strict Version is running"}

@app.get("/api/scrape/stream")
async def stream_scrape(request: Request, keywords: str, targets: str = ""):
    host = request.url.hostname
    port = request.url.port or 8000
    base_url = f"http://{host}:{port}"
    scraper = NaverAiUltimate()
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    target_list = [t.strip() for t in targets.split(",") if t.strip()]
    
    async def event_generator():
        for idx, kw in enumerate(keyword_list):
            if await request.is_disconnected(): break
            img_filename = f"final_{int(time.time())}_{idx}.png"
            exposed, source_data, filename, matched = await scraper.scrape_and_capture(kw, target_list, img_filename)
            img_url = f"{base_url}/screenshots/{filename}" if filename else None
            result = {
                "keyword": kw,
                "exposed": exposed,
                "sources": source_data,
                "screenshotUrl": img_url,
                "matchedKeywords": matched,
                "allTargetKeywords": target_list,
                "currentIndex": idx + 1,
                "totalCount": len(keyword_list)
            }
            yield {"event": "message", "data": json.dumps(result)}
            await asyncio.sleep(1)
        yield {"event": "done", "data": "finished"}
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
