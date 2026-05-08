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

export async function fetchAdminReservations(): Promise<
  Array<{ reservation_id: number; user_id: number; venue: string; datetime_text: string; status: string }>
> {
  const response = await fetch(`${apiBase}/admin/reservations`);
  if (!response.ok) throw new Error("Failed to load reservations");
  const data = (await response.json()) as { ok: boolean; reservations: any[] };
  return data.reservations;
}

export async function updateReservationStatus(
  reservationId: number,
  status: "accepted" | "rejected" | "cancelled" | "pending"
): Promise<void> {
  const response = await fetch(`${apiBase}/admin/reservations/${reservationId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  if (!response.ok) throw new Error("Failed to update reservation status");
}

export async function fetchAdminOrders(): Promise<
  Array<{ order_id: number; user_id: number; total: number; status: string }>
> {
  const response = await fetch(`${apiBase}/admin/orders`);
  if (!response.ok) throw new Error("Failed to load orders");
  const data = (await response.json()) as { ok: boolean; orders: any[] };
  return data.orders;
}

export async function updateOrderStatus(
  orderId: number,
  status: "accepted" | "preparing" | "delivering" | "completed" | "cancelled" | "created"
): Promise<void> {
  const response = await fetch(`${apiBase}/admin/orders/${orderId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  if (!response.ok) throw new Error("Failed to update order status");
}
