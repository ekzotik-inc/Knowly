import { createRoot } from "react-dom/client";
import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
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
type Profile = { id: string; display_name: string; avatar_url: string | null; character: CharacterConfig | null; onboarding_required: boolean; locale: "ru" | "en" | "uz"; result_visibility: string; sound_enabled: boolean; haptic_enabled: boolean };
type Progress = { xp: number; level: number; next_level_xp: number; tests_created: number; tests_completed: number };

type TelegramWebApp = {
  initData: string;
  initDataUnsafe?: { start_param?: string; user?: { first_name?: string } };
  ready: () => void;
  expand: () => void;
  openInvoice?: (url: string, callback?: (status: string) => void) => void;
  openTelegramLink?: (url: string) => void;
  HapticFeedback?: { impactOccurred?: (style: "light" | "medium" | "heavy") => void; notificationOccurred?: (type: "error" | "success" | "warning") => void };
  showPopup?: (params: { title?: string; message: string; buttons?: { type: "ok"; text?: string }[] }, callback?: () => void) => void;
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

function telegram() { return window.Telegram?.WebApp; }
function haptic(style: "light" | "medium" | "heavy" = "light") { telegram()?.HapticFeedback?.impactOccurred?.(style); }
function botLink() { return `https://t.me/${BOT_USERNAME}`; }
function shareTelegram(url: string, text: string) {
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
  if (telegram()?.openTelegramLink) telegram()?.openTelegramLink?.(shareUrl);
  else window.open(shareUrl, "_blank", "noopener,noreferrer");
}

async function authenticate() {
  const initData = telegram()?.initData;
  if (!initData && import.meta.env.VITE_LOCAL_DEMO_AUTH !== "true") throw new Error("Откройте приложение внутри Telegram");
  const response = initData
    ? await fetch(`${API_URL}/api/v1/auth/telegram`, { method: "POST", headers: { Authorization: `TWA ${initData}` } })
    : await fetch(`${API_URL}/api/v1/auth/local`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ display_name: "Local Tester" }) });
  if (!response.ok) throw new Error("Не удалось подтвердить пользователя");
  accessToken = (await response.json() as { access_token: string }).access_token;
}

const blankQuestion = (): QuestionDraft => ({ text: "", options: ["", ""], correct_option: "" });
const optionLetter = (index: number) => String.fromCharCode(65 + index);

function App() {
  const [screen, setScreen] = useState<"home" | "create" | "take" | "result">("home");
  const [firstName, setFirstName] = useState("друг");
  const [tests, setTests] = useState<TestSummary[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [entitlements, setEntitlements] = useState<Entitlement[]>([]);
  const [publicTest, setPublicTest] = useState<PublicTest | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [resultDetail, setResultDetail] = useState<ResultDetail | null>(null);
  const [character, setCharacter] = useState<CharacterConfig>(defaultCharacter);
  const [onboardingRequired, setOnboardingRequired] = useState(false);
  const [characterSaving, setCharacterSaving] = useState(false);
  const [characterOpen, setCharacterOpen] = useState(false);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [title, setTitle] = useState("Насколько ты меня знаешь?");
  const [drafts, setDrafts] = useState<QuestionDraft[]>([blankQuestion(), blankQuestion(), blankQuestion()]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const hasPremiumReview = entitlements.some((item) => item.entitlement_key === "premium_results" && item.active);
  const currentQuestion = publicTest?.questions[questionIndex];
  const startParam = useMemo(() => window.Telegram?.WebApp?.initDataUnsafe?.start_param ?? new URLSearchParams(location.search).get("startapp") ?? "", []);
  const validDrafts = drafts.filter((draft) => draft.text.trim() && draft.options.filter(Boolean).length >= 2 && draft.correct_option.trim());
  const canPublish = title.trim().length > 2 && validDrafts.length === drafts.length;

  function notify(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(""), 2800);
  }

  async function loadHome() {
    setBusy(true); setError("");
    try {
      await authenticate();
      setFirstName(telegram()?.initDataUnsafe?.user?.first_name ?? "друг");
      const [myTests, catalog, owned, profile, profileProgress] = await Promise.all([
        api<TestSummary[]>("/api/v1/tests"), api<Product[]>("/api/v1/payments/products"), api<Entitlement[]>("/api/v1/payments/entitlements"), api<Profile>("/api/v1/profile"), api<Progress>("/api/v1/progression"),
      ]);
      setTests(myTests); setProducts(catalog); setEntitlements(owned); setProgress(profileProgress);
      const needsCharacter = profile.onboarding_required || !profile.character;
      setOnboardingRequired(needsCharacter);
      if (profile.character) setCharacter(profile.character);
      if (needsCharacter) { setScreen("home"); setCharacterOpen(true); }
      else if (startParam === "characters") setCharacterOpen(true);
      else if (startParam) await openTest(startParam);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Неизвестная ошибка"); }
    finally { setBusy(false); }
  }

  useEffect(() => { telegram()?.ready(); telegram()?.expand(); void loadHome(); }, []);

  async function openTest(token: string) {
    setBusy(true); setError("");
    try { setPublicTest(await api<PublicTest>(`/api/v1/public/tests/${encodeURIComponent(token)}`)); setQuestionIndex(0); setSessionId(""); setSelectedOption(null); setScreen("take"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Тест не найден"); }
    finally { setBusy(false); }
  }

  async function beginTest() {
    if (!publicTest) return;
    setBusy(true); haptic("medium");
    try { const started = await api<{ session_id: string }>(`/api/v1/public/tests/${publicTest.public_token}/sessions`, { method: "POST" }); setSessionId(started.session_id); setQuestionIndex(0); notify("Игра началась"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось начать тест"); }
    finally { setBusy(false); }
  }

  async function answer(option: string) {
    if (!publicTest || !sessionId || !currentQuestion) return;
    setSelectedOption(option); setBusy(true); haptic("light");
    try {
      await api(`/api/v1/sessions/${sessionId}/answers`, { method: "POST", body: JSON.stringify({ question_id: currentQuestion.id, selected_option: option }) });
      if (questionIndex + 1 < publicTest.questions.length) { setQuestionIndex((value) => value + 1); setSelectedOption(null); }
      else { const completed = await api<Result>(`/api/v1/sessions/${sessionId}/complete`, { method: "POST" }); setResult(completed); setResultDetail(await api<ResultDetail>(`/api/v1/results/${completed.result_id}`)); setScreen("result"); haptic("heavy"); }
    } catch (reason) { setSelectedOption(null); setError(reason instanceof Error ? reason.message : "Не удалось сохранить ответ"); }
    finally { setBusy(false); }
  }

  function updateDraft(index: number, patch: Partial<QuestionDraft>) { setDrafts((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item)); }
  function updateOption(index: number, optionIndex: number, value: string) { setDrafts((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, options: item.options.map((option, i) => i === optionIndex ? value : option), correct_option: item.correct_option === item.options[optionIndex] ? value : item.correct_option } : item)); }

  async function saveCharacter() {
    setCharacterSaving(true); setError("");
    try {       const profile = await api<Profile>("/api/v1/profile", { method: "PUT", body: JSON.stringify({ display_name: firstName, avatar_url: null, character }) });
      if (profile.character) setCharacter(profile.character);
      setOnboardingRequired(profile.onboarding_required);
      setCharacterOpen(false); notify("Твой персонаж сохранён"); haptic("light");
 }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось сохранить персонажа"); }
    finally { setCharacterSaving(false); }
  }

  async function createTest() {
    if (!canPublish) { setError("Заполни каждый вопрос и отметь правильный вариант"); return; }
    setBusy(true); setError(""); haptic("medium");
    try { const created = await api<TestSummary>("/api/v1/tests", { method: "POST", body: JSON.stringify({ title, questions: drafts }) }); setTests((items) => [created, ...items]); setScreen("home"); setDrafts([blankQuestion(), blankQuestion(), blankQuestion()]); notify("Тест опубликован — можно делиться"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось создать тест"); }
    finally { setBusy(false); }
  }

  async function buy(product: Product) {
    setBusy(true); setError("");
    try { const invoice = await api<{ invoice_link: string }>("/api/v1/payments/invoice", { method: "POST", body: JSON.stringify({ product_code: product.code }) }); if (!telegram()?.openInvoice) throw new Error("Telegram invoice API недоступен"); telegram()?.openInvoice?.(invoice.invoice_link, (status) => { if (status === "paid") void loadHome(); if (status === "failed") setError("Оплата не прошла"); }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось открыть оплату"); }
    finally { setBusy(false); }
  }

  function shareTest(test: TestSummary) {
    const url = shareUrl(test.public_token); shareTelegram(url, `Проверь, насколько хорошо ты знаешь меня в Knowly: ${test.title}`); notify("Открываю выбор чата"); haptic("light");
  }

  function copyTest(test: TestSummary) {
    const url = shareUrl(test.public_token);
    navigator.clipboard?.writeText(url).then(() => notify("Ссылка скопирована")).catch(() => notify(url));
  }

  function shareResult() {
    if (!result) return;
    const text = `Я набрал ${result.percentage}% в Knowly. Сможешь лучше?`;
    shareTelegram(window.location.href, text); notify("Поделись результатом");
  }

  function openBot() {
    if (BOT_USERNAME === "your_knowly_bot") { notify("Добавь username бота в настройках Render"); return; }
    telegram()?.openTelegramLink?.(botLink());
  }

  function goHome() { setScreen("home"); setPublicTest(null); setResult(null); setResultDetail(null); setSessionId(""); setSelectedOption(null); }

  const backButton = (label = "На главную") => <button className="back-button" onClick={goHome}><span>‹</span>{label}</button>;

  if (screen === "take" && publicTest) return <main className="app-shell quiz-screen"><header className="topbar">{backButton("Выйти из игры")}<span className="topbar-label">KNOWLY / ИГРА</span><span className="topbar-dot" /></header><section className={`quiz-card ${sessionId ? "is-playing" : ""}`}>{!sessionId ? <><div className="quiz-intro-visual"><div className="spark spark-one">✦</div><Character config={character} emotion="excited" pose="bounce" compact /><div className="intro-orb">♡</div></div><span className="eyebrow">ТЕСТ ОТ {publicTest.owner_name.toUpperCase()}</span><h1>{publicTest.title}</h1><p className="body-copy">Проверь, насколько хорошо ты знаешь {publicTest.owner_name}. Здесь всего {publicTest.questions.length} вопросов — отвечай быстро, не подглядывая.</p><div className="quiz-meta"><span><b>{publicTest.questions.length}</b> вопросов</span><span><b>∞</b> попыток</span><span><b>♥</b> fun</span></div><button className="primary-button wide" onClick={() => void beginTest()} disabled={busy}>Начать игру <span>→</span></button></> : currentQuestion ? <><div className="quiz-progress-header"><span>Вопрос {String(questionIndex + 1).padStart(2, "0")}</span><strong>{Math.round(((questionIndex + 1) / publicTest.questions.length) * 100)}%</strong></div><div className="progress-track"><i style={{ width: `${((questionIndex + 1) / publicTest.questions.length) * 100}%` }} /></div><div className="question-companion"><Character config={character} emotion="thinking" compact /><span>Выбирай сердцем.<br />Или памятью.</span></div><h2 className="quiz-question">{currentQuestion.text}</h2><div className="answer-grid">{currentQuestion.options.map((option, index) => <button className={`answer-card ${selectedOption === option ? "selected" : ""}`} key={option} disabled={busy} onClick={() => void answer(option)}><span className="answer-letter">{optionLetter(index)}</span><span>{option}</span><b>↗</b></button>)}</div></> : null}</section>{error && <div className="notice error">{error}</div>}{toast && <div className="toast">{toast}</div>}</main>;

  if (screen === "result" && result) { const scoreStyle = { background: `conic-gradient(#f25d9a ${result.percentage}%, #f2e7ef 0)` }; return <main className="app-shell result-screen"><header className="topbar">{backButton()}<span className="topbar-label">KNOWLY / ИТОГ</span><span className="topbar-dot pink" /></header><section className="result-card-new"><div className="result-confetti">✦ <span>✦</span> ♥</div><Character config={character} emotion={result.percentage >= 81 ? "proud" : "thinking"} pose="victory" compact /><span className="eyebrow">РЕЗУЛЬТАТ ГОТОВ</span><h1>Вы совпали на<br /><em>{result.percentage}%</em></h1><p className="result-subtitle">{result.percentage >= 81 ? "Это уже уровень лучших друзей." : result.percentage >= 61 ? "Очень неплохо. Вы явно на одной волне." : "Ничего, теперь есть повод узнать друг друга лучше."}</p><div className="result-score-row"><div className="score-ring-new" style={scoreStyle}><div><strong>{result.correct_answers}</strong><small>из {result.total_questions}</small></div></div><div className="score-note"><span>Твой результат</span><strong>{result.percentage}%</strong><small>ответов совпало</small></div></div>{resultDetail && !resultDetail.review_locked && <div className="review-list-new"><div className="review-heading"><strong>Разбор ответов</strong><span>{result.correct_answers}/{result.total_questions}</span></div>{resultDetail.review.map((item, index) => <div className={`review-row ${item.is_correct ? "correct" : "wrong"}`} key={item.question_id}><span className="review-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{item.is_correct ? "Точно в яблочко" : "Почти получилось"}</strong><small>Твой ответ: {item.selected_option}</small></div><b>{item.is_correct ? "✓" : "×"}</b></div>)}</div>}{resultDetail?.review_locked && !hasPremiumReview && products.find((item) => item.code === "premium_results") && <div className="premium-cta"><span className="premium-icon">✦</span><div><strong>Разблокировать разбор</strong><small>Узнай, где именно вы совпали — за {products.find((item) => item.code === "premium_results")?.stars} ⭐</small></div><button onClick={() => void buy(products.find((item) => item.code === "premium_results")!)}>Открыть</button></div>}<div className="result-actions"><button className="primary-button wide" onClick={shareResult}>Поделиться результатом <span>↗</span></button><button className="ghost-button wide" onClick={goHome}>Создать свой тест</button></div></section>{toast && <div className="toast">{toast}</div>}</main>; }

  if (screen === "create") return <main className="app-shell create-screen"><header className="topbar">{backButton()}<span className="topbar-label">KNOWLY / СОЗДАНИЕ</span><span className="topbar-dot violet" /></header><section className="create-heading"><div className="create-heading-character"><Character config={character} emotion="playful" compact /></div><div><span className="eyebrow">СОЗДАЙ СВОЮ ИГРУ</span><h1>Кто знает тебя лучше всех?</h1><p>Собери вопросы, отправь ссылку и узнай правду.</p></div></section><div className="step-chip"><span>01</span><div><strong>Сначала — заголовок</strong><small>Он задаст настроение всей игре</small></div></div><label className="field field-large"><span>Название теста</span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Например: Насколько ты меня знаешь?" /></label><div className="questions-heading"><div><span className="eyebrow">02 / ВОПРОСЫ</span><h2>Добавь свои вопросы</h2></div><span className="question-count">{validDrafts.length}/{drafts.length}</span></div>{drafts.map((draft, index) => <article className="draft-card" key={index}><div className="draft-card-top"><span className="draft-number">{String(index + 1).padStart(2, "0")}</span><div><strong>Вопрос {index + 1}</strong><small>{draft.options.filter(Boolean).length} варианта · {draft.correct_option ? "ответ выбран" : "выбери ответ"}</small></div><span className={`draft-status ${draft.text && draft.correct_option ? "done" : ""}`}>{draft.text && draft.correct_option ? "✓" : "·"}</span></div><input placeholder="Что я выберу вечером?" value={draft.text} onChange={(event) => updateDraft(index, { text: event.target.value })} />{draft.options.map((option, optionIndex) => <div className="option-input" key={optionIndex}><span>{optionLetter(optionIndex)}</span><input placeholder={`Вариант ${optionIndex + 1}`} value={option} onChange={(event) => updateOption(index, optionIndex, event.target.value)} /><label title="Отметить правильный ответ"><input type="radio" name={`correct-${index}`} checked={draft.correct_option === option && option !== ""} onChange={() => updateDraft(index, { correct_option: option })} /><i /></label></div>)}</article>)}<button className="add-question" onClick={() => setDrafts((items) => [...items, blankQuestion()])} disabled={drafts.length >= 15}><span>＋</span> Добавить ещё вопрос</button><button className="primary-button wide publish-button" onClick={() => void createTest()} disabled={busy || !canPublish}>Опубликовать тест <span>→</span></button>{!canPublish && <p className="form-hint">Заполни название, вопросы и выбери правильный вариант в каждой карточке.</p>}{error && <div className="notice error">{error}</div>}{toast && <div className="toast">{toast}</div>}</main>;

    if (onboardingRequired && screen === "home") return <main className="app-shell onboarding-screen"><header className="topbar home-topbar"><div className="brand-lockup"><span className="brand-mark">✦</span><div><strong>knowly</strong><small>your social quiz game</small></div></div><span className="onboarding-step">01 / 01</span></header><section className="onboarding-hero"><div className="onboarding-copy"><span className="eyebrow">ТВОЙ KNOWLY COMPANION</span><h1>Сначала создай<br /><em>своего персонажа.</em></h1><p>Это твой личный спутник в игре. Настрой его один раз — и он будет рядом в каждом тесте, результате и сообщении.</p></div><div className="onboarding-character"><Character config={character} emotion="happy" pose="bounce" /></div></section><CharacterEditor config={character} onChange={setCharacter} onSave={() => void saveCharacter()} saving={characterSaving} onboarding />{error && <div className="notice error">{error}</div>}{busy && <div className="loading-line"><i /> Создаём твоё пространство…</div>}</main>;

  return <main className="app-shell home-screen"><header className="topbar home-topbar">
<div className="brand-lockup"><span className="brand-mark">✦</span><div><strong>knowly</strong><small>social quiz game</small></div></div><div className="profile-orb">{firstName.slice(0, 1).toUpperCase()}</div></header><section className="home-hero"><div className="hero-copy"><span className="eyebrow">ПРИВЕТ, {firstName.toUpperCase()}</span><h1>Кто знает тебя<br /><em>по-настоящему?</em></h1><p>Создай игру о себе. Отправь друзьям. Смотри, кто угадал.</p><div className="hero-actions"><button className="primary-button" onClick={() => { setScreen("create"); haptic("light"); }}>Создать тест <span>→</span></button><button className="round-button" onClick={openBot} aria-label="Открыть бота">↗</button></div></div><div className="hero-character personal-scene"><div className="hero-bubble">твой<br /><b>♡</b></div><Character config={character} emotion="happy" pose="bounce" /></div><div className="hero-glow glow-one" /><div className="hero-glow glow-two" /></section><section className="stats-row"><div><span>Уровень</span><strong>{progress?.level ?? 1}</strong></div><div><span>XP собрано</span><strong>{progress?.xp ?? 0}</strong></div><div><span>Тестов создано</span><strong>{progress?.tests_created ?? tests.length}</strong></div></section><section className="section-block character-section"><div className="section-title"><div><span className="eyebrow">ТВОЙ ПЕРСОНАЖ</span><h2>Твой Knowly companion</h2></div><button className="text-button" onClick={() => setCharacterOpen((value) => !value)}>{characterOpen ? "Свернуть" : "Изменить"} <span>→</span></button></div>{characterOpen ? <CharacterEditor config={character} onChange={setCharacter} onSave={() => void saveCharacter()} saving={characterSaving} /> : <div className="companion-preview personal-preview"><div className="personal-thumb"><Character config={character} emotion="happy" compact /></div><div><strong>Это твой персонаж</strong><p>Он рядом в каждом тесте и результате. Настрой его так, чтобы он был похож на тебя.</p></div><button className="mini-arrow" onClick={() => setCharacterOpen(true)}>→</button></div>}</section><section className="section-block"><div className="section-title"><div><span className="eyebrow">ТВОИ ИГРЫ</span><h2>Тесты, которыми делятся</h2></div><span className="section-counter">{tests.length}</span></div>{tests.length === 0 ? <div className="empty-state"><div className="empty-icon">✦</div><strong>Здесь появится твоя первая игра</strong><p>Начни с трёх вопросов — это займёт пару минут.</p><button className="text-button" onClick={() => setScreen("create")}>Начать создание <span>→</span></button></div> : <div className="test-list">{tests.map((test, index) => <article className="test-card-new" key={test.id}><div className="test-card-index">{String(index + 1).padStart(2, "0")}</div><div className="test-card-copy"><strong>{test.title}</strong><span>{test.question_count} вопросов <i>·</i> опубликован</span></div><div className="test-card-actions"><button onClick={() => shareTest(test)} aria-label="Поделиться тестом">↗</button><button onClick={() => copyTest(test)} aria-label="Скопировать ссылку">⧉</button></div></article>)}</div>}</section><section className="bot-card"><div className="bot-card-symbol">✦</div><div><span className="eyebrow">НЕ ТЕРЯЙСЯ В ЧАТАХ</span><strong>Knowly живёт и в боте</strong><p>Запускай игры из Telegram, возвращайся к результатам и открывай своего персонажа в один тап.</p></div><button className="mini-arrow" onClick={openBot}>↗</button></section>{products.length > 0 ? <section className="section-block"><div className="section-title"><div><span className="eyebrow">ДОПОЛНЕНИЯ</span><h2>Открыть premium</h2></div><span className="section-counter">⭐</span></div>{products.map((product) => <article className="product-card-new" key={product.code}><div className="product-icon">✦</div><div><strong>{product.title}</strong><p>{product.description}</p></div>{entitlements.some((item) => item.entitlement_key === product.entitlement_key && item.active) ? <span className="owned">Доступно</span> : <button onClick={() => void buy(product)} disabled={busy}>{product.stars} ⭐</button>}</article>)}</section> : <div className="free-mode-note"><span>♡</span><div><strong>Сейчас всё бесплатно</strong><p>Мы тестируем Knowly. Premium появится позже — игровой процесс уже доступен.</p></div></div>}{error && <div className="notice error">{error}</div>}{busy && <div className="loading-line"><i /> Загружаем твой Knowly…</div>}{toast && <div className="toast">{toast}</div>}</main>;
}

const shareUrl = (token: string) => `https://t.me/${BOT_USERNAME}?startapp=${encodeURIComponent(token)}`;

createRoot(document.getElementById("root")!).render(<App />);
