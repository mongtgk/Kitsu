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
    handleAuthError(error);
  },
);

export { setAuthFailureHandler };
