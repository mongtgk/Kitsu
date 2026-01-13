"use client";

import { useMemo } from "react";

import { type IAuth, useAuthSelector } from "@/store/auth-store";

export type Role = "guest" | "user" | "admin";
export type Permission =
  | "read:profile"
  | "write:profile"
  | "read:content"
  | "write:content"
  | "admin:*";

export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  guest: ["read:content"],
  user: ["read:profile", "write:profile", "read:content", "write:content"],
  admin: [
    "read:profile",
    "write:profile",
    "read:content",
    "write:content",
    "admin:*",
  ],
};

const isRole = (value: unknown): value is Role =>
  typeof value === "string" && value in ROLE_PERMISSIONS;

export const resolveRole = (auth: IAuth | null): Role => {
  const explicitRole = (auth as { role?: Role | string } | null)?.role;
  if (isRole(explicitRole)) {
    return explicitRole;
  }
  if (!auth) return "guest";
  return "user";
};

export const resolvePermissions = (role: Role): Permission[] => {
  return [...ROLE_PERMISSIONS[role]];
};

export const useRole = () => {
  const auth = useAuthSelector((state) => state.auth);
  return useMemo(() => resolveRole(auth), [auth]);
};

export const usePermissions = () => {
  const role = useRole();
  return useMemo(() => resolvePermissions(role), [role]);
};
