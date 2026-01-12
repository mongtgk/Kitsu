import { AxiosError } from "axios";
import { ROUTES } from "@/constants/routes";
import { getAuthStore } from "@/store/auth-store";

export type ApiError = {
  code: string;
  message: string;
  status?: number;
  details?: unknown;
};

export const normalizeApiError = (error: unknown): ApiError => {
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
        message: payload?.message || "Session expired. Please sign in again.",
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
  if (error && typeof error === "object") {
    const candidate = error as ApiError;
    if (candidate.code && candidate.message) {
      return candidate;
    }
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

export const handleAuthError = (error: unknown): never | void => {
  const normalizedError = normalizeApiError(error);

  if (normalizedError.status === 401) {
    if (!isAuthFailureHandled(error)) {
      trackAuthFailureError(error);
      handleAuthFailure();
    }
    throw normalizedError;
  }

  // Network or unknown auth errors are propagated without logout.
  throw normalizedError;
};
