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

#병렬처리 (M4 터보: 10개 동시 실행)
MAX_CONCURRENT_TASKS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

class NaverAiUltimate:
    def __init__(self):
        self.base_url = "https://search.naver.com/search.naver"
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

    async def scrape_and_capture(self, keyword, target_keywords, filename, browser):
        """병렬 실행을 위한 개별 키워드 분석 로직"""
        async with semaphore:
            print(f"🚀 [{keyword}] 분석 시작...")
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 2000},
                user_agent=self.user_agent
            )
            
            async with context:
                page = await context.new_page()
                url = f"{self.base_url}?where=nexearch&query={keyword}"
                
                found_data = []
                seen_pairs = set()
                is_exposed = False
                matched_targets = []
                full_text = ""

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(5)
                    
                    aib_container = await page.query_selector('[data-block-id*="ai-briefing"]')
                    aib_header = await page.query_selector(".fds-aib-header-container")
                    
                    is_actually_exposed = False
                    if aib_container and aib_header:
                        header_text = await aib_header.inner_text()
                        if "AI 브리핑" in header_text:
                            is_actually_exposed = True
                    
                    if is_actually_exposed:
                        is_exposed = True
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

                        # 링크 수집
                        multimedia_items = await aib_container.query_selector_all('.fds-multimedia-item a')
                        for link in multimedia_items:
                            href = await link.get_attribute("href")
                            if href and href.startswith("http"):
                                u_clean = href.split('?')[0].split('#')[0]
                                pair = (u_clean, "상단 캐러셀")
                                if pair not in seen_pairs:
                                    seen_pairs.add(pair)
                                    found_data.append({"url": u_clean, "location": "상단 캐러셀"})

                        source_panel = await page.query_selector('.fds-aib-multi-source-scroll-area')
                        if source_panel:
                            panel_links = await source_panel.query_selector_all('a')
                            for link in panel_links:
                                href = await link.get_attribute("href")
                                if href and href.startswith("http"):
                                    u_clean = href.split('?')[0].split('#')[0]
                                    pair = (u_clean, "출처 패널")
                                    if pair not in seen_pairs:
                                        seen_pairs.add(pair)
                                        found_data.append({"url": u_clean, "location": "출처 패널"})
                    
                    save_path = os.path.join(SCREENSHOT_DIR, filename)
                    await page.screenshot(path=save_path)
                    print(f"✅ [{keyword}] 분석 완료")
                    return is_exposed, found_data, filename, matched_targets
                except Exception as e:
                    print(f"  ❌ [{keyword}] 오류: {e}")
                    return False, [], None, []

@app.get("/")
async def root():
    return {"status": "ok", "message": "Naver AI Briefing Scraper v2.1 (Turbo + Stop Support) is running"}

@app.get("/api/scrape/stream")
async def stream_scrape(request: Request, keywords: str, targets: str = ""):
    host = request.url.hostname
    port = request.url.port or 8000
    base_url = f"http://{host}:{port}"
    
    scraper = NaverAiUltimate()
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    target_list = [t.strip() for t in targets.split(",") if t.strip()]
    total_count = len(keyword_list)

    async def event_generator():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # 작업을 태스크 리스트로 관리
            tasks = []
            for idx, kw in enumerate(keyword_list):
                img_filename = f"final_{int(time.time())}_{idx}.png"
                # asyncio.create_task를 사용하여 개별 작업을 비동기로 실행
                task = asyncio.create_task(scraper.scrape_and_capture(kw, target_list, img_filename, browser))
                tasks.append((kw, task))

            completed_count = 0
            try:
                # 모든 태스크가 완료될 때까지 기다리되, 연결 끊김을 실시간 감시
                while completed_count < total_count:
                    if await request.is_disconnected():
                        print("⏹ 클라이언트 연결 종료 감지. 모든 작업 취소 중...")
                        for _, t in tasks:
                            if not t.done(): t.cancel()
                        break

                    # 완료된 태스크 확인
                    for i in range(len(tasks)):
                        kw, task = tasks[i]
                        if task and task.done() and not task.cancelled():
                            try:
                                exposed, source_data, filename, matched = await task
                                completed_count += 1
                                tasks[i] = (kw, None) # 완료된 태스크는 비움

                                img_url = f"{base_url}/screenshots/{filename}" if filename else None
                                result = {
                                    "keyword": kw,
                                    "exposed": exposed,
                                    "sources": source_data,
                                    "screenshotUrl": img_url,
                                    "matchedKeywords": matched,
                                    "allTargetKeywords": target_list,
                                    "currentIndex": completed_count,
                                    "totalCount": total_count
                                }
                                yield {"event": "message", "data": json.dumps(result)}
                            except Exception as e:
                                print(f"Error processing task result: {e}")
                                completed_count += 1
                                tasks[i] = (kw, None)

                    await asyncio.sleep(0.5) # 감시 루프 딜레이
            finally:
                # 안전하게 브라우저 닫기
                await browser.close()
                print("🏁 브라우저 리소스 정리 완료")

            yield {"event": "done", "data": "finished"}

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
