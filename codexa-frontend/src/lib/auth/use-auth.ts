"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authClient, ApiError } from "@/lib/api/client";
import type { AuthSession, UserIdentity } from "@/types/contracts";

const AUTH_QUERY_KEY = ["auth", "me"] as const;

export function useAuth() {
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: AUTH_QUERY_KEY,
    queryFn: authClient.me,
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: authClient.login,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: AUTH_QUERY_KEY });
    },
  });

  const signupMutation = useMutation({ mutationFn: authClient.signup });
  const verifyMutation = useMutation({ mutationFn: authClient.verify });

  const logoutMutation = useMutation({
    mutationFn: authClient.logout,
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: AUTH_QUERY_KEY });
    },
  });

  const user =
    meQuery.data && "sub" in meQuery.data && typeof meQuery.data.sub === "string"
      ? ({
          sub: meQuery.data.sub,
          email: meQuery.data.email,
          email_verified: meQuery.data.email_verified,
        } satisfies UserIdentity)
      : null;

  const authError = meQuery.error as ApiError | null;
  const isAuthenticated = Boolean(user) && !authError;
  const meDisplayError = authError && authError.status !== 401 ? authError : null;

  const session: AuthSession = {
    isAuthenticated,
    isLoading: meQuery.isLoading,
    refreshInFlight: meQuery.isFetching,
    user,
  };

  return {
    session,
    login: loginMutation.mutateAsync,
    signup: signupMutation.mutateAsync,
    verify: verifyMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    isAuthenticating: loginMutation.isPending || signupMutation.isPending || verifyMutation.isPending,
    authError: (loginMutation.error || signupMutation.error || verifyMutation.error || meDisplayError) as
      | ApiError
      | null,
  };
}
