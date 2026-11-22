/**
 * api.js — Cliente HTTP central.
 *
 * Uso:
 *   import { apiFetch, getToken, setToken, clearToken } from "./api.js";
 *
 *   const tareas = await apiFetch("/tareas");
 *   await apiFetch("/tareas", { method: "POST", body: JSON.stringify({...}) });
 *   await apiFetch("/auth/login", { method: "POST", body: ..., skipAuth: true });
 *
 * Responsabilidades:
 *   - URL base (misma origen si la app la sirve FastAPI, si no, fallback)
 *   - Adjuntar `Authorization: Bearer <token>` automáticamente
 *   - Redirigir a login en 401
 *   - Convertir `{detail: "..."}` o `{detail: [{msg: "..."}]}` en `Error`
 *   - Devolver `null` en 204
 */

const BASE_URL = window.location.origin.startsWith("http")
  ? window.location.origin           // servido por FastAPI en /app
  : "http://127.0.0.1:8000";         // abierto desde file:// u otro host

export function getToken() {
  return localStorage.getItem("access_token");
}

export function setToken(token) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

export async function apiFetch(path, options = {}) {
  const { skipAuth = false, ...rest } = options;

  const headers = {
    "Content-Type": "application/json",
    ...(rest.headers || {}),
  };

  if (!skipAuth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(BASE_URL + path, { ...rest, headers });
  } catch {
    throw new Error("No se pudo conectar con el servidor");
  }

  // Token expirado/inválido → fuera (salvo que el propio login devuelva 401)
  if (res.status === 401 && !skipAuth) {
    clearToken();
    location.replace("login.html");
    throw new Error("Sesión expirada");
  }

  // DELETE exitoso no trae body
  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    let msg = "Ocurrió un error inesperado";
    if (typeof data.detail === "string") msg = data.detail;
    else if (Array.isArray(data.detail) && data.detail[0]?.msg) msg = data.detail[0].msg;
    throw new Error(msg);
  }

  return data;
}
