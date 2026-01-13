"use client";

import { IEpisodeServers } from "@/types/episodes";
import { getLocalStorageJSON } from "./storage";

type Preference = {
  server: string;
  key: "sub" | "dub" | "raw";
};

export function getFallbackServer(serversData: IEpisodeServers | undefined): {
  serverName: string;
  key: string;
} {
  if (typeof window === "undefined") {
    return {
      serverName: "",
      key: "",
    };
  }

  const preference = getLocalStorageJSON<Preference | null>("serverPreference", null);

  if (preference?.key) {
    const serverList = serversData?.[preference.key];
    if (serverList && serverList[0]?.serverName) {
      return {
        serverName: serverList[0].serverName,
        key: preference.key,
      };
    }
  }

  if (serversData) {
    const keys: Array<"sub" | "dub" | "raw"> = ["sub", "dub", "raw"]; // Only valid keys
    for (const key of keys) {
      const serverList = serversData[key]; // Safely index the object
      if (serverList && serverList[0]?.serverName) {
        return {
          serverName: serverList[0].serverName,
          key,
        };
      }
    }
  }
  return {
    serverName: "",
    key: "",
  }; // Fallback if no valid server is found
}
