import { NextResponse, type NextRequest } from "next/server";

import { PROTECTED_ROUTE_RULES, PUBLIC_ROUTES } from "@/constants/routes";

function parseRoles(request: NextRequest): string[] {
  const raw = request.cookies.get("user_roles")?.value;
  if (!raw) return [];
  return raw
    .split(",")
    .map((r) => r.trim())
    .filter(Boolean);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
  if (isPublic) return NextResponse.next();

  const accessToken = request.cookies.get("access_token")?.value;
  if (!accessToken) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  const matchingRule = PROTECTED_ROUTE_RULES.find((rule) => pathname.startsWith(rule.prefix));
  if (!matchingRule) return NextResponse.next();

  const roles = parseRoles(request);
  const hasRole = matchingRule.roles.some((role) => roles.includes(role));
  if (!hasRole) {
    const unauthorizedUrl = new URL("/unauthorized", request.url);
    return NextResponse.redirect(unauthorizedUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
