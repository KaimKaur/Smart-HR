const ACCESS_TOKEN_KEY = "smart_hr_access_token";
const REFRESH_TOKEN_KEY = "smart_hr_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  document.cookie = `access_token=${accessToken}; path=/; samesite=lax`;
}

export function setRoleCookie(roles: string[]) {
  if (typeof window === "undefined") return;
  document.cookie = `user_roles=${roles.join(",")}; path=/; samesite=lax`;
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  document.cookie = "access_token=; Max-Age=0; path=/; samesite=lax";
  document.cookie = "user_roles=; Max-Age=0; path=/; samesite=lax";
}
