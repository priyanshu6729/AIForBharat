import { type NextResponse } from "next/server";

export const AUTH_COOKIE_ID = "codexa_id_token";
export const AUTH_COOKIE_ACCESS = "codexa_access_token";
export const AUTH_COOKIE_REFRESH = "codexa_refresh_token";

export type AuthTokens = {
  idToken?: string;
  accessToken?: string;
  refreshToken?: string;
  expiresIn?: number;
};

function baseCookieOptions(maxAge: number) {
  const domain = process.env.COOKIE_DOMAIN;
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge,
    ...(domain ? { domain } : {}),
  };
}

export function setAuthCookies(response: NextResponse, tokens: AuthTokens) {
  if (tokens.idToken) {
    response.cookies.set(AUTH_COOKIE_ID, tokens.idToken, baseCookieOptions(tokens.expiresIn ?? 3600));
  }
  if (tokens.accessToken) {
    response.cookies.set(AUTH_COOKIE_ACCESS, tokens.accessToken, baseCookieOptions(tokens.expiresIn ?? 3600));
  }
  if (tokens.refreshToken) {
    response.cookies.set(AUTH_COOKIE_REFRESH, tokens.refreshToken, baseCookieOptions(60 * 60 * 24 * 30));
  }
}

export function clearAuthCookies(response: NextResponse) {
  response.cookies.set(AUTH_COOKIE_ID, "", { ...baseCookieOptions(0), maxAge: 0 });
  response.cookies.set(AUTH_COOKIE_ACCESS, "", { ...baseCookieOptions(0), maxAge: 0 });
  response.cookies.set(AUTH_COOKIE_REFRESH, "", { ...baseCookieOptions(0), maxAge: 0 });
}
