import type { AuthTokens } from "@/lib/auth/cookies";

export async function refreshWithCognito(refreshToken: string): Promise<AuthTokens | null> {
  const tokenEndpoint = process.env.COGNITO_TOKEN_ENDPOINT;
  const clientId = process.env.COGNITO_CLIENT_ID;

  if (!tokenEndpoint || !clientId || !refreshToken) {
    return null;
  }

  const payload = new URLSearchParams({
    grant_type: "refresh_token",
    client_id: clientId,
    refresh_token: refreshToken,
  });

  const response = await fetch(tokenEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: payload.toString(),
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }

  const data = (await response.json()) as {
    id_token?: string;
    access_token?: string;
    expires_in?: number;
  };

  if (!data.id_token && !data.access_token) {
    return null;
  }

  return {
    idToken: data.id_token,
    accessToken: data.access_token,
    expiresIn: data.expires_in,
  };
}
