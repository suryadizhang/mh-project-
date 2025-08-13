export function setTawkVisitor(attrs: Record<string, string>) {
  if (typeof window === "undefined") return;
  const Tawk_API = window.Tawk_API;
  if (!Tawk_API) return;

  if (typeof Tawk_API.onLoad === "function") {
    if (typeof Tawk_API.setAttributes === "function") {
      Tawk_API.setAttributes(attrs, function (err: unknown) {
        if (err) console.error("Tawk setAttributes error:", err);
      });
    }
  } else {
    // If widget not loaded yet, hook onLoad once
    window.Tawk_API = Tawk_API || {};
    window.Tawk_API.onLoad = function () {
      if (typeof window.Tawk_API?.setAttributes === "function") {
        window.Tawk_API.setAttributes(attrs, function (err: unknown) {
          if (err) console.error("Tawk setAttributes error:", err);
        });
      }
    };
  }
}

// Helper to open chat programmatically
export function openTawkChat() {
  if (typeof window === "undefined") return;
  const Tawk_API = window.Tawk_API;
  if (!Tawk_API) return;

  // Use maximize method to open the chat
  if (typeof Tawk_API.maximize === "function") {
    Tawk_API.maximize();
  }
}
