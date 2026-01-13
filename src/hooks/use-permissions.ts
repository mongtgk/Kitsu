"use client";

import { useMemo } from "react";

import { resolvePermissions } from "@/auth";
import { useRole } from "./use-role";

export const usePermissions = () => {
  const role = useRole();
  return useMemo(() => resolvePermissions(role), [role]);
};
