import requests
import re
import time
import random
import json
import csv
from datetime import datetime
from urllib.parse import unquote

class NaverAiV2:
    def __init__(self):
        self.base_url = "https://search.naver.com/search.naver"
        # 보내주신 소스 코드의 실제 헤더와 100% 일치시킴
        self.headers = {
            "authority": "search.naver.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "upgrade-insecure-requests": "1"
        }

    def fetch(self, keyword):
        """매 요청마다 세션을 새로 생성하여 완전한 인코그니토 상태를 유지합니다."""
        params = {"where": "nexearch", "query": keyword, "sm": "top_hty"}
        with requests.Session() as session:
            try:
                # 쿠키를 아예 보내지 않음 (완전 시크릿 모드)
                resp = session.get(self.base_url, params=params, headers=self.headers, timeout=10)
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                print(f"\n❌ [Network Error] {keyword}: {e}")
                return None

    def parse_ai_data(self, html):
        """Fender 렌더러 기반의 JSON 블록에서 출처 URL을 정밀 추출합니다."""
        if not html: return False, []

        # 1. AI 브리핑 존재 여부 체크 (aibAnswer 또는 aibAnswerRuntime)
        if not re.search(r'"templateId":"aibAnswer(Runtime)?"', html):
            return False, []

        # 2. JSON 데이터 블록 추출 (Fender bootstrap 패턴)
        try:
            # 이스케이프된 URL 패턴 https:\/\/... 추출
            pattern = r'"url":"(https?:\\\/\\\/[^"]+)"'
            raw_urls = re.findall(pattern, html)
            
            # 3. URL 정제 (중복 제거 및 이스케이프 해제)
            clean_urls = set()
            for url in raw_urls:
                u = url.replace(r'\/', '/')
                # 수집된 URL 중 실제 외부 링크인 경우만 저장 (필터링)
                if "cr.naver.com" not in u and "https" in u:
                    clean_urls.add(u)
            
            return True, sorted(list(clean_urls))
        except Exception:
            return True, []

    def run(self, keywords):
        print(f"\n🚀 [Naver AI Briefing Scraper v2 - Incognito Mode]")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        results = []
        for idx, kw in enumerate(keywords):
            kw = kw.strip()
            if not kw: continue
            
            print(f" 🔎 [{idx+1}/{len(keywords)}] '{kw}' 분석 중...", end="\r")
            
            html = self.fetch(kw)
            is_exposed, urls = self.parse_ai_data(html)
            
            results.append({
                "keyword": kw,
                "exposed": "✅" if is_exposed else "❌",
                "count": len(urls),
                "urls": urls
            })
            
            time.sleep(random.uniform(1.8, 3.2))

        print("\n\n" + "━"*75)
        print(f"{'키워드':<18} | {'AI 노출':<5} | {'출처수':<5} | {'대표 출처 URL'}")
        print("─"*75)
        for r in results:
            first_url = r['urls'][0] if r['urls'] else "-"
            print(f"{r['keyword']:<18} | {r['exposed']:^8} | {r['count']:^8} | {first_url}")
            if len(r['urls']) > 1:
                print(f"{'':<18} | {'':^8} | {'':^8} | {r['urls'][1]}")

        self.save_csv(results)

    def save_csv(self, results):
        fname = f"naver_ai_{datetime.now().strftime('%m%d_%H%M')}.csv"
        with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'Exposed', 'SourceCount', 'URLs'])
            for r in results:
                writer.writerow([r['keyword'], r['exposed'], r['count'], ", ".join(r['urls'])])
        print(f"\n💾 [저장 완료] {fname}")

if __name__ == "__main__":
    import sys
    # 인자가 있으면 인자를 사용하고, 없으면 input을 받음 (테스트 자동화를 위함)
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
    else:
        raw_input = input("⌨️  검색 키워드 (쉼표 구분): ")
    
    keywords = raw_input.split(",")
    scraper = NaverAiV2()
    scraper.run(keywords)
