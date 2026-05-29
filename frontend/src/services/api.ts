import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth-storage";
import type { ErrorResponse, SuccessResponse } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";

type RefreshPayload = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
};

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return null;

    try {
      const { data } = await axios.post<SuccessResponse<RefreshPayload>>(
        `${BASE_URL}/auth/refresh`,
        { refresh_token: refreshToken },
      );
      setTokens(data.data.access_token, data.data.refresh_token);
      return data.data.access_token;
    } catch {
      clearTokens();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const status = error.response?.status;
    const originalRequest = error.config as RetriableRequestConfig | undefined;

    if (status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      const accessToken = await refreshAccessToken();
      if (!accessToken) {
        if (typeof window !== "undefined") window.location.href = "/login";
        return Promise.reject(error);
      }
      originalRequest.headers.Authorization = `Bearer ${accessToken}`;
      return api(originalRequest);
    }

    if (status === 403 && typeof window !== "undefined") {
      window.location.href = "/unauthorized";
    }

    return Promise.reject(error);
  },
);
