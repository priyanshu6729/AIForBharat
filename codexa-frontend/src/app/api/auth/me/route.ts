import { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { AUTH_COOKIE_ACCESS, AUTH_COOKIE_ID } from "@/lib/auth/cookies";
import { proxyWithAuth } from "@/lib/api/proxy";

export async function GET(request: NextRequest) {
  const idToken = request.cookies.get(AUTH_COOKIE_ID)?.value;
  const accessToken = request.cookies.get(AUTH_COOKIE_ACCESS)?.value;

  if (!idToken && !accessToken) {
    return NextResponse.json({ authenticated: false, user: null });
  }

  return proxyWithAuth(request, { backendPath: "/api/auth/me", method: "GET" });
}
