import { useState } from 'react';
import { Search, Download, Loader2, CheckCircle2, XCircle, FileText, BadgeCheck } from 'lucide-react';
import './App.css';

interface SourceData {
  url: string;
  location: string;
}

interface ScrapeResult {
  keyword: string;
  exposed: boolean;
  sources: SourceData[];
  screenshotUrl?: string;
  matchedKeywords?: string[];
  allTargetKeywords?: string[];
  currentIndex?: number;
  totalCount?: number;
}

function App() {
  const [inputValue, setInputValue] = useState('');
  const [targetValue, setTargetValue] = useState('');
  const [results, setResults] = useState<ScrapeResult[]>([]);
  const [isScraping, setIsScraping] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  const startScraping = () => {
    if (!inputValue.trim()) return;

    const keywordList = inputValue.split(',').map(k => k.trim()).filter(k => k);
    setResults([]);
    setIsScraping(true);
    setIsFinished(false);
    // 시작 즉시 진행률 초기화 (0/N)
    setProgress({ current: 0, total: keywordList.length });

    const keywordsParam = encodeURIComponent(inputValue);
    const targetsParam = encodeURIComponent(targetValue);
    
    // 현재 브라우저 주소창의 호스트(localhost, IP, 또는 도메인)를 자동으로 감지합니다.
    const currentHost = window.location.hostname;
    const apiUrl = `http://${currentHost}:8000/api/scrape/stream?keywords=${keywordsParam}&targets=${targetsParam}`;

    try {
      const eventSource = new EventSource(apiUrl);

      eventSource.onmessage = (event) => {
        const data: ScrapeResult = JSON.parse(event.data);
        setResults((prev) => [...prev, data]);
        if (data.currentIndex && data.totalCount) {
          setProgress({ current: data.currentIndex, total: data.totalCount });
        }
      };

      eventSource.addEventListener('done', () => {
        setIsScraping(false);
        setIsFinished(true);
        eventSource.close();
      });

      eventSource.onerror = (err) => {
        console.error("SSE Error:", err);
        setIsScraping(false);
        eventSource.close();
      };
    } catch (e) {
      console.error("Error creating EventSource:", e);
      setIsScraping(false);
    }
  };

  const downloadCSV = () => {
    const headers = ['Keyword', 'AI Exposed', 'Source Count', 'Matched Keywords', 'URLs'];
    const rows = results.map(r => [
      r.keyword,
      r.exposed ? 'O' : 'X',
      r.sources.length,
      r.matchedKeywords?.join('|') || '',
      r.sources.map(s => s.url).join(' | ')
    ]);

    const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
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
        <p className="subtitle">네이버 AI 검색 결과와 출처 URL을 실시간으로 수집 및 검증합니다.</p>
      </header>

      <div className="input-section">
        <div className="field-group">
          <label className="field-label"><Search size={16} /> 네이버 검색 키워드</label>
          <textarea
            placeholder="검색할 키워드들을 쉼표(,)로 구분하여 입력하세요..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isScraping}
          />
        </div>

        <div className="field-group">
          <label className="field-label"><BadgeCheck size={16} /> 내용 검증 키워드 (Optional)</label>
          <textarea
            placeholder="AI 답변 내에서 등장을 확인할 키워드들을 입력하세요..."
            value={targetValue}
            onChange={(e) => setTargetValue(e.target.value)}
            disabled={isScraping}
            style={{ height: '60px' }}
          />
        </div>

        <button 
          className="start-btn" 
          onClick={startScraping}
          disabled={isScraping || !inputValue.trim()}
        >
          {isScraping ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
              <Loader2 className="animate-spin" /> 수집 중...
            </span>
          ) : '분석 및 검증 시작하기'}
        </button>
      </div>

      <div className="results-section">
        {isScraping && progress.total > 0 && (
          <div className="progress-container">
            <div className="progress-header">
              <span className="loading-text">네이버 AI 데이터 분석 중</span>
              <span>{progress.current} / {progress.total} 완료</span>
            </div>
            <div className="progress-bar-bg">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              ></div>
            </div>
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

            {res.allTargetKeywords && res.allTargetKeywords.length > 0 && (
              <div className="validation-section">
                <div className="validation-title"><FileText size={14} /> 내용 검증 결과</div>
                {res.allTargetKeywords.map((tk, i) => {
                  const isMatched = res.matchedKeywords?.includes(tk);
                  return (
                    <span key={i} className={`match-badge ${isMatched ? 'found' : 'missing'}`}>
                      {isMatched ? '✓' : '✗'} {tk}
                    </span>
                  );
                })}
              </div>
            )}

            {res.sources.length > 0 ? (
              <ul className="url-list">
                {res.sources.map((src, i) => (
                  <li key={i} className="url-item">
                    <a href={src.url} target="_blank" rel="noopener noreferrer" className="url-link">
                      {src.url}
                    </a>
                    <span className="location-tag">{src.location}</span>
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
