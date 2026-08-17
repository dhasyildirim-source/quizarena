import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import Animated, { FadeIn } from "react-native-reanimated";

import { theme } from "@/src/theme";
import { GButton } from "@/src/components/ui";
import { useAuth } from "@/src/auth/AuthContext";

export default function SignIn() {
  const { signIn, user, loading } = useAuth();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) router.replace("/(tabs)");
  }, [user]);

  const onGoogle = async () => {
    setError(null);
    setBusy(true);
    try {
      await signIn();
    } catch (e: any) {
      setError(e?.message || "Giriş başarısız oldu");
    } finally {
      setBusy(false);
    }
  };

  return (
    <LinearGradient colors={["#0D1B3E", "#132347", "#0D1B3E"]} style={{ flex: 1 }}>
      <SafeAreaView style={styles.container}>
        <Animated.View entering={FadeIn} style={styles.hero}>
          <View style={styles.logoBadge}>
            <Ionicons name="flash" size={48} color={theme.colors.bg} />
          </View>
          <Text style={styles.title}>QuizArena</Text>
          <Text style={styles.subtitle}>Arenaya katıl, efsane ol!</Text>
        </Animated.View>

        <View style={styles.footer}>
          {error ? (
            <Text style={styles.error} testID="signin-error">{error}</Text>
          ) : null}
          <GButton
            testID="google-signin-button"
            title="Google ile Giriş Yap"
            icon="logo-google"
            onPress={onGoogle}
            loading={busy || loading}
          />
          <Text style={styles.terms}>
            Giriş yaparak Kullanım Koşulları'nı kabul etmiş olursun.
          </Text>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: theme.spacing.lg, justifyContent: "space-between" },
  hero: { flex: 1, alignItems: "center", justifyContent: "center", gap: theme.spacing.md },
  logoBadge: {
    width: 96, height: 96, borderRadius: 26, backgroundColor: theme.colors.gold,
    alignItems: "center", justifyContent: "center", marginBottom: theme.spacing.md,
    shadowColor: theme.colors.gold, shadowOpacity: 0.5, shadowRadius: 20, shadowOffset: { width: 0, height: 0 },
  },
  title: { fontFamily: theme.fonts.display, fontSize: 40, color: theme.colors.white, letterSpacing: -1 },
  subtitle: { fontFamily: theme.fonts.body, fontSize: 16, color: theme.colors.muted },
  footer: { gap: theme.spacing.md },
  error: { fontFamily: theme.fonts.bold, color: theme.colors.red, textAlign: "center" },
  terms: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.muted, textAlign: "center" },
});
