import { NextRequest, NextResponse } from "next/server";

import { setAuthCookies } from "@/lib/auth/cookies";
import { proxyPublicPost } from "@/lib/api/proxy";

export async function POST(request: NextRequest) {
  const proxied = await proxyPublicPost(request, "/api/auth/login");

  if (!proxied.ok) {
    return proxied;
  }

  const data = await proxied.json();
  const response = NextResponse.json({
    user: {
      email: data.email,
    },
  });

  setAuthCookies(response, {
    idToken: data.id_token,
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresIn: data.expires_in,
  });

  return response;
}
