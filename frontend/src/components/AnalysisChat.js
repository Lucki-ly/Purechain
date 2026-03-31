import { useState } from 'react';

const AnalysisChat = ({ onAnalyze, loading, currentQuery }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) onAnalyze(query);
  };

  return (
    <div className="chat-box">
      <h3>自然语言提问</h3>
      <form onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="例如：分析本月营收趋势，找出异常值，给出运营建议"
          rows="4"
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Agent 思考中...' : '开始分析'}
        </button>
      </form>
      {currentQuery && <p className="current-query">当前问题：{currentQuery}</p>}
    </div>
  );
};

export default AnalysisChat;