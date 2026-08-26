import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Product = {
  code: string;
  title: string;
  description: string;
  stars: number;
  entitlement_key: string;
};

type Entitlement = {
  entitlement_key: string;
  active: boolean;
};

type TelegramWebApp = {
  initData: string;
  initDataUnsafe?: { user?: { first_name?: string } };
  ready: () => void;
  expand: () => void;
  openInvoice?: (url: string, callback?: (status: string) => void) => void;
  showPopup?: (params: { title?: string; message: string; buttons?: { type: "ok" }[] }) => void;
};

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
let accessToken = "";

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(options.headers ?? {}),
    },
  });
  if (!response.ok) throw new Error((await response.text()) || "Ошибка API");
  return response.json() as Promise<T>;
}

async function authenticate(): Promise<void> {
  const initData = window.Telegram?.WebApp?.initData;
  if (!initData) throw new Error("Откройте приложение внутри Telegram");
  const response = await fetch(`${API_URL}/api/v1/auth/telegram`, {
    method: "POST",
    headers: { Authorization: `TWA ${initData}` },
  });
  if (!response.ok) throw new Error("Не удалось подтвердить Telegram-пользователя");
  const result = (await response.json()) as { access_token: string };
  accessToken = result.access_token;
}

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [entitlements, setEntitlements] = useState<Entitlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const firstName = useMemo(
    () => window.Telegram?.WebApp?.initDataUnsafe?.user?.first_name ?? "друг",
    [],
  );

  async function load() {
    setLoading(true);
    setError("");
    try {
      await authenticate();
      const [catalog, owned] = await Promise.all([
        api<Product[]>("/api/v1/payments/products"),
        api<Entitlement[]>("/api/v1/payments/entitlements"),
      ]);
      setProducts(catalog);
      setEntitlements(owned);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Неизвестная ошибка");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    webApp?.ready();
    webApp?.expand();
    void load();
  }, []);

  async function buy(product: Product) {
    setBusy(product.code);
    setError("");
    try {
      const invoice = await api<{ invoice_link: string }>("/api/v1/payments/invoice", {
        method: "POST",
        body: JSON.stringify({ product_code: product.code }),
      });
      const openInvoice = window.Telegram?.WebApp?.openInvoice;
      if (!openInvoice) throw new Error("Telegram invoice API недоступен");
      openInvoice(invoice.invoice_link, (status) => {
        if (status === "paid") void load();
        if (status === "failed" || status === "cancelled") {
          setError(status === "failed" ? "Оплата не прошла" : "Оплата отменена");
        }
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось открыть оплату");
    } finally {
      setBusy(null);
    }
  }

  const has = (key: string) => entitlements.some((item) => item.entitlement_key === key && item.active);

  return (
    <main className="shell">
      <section className="hero">
        <div className="orb" aria-hidden="true">✦</div>
        <p className="eyebrow">KNOWLY PREMIUM</p>
        <h1>Привет, {firstName}</h1>
        <p className="lead">Добавь тесту больше эмоций и открой особенные возможности за Telegram Stars.</p>
      </section>
      {error && <div className="notice error" role="alert">{error}</div>}
      {loading ? <div className="loading">Загружаем твой профиль…</div> : (
        <section className="catalog" aria-label="Платные функции">
          <div className="section-heading"><span>Для твоего теста</span><strong>Premium</strong></div>
          {products.map((product) => (
            <article className="product" key={product.code}>
              <div className="product-copy">
                <div className="product-icon">♡</div>
                <div><h2>{product.title}</h2><p>{product.description}</p></div>
              </div>
              {has(product.entitlement_key) ? (
                <span className="owned">Доступно</span>
              ) : (
                <button type="button" disabled={busy === product.code} onClick={() => void buy(product)}>
                  {busy === product.code ? "Открываем…" : `${product.stars} ⭐`}
                </button>
              )}
            </article>
          ))}
        </section>
      )}
      <p className="footnote">Оплата проходит внутри Telegram Stars. Доступ активируется только после подтверждения платежа сервером.</p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
