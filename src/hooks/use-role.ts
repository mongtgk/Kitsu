"use client";

import { useMemo } from "react";

import { resolveRole, type Role } from "@/auth";
import { useAuthSelector } from "@/store/auth-store";

export const useRole = (): Role => {
  const auth = useAuthSelector((state) => state.auth);
  return useMemo(() => resolveRole(auth), [auth]);
};
