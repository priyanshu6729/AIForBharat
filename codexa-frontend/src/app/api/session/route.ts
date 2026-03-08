import { NextRequest } from "next/server";

import { proxyWithAuth } from "@/lib/api/proxy";

export async function GET(request: NextRequest) {
  const id = request.nextUrl.searchParams.get("id");
  const backendPath = id ? `/api/session/${id}` : "/api/session";
  return proxyWithAuth(request, { backendPath, method: "GET", search: "" });
}

export async function POST(request: NextRequest) {
  return proxyWithAuth(request, { backendPath: "/api/session/save", method: "POST" });
}
