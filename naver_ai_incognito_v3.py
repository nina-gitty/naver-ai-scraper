import requests
import re
import time
import random
import csv
import json
from datetime import datetime

class NaverAiV3:
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
        
        # 완전한 인코그니토 세션 생성
        with requests.Session() as session:
            try:
                # [Step 1] 메인 검색 페이지 접속 (토큰 및 API URL 추출용)
                params = {"where": "nexearch", "query": keyword}
                resp = session.get(self.base_url, params=params, headers=self.headers, timeout=10)
                html = resp.text

                # AI 브리핑 존재 여부 확인 (Runtime 패턴 포함)
                if '"templateId":"aibAnswer' not in html:
                    return results
                
                results["exposed"] = "✅"

                # [Step 2] API 호출을 위한 핵심 파라미터 추출
                api_url_match = re.search(r'"apiURL":\s*"(https://aib-api\.naver\.com/[^"]+)"', html)
                token_match = re.search(r'"X-NX-Query-Info":\s*"([^"]+)"', html)

                if api_url_match and token_match:
                    api_url = api_url_match.group(1).replace(r'\/', '/')
                    token = token_match.group(1)
                    
                    # API 전용 헤더 구성
                    api_headers = self.headers.copy()
                    api_headers.update({
                        "authority": "aib-api.naver.com",
                        "accept": "application/json, text/plain, */*",
                        "x-nx-query-info": token,
                        "referer": resp.url
                    })

                    # [Step 3] 실제 AI 답변 데이터(JSON) 요청
                    api_resp = session.get(api_url, headers=api_headers, timeout=10)
                    if api_resp.status_code == 200:
                        api_data = api_resp.json()
                        data_str = json.dumps(api_data)
                        
                        # JSON 내 모든 URL 패턴 추출
                        found_urls = re.findall(r'"url":"(https?://[^"]+)"', data_str)
                        
                        clean_urls = set()
                        for u in found_urls:
                            u_clean = u.replace(r'\/', '/')
                            if "cr.naver.com" not in u_clean and "ad.naver.com" not in u_clean:
                                clean_urls.add(u_clean)
                        
                        results["urls"] = sorted(list(clean_urls))
                
                return results

            except Exception as e:
                return results

    def run(self, keywords):
        print(f"\n🚀 [Naver AI Briefing Scraper v3 - Deep Extraction Mode]")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        final_results = []
        for idx, kw in enumerate(keywords):
            kw = kw.strip()
            print(f" 🔎 [{idx+1}/{len(keywords)}] '{kw}' 정밀 분석 중...", end="\r")
            
            res = self.scrape(kw)
            final_results.append(res)
            
            time.sleep(random.uniform(2.0, 3.5))

        print("\n\n" + "━"*85)
        print(f"{'키워드':<18} | {'AI 노출':<5} | {'출처수':<5} | {'참고 URL 목록'}")
        print("─"*85)
        for r in final_results:
            url_display = r['urls'][0] if r['urls'] else "-"
            print(f"{r['keyword']:<18} | {r['exposed']:^8} | {len(r['urls']):^8} | {url_display}")
            if len(r['urls']) > 1:
                for sub_url in r['urls'][1:2]: # 한 개만 더 출력
                    print(f"{'':<18} | {'':^8} | {'':^8} | {sub_url}")
        
        self.save_csv(final_results)

    def save_csv(self, results):
        fname = f"naver_ai_v3_{datetime.now().strftime('%m%d_%H%M')}.csv"
        with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'Exposed', 'SourceCount', 'URLs'])
            for r in results:
                writer.writerow([r['keyword'], r['exposed'], len(r['urls']), ", ".join(r['urls'])])
        print(f"\n💾 [정밀 수집 완료] {fname}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
    else:
        raw_input = "네이버 크롤링, 네이버 ai브리핑, 강남역 맛집, 대한민국 16대 대통령, 홈캠 추천"
    
    keywords = raw_input.split(",")
    scraper = NaverAiV3()
    scraper.run(keywords)
