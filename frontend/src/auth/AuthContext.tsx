import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { Platform } from "react-native";
import * as WebBrowser from "expo-web-browser";
import * as Linking from "expo-linking";

import { storage } from "@/src/utils/storage";
import { api, setToken } from "@/src/api";

export type User = {
  user_id: string;
  username: string;
  displayName: string;
  email: string;
  avatarUrl?: string | null;
  gender: string;
  level: number;
  currentXP: number;
  totalXP: number;
  coins: number;
  rankPoints: number;
  isPremium: boolean;
  activeTitle?: string | null;
  activeFrameId?: string | null;
  activeCardId?: string | null;
  totalMatches: number;
  wins: number;
  losses: number;
  currentStreak: number;
  longestStreak: number;
  loginStreak: number;
  countryCode?: string | null;
  [k: string]: any;
};

type AuthState = {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
  setUser: (u: User) => void;
};

const AuthContext = createContext<AuthState>({} as AuthState);
export const useAuth = () => useContext(AuthContext);

const AUTH_BASE = "https://auth.emergentagent.com";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    try {
      const me = await api<User>("/auth/me");
      setUserState(me);
    } catch {
      setUserState(null);
      await storage.secureRemove("qa_token");
      setToken(null);
    }
  }, []);

  const processSessionId = useCallback(async (sessionId: string) => {
    const data = await api<{ session_token: string; user: User }>("/auth/session", {
      method: "POST",
      body: { session_id: sessionId },
    });
    await storage.secureSet("qa_token", data.session_token);
    setToken(data.session_token);
    setUserState(data.user);
  }, []);

  useEffect(() => {
    (async () => {
      const token = await storage.secureGet<string>("qa_token", "");
      if (token) {
        setToken(token);
        await loadMe();
      }
      setLoading(false);
    })();
  }, [loadMe]);

  const signIn = useCallback(async () => {
    const redirectUrl =
      Platform.OS === "web" ? window.location.origin + "/" : Linking.createURL("auth");
    const authUrl = `${AUTH_BASE}/?redirect=${encodeURIComponent(redirectUrl)}`;

    if (Platform.OS === "web") {
      window.location.href = authUrl;
      return;
    }
    const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl);
    if (result.type === "success" && result.url) {
      const url = result.url;
      const match = url.match(/[#?&]session_id=([^&]+)/);
      if (match) {
        setLoading(true);
        try {
          await processSessionId(decodeURIComponent(match[1]));
        } finally {
          setLoading(false);
        }
      }
    }
  }, [processSessionId]);

  const signOut = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch {}
    await storage.secureRemove("qa_token");
    setToken(null);
    setUserState(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, signIn, signOut, refresh: loadMe, setUser: setUserState }}
    >
      {children}
    </AuthContext.Provider>
  );
}
