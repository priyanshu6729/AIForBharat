import { NextRequest } from "next/server";

import { proxyPublicPost } from "@/lib/api/proxy";

export async function POST(request: NextRequest) {
  return proxyPublicPost(request, "/api/auth/register");
}
