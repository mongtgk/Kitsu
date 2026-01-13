import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { env } from "next-runtime-env";
import { handleAuthError, setAuthFailureHandler } from "./auth-errors";
import { getAuthStore } from "@/store/auth-store";

const baseURL =
  env("NEXT_PUBLIC_API_BASE_URL") ||
  env("NEXT_PUBLIC_API_URL") ||
  "";

export const api = axios.create({
  baseURL,
  timeout: 10000,
});

const refreshClient = axios.create({
  baseURL,
  timeout: 10000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAuthStore().getState().auth?.accessToken;
  if (token) {
    // eslint-disable-next-line no-param-reassign
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

type RetriableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const config = error.config as RetriableRequestConfig | undefined;
    const isRefreshRequest = config?.url?.includes("/auth/refresh");

    if (status === 403) {
      return handleAuthError(error);
    }

    if (status === 401 && config && !config._retry && !isRefreshRequest) {
      const authStore = getAuthStore();
      const refreshToken = authStore.getState().auth?.refreshToken;

      if (!refreshToken) {
        return handleAuthError(error);
      }

      config._retry = true;
      try {
        authStore.getState().setIsRefreshing(true);
        const refreshResponse = await refreshClient.post("/auth/refresh", {
          refresh_token: refreshToken,
        });
        const tokens = refreshResponse.data as {
          access_token?: string;
          refresh_token?: string;
          token?: string;
          accessToken?: string;
          refreshToken?: string;
        };
        const accessToken =
          tokens.access_token || tokens.accessToken || tokens.token;
        const newRefreshToken = tokens.refresh_token || tokens.refreshToken;

        if (!accessToken || !newRefreshToken) {
          throw new Error("Invalid refresh response");
        }

        const currentAuth = authStore.getState().auth;
        authStore.getState().setAuth({
          ...(currentAuth ?? {}),
          accessToken,
          refreshToken: newRefreshToken,
        });

        if (!config.headers) {
          config.headers = {};
        }
        config.headers.Authorization = `Bearer ${accessToken}`;
        return api(config);
      } catch (refreshError) {
        return handleAuthError(refreshError);
      } finally {
        authStore.getState().setIsRefreshing(false);
      }
    }

    return handleAuthError(error);
  },
);

export { setAuthFailureHandler };
