"use client";
import { usePathname } from "next/navigation";
import TawkScript from "./TawkScript";

const HIDE_ROUTES = ["/admin", "/superadmin", "/checkout"];

export default function TawkWrapper() {
  const pathname = usePathname();
  const hide = HIDE_ROUTES.some((r) => pathname?.startsWith(r));
  return hide ? null : <TawkScript />;
}
