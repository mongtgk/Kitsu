export type Role = "guest" | "user" | "admin";
export type Permission = string;

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

type MinimalAuth = { role?: Role | string; accessToken?: string | null } | null;

export const resolveRole = (auth: MinimalAuth): Role => {
  if (auth && isRole(auth.role)) {
    return auth.role;
  }
  if (auth?.accessToken) {
    return "user";
  }
  return "guest";
};

export const resolvePermissions = (role: Role): Permission[] => [
  ...ROLE_PERMISSIONS[role],
];
