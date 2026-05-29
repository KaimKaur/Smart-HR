import { api } from "@/services/api";
import type { SuccessResponse, User } from "@/types/api";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordData {
  reset_token: string | null;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export async function login(payload: LoginRequest): Promise<TokenPair> {
  const { data } = await api.post<SuccessResponse<TokenPair>>("/auth/login", payload);
  return data.data;
}

export async function refreshToken(refresh_token: string): Promise<TokenPair> {
  const { data } = await api.post<SuccessResponse<TokenPair>>("/auth/refresh", {
    refresh_token,
  });
  return data.data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<SuccessResponse<User>>("/auth/me");
  return data.data;
}

export async function forgotPassword(payload: ForgotPasswordRequest): Promise<ForgotPasswordData> {
  const { data } = await api.post<SuccessResponse<ForgotPasswordData>>("/auth/forgot-password", payload);
  return data.data;
}

export async function resetPassword(payload: ResetPasswordRequest): Promise<void> {
  await api.post<SuccessResponse<null>>("/auth/reset-password", payload);
}
