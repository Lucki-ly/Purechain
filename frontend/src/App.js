import { useRef, useState } from "react";
import EchartsRenderer from "./components/EchartsRenderer";
import { chatWithAgent, uploadFiles } from "./api";

function App() {
  const [data, setData] = useState(null);
  const [tableMeta, setTableMeta] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "你好，我是 Pureclaw Agent。你可以先直接聊天，也可以上传 Excel/CSV 后让我做数据分析。",
      charts: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const fileRef = useRef(null);
  const abortRef = useRef(null);

  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      const res = await uploadFiles(files);
      // 上传成功：与后端 UploadResponse 对齐
      setData(res.preview || []);
      setTableMeta({
        columns: res.columns || [],
        shape: res.df_shape || [0, 0],
      });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `数据已上传完成：${res.df_shape?.[0] ?? 0} 行，${res.df_shape?.[1] ?? 0} 列。你现在可以直接提问。`,
          charts: [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "上传失败，请确认后端已启动且文件格式正确。", charts: [] },
      ]);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const sendMessage = async () => {
    const query = input.trim();
    if (!query || loading) return;

    const nextUser = { role: "user", content: query, charts: [] };
    const conversation = [...messages, nextUser];
    setMessages(conversation);
    setInput("");
    setLoading(true);
    abortRef.current = new AbortController();
    try {
      const res = await chatWithAgent({
        query,
        messages: conversation.map((m) => ({ role: m.role, content: m.content })),
        dfData: data || null,
        signal: abortRef.current.signal,
      });
      if (res.error) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `发生错误：${res.error}`, charts: [] },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: res.answer || "已完成。", charts: res.charts || [] },
        ]);
      }
    } catch (err) {
      const isAbort = err?.name === "CanceledError" || err?.code === "ERR_CANCELED";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: isAbort ? "已中断本次思考。" : "请求失败，请检查后端、Ollama 和模型状态。",
          charts: [],
        },
      ]);
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  };

  const stopThinking = () => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="brand">
          <span className="logo-badge">P</span>
          <div>
            <h1>Pureclaw Agent</h1>
            <p>可对话、可分析、可视化的一体化数据助手</p>
          </div>
        </div>
      </header>

      <main className="chat-layout">
        <section className="chat-stream">
          {messages.map((m, idx) => (
            <div key={idx} className={`bubble-row ${m.role === "user" ? "is-user" : "is-assistant"}`}>
              <div className={`avatar ${m.role === "user" ? "avatar-user" : "avatar-assistant"}`}>
                {m.role === "user" ? "🙂" : "🤖"}
              </div>
              <div className="bubble">
                <div className="bubble-role">{m.role === "user" ? "你" : "Pureclaw"}</div>
                <div className="insights">{m.content}</div>
                {m.charts && m.charts.length > 0 && (
                  <div className="result-panel" style={{ marginTop: 10 }}>
                    {m.charts.map((option, chartIdx) => (
                      <div key={chartIdx} className="chart-wrapper">
                        <EchartsRenderer option={option} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="bubble-row is-assistant">
              <div className="avatar avatar-assistant">🤖</div>
              <div className="bubble">
                <div className="bubble-role">Pureclaw</div>
                <div className="thinking">
                  <span>思考中</span>
                  <span className="dot-loader"><i /><i /><i /></span>
                </div>
              </div>
            </div>
          )}
        </section>

        <section className="composer">
          <label className="upload-label">
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".xlsx,.xls,.csv"
              onChange={(e) => handleUpload(e.target.files)}
              disabled={uploading || loading}
            />
            <span>{uploading ? "上传中…" : "上传文件"}</span>
          </label>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="直接和 Agent 对话，或上传数据后提问..."
            rows={2}
            disabled={loading}
          />
          <button type="button" onClick={sendMessage} disabled={loading || !input.trim()}>
            {loading ? "思考中..." : "发送"}
          </button>
          {loading && (
            <button type="button" className="stop-btn" onClick={stopThinking}>
              中断
            </button>
          )}
        </section>
      </main>

      <button
        type="button"
        className="drawer-toggle"
        onClick={() => setDrawerOpen((v) => !v)}
        disabled={!data || data.length === 0}
        title={drawerOpen ? "关闭数据窗口" : "打开数据窗口"}
      >
        {drawerOpen ? "收起数据" : "查看数据"}
      </button>

      {drawerOpen && data && data.length > 0 && tableMeta && (
        <aside className="data-drawer">
          <section className="data-preview">
            <div className="panel-header">
              <h3>当前数据</h3>
              <span className="badge">
                {tableMeta.shape?.[0]} 行 · {tableMeta.shape?.[1]} 列
              </span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    {tableMeta.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.slice(0, 14).map((row, idx) => (
                    <tr key={idx}>
                      {tableMeta.columns.map((col) => (
                        <td key={col}>{row[col]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </aside>
      )}
    </div>
  );
}

export default App;