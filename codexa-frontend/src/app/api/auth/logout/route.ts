import { NextRequest, NextResponse } from "next/server";

import { clearAuthCookies } from "@/lib/auth/cookies";
import { CODEXA_INTENT_HEADER, CODEXA_INTENT_VALUE } from "@/lib/api/constants";

export async function POST(request: NextRequest) {
  const intent = request.headers.get(CODEXA_INTENT_HEADER);
  if (intent !== CODEXA_INTENT_VALUE) {
    return NextResponse.json({ detail: "Missing or invalid intent header" }, { status: 403 });
  }

  const response = NextResponse.json({ message: "Logged out" });
  clearAuthCookies(response);
  return response;
}
