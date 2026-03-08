import { redirect } from "next/navigation";

export default function SessionsRedirect({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const query = new URLSearchParams();
  Object.entries(searchParams).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((v) => query.append(key, v));
    } else if (value) {
      query.set(key, value);
    }
  });
  query.set("panel", "sessions");
  redirect(`/workspace${query.toString() ? `?${query.toString()}` : ""}`);
}
