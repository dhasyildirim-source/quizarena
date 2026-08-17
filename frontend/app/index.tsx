import { useEffect } from "react";
import { View, Text, StyleSheet, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { FadeIn } from "react-native-reanimated";

import { useAuth } from "@/src/auth/AuthContext";
import { theme } from "@/src/theme";

export default function Index() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    const t = setTimeout(() => {
      router.replace(user ? "/(tabs)" : "/onboarding");
    }, 900);
    return () => clearTimeout(t);
  }, [loading, user]);

  return (
    <LinearGradient colors={["#0D1B3E", "#132347", "#0D1B3E"]} style={styles.container}>
      <Animated.View entering={FadeIn.duration(600)} style={styles.logoWrap}>
        <View style={styles.logoBadge}>
          <Ionicons name="flash" size={54} color={theme.colors.bg} />
        </View>
        <Text style={styles.title}>QuizArena</Text>
        <Text style={styles.subtitle}>Bilgi Savaşı Arenası</Text>
      </Animated.View>
      <ActivityIndicator color={theme.colors.gold} style={{ marginTop: 40 }} testID="splash-loader" />
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  logoWrap: { alignItems: "center" },
  logoBadge: {
    width: 100, height: 100, borderRadius: 28, backgroundColor: theme.colors.gold,
    alignItems: "center", justifyContent: "center", marginBottom: theme.spacing.lg,
    shadowColor: theme.colors.gold, shadowOpacity: 0.5, shadowRadius: 20, shadowOffset: { width: 0, height: 0 },
  },
  title: { fontFamily: theme.fonts.display, fontSize: 40, color: theme.colors.white, letterSpacing: -1 },
  subtitle: { fontFamily: theme.fonts.body, fontSize: 16, color: theme.colors.muted, marginTop: 4 },
});
