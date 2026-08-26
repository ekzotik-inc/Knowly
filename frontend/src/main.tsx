import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Character, defaultCharacter } from "./components/Character";
import { CharacterEditor } from "./components/CharacterEditor";
import type { CharacterConfig } from "./components/character-types";
import "./styles.css";

type Product = { code: string; title: string; description: string; stars: number; entitlement_key: string };
type Entitlement = { entitlement_key: string; active: boolean };
type TestSummary = { id: string; title: string; public_token: string; status: string; question_count: number };
type PublicQuestion = { id: string; text: string; options: string[]; position: number };
type PublicTest = { id: string; title: string; owner_name: string; public_token: string; questions: PublicQuestion[] };
type Result = { result_id: string; test_id: string; correct_answers: number; total_questions: number; percentage: number };
type ResultDetail = Result & { review_locked: boolean; review: { question_id: string; selected_option: string; correct_option: string; is_correct: boolean }[] };
type QuestionDraft = { text: string; options: string[]; correct_option: string };
type Profile = { id: string; display_name: string; avatar_url: string | null; character: CharacterConfig; locale: "ru" | "en" | "uz"; result_visibility: string; sound_enabled: boolean; haptic_enabled: boolean };
type Progress = { xp: number; level: number; next_level_xp: number; tests_created: number; tests_completed: number };

type TelegramWebApp = {
  initData: string;
  initDataUnsafe?: { start_param?: string; user?: { first_name?: string } };
  ready: () => void;
  expand: () => void;
  openInvoice?: (url: string, callback?: (status: string) => void) => void;
};

declare global { interface Window { Telegram?: { WebApp?: TelegramWebApp } } }

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME ?? "your_knowly_bot";
let accessToken = "";

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}), ...(options.headers ?? {}) },
  });
  if (!response.ok) throw new Error((await response.text()) || "Ошибка API");
  return response.json() as Promise<T>;
}

async function authenticate() {
  const initData = window.Telegram?.WebApp?.initData;
  if (!initData) throw new Error("Откройте приложение внутри Telegram");
  const response = await fetch(`${API_URL}/api/v1/auth/telegram`, { method: "POST", headers: { Authorization: `TWA ${initData}` } });
  if (!response.ok) throw new Error("Не удалось подтвердить Telegram-пользователя");
  accessToken = (await response.json() as { access_token: string }).access_token;
}

const blankQuestion = (): QuestionDraft => ({ text: "", options: ["", ""], correct_option: "" });

