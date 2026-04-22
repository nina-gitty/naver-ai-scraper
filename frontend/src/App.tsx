import { useState, useRef, useEffect } from 'react';
import { Search, Download, Loader2, CheckCircle2, XCircle, FileText, BadgeCheck, Square } from 'lucide-react';
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
  dailyCount?: number;
  dailyLimit?: number;
}

function App() {
  const [inputValue, setInputValue] = useState('');
  const [targetValue, setTargetValue] = useState('');
  const [results, setResults] = useState<ScrapeResult[]>([]);
  const [isScraping, setIsScraping] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [eta, setEta] = useState<string | null>(null);
  const [quota, setQuota] = useState<{count: number, limit: number}>({count: 0, limit: 200});

  // 실시간 키워드 개수 및 예상 소요 시간 계산
  const currentKeywordCount = inputValue.split(',').map(k => k.trim()).filter(k => k).length;
  
  const getInitialEta = (count: number) => {
    if (count === 0) return null;
    const batchSize = 5; 
    const secPerBatch = 18; 
    const totalSeconds = Math.ceil(count / batchSize) * secPerBatch;
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins > 0 ? `${mins}분 ` : ''}${secs}초`;
  };

  const initialEta = getInitialEta(currentKeywordCount);
  
  // SSE 연결 및 시간 측정을 위한 ref
  const eventSourceRef = useRef<EventSource | null>(null);
  const startTimeRef = useRef<number | null>(null);

  // 초기 쿼터 정보 가져오기
  useEffect(() => {
    const host = window.location.hostname;
    fetch(`http://${host}:8000/api/quota`)
      .then(res => res.json())
      .then(data => setQuota({count: data.count, limit: data.limit}))
      .catch(err => console.error("Quota fetch error:", err));
  }, []);

  const startScraping = () => {
    if (!inputValue.trim()) return;

    const keywords = inputValue.split(',').map(k => k.trim()).filter(k => k);
    setResults([]);
    setIsScraping(true);
    setIsFinished(false);
    setProgress({ current: 0, total: keywords.length });
    setEta(null);
    startTimeRef.current = Date.now();

    const keywordsParam = encodeURIComponent(inputValue);
    const targetsParam = encodeURIComponent(targetValue);
    
    const host = window.location.hostname;
    const apiUrl = `http://${host}:8000/api/scrape/stream?keywords=${keywordsParam}&targets=${targetsParam}`;

    try {
      const eventSource = new EventSource(apiUrl);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        const data: ScrapeResult = JSON.parse(event.data);
        setResults((prev) => [...prev, data]);
        
        if (data.dailyCount !== undefined) {
          setQuota({ count: data.dailyCount, limit: data.dailyLimit || 200 });
        }

        if (data.currentIndex && data.totalCount && startTimeRef.current) {
          setProgress({ current: data.currentIndex, total: data.totalCount });
          
          // ETA 계산
          const elapsed = (Date.now() - startTimeRef.current) / 1000;
          const completed = data.currentIndex;
          const total = data.totalCount;
          
          if (completed > 0) {
            const timePerItem = elapsed / completed;
            const remaining = total - completed;
            const remainingSeconds = Math.round(timePerItem * remaining);
            
            if (remainingSeconds > 0) {
              const minutes = Math.floor(remainingSeconds / 60);
              const seconds = remainingSeconds % 60;
              setEta(`${minutes > 0 ? `${minutes}분 ` : ''}${seconds}초 남음`);
            } else {
              setEta('완료 중...');
            }
          }
        }
      };

      eventSource.addEventListener('done', () => {
        cleanup();
        setIsFinished(true);
        setEta(null);
      });

      eventSource.onerror = (err) => {
        console.error("SSE Error:", err);
        cleanup();
      };
    } catch (e) {
      console.error("Error creating EventSource:", e);
      setIsScraping(false);
    }
  };

  const stopScraping = () => {
    console.log("⏹ 수집 중단 요청");
    cleanup();
  };

  const cleanup = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsScraping(false);
  };

  const downloadCSV = () => {
    const headers = ['Keyword', 'AI Exposed', 'Matched Keywords', 'Carousel Count', 'Carousel URLs', 'Panel Count', 'Panel URLs'];
    
    const rows = results.map(r => {
      const carouselSources = r.sources.filter(s => s.location === '상단 캐러셀').map(s => s.url);
      const panelSources = r.sources.filter(s => s.location === '출처 패널').map(s => s.url);
      
      return [
        r.keyword,
        r.exposed ? 'O' : 'X',
        r.matchedKeywords?.join('|') || '',
        carouselSources.length,
        carouselSources.join(' | '),
        panelSources.length,
        panelSources.join(' | ')
      ];
    });

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

  const quotaPercentage = (quota.count / quota.limit) * 100;
  const quotaStatus = quotaPercentage < 50 ? 'safe' : quotaPercentage < 80 ? 'warning' : 'danger';
  const statusColors = { safe: '#28a745', warning: '#fd7e14', danger: '#dc3545' };

  return (
    <div className="container">
      <header>
        <h1><Search size={40} /> Naver AI Briefing Scraper</h1>
        <p className="subtitle">네이버 AI 검색 결과와 출처 URL을 실시간으로 수집 및 검증합니다.</p>
        
        <div className="quota-card" style={{
          marginTop: '20px',
          background: 'white',
          padding: '15px 20px',
          borderRadius: '12px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
          border: `1px solid ${statusColors[quotaStatus]}22`,
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#444', display: 'flex', alignItems: 'center', gap: '6px' }}>
              🛡️ Safe Guard Quota
            </span>
            <span style={{ fontSize: '0.85rem', fontWeight: 'bold', color: statusColors[quotaStatus] }}>
              {quota.count} / {quota.limit} (오늘 수집량)
            </span>
          </div>
          <div style={{ width: '100%', height: '8px', background: '#eee', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ 
              width: `${Math.min(quotaPercentage, 100)}%`, 
              height: '100%', 
              background: statusColors[quotaStatus],
              transition: 'width 0.5s ease'
            }} />
          </div>
          <p style={{ fontSize: '0.75rem', color: '#888', margin: 0 }}>
            {quotaStatus === 'safe' && "✅ 안정적인 수집 상태입니다."}
            {quotaStatus === 'warning' && "⚠️ 주의: 수집량이 많습니다. 딜레이를 늘리거나 휴식을 권장합니다."}
            {quotaStatus === 'danger' && "🚨 위험: 차단 가능성이 높습니다! IP 변경 후 작업을 권장합니다."}
          </p>
        </div>
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

        <div className="keyword-counter" style={{ 
          fontSize: '0.85rem', 
          color: '#666', 
          textAlign: 'right', 
          marginBottom: '-10px',
          fontWeight: '500'
        }}>
          {currentKeywordCount > 0 && (
            <span>
              총 <strong>{currentKeywordCount}개</strong> 감지됨 
              {!isScraping && ` (최대 예상: 약 ${initialEta})`}
            </span>
          )}
        </div>

        <div className="button-group" style={{ display: 'flex', gap: '10px' }}>
          <button 
            className="start-btn" 
            onClick={startScraping}
            disabled={isScraping || !inputValue.trim()}
            style={{ flex: isScraping ? 3 : 1 }}
          >
            {isScraping ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <Loader2 className="animate-spin" /> 분석 중...
              </span>
            ) : `분석 및 검증 시작하기 (${currentKeywordCount}개)`}
          </button>
          
          {isScraping && (
            <button 
              className="stop-btn" 
              onClick={stopScraping}
              style={{ 
                flex: 1, 
                backgroundColor: '#dc3545', 
                color: 'white', 
                border: 'none', 
                borderRadius: '12px',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              <Square size={16} fill="white" /> 중단
            </button>
          )}
        </div>
      </div>

      <div className="results-section">
        {isScraping && progress.total > 0 && (
          <div className="progress-container">
            <div className="progress-header">
              <span className="loading-text">네이버 AI 데이터 분석 중</span>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '4px' }}>
                  {eta && <span>⏳ 최대 예상: {eta}</span>}
                </div>
                <span>{progress.current} / {progress.total} 완료</span>
              </div>
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

      {(isFinished || results.length > 0) && (
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
