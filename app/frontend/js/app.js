/**
 * app.js — Bootstrap de app.html
 *
 * Orden de arranque:
 *   1. Tema
 *   2. Logout
 *   3. GET /auth/me  (valida sesión + llena el chip)
 *   4. Router (estado de vistas)
 *   5. Tareas (filtros + primera carga)
 *   6. Botones "+ Nueva tarea"
 *   7. Badge de notificaciones
 */
import { apiFetch, clearToken } from "./api.js";
import { setupTheme } from "./theme.js";
import { initRouter } from "./router.js";
import { initTareas, abrirModal } from "./tareas.js";
import { initKanban }        from "./kanban.js";
import { initDashboard }     from "./dashboard.js";
import { initNotificaciones } from "./notificaciones.js";

/* ─── Usuario ─────────────────────────────────────────────────── */
async function cargarUsuario() {
  const u = await apiFetch("/auth/me");
  const inicial = (u.nombre || "·").trim().charAt(0).toUpperCase();
  document.querySelector("[data-user-initial]").textContent = inicial;
  document.querySelector("[data-user-name]").textContent    = u.nombre;
  document.querySelector("[data-user-email]").textContent   = u.email;
}

/* ─── Logout ──────────────────────────────────────────────────── */
function setupLogout() {
  document.querySelector('[data-action="logout"]')?.addEventListener("click", () => {
    clearToken();
    location.replace("login.html");
  });
}

/* ─── Botones "nueva tarea" (tareas y kanban) ─────────────────── */
function setupNuevaTarea() {
  document.querySelectorAll('[data-action="nueva-tarea"]').forEach(btn => {
    btn.addEventListener("click", () => abrirModal(null));
  });
}

/* ─── Badge de notificaciones ─────────────────────────────────── */
async function refrescarBadge() {
  const badge = document.querySelector('[data-badge="notificaciones"]');
  if (!badge) return;
  try {
    const { total } = await apiFetch("/notificaciones/conteo");
    if (total > 0) {
      badge.textContent = total;
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  } catch {
    badge.hidden = true;
  }
}

/* ─── Bootstrap ───────────────────────────────────────────────── */
async function bootstrap() {
  setupTheme();
  setupLogout();

  try {
    await cargarUsuario();
  } catch (err) {
    // apiFetch ya redirige en 401. Otros errores → toast.
    console.error(err);
    return;
  }

  initRouter();
  initTareas();
  initKanban();
  initDashboard();
  initNotificaciones();
  setupNuevaTarea();

  // Badge: carga inicial + refresco ante cambios en tareas
  refrescarBadge();
  document.addEventListener("tareas:changed", refrescarBadge);

  // Bloques 4-6 conectarán aquí:
  //   initKanban();  initDashboard();  initNotificaciones();
}

bootstrap();
