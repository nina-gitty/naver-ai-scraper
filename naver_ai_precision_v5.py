import requests
import re
import time
import random
import csv
import json
from datetime import datetime

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

    def scrape(self, keyword):
        results = {"keyword": keyword, "exposed": "❌", "urls": []}
        with requests.Session() as session:
            try:
                # [Step 1] 메인 페이지 요청
                params = {"where": "nexearch", "query": keyword}
                resp = session.get(self.base_url, params=params, headers=self.headers, timeout=10)
                html = resp.text

                # AI 브리핑 존재 여부 확인
                if '"templateId":"aibAnswer' not in html:
                    return results
                
                results["exposed"] = "✅"

                # [Step 2] AI 출처 URL 정밀 수집
                all_found_urls = []

                # 1. 비동기 데이터(Runtime)용 토큰/URL 추출 및 호출
                api_url_match = re.search(r'"apiURL":\s*"(https://aib-api\.naver\.com/[^"]+)"', html)
                token_match = re.search(r'"X-NX-Query-Info":\s*"([^"]+)"', html)

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
                        # API 결과에서 URL 추출
                        all_found_urls += re.findall(r'"url":"(https?://[^"]+)"', api_resp.text)

                # 2. HTML 내에 이미 구워져 있는 출처 데이터(Hydrated) 추출
                # 'fds-source-overlay-item' 관련 JSON 데이터 타격
                all_found_urls += re.findall(r'"url":"(https?://[^"]+)"', html)

                # [Step 3] 데이터 정제 및 필터링
                clean_urls = set()
                for url in all_found_urls:
                    u = url.replace(r'\/', '/')
                    # 유효 도메인 체크 (사용자 지정 도메인 포함)
                    valid_domains = ["premium.naver.com", "blog.naver", "cafe.naver", "namu.wiki", "news.naver", "kin.naver"]
                    if any(d in u for d in valid_domains):
                        # 추적 파라미터 제거
                        clean_url = u.split('?')[0]
                        clean_urls.add(clean_url)
                
                results["urls"] = sorted(list(clean_urls))
                return results

            except Exception:
                return results

    def run(self, keywords):
        print(f"\n🚀 [Naver AI Scraper v5 - Precision Mode]")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        final_results = []
        for idx, kw in enumerate(keywords):
            kw = kw.strip()
            print(f" 🔎 [{idx+1}/{len(keywords)}] '{kw}' 정밀 분석 중...", end="\r")
            
            res = self.scrape(kw)
            final_results.append(res)
            
            time.sleep(random.uniform(1.8, 3.2))

        print("\n\n" + "━"*85)
        print(f"{'키워드':<18} | {'AI 노출':<5} | {'출처수':<5} | {'수집된 원본 출처 URL'}")
        print("─"*85)
        for r in final_results:
            url_list = r['urls']
            # 프리미엄 콘텐츠 우선순위 배정
            premium = [u for u in url_list if "premium" in u]
            others = [u for u in url_list if "premium" not in u]
            sorted_urls = premium + others
            
            first_url = sorted_urls[0] if sorted_urls else "-"
            print(f"{r['keyword']:<18} | {r['exposed']:^8} | {len(r['urls']):^8} | {first_url}")
            if len(sorted_urls) > 1:
                print(f"{'':<18} | {'':^8} | {'':^8} | {sorted_urls[1]}")

        self.save_csv(final_results)

    def save_csv(self, results):
        fname = f"naver_ai_precision_{datetime.now().strftime('%m%d_%H%M')}.csv"
        with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'AI_Exposed', 'SourceCount', 'URLs'])
            for r in results:
                writer.writerow([r['keyword'], r['exposed'], len(r['urls']), "\n".join(r['urls'])])
        print(f"\n💾 [정밀 수집 완료] {fname}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
    else:
        raw_input = "네이버 크롤링, 네이버 ai브리핑, 강남역 맛집, 대한민국 16대 대통령, 홈캠 추천"
    
    keywords = raw_input.split(",")
    scraper = NaverAiPrecision()
    scraper.run(keywords)
