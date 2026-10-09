export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");


export class ApiError extends Error {
  public status: number;
  public details: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? (localStorage.getItem("token") || sessionStorage.getItem("token")) : null;
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    let message = "Unauthorized";
    try {
      const errJson = await response.json();
      message = errJson.detail || message;
    } catch {}

    if (endpoint !== "/auth/login" && endpoint !== "/auth/register") {
      if (typeof window !== 'undefined') {
        localStorage.removeItem("token");
        sessionStorage.removeItem("token");
        window.location.href = "/login";
      }
    }
    throw new ApiError(message, 401);
  }

  if (!response.ok) {
    let message = "API Request Failed";
    let details = null;
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        message = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        message = errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
      } else if (errorData.detail && typeof errorData.detail === 'object') {
        message = JSON.stringify(errorData.detail);
      } else if (errorData.message) {
        message = errorData.message;
      }
      details = errorData;
    } catch {
      // Ignored
    }
    throw new ApiError(message, response.status, details);
  }

  return response.json() as Promise<T>;
}
