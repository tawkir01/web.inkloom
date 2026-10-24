
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || ""
).replace(/\/+$/, "");

export default function apiFetch(path, options) {
  const url = path.startsWith("/")
    ? `${API_BASE_URL}${path}`
    : path;

  return fetch(url, options);
}
