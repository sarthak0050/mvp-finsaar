import { useEffect, useRef, useState } from "react";
import { RefreshCw, RotateCcw, Send, Sparkles, WifiOff, X } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const PROMPTS = {
  dip: ["Iska matlab paisa doob gaya?", "Why are my units going up but value going down?", "Should I stop my SIP?"],
  normal: ["XIRR ko simple mein samjhao", "What is NAV and how does it affect my SIP?"],
};

const Answer = ({ m, i }) => (
  <div className="bot-message answer" data-testid={`chat-answer-${i}`}>
    <Sparkles size={15} />
    <div>
      <p style={{ whiteSpace: "pre-line" }}>{m.text.replace(/\*\*|__|^#+\s/gm, "") || "Checking your answer against your data…"}</p>
      {!m.pending && <small data-testid={`chat-source-${i}`}>✓ {m.source || "Your SIP data"}{m.replaced ?? m.fallback ? " · Simplified for safety" : ""}</small>}
    </div>
  </div>
);

async function streamAnswer(body, onToken, signal) {
  const res = await fetch(`${API}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "", meta = null;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop();
    parts.forEach((part) => {
      if (!part.startsWith("data: ")) return;
      const e = JSON.parse(part.slice(6));
      if (e.token) onToken(e.token);
      if (e.done) meta = e;
    });
  }
  if (!meta) throw new Error("incomplete");
  return meta;
}

// language is the user's explicit toggle choice, or null: replies then follow the language of each question.
export const Chat = ({ language, setLanguage, onClose, messages, setMessages, scenario, seed }) => {
  const lastReplyLanguage = [...messages].reverse().find((m) => m.role === "assistant" && m.language)?.language;
  const activeLanguage = language || lastReplyLanguage || "English";
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bodyRef = useRef(null);
  const abortRef = useRef(null);
  const seeded = useRef(false);

  const ask = async (q, retry = false) => {
    if (!q?.trim() || loading) return;
    setText(""); setError(null); setLoading(true);
    const history = (retry ? messages.slice(0, -1) : messages).filter((m) => !m.pending).slice(-6).map(({ role, text: t }) => ({ role, text: t }));
    setMessages((ms) => [...(retry ? ms : [...ms, { role: "user", text: q }]), { role: "assistant", text: "", pending: true }]);
    const patchLast = (fn) => setMessages((ms) => (ms.length && ms[ms.length - 1].pending ? [...ms.slice(0, -1), fn(ms[ms.length - 1])] : ms));
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const meta = await streamAnswer({ question: q, language, scenario, history }, (tok) => patchLast((m) => ({ ...m, text: m.text + tok })), controller.signal);
      patchLast((m) => ({ ...m, pending: false, source: meta.source, path: meta.path, topic: meta.topic, language: meta.language, replaced: meta.replaced ?? meta.fallback_used }));
    } catch (e) {
      setMessages((ms) => (ms.length && ms[ms.length - 1].pending ? ms.slice(0, -1) : ms));
      if (e.name !== "AbortError") setError(q);
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  };

  useEffect(() => { if (seed && !seeded.current) { seeded.current = true; ask(seed); } }, [seed]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const el = bodyRef.current; if (el) el.scrollTop = el.scrollHeight; }, [messages, error]);
  useEffect(() => { document.body.style.overflow = "hidden"; return () => { document.body.style.overflow = ""; }; }, []);
  const newChat = () => { abortRef.current?.abort(); setLoading(false); setMessages([]); setError(null); };
  const close = () => { abortRef.current?.abort(); setMessages((ms) => { const kept = ms.filter((m) => !m.pending); return kept.length && kept[kept.length - 1].role === "user" && loading ? kept.slice(0, -1) : kept; }); onClose(); };

  return (
    <div className="chat-overlay">
      <div className="chat-panel" data-testid="chat-panel">
        <div className="chat-head">
          <div><span className="eyebrow">FINSAAR</span><h2>Let’s make this simple</h2></div>
          <div className="chat-head-actions">
            {messages.length > 0 && <button className="new-chat" data-testid="chat-new-button" onClick={newChat}><RotateCcw size={14} /> New chat</button>}
            <button data-testid="close-chat-button" aria-label="Close" onClick={close}><X size={19} /></button>
          </div>
        </div>
        <div className="language-toggle">
          {["English", "Hinglish"].map((l) => <button key={l} className={activeLanguage === l ? "active" : ""} aria-pressed={activeLanguage === l} data-testid={`chat-language-${l.toLowerCase()}`} onClick={() => setLanguage(l)}>{l}{!language && activeLanguage === l ? " · auto" : ""}</button>)}
        </div>
        <p className="language-hint" data-testid="chat-language-hint">{language ? <>FinSaar replies only in {language}. <button className="language-auto" data-testid="chat-language-auto" onClick={() => setLanguage(null)}>Match my language</button></> : "FinSaar replies in the language you write in. Tap a language to fix it."}</p>
        <div className="chat-body" data-testid="chat-thread" ref={bodyRef}>
          <div className="bot-message"><Sparkles size={15} /><p>{activeLanguage === "Hinglish" ? "Namaste. Main aapke SIP ke numbers ko simple shabdon mein samjha sakta hoon. Kya samajhna chahenge?" : "Hi. I can explain your SIP numbers in simple words. What would you like to understand?"}</p></div>
          {messages.map((m, i) => (m.role === "user" ? <div className="user-message" key={i} data-testid={`chat-user-message-${i}`}>{m.text}</div> : <Answer key={i} m={m} i={i} />))}
          {error && <div className="chat-error" role="alert" data-testid="chat-error"><WifiOff size={15} /><p>FinSaar couldn’t answer right now. This is a connection problem, not your data.</p><button data-testid="chat-retry-button" onClick={() => ask(error, true)}><RefreshCw size={13} /> Try again</button></div>}
          {!loading && messages.length === 0 && <div className="prompt-row">{PROMPTS[scenario].map((q, i) => <button key={q} data-testid={`chat-prompt-${i}`} onClick={() => ask(q)}>{q}</button>)}</div>}
                  </div>
        <div className="chat-input">
          <input data-testid="chat-input" value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask(text)} placeholder={messages.length ? "Ask a follow-up" : "Ask about your numbers"} maxLength={500} />
          <button data-testid="chat-send-button" aria-label="Send" onClick={() => ask(text)} disabled={loading}><Send size={17} /></button>
        </div>
        <p className="chat-disclaimer" data-testid="chat-disclaimer">Educational only. FinSaar doesn’t give investment advice or predictions.</p>
      </div>
    </div>
  );
};
