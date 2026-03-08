import { NextRequest } from "next/server";

import { proxyWithAuth } from "@/lib/api/proxy";

export async function GET(request: NextRequest) {
  const pathId = request.nextUrl.searchParams.get("pathId");
  const backendPath = pathId ? `/api/learn/paths/${pathId}` : "/api/learn/paths";
  return proxyWithAuth(request, { backendPath, method: "GET", search: "" });
}
