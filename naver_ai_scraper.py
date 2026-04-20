import requests
import re
import time
import random
import json
import csv
from datetime import datetime

class NaverAIScraper:
    def __init__(self, nid_aut, nid_ses):
        self.base_url = "https://search.naver.com/search.naver"
        self.session = requests.Session()
        
        # 100% 리얼 브라우저 기반 Full Headers 설정
        self.headers = {
            "authority": "search.naver.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }
        
        # 인증 쿠키 설정 (필터 버블 방지용 부계정 권장)
        self.cookies = {
            "NID_AUT": nid_aut,
            "NID_SES": nid_ses
        }

    def fetch_serp(self, keyword):
        """네이버 검색 결과 HTML을 가져옵니다."""
        params = {"where": "nexearch", "query": keyword, "sm": "top_hty", "fbm": "0", "ie": "utf8"}
        try:
            response = self.session.get(
                self.base_url, 
                params=params, 
                headers=self.headers, 
                cookies=self.cookies,
                timeout=10
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  [Error] {keyword} 요청 실패: {e}")
            return None

    def parse_ai_briefing(self, html):
        """HTML 내 script 태그에서 AI 브리핑 데이터를 파싱합니다."""
        if not html:
            return False, []

        # 1. AI 브리핑 노출 여부 확인
        if '"templateId":"aibAnswer"' not in html:
            return False, []

        # 2. URL 추출 (정규표현식 사용)
        # sources 내의 url 필드만 추출. 이스케이프된 슬래시(\/) 포함 패턴
        pattern = r'"url":"(https?:\\\/\\\/[^"]+)"'
        raw_urls = re.findall(pattern, html)
        
        # 3. URL 정제 (중복 제거 및 이스케이프 해제)
        clean_urls = sorted(list(set([url.replace(r'\/', '/') for url in raw_urls])))
        
        return True, clean_urls

    def run(self, keywords):
        results = []
        print(f"\n[🚀 수집 시작] 총 {len(keywords)}개의 키워드 분석 중...")
        
        for idx, kw in enumerate(keywords):
            kw = kw.strip()
            if not kw: continue
            
            print(f"[{idx+1}/{len(keywords)}] 키워드: '{kw}' 분석 중...", end="\r")
            
            html = self.fetch_serp(kw)
            is_exposed, urls = self.parse_ai_briefing(html)
            
            results.append({
                "keyword": kw,
                "exposed": "O" if is_exposed else "X",
                "url_count": len(urls),
                "urls": urls
            })
            
            # 안티봇 우회를 위한 랜덤 딜레이
            if idx < len(keywords) - 1:
                time.sleep(random.uniform(1.8, 3.2))
        
        print("\n\n" + "="*80)
        print(f"{'키워드':<20} | {'AI노출':<6} | {'출처수':<6} | {'주요 출처 URL'}")
        print("-" * 80)
        
        for res in results:
            first_url = res['urls'][0] if res['urls'] else "-"
            print(f"{res['keyword']:<20} | {res['exposed']:^8} | {res['url_count']:^8} | {first_url}")
            if len(res['urls']) > 1:
                for other_url in res['urls'][1:3]: # 상위 3개까지만 터미널 출력
                    print(f"{'':<20} | {'':^8} | {'':^8} | {other_url}")
                if len(res['urls']) > 3:
                    print(f"{'':<20} | {'':^8} | {'':^8} | ... 외 {len(res['urls'])-3}개 더 있음")
        
        self.save_to_csv(results)

    def save_to_csv(self, results):
        filename = f"naver_ai_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'AI Exposed', 'Source Count', 'URLs'])
            for res in results:
                writer.writerow([res['keyword'], res['exposed'], res['url_count'], ", ".join(res['urls'])])
        print(f"\n[💾 저장 완료] 결과가 '{filename}'에 저장되었습니다.")

if __name__ == "__main__":
    # ---------------------------------------------------------
    # 여기에 실제 쿠키값을 입력하세요 (부계정 사용 권장)
    # ---------------------------------------------------------
    NID_AUT = "YOUR_NID_AUT_HERE"
    NID_SES = "YOUR_NID_SES_HERE"
    
    if NID_AUT == "YOUR_NID_AUT_HERE":
        print("⚠️ [Warning] NID_AUT와 NID_SES 쿠키값을 설정해야 정확한 수집이 가능합니다.")
    
    # CLI 입력 처리
    user_input = input("🔍 검색할 키워드들을 입력하세요 (쉼표로 구분): ")
    keywords_list = user_input.split(",")
    
    scraper = NaverAIScraper(NID_AUT, NID_SES)
    scraper.run(keywords_list)
