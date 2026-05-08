import { useEffect, useMemo, useState } from "react";
import { Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import {
  fetchAdminOrders,
  fetchAdminReservations,
  fetchMenu,
  fetchProfile,
  updateOrderStatus,
  updateReservationStatus
} from "./api";
import { initTelegramWebApp } from "./twa";
import type { CartItem, Venue } from "./types";

const CART_KEY = "smartmenu_cart_v1";

export function App() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [cart, setCart] = useState<CartItem[]>(() => {
    const raw = localStorage.getItem(CART_KEY);
    return raw ? (JSON.parse(raw) as CartItem[]) : [];
  });
  const [profile, setProfile] = useState<{
    loyalty_points: number;
    orders_count: number;
    preferred_venue: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();

  const total = useMemo(() => cart.reduce((acc, item) => acc + item.price, 0), [cart]);

  useEffect(() => {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    const twa = initTelegramWebApp();
    void (async () => {
      try {
        const [loadedMenu, loadedProfile] = await Promise.all([
          fetchMenu(),
          fetchProfile(twa?.initDataUnsafe?.user?.id ?? 1)
        ]);
        setVenues(loadedMenu);
        setProfile(loadedProfile);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Load error");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    const twa = initTelegramWebApp();
    if (!twa) return;
    const onBack = () => navigate(-1);
    if (location.pathname !== "/") twa.BackButton.show();
    else twa.BackButton.hide();
    twa.BackButton.onClick(onBack);
    return () => twa.BackButton.offClick(onBack);
  }, [location.pathname, navigate]);

  useEffect(() => {
    const twa = initTelegramWebApp();
    if (!twa) return;
    if (cart.length === 0) {
      twa.MainButton.hide();
      return;
    }
    twa.MainButton.setParams({
      text: `Підтвердити (${total} грн)`,
      is_visible: true
    });
    const onClick = () => {
      twa.HapticFeedback.notificationOccurred("success");
      twa.sendData(JSON.stringify({ type: "order_confirm", cart, total }));
    };
    twa.MainButton.onClick(onClick);
    return () => twa.MainButton.offClick(onClick);
  }, [cart, total]);

  if (loading) return <div className="page">Loading SmartMenu...</div>;
  if (error) return <div className="page">Error: {error}</div>;

  return (
    <div className="page">
      <header className="header">
        <h1>SmartMenu WebApp</h1>
        <nav>
          <Link to="/">Меню</Link>
          <Link to="/cart">Кошик ({cart.length})</Link>
          <Link to="/profile">Профіль</Link>
          <Link to="/admin">Admin</Link>
        </nav>
      </header>

      <Routes>
        <Route
          path="/"
          element={<MenuScreen venues={venues} onAdd={(item) => setCart((prev) => [...prev, item])} />}
        />
        <Route
          path="/cart"
          element={
            <CartScreen
              cart={cart}
              total={total}
              onRemove={(dishId) => setCart((prev) => prev.filter((x) => x.dishId !== dishId))}
              onClear={() => setCart([])}
            />
          }
        />
        <Route path="/profile" element={<ProfileScreen profile={profile} />} />
        <Route path="/admin" element={<AdminScreen />} />
      </Routes>
    </div>
  );
}

function MenuScreen({
  venues,
  onAdd
}: {
  venues: Venue[];
  onAdd: (item: CartItem) => void;
}) {
  return (
    <section>
      {venues.map((venue) => (
        <article className="panel" key={venue.id}>
          <h2>{venue.name}</h2>
          {venue.categories.map((category) => (
            <div key={category.id}>
              <h3>{category.name}</h3>
              <ul className="list">
                {category.dishes.map((dish) => (
                  <li key={dish.id}>
                    <div>
                      <strong>{dish.name}</strong> - {dish.price} грн
                    </div>
                    <button
                      onClick={() =>
                        onAdd({
                          venueId: venue.id,
                          categoryId: category.id,
                          dishId: dish.id,
                          name: dish.name,
                          price: dish.price
                        })
                      }
                    >
                      Додати
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </article>
      ))}
    </section>
  );
}

function CartScreen({
  cart,
  total,
  onRemove,
  onClear
}: {
  cart: CartItem[];
  total: number;
  onRemove: (dishId: string) => void;
  onClear: () => void;
}) {
  return (
    <section className="panel">
      <h2>Кошик</h2>
      {cart.length === 0 ? (
        <p>Порожньо</p>
      ) : (
        <>
          <ul className="list">
            {cart.map((item) => (
              <li key={`${item.dishId}-${item.venueId}`}>
                <span>
                  {item.name} - {item.price} грн
                </span>
                <button onClick={() => onRemove(item.dishId)}>Видалити</button>
              </li>
            ))}
          </ul>
          <p>
            <strong>Разом: {total} грн</strong>
          </p>
          <button onClick={onClear}>Очистити</button>
        </>
      )}
    </section>
  );
}

function ProfileScreen({
  profile
}: {
  profile: {
    loyalty_points: number;
    orders_count: number;
    preferred_venue: string;
  } | null;
}) {
  return (
    <section className="panel">
      <h2>Профіль</h2>
      {!profile ? (
        <p>No profile data</p>
      ) : (
        <>
          <p>Бонуси: {profile.loyalty_points}</p>
          <p>Замовлень: {profile.orders_count}</p>
          <p>Улюблений заклад: {profile.preferred_venue}</p>
        </>
      )}
    </section>
  );
}

function AdminScreen() {
  const [reservations, setReservations] = useState<
    Array<{ reservation_id: number; user_id: number; venue: string; datetime_text: string; status: string }>
  >([]);
  const [orders, setOrders] = useState<
    Array<{ order_id: number; user_id: number; total: number; status: string }>
  >([]);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    try {
      const [res, ord] = await Promise.all([fetchAdminReservations(), fetchAdminOrders()]);
      setReservations(res);
      setOrders(ord);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Admin load failed");
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  return (
    <section className="panel">
      <h2>Admin Dashboard</h2>
      {error && <p>Error: {error}</p>}
      <h3>Reservations</h3>
      {reservations.length === 0 ? (
        <p>Немає бронювань</p>
      ) : (
        <ul className="list">
          {reservations.map((reservation) => (
            <li key={reservation.reservation_id}>
              <span>
                #{reservation.reservation_id} {reservation.venue} {reservation.datetime_text} [
                {reservation.status}]
              </span>
              <div>
                <button
                  onClick={async () => {
                    await updateReservationStatus(reservation.reservation_id, "accepted");
                    await reload();
                  }}
                >
                  Прийняти
                </button>
                <button
                  onClick={async () => {
                    await updateReservationStatus(reservation.reservation_id, "rejected");
                    await reload();
                  }}
                >
                  Відхилити
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <h3>Orders</h3>
      {orders.length === 0 ? (
        <p>Немає замовлень</p>
      ) : (
        <ul className="list">
          {orders.map((order) => (
            <li key={order.order_id}>
              <span>
                #{order.order_id} user={order.user_id} total={(order.total / 100).toFixed(2)} [{order.status}]
              </span>
              <div>
                <button
                  onClick={async () => {
                    await updateOrderStatus(order.order_id, "preparing");
                    await reload();
                  }}
                >
                  Готується
                </button>
                <button
                  onClick={async () => {
                    await updateOrderStatus(order.order_id, "completed");
                    await reload();
                  }}
                >
                  Завершено
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