function App() {
  const [screen, setScreen] = useState<"home" | "create" | "take" | "result">("home");
  const [firstName, setFirstName] = useState("друг");
  const [tests, setTests] = useState<TestSummary[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [entitlements, setEntitlements] = useState<Entitlement[]>([]);
  const [publicTest, setPublicTest] = useState<PublicTest | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const [resultDetail, setResultDetail] = useState<ResultDetail | null>(null);
  const [character, setCharacter] = useState<CharacterConfig>(defaultCharacter);
  const [characterSaving, setCharacterSaving] = useState(false);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [title, setTitle] = useState("Насколько ты меня знаешь?");
  const [drafts, setDrafts] = useState<QuestionDraft[]>([blankQuestion(), blankQuestion(), blankQuestion()]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const hasPremiumReview = entitlements.some((item) => item.entitlement_key === "premium_results" && item.active);
  const currentQuestion = publicTest?.questions[questionIndex];
  const startParam = useMemo(() => window.Telegram?.WebApp?.initDataUnsafe?.start_param ?? new URLSearchParams(location.search).get("startapp") ?? "", []);

  async function loadHome() {
    setBusy(true); setError("");
    try {
      await authenticate();
      setFirstName(window.Telegram?.WebApp?.initDataUnsafe?.user?.first_name ?? "друг");
      const [myTests, catalog, owned, profile, profileProgress] = await Promise.all([
        api<TestSummary[]>("/api/v1/tests"),
        api<Product[]>("/api/v1/payments/products"),
        api<Entitlement[]>("/api/v1/payments/entitlements"),
        api<Profile>("/api/v1/profile"),
        api<Progress>("/api/v1/progression"),
      ]);
      setTests(myTests); setProducts(catalog); setEntitlements(owned); setCharacter(profile.character); setProgress(profileProgress);
      if (startParam) await openTest(startParam);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Неизвестная ошибка"); }
    finally { setBusy(false); }
  }

  useEffect(() => { window.Telegram?.WebApp?.ready(); window.Telegram?.WebApp?.expand(); void loadHome(); }, []);

  async function openTest(token: string) {
    setBusy(true); setError("");
    try { setPublicTest(await api<PublicTest>(`/api/v1/public/tests/${encodeURIComponent(token)}`)); setQuestionIndex(0); setScreen("take"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Тест не найден"); }
    finally { setBusy(false); }
  }

  async function beginTest() {
    if (!publicTest) return;
    setBusy(true);
    try {
      const started = await api<{ session_id: string }>(`/api/v1/public/tests/${publicTest.public_token}/sessions`, { method: "POST" });
      setSessionId(started.session_id); setQuestionIndex(0);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось начать тест"); }
    finally { setBusy(false); }
  }

  async function answer(option: string) {
    if (!publicTest || !sessionId || !currentQuestion) return;
    setBusy(true);
    try {
      await api(`/api/v1/sessions/${sessionId}/answers`, { method: "POST", body: JSON.stringify({ question_id: currentQuestion.id, selected_option: option }) });
      if (questionIndex + 1 < publicTest.questions.length) setQuestionIndex((value) => value + 1);
      else { const completed = await api<Result>(`/api/v1/sessions/${sessionId}/complete`, { method: "POST" }); setResult(completed); setResultDetail(await api<ResultDetail>(`/api/v1/results/${completed.result_id}`)); setScreen("result"); }
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось сохранить ответ"); }
    finally { setBusy(false); }
  }

  function updateDraft(index: number, patch: Partial<QuestionDraft>) { setDrafts((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item)); }
  function updateOption(index: number, optionIndex: number, value: string) { setDrafts((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, options: item.options.map((option, i) => i === optionIndex ? value : option) } : item)); }

  async function saveCharacter() {
    setCharacterSaving(true); setError("");
    try {
      const profile = await api<Profile>("/api/v1/profile", { method: "PUT", body: JSON.stringify({ display_name: firstName, avatar_url: null, character }) });
      setCharacter(profile.character);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось сохранить персонажа"); }
    finally { setCharacterSaving(false); }
  }

  async function createTest() {
    setBusy(true); setError("");
    try {
      const created = await api<TestSummary>("/api/v1/tests", { method: "POST", body: JSON.stringify({ title, questions: drafts }) });
      setTests((items) => [created, ...items]); setScreen("home"); setDrafts([blankQuestion(), blankQuestion(), blankQuestion()]);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось создать тест"); }
    finally { setBusy(false); }
  }

  async function buy(product: Product) {
    setBusy(true); setError("");
    try {
      const invoice = await api<{ invoice_link: string }>("/api/v1/payments/invoice", { method: "POST", body: JSON.stringify({ product_code: product.code }) });
      if (!window.Telegram?.WebApp?.openInvoice) throw new Error("Telegram invoice API недоступен");
      window.Telegram.WebApp.openInvoice(invoice.invoice_link, (status) => { if (status === "paid") void loadHome(); if (status === "failed") setError("Оплата не прошла"); });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось открыть оплату"); }
    finally { setBusy(false); }
  }

  const shareUrl = (token: string) => `https://t.me/${BOT_USERNAME}?startapp=${encodeURIComponent(token)}`;

  if (screen === "take" && publicTest) return <main className="shell"><button className="back" onClick={() => setScreen("home")}>← Назад</button><section className="game-card"><Character config={character} emotion="thinking" compact /><div className="game-avatar">♡</div><p className="eyebrow">ТЕСТ ОТ {publicTest.owner_name.toUpperCase()}</p><h1>{publicTest.title}</h1>{!sessionId ? <><p className="lead dark">Проверь, насколько хорошо ты знаешь {publicTest.owner_name}.</p><button className="primary wide" onClick={() => void beginTest()} disabled={busy}>Начать игру</button></> : currentQuestion ? <><div className="progress-line"><span>{questionIndex + 1} / {publicTest.questions.length}</span><i><b style={{ width: `${((questionIndex + 1) / publicTest.questions.length) * 100}%` }} /></i></div><h2 className="question">{currentQuestion.text}</h2><div className="answers">{currentQuestion.options.map((option) => <button key={option} disabled={busy} onClick={() => void answer(option)}>{option}</button>)}</div></> : null}</section>{error && <div className="notice error">{error}</div>}</main>;

  if (screen === "result" && result) return <main className="shell"><section className="result-card"><Character config={character} emotion={result.percentage >= 81 ? "proud" : "thinking"} compact /><div className="result-heart">♥</div><p className="eyebrow">РЕЗУЛЬТАТ</p><h1>Ты знаешь {publicTest?.owner_name ?? "его"} на {result.percentage}%</h1><p className="score">{result.correct_answers} из {result.total_questions} правильных ответов</p><div className="score-ring">{result.percentage}%</div>      <p className="result-caption">{result.percentage >= 81 ? "Ого. Это уже серьёзно" : result.percentage >= 61 ? "Ты действительно хорошо знаешь его" : "Есть куда расти"}</p>{resultDetail && !resultDetail.review_locked && <div className="review-list"><strong>Разбор ответов</strong>{resultDetail.review.map((item) => <div className={item.is_correct ? "review correct" : "review wrong"} key={item.question_id}><span>{item.is_correct ? "Угадал ♥" : "Не угадал"}</span><small>Твой ответ: {item.selected_option} · Правильный: {item.correct_option}</small></div>)}</div>}{resultDetail?.review_locked && !hasPremiumReview && products.find((item) => item.code === "premium_results") && <div className="premium-cta">
<strong>Открыть подробный разбор</strong><span>Узнай, где именно вы совпали — за {products.find((item) => item.code === "premium_results")?.stars} ⭐</span><button onClick={() => void buy(products.find((item) => item.code === "premium_results")!)}>Открыть premium</button></div>}<button className="secondary wide" onClick={() => { setResult(null); setResultDetail(null); setPublicTest(null); setScreen("home"); }}>Создать свой тест ♡</button></section></main>;

  if (screen === "create") return <main className="shell"><button className="back" onClick={() => setScreen("home")}>← Назад</button><section className="page-heading"><Character config={character} emotion="playful" compact /><p className="eyebrow">ТВОЙ ТЕСТ</p><h1>Давай узнаем, кто тебя правда знает</h1><p>Добавь минимум три вопроса — потом ссылкой можно поделиться с друзьями.</p></section><label className="field"><span>Название</span><input value={title} onChange={(event) => setTitle(event.target.value)} /></label>{drafts.map((draft, index) => <article className="draft" key={index}><div className="draft-top"><strong>Вопрос {index + 1}</strong><span>{draft.options.length} варианта</span></div><input placeholder="Например: Что я выберу вечером?" value={draft.text} onChange={(event) => updateDraft(index, { text: event.target.value })} />{draft.options.map((option, optionIndex) => <div className="option-row" key={optionIndex}><input placeholder={`Вариант ${optionIndex + 1}`} value={option} onChange={(event) => updateOption(index, optionIndex, event.target.value)} /><label><input type="radio" name={`correct-${index}`} checked={draft.correct_option === option && option !== ""} onChange={() => updateDraft(index, { correct_option: option })} /> правильный</label></div>)}</article>)}<button className="secondary wide" onClick={() => setDrafts((items) => [...items, blankQuestion()])} disabled={drafts.length >= 15}>+ Добавить вопрос</button><button className="primary wide" onClick={() => void createTest()} disabled={busy}>Опубликовать тест</button>{error && <div className="notice error">{error}</div>}</main>;

  return <main className="shell"><section className="hero"><Character config={character} emotion="default" compact /><div className="orb">✦</div><p className="eyebrow">KNOWLY</p><h1>Привет, {firstName}</h1><p className="lead">Создай маленькую игру о себе и узнай, кто читает твои мысли.</p>{progress && <div className="progress-pill">Level {progress.level} · {progress.xp} XP</div>}<button className="primary" onClick={() => setScreen("create")}>Создать свой тест <span>♡</span></button></section><CharacterEditor config={character} onChange={setCharacter} onSave={() => void saveCharacter()} saving={characterSaving} />{error && <div className="notice error">{error}</div>}<section className="home-section"><div className="section-heading"><span>Твои тесты</span><strong>{tests.length}</strong></div>{tests.length === 0 ? <div className="empty">Здесь появится твой первый тест.<br /><button onClick={() => setScreen("create")}>Начать создание →</button></div> : tests.map((test) => <article className="test-card" key={test.id}><div><h2>{test.title}</h2><p>{test.question_count} вопросов · опубликован</p></div><button onClick={() => navigator.clipboard?.writeText(shareUrl(test.public_token))}>Поделиться</button></article>)}</section><section className="home-section"><div className="section-heading"><span>Открыть premium</span><strong>Stars</strong></div>{products.map((product) => <article className="product" key={product.code}><div className="product-copy"><div className="product-icon">♡</div><div><h2>{product.title}</h2><p>{product.description}</p></div></div>{entitlements.some((item) => item.entitlement_key === product.entitlement_key && item.active) ? <span className="owned">Доступно</span> : <button onClick={() => void buy(product)} disabled={busy}>{product.stars} ⭐</button>}</article>)}</section>{busy && <p className="loading">Загружаем…</p>}</main>;
}

createRoot(document.getElementById("root")!).render(<App />);
