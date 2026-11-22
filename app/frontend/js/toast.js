/**
 * toast.js — Notificación flotante arriba a la derecha.
 * Uso: toast("Tarea creada", "success" | "error" | "info")
 */
export function toast(message, type = "info") {
  const stack = document.querySelector("[data-toasts]");
  if (!stack) return;

  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  stack.appendChild(el);

  setTimeout(() => {
    el.style.transition = "opacity 200ms, transform 200ms";
    el.style.opacity = "0";
    el.style.transform = "translateX(16px)";
    setTimeout(() => el.remove(), 200);
  }, 3500);
}
