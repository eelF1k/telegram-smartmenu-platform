import WebApp from "@twa-dev/sdk";

export function initTelegramWebApp() {
  try {
    WebApp.ready();
    WebApp.expand();
    return WebApp;
  } catch {
    return null;
  }
}
