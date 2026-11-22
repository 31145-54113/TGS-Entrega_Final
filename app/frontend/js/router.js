/**
 * router.js — Navegación por hash entre vistas.
 *
 * Vistas válidas: tareas | kanban | dashboard | notificaciones
 * Emite `document` → CustomEvent("view:changed", { detail: { view } })
 * cuando el usuario cambia de vista (NO en el render inicial).
 */
const VIEWS = ["tareas", "kanban", "dashboard", "notificaciones"];

function vistaActual() {
  const h = location.hash.replace("#", "");
  return VIEWS.includes(h) ? h : "tareas";
}

let vistaPrevia = null;

function render(fireEvent = true) {
  const view = vistaActual();
  const cambio = view !== vistaPrevia;
  vistaPrevia = view;

  document.querySelectorAll("[data-view]").forEach(el => {
    el.hidden = el.dataset.view !== view;
  });
  document.querySelectorAll("[data-nav]").forEach(el => {
    el.classList.toggle("is-active", el.dataset.nav === view);
  });

  if (fireEvent && cambio) {
    document.dispatchEvent(
      new CustomEvent("view:changed", { detail: { view } })
    );
  }
}

export function initRouter() {
  window.addEventListener("hashchange", () => render(true));
  if (!location.hash) history.replaceState(null, "", "#tareas");
  render(false); // bootstrap: no emite evento
}

export function irA(view) {
  if (vistaActual() === view) render(false);
  else location.hash = view;
}
