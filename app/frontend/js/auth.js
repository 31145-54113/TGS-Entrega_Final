/**
 * auth.js — Lógica de login.html
 *
 * Responsabilidades:
 *   - Cambiar entre tabs Login / Registro
 *   - Enviar POST /auth/login y /auth/registro
 *   - Guardar token y redirigir a app.html
 *   - Mostrar errores inline (sin alert())
 *   - Toggle de tema claro/oscuro
 */

import { apiFetch, setToken } from "./api.js";
import { setupTheme } from "./theme.js";

/* ─── Tabs ────────────────────────────────────────────────────────── */
function setupTabs() {
  const tabs   = document.querySelectorAll("[data-tab]");
  const panels = document.querySelectorAll("[data-form-panel]");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const name = tab.dataset.tab;

      tabs.forEach(t => {
        const active = t === tab;
        t.classList.toggle("is-active", active);
        t.setAttribute("aria-selected", active ? "true" : "false");
      });

      panels.forEach(p => {
        p.hidden = p.dataset.formPanel !== name;
      });
    });
  });
}

/* ─── Errores inline ──────────────────────────────────────────────── */
function showError(formName, message) {
  const el = document.querySelector(`[data-error-for="${formName}"]`);
  if (!el) return;
  el.textContent = message;
  el.hidden = !message;
}

/* ─── Submit genérico ─────────────────────────────────────────────── */
async function submitForm({ form, endpoint, formName, successLabel, loadingLabel }) {
  const data = Object.fromEntries(new FormData(form));
  const btn  = form.querySelector("button[type=submit]");

  showError(formName, "");
  btn.disabled = true;
  btn.textContent = loadingLabel;

  try {
    const res = await apiFetch(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
      skipAuth: true,
    });
    setToken(res.access_token);
    location.replace("app.html");
  } catch (err) {
    showError(formName, err.message);
    btn.disabled = false;
    btn.textContent = successLabel;
  }
}

/* ─── Bootstrap ───────────────────────────────────────────────────── */
setupTheme();
setupTabs();

const loginForm    = document.querySelector('[data-form="login"]');
const registroForm = document.querySelector('[data-form="registro"]');

loginForm?.addEventListener("submit", (e) => {
  e.preventDefault();
  submitForm({
    form: loginForm,
    endpoint: "/auth/login",
    formName: "login",
    successLabel: "Entrar",
    loadingLabel: "Entrando…",
  });
});

registroForm?.addEventListener("submit", (e) => {
  e.preventDefault();
  submitForm({
    form: registroForm,
    endpoint: "/auth/registro",
    formName: "registro",
    successLabel: "Crear cuenta",
    loadingLabel: "Creando…",
  });
});
