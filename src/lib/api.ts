import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { env } from "next-runtime-env";
import {
  handleAuthError,
  normalizeApiError,
  setAuthFailureHandler,
  type ApiError,
} from "./auth-errors";
import { getAuthStore } from "@/store/auth-store";
export type { ApiError } from "./auth-errors";

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
      const { setAuth, setIsRefreshing } = authStore.getState();
      const refreshToken = authStore.getState().auth?.refreshToken;

      if (!refreshToken) {
        const terminalAuthError: ApiError = {
          code: "unauthorized",
          status: 401,
          message: "Session expired",
        };
        handleAuthError(terminalAuthError);
      }

      if (authStore.getState().isRefreshing) {
        return refreshPromise!
          .then((token) => {
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => {
            handleAuthError(err);
          });
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
            const refreshError: ApiError = {
              code: "unauthorized",
              status: 401,
              message: "Session expired",
            };
            handleAuthError(refreshError);
          }
          return newToken;
        } catch {
          const refreshFailure: ApiError = {
            code: "unauthorized",
            status: 401,
            message: "Session expired",
          };
          handleAuthError(refreshFailure);
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
      } catch {
        const refreshFailure: ApiError = {
          code: "unauthorized",
          status: 401,
          message: "Session expired",
        };
        handleAuthError(refreshFailure);
      }
    }

    if (error.response?.status === 401) {
      handleAuthError(error);
    }
    throw normalizeApiError(error);
  },
);

export { setAuthFailureHandler };
