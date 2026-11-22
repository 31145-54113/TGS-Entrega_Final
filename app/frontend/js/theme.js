/**
 * theme.js — Toggle de tema claro/oscuro.
 * El tema ya viene aplicado por la IIFE del <head>; este módulo
 * solo sincroniza el icono y maneja el click.
 */
export function setupTheme() {
  const btns  = document.querySelectorAll("[data-theme-toggle]");
  const icons = document.querySelectorAll("[data-theme-icon]");

  const paint = () => {
    const t = document.documentElement.dataset.theme || "light";
    icons.forEach(el => (el.textContent = t === "dark" ? "☀" : "☾"));
  };

  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      const cur  = document.documentElement.dataset.theme || "light";
      const next = cur === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      localStorage.setItem("theme", next);
      paint();
    });
  });

  paint();
}
