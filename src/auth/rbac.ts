"use client";

import { useAuthSelector, type IAuth } from "@/store/auth-store";

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

export const resolveRole = (auth: IAuth | null | undefined): Role => {
  if (!auth?.accessToken) {
    return "guest";
  }
  return "user";
};

export const resolvePermissions = (role: Role): Permission[] => {
  return ROLE_PERMISSIONS[role] ?? [];
};

export const getCurrentRole = (auth: IAuth | null | undefined): Role => {
  return resolveRole(auth);
};

export const getCurrentPermissions = (
  auth: IAuth | null | undefined,
): Permission[] => {
  const role = resolveRole(auth);
  return resolvePermissions(role);
};

export const useRole = (): Role => {
  const auth = useAuthSelector((state) => state.auth);
  return resolveRole(auth);
};

export const usePermissions = (): Permission[] => {
  const role = useRole();
  return resolvePermissions(role);
};
