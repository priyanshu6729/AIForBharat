import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_COOKIE_ACCESS,
  AUTH_COOKIE_ID,
  AUTH_COOKIE_REFRESH,
  setAuthCookies,
} from "@/lib/auth/cookies";
import { refreshWithCognito } from "@/lib/auth/refresh";
import { BACKEND_URL, CODEXA_INTENT_HEADER, CODEXA_INTENT_VALUE } from "@/lib/api/constants";

type ProxyOptions = {
  backendPath: string;
  method?: string;
  passThroughStream?: boolean;
  search?: string;
};

function buildBackendUrl(path: string, search: string) {
  return `${BACKEND_URL}${path}${search}`;
}

function rejectCsrfIfNeeded(request: NextRequest): NextResponse | null {
  if (["GET", "HEAD", "OPTIONS"].includes(request.method)) {
    return null;
  }

  const intent = request.headers.get(CODEXA_INTENT_HEADER);
  if (intent !== CODEXA_INTENT_VALUE) {
    return NextResponse.json(
      { detail: "Missing or invalid intent header" },
      { status: 403 }
    );
  }

  return null;
}

async function readSafeBody(request: NextRequest) {
  if (["GET", "HEAD"].includes(request.method)) return undefined;
  const text = await request.text();
  return text || undefined;
}

async function forwardToBackend(
  url: string,
  method: string,
  bearerToken: string,
  body?: string,
  headers: HeadersInit = {}
) {
  return fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${bearerToken}`,
      "Content-Type": "application/json",
      ...headers,
    },
    body,
    cache: "no-store",
  });
}

async function normalizeBackendResponse(response: Response, passThroughStream?: boolean) {
  const contentType = response.headers.get("content-type") || "";

  if (passThroughStream && response.body) {
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "Content-Type": contentType || "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  }

  if (contentType.includes("application/json")) {
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  }

  const text = await response.text();
  return new NextResponse(text, { status: response.status });
}

export async function proxyWithAuth(request: NextRequest, options: ProxyOptions) {
  const csrfError = rejectCsrfIfNeeded(request);
  if (csrfError) return csrfError;

  const method = options.method || request.method;
  const search = options.search ?? request.nextUrl.search;
  const url = buildBackendUrl(options.backendPath, search);
  const body = await readSafeBody(request);

  const idToken = request.cookies.get(AUTH_COOKIE_ID)?.value;
  const accessToken = request.cookies.get(AUTH_COOKIE_ACCESS)?.value;
  const refreshToken = request.cookies.get(AUTH_COOKIE_REFRESH)?.value;

  const bearer = idToken || accessToken;
  if (!bearer) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  let backendRes = await forwardToBackend(url, method, bearer, body);

  let refreshed = false;
  if (backendRes.status === 401 && refreshToken) {
    const nextTokens = await refreshWithCognito(refreshToken);
    if (nextTokens?.idToken || nextTokens?.accessToken) {
      const retriedBearer = nextTokens.idToken || nextTokens.accessToken || bearer;
      backendRes = await forwardToBackend(url, method, retriedBearer, body);
      refreshed = true;

      const response = await normalizeBackendResponse(backendRes, options.passThroughStream);
      setAuthCookies(response, {
        idToken: nextTokens.idToken,
        accessToken: nextTokens.accessToken,
        refreshToken,
        expiresIn: nextTokens.expiresIn,
      });
      return response;
    }
  }

  const response = await normalizeBackendResponse(backendRes, options.passThroughStream);
  if (!refreshed && backendRes.status === 401) {
    response.cookies.delete(AUTH_COOKIE_ID);
    response.cookies.delete(AUTH_COOKIE_ACCESS);
    response.cookies.delete(AUTH_COOKIE_REFRESH);
  }
  return response;
}

export async function proxyPublicPost(request: NextRequest, backendPath: string) {
  const csrfError = rejectCsrfIfNeeded(request);
  if (csrfError) return csrfError;

  const text = await request.text();
  const response = await fetch(`${BACKEND_URL}${backendPath}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: text,
    cache: "no-store",
  });

  return normalizeBackendResponse(response);
}
