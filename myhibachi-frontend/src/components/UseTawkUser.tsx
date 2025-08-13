"use client";
import { useEffect } from "react";
import { setTawkVisitor } from "@/lib/tawk";

interface UseTawkUserProps {
  name?: string;
  email?: string;
}

export default function UseTawkUser({ name, email }: UseTawkUserProps) {
  useEffect(() => {
    if (name || email) {
      setTawkVisitor({
        ...(name ? { name } : {}),
        ...(email ? { email } : {}),
      });
    }
  }, [name, email]);

  return null;
}
