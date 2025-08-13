/*
 * Example Pages Router integration (_app.tsx)
 * Use this if your project uses Pages Router instead of App Router
 */

import type { AppProps } from "next/app";
import TawkWrapperPages from "@/components/TawkWrapperPages";
// import TawkEmailPrompt from "@/components/TawkEmailPrompt"; // Uncomment if using email prompt
import "@/app/globals.css";

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Component {...pageProps} />
      <TawkWrapperPages />
      {/* Optional: Uncomment to enable email capture prompt
      <TawkEmailPrompt />
      */}
    </>
  );
}
