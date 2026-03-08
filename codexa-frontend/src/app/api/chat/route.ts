import { NextRequest } from "next/server";

import { proxyWithAuth } from "@/lib/api/proxy";

export async function POST(request: NextRequest) {
  return proxyWithAuth(request, { backendPath: "/api/chat", method: "POST" });
}
