export function setTawkVisitor(attrs: Record<string, string>) {
  if (typeof window === "undefined") return;
  const Tawk_API = window.Tawk_API;
  if (!Tawk_API) return;

  const apply = () => {
    if (typeof Tawk_API.setAttributes === "function") {
      Tawk_API.setAttributes(attrs, (err: unknown) => {
        if (err) console.error("Tawk setAttributes error:", err);
      });
    }
  };

  if (typeof Tawk_API.onLoad === "function") {
    // If widget has onLoad, hook it
    const originalOnLoad = Tawk_API.onLoad;
    window.Tawk_API.onLoad = function() {
      if (originalOnLoad) originalOnLoad();
      apply();
    };
  } else {
    // Fallback: attempt after a short delay
    setTimeout(apply, 1500);
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
