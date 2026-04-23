import asyncio
import requests
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def deep_diagnostic():
    # 1. 실제 외부 IP 확인
    try:
        current_ip = requests.get("https://api.ipify.org").text
        print(f"🌍 Current Public IP: {current_ip}")
    except:
        print("❌ Could not determine public IP")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 새로운 컨텍스트 생성 (이전 세션 영향 제거)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            extra_http_headers={
                "Referer": "https://www.naver.com/",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8"
            }
        )
        page = await context.new_page()
        # 정확한 스텔스 호출 방식 (v2.x 기준)
        await Stealth().apply_stealth_async(page)

        # 2. Stealth 성공 여부 체크 (기본적인 봇 감지 우회 확인)
        await page.goto("https://bot.sannysoft.com/")
        await asyncio.sleep(3)
        webdriver_status = await page.evaluate("() => navigator.webdriver")
        print(f"🛡️ Stealth Check (navigator.webdriver): {'FAILED (True)' if webdriver_status else 'PASSED (False)'}")

        # 3. 네이버 접속 테스트
        keyword = "강남역 맛집"
        url = f"https://search.naver.com/search.naver?where=nexearch&query={keyword}"
        print(f"🔍 Testing Naver: {url}")
        
        try:
            resp = await page.goto(url, timeout=30000)
            await asyncio.sleep(5)
            
            content = await page.content()
            title = await page.title()
            print(f"📄 Page Title: {title}")

            if "ip_ban" in content or "비정상적인 접근" in content:
                print("🚨 STILL BLOCKED: Naver identified this request as a bot.")
            elif await page.query_selector('[data-block-id*="ai-briefing"]'):
                print("✅ SUCCESS: AI Briefing found!")
            else:
                print("⚠️ UNDETERMINED: No block detected, but no AI Briefing found either.")

            await page.screenshot(path="deep_diagnostic.png")
            print("📸 Diagnostic screenshot saved: 'deep_diagnostic.png'")

        except Exception as e:
            print(f"❌ Navigation Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(deep_diagnostic())
