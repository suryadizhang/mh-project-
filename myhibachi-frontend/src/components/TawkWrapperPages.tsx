"use client";
import { useRouter } from "next/router";
import TawkScript from "./TawkScript";

const HIDE_ROUTES = ["/admin", "/superadmin", "/checkout"];

export default function TawkWrapperPages() {
  const { pathname } = useRouter();
  const hide = HIDE_ROUTES.some((r) => pathname.startsWith(r));
  return hide ? null : <TawkScript />;
}
