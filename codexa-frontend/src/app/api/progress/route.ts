import { NextRequest } from "next/server";

import { proxyWithAuth } from "@/lib/api/proxy";

export async function GET(request: NextRequest) {
  return proxyWithAuth(request, { backendPath: "/api/progress", method: "GET" });
}

export async function POST(request: NextRequest) {
  return proxyWithAuth(request, { backendPath: "/api/progress", method: "POST" });
}
