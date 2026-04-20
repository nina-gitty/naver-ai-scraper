import { useState, useEffect } from 'react';
import { Search, Download, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import './App.css';

interface ScrapeResult {
  keyword: string;
  exposed: boolean;
  urls: string[];
  screenshotUrl?: string;
}


function App() {
  const [inputValue, setInputValue] = useState('');
  const [results, setResults] = useState<ScrapeResult[]>([]);
  const [isScraping, setIsScraping] = useState(false);
  const [isFinished, setIsFinished] = useState(false);

  const startScraping = () => {
    if (!inputValue.trim()) return;

    setResults([]);
    setIsScraping(true);
    setIsFinished(false);

    const keywordsParam = encodeURIComponent(inputValue);
    const eventSource = new EventSource(`http://localhost:8000/api/scrape/stream?keywords=${keywordsParam}`);

    eventSource.onmessage = (event) => {
      const data: ScrapeResult = JSON.parse(event.data);
      // 데이터가 들어오는 즉시 상태 업데이트 (Flush 효과)
      setResults((prev) => [...prev, data]);
    };

    eventSource.addEventListener('done', () => {
      setIsScraping(false);
      setIsFinished(true);
      eventSource.close();
    });

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      setIsScraping(false);
      eventSource.close();
    };
  };

  const downloadCSV = () => {
    const headers = ['Keyword', 'AI Exposed', 'Source Count', 'URLs'];
    const rows = results.map(r => [
      r.keyword,
      r.exposed ? 'O' : 'X',
      r.urls.length,
      r.urls.join(' | ')
    ]);

    const csvContent = [headers, ...rows]
      .map(e => e.join(","))
      .join("\n");

    const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `naver_ai_results_${new Date().getTime()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="container">
      <header>
        <h1><Search size={40} /> Naver AI Briefing Scraper</h1>
        <p className="subtitle">네이버 AI 검색 결과와 출처 URL을 실시간으로 수집합니다.</p>
      </header>

      <div className="input-section">
        <textarea
          placeholder="검색할 키워드들을 쉼표(,)로 구분하여 입력하세요... (예: 아이폰 16, 삼성전자 주가)"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isScraping}
        />
        <button 
          className="start-btn" 
          onClick={startScraping}
          disabled={isScraping || !inputValue.trim()}
        >
          {isScraping ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10' }}>
              <Loader2 className="animate-spin" /> 수집 중...
            </span>
          ) : '분석 시작하기'}
        </button>
      </div>

      <div className="results-section">
        {isScraping && results.length === 0 && (
          <div className="empty-state">
            <Loader2 className="animate-spin" size={40} style={{ marginBottom: 20, color: 'var(--primary-color)' }} />
            첫 번째 키워드를 분석 중입니다... 잠시만 기다려 주세요.
          </div>
        )}
        
        {results.length === 0 && !isScraping && (
          <div className="empty-state">
            검색창에 키워드를 입력하고 분석을 시작해 보세요!
          </div>
        )}
        
        {results.map((res, index) => (
          <div key={index} className="result-card">
            <div className="card-header">
              <span className="keyword-badge">{res.keyword}</span>
              <span className={`status-badge ${res.exposed ? 'success' : 'error'}`}>
                {res.exposed ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><CheckCircle2 size={16} /> AI 노출됨</span>
                ) : (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><XCircle size={16} /> AI 미노출</span>
                )}
              </span>
            </div>

            {res.screenshotUrl && (
              <div className="screenshot-container">
                <img 
                  src={res.screenshotUrl} 
                  alt={`${res.keyword} 스크린샷`} 
                  className="screenshot-img"
                  onClick={() => window.open(res.screenshotUrl, '_blank')}
                />
              </div>
            )}

            {res.urls.length > 0 ? (

              <ul className="url-list">
                {res.urls.map((url, i) => (
                  <li key={i} className="url-item">
                    <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ color: '#999', fontSize: '0.9rem' }}>수집된 출처 URL이 없습니다.</p>
            )}
          </div>
        ))}
      </div>

      {isFinished && (
        <div className="export-section">
          <button className="export-btn" onClick={downloadCSV}>
            <Download size={18} style={{ marginRight: 8 }} /> CSV로 저장하기
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
