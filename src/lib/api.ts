import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { env } from "next-runtime-env";
import { ROUTES } from "@/constants/routes";
import { getAuthStore } from "@/store/auth-store";

const baseURL =
  env("NEXT_PUBLIC_API_BASE_URL") ||
  env("NEXT_PUBLIC_API_URL") ||
  "";

export const api = axios.create({
  baseURL,
  timeout: 10000,
});

const authClient = axios.create({
  baseURL,
  timeout: 10000,
});

type TokenPayload = {
  access_token?: string;
  accessToken?: string;
  token?: string;
  refresh_token?: string;
  refreshToken?: string;
};

let refreshPromise: Promise<string | null> | null = null;

const extractTokens = (payload: TokenPayload) => {
  const accessToken =
    payload?.access_token ||
    payload?.accessToken ||
    payload?.token ||
    "";
  const refreshToken =
    payload?.refresh_token ||
    payload?.refreshToken ||
    "";
  return { accessToken, refreshToken };
};

const resolveAccessToken = (tokens: ReturnType<typeof extractTokens>) => {
  const fallbackToken = getAuthStore().getState().auth?.accessToken || null;
  if (!tokens.accessToken && fallbackToken) {
    // eslint-disable-next-line no-console
    console.warn("Using existing access token because refresh returned none");
  }
  return tokens.accessToken || fallbackToken;
};

export type ApiError = {
  code: string;
  message: string;
  status?: number;
  details?: unknown;
};

const normalizeApiError = (error: unknown): ApiError => {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const payload = error.response?.data as {
      code?: string;
      message?: string;
      details?: unknown;
    } | undefined;
    const baseMessage =
      typeof payload?.message === "string"
        ? payload.message
        : error.message || "Request failed. Please try again.";
    if (status === 401) {
      return {
        code: payload?.code || "unauthorized",
        message:
          payload?.message || "Session expired. Please sign in again.",
        details: payload?.details,
        status,
      };
    }
    if (status === 403) {
      return {
        code: payload?.code || "forbidden",
        message: payload?.message || "Access denied.",
        details: payload?.details,
        status,
      };
    }
    if (status && status >= 500) {
      return {
        code: payload?.code || "server_error",
        message:
          payload?.message ||
          "Something went wrong on our side. Please try again.",
        details: payload?.details,
        status,
      };
    }
    if (error.code === "ECONNABORTED") {
      return {
        code: "timeout",
        message: "Request timed out. Please retry.",
        status,
        details: payload?.details,
      };
    }
    return {
      code: payload?.code || "request_failed",
      message: baseMessage,
      status,
      details: payload?.details,
    };
  }
  return {
    code: "unknown_error",
    message: "Unexpected error occurred.",
  };
};

// Tracks error objects that already triggered auth handling to avoid duplicate redirects
const handledAuthFailures = new WeakSet<object>();

const authFailureHandlers = new Set<(redirectTo: string) => void>();

export const setAuthFailureHandler = (handler: (redirectTo: string) => void) => {
  authFailureHandlers.add(handler);
  return () => {
    authFailureHandlers.delete(handler);
  };
};

const isAuthFailureHandled = (error: unknown) =>
  error && typeof error === "object" && handledAuthFailures.has(error as object);

const trackAuthFailureError = (error: unknown) => {
  if (error && typeof error === "object") {
    handledAuthFailures.add(error as object);
  }
};

const navigateHome = () => {
  if (typeof window === "undefined" || window.location.pathname === ROUTES.HOME) {
    return;
  }
  window.location.replace(ROUTES.HOME);
};

let isHandlingAuthFailure = false;

const handleAuthFailure = () => {
  if (isHandlingAuthFailure) {
    return;
  }
  isHandlingAuthFailure = true;
  try {
    getAuthStore().getState().clearAuth();
    if (authFailureHandlers.size > 0) {
      authFailureHandlers.forEach((handler) => handler(ROUTES.HOME));
      return;
    }
    navigateHome();
  } finally {
    isHandlingAuthFailure = false;
  }
};

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAuthStore().getState().auth?.accessToken;
  if (token) {
    // eslint-disable-next-line no-param-reassign
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const authStore = getAuthStore();
      const { clearAuth, setAuth, setIsRefreshing } = authStore.getState();
      const refreshToken = authStore.getState().auth?.refreshToken;

      if (!refreshToken) {
        clearAuth();
        return Promise.reject(normalizeApiError(error));
      }

      if (authStore.getState().isRefreshing) {
        return refreshPromise!
          .then((token) => {
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(normalizeApiError(err)));
      }

      setIsRefreshing(true);

      refreshPromise = (async () => {
        try {
          const { data } = await authClient.post("/auth/refresh", {
            refresh_token: refreshToken,
          });
          const tokens = extractTokens(data as TokenPayload);
          const currentAuth = authStore.getState().auth;
          if (currentAuth) {
            setAuth({
              ...currentAuth,
              accessToken: tokens.accessToken || currentAuth.accessToken,
              refreshToken: tokens.refreshToken || currentAuth.refreshToken,
            });
          }
          // Prefer freshly issued token; fall back to stored token only when backend omits tokens
          // Some refresh endpoints may skip returning tokens if a session was just rotated.
          // In that case we reuse the last known access token to avoid dropping the user abruptly.
          const newToken = resolveAccessToken(tokens);
          if (!newToken) {
            const apiError = normalizeApiError(
              new Error("No token returned from refresh"),
            );
            clearAuth();
            throw apiError;
          }
          return newToken;
        } catch (err) {
          trackAuthFailureError(err);
          handleAuthFailure();
          throw err;
        } finally {
          setIsRefreshing(false);
          refreshPromise = null;
        }
      })();

      try {
        const newToken = await refreshPromise;
        if (originalRequest.headers && newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return api(originalRequest);
      } catch (err) {
        return Promise.reject(normalizeApiError(err));
      }
    }

    const normalizedError = normalizeApiError(error);
    if (normalizedError.status === 401 && !isAuthFailureHandled(error)) {
      trackAuthFailureError(error);
      handleAuthFailure();
    }
    return Promise.reject(normalizedError);
  },
);

export const parseApiError = normalizeApiError;
