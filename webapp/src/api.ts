import type { Venue } from "./types";

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchMenu(): Promise<Venue[]> {
  const response = await fetch(`${apiBase}/webapp/menu`);
  if (!response.ok) throw new Error("Failed to load menu");
  const data = (await response.json()) as { ok: boolean; venues: Venue[] };
  return data.venues;
}

export async function fetchProfile(userId: number): Promise<{
  loyalty_points: number;
  orders_count: number;
  preferred_venue: string;
}> {
  const response = await fetch(`${apiBase}/webapp/profile/${userId}`);
  if (!response.ok) throw new Error("Failed to load profile");
  const data = (await response.json()) as {
    ok: boolean;
    profile: { loyalty_points: number; orders_count: number; preferred_venue: string };
  };
  return data.profile;
}
