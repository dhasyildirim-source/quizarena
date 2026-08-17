import React from "react";
import {
  View, Text, TouchableOpacity, StyleSheet, ActivityIndicator,
  ViewStyle, TextStyle, Pressable,
} from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from "react-native-reanimated";
import { theme, LEAGUE_COLORS } from "@/src/theme";

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function GButton({
  title, onPress, variant = "primary", icon, disabled, style, testID, loading,
}: {
  title: string; onPress: () => void; variant?: "primary" | "secondary" | "danger" | "success";
  icon?: keyof typeof Ionicons.glyphMap; disabled?: boolean; style?: ViewStyle; testID?: string; loading?: boolean;
}) {
  const scale = useSharedValue(1);
  const aStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  const bg =
    variant === "primary" ? theme.colors.gold
    : variant === "danger" ? theme.colors.red
    : variant === "success" ? theme.colors.green
    : theme.colors.bgLight;
  const color = variant === "primary" ? theme.colors.bg : theme.colors.white;
  return (
    <AnimatedTouchable
      testID={testID}
      activeOpacity={0.9}
      disabled={disabled || loading}
      onPressIn={() => (scale.value = withSpring(0.95))}
      onPressOut={() => (scale.value = withSpring(1))}
      onPress={onPress}
      style={[
        styles.btn,
        { backgroundColor: bg, borderWidth: variant === "secondary" ? 1 : 0, borderColor: theme.colors.border },
        (disabled || loading) && { opacity: 0.5 },
        aStyle, style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={color} />
      ) : (
        <View style={styles.btnRow}>
          {icon && <Ionicons name={icon} size={18} color={color} style={{ marginRight: 8 }} />}
          <Text style={[styles.btnText, { color }]}>{title}</Text>
        </View>
      )}
    </AnimatedTouchable>
  );
}

export function Card({ children, style, testID }: { children: React.ReactNode; style?: ViewStyle; testID?: string }) {
  return <View testID={testID} style={[styles.card, style]}>{children}</View>;
}

export function Avatar({ uri, size = 48, frame, style }: { uri?: string | null; size?: number; frame?: string | null; style?: ViewStyle }) {
  const border = frame ? theme.colors.gold : theme.colors.border;
  return (
    <View style={[{ width: size, height: size, borderRadius: size / 2, borderWidth: frame ? 2.5 : 1, borderColor: border, overflow: "hidden", backgroundColor: theme.colors.bgLight }, style]}>
      {uri ? (
        <Image source={{ uri }} style={{ width: "100%", height: "100%" }} contentFit="cover" transition={200} />
      ) : (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <Ionicons name="person" size={size * 0.5} color={theme.colors.muted} />
        </View>
      )}
    </View>
  );
}

export function LeagueBadge({ tier, size = 14 }: { tier: string; size?: number }) {
  const color = LEAGUE_COLORS[tier] || theme.colors.gold;
  return (
    <View style={[styles.leaguePill, { borderColor: color }]}>
      <Ionicons name="shield" size={size} color={color} />
      <Text style={[styles.leagueText, { color, fontSize: size - 2 }]}>{tier}</Text>
    </View>
  );
}

export function ProgressBar({ progress, color = theme.colors.blue, height = 8, bg = theme.colors.bgLight }: { progress: number; color?: string; height?: number; bg?: string }) {
  const p = Math.max(0, Math.min(1, progress));
  return (
    <View style={{ height, backgroundColor: bg, borderRadius: theme.radius.full, overflow: "hidden" }}>
      <View style={{ width: `${p * 100}%`, height: "100%", backgroundColor: color, borderRadius: theme.radius.full }} />
    </View>
  );
}

export function Pill({ icon, value, color = theme.colors.gold, testID }: { icon: keyof typeof Ionicons.glyphMap; value: string | number; color?: string; testID?: string }) {
  return (
    <View style={styles.pill} testID={testID}>
      <Ionicons name={icon} size={16} color={color} />
      <Text style={styles.pillText}>{value}</Text>
    </View>
  );
}

export function ScreenHeader({ title, subtitle, right, onBack }: { title: string; subtitle?: string; right?: React.ReactNode; onBack?: () => void }) {
  return (
    <View style={styles.header}>
      <View style={styles.headerRow}>
        {onBack && (
          <Pressable onPress={onBack} style={styles.backBtn} testID="back-button" hitSlop={10}>
            <Ionicons name="chevron-back" size={24} color={theme.colors.white} />
          </Pressable>
        )}
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle}>{title}</Text>
          {subtitle ? <Text style={styles.headerSub}>{subtitle}</Text> : null}
        </View>
        {right}
      </View>
    </View>
  );
}

export function Loading({ label }: { label?: string }) {
  return (
    <View style={styles.center}>
      <ActivityIndicator color={theme.colors.gold} size="large" />
      {label ? <Text style={[styles.headerSub, { marginTop: 12 }]}>{label}</Text> : null}
    </View>
  );
}

export function EmptyState({ icon = "cube-outline", text }: { icon?: keyof typeof Ionicons.glyphMap; text: string }) {
  return (
    <View style={styles.center}>
      <Ionicons name={icon} size={48} color={theme.colors.muted} />
      <Text style={[styles.headerSub, { marginTop: 12, textAlign: "center" }]}>{text}</Text>
    </View>
  );
}

export function GradientBg({ children, colors }: { children: React.ReactNode; colors?: [string, string, ...string[]] }) {
  return (
    <LinearGradient colors={colors || ["#0D1B3E", "#132347"]} style={{ flex: 1 }}>
      {children}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  btn: {
    borderRadius: theme.radius.full, paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md, alignItems: "center", justifyContent: "center", minHeight: 52,
  },
  btnRow: { flexDirection: "row", alignItems: "center" },
  btnText: { fontFamily: theme.fonts.bold, fontSize: 16 },
  card: {
    backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.md,
    borderWidth: 1, borderColor: theme.colors.border, padding: theme.spacing.md,
  },
  leaguePill: {
    flexDirection: "row", alignItems: "center", gap: 4, borderWidth: 1.5,
    borderRadius: theme.radius.full, paddingHorizontal: 10, paddingVertical: 4,
  },
  leagueText: { fontFamily: theme.fonts.bold, letterSpacing: 0.5 },
  pill: {
    flexDirection: "row", alignItems: "center", gap: 6, backgroundColor: theme.colors.bgLight,
    borderRadius: theme.radius.full, paddingHorizontal: 12, paddingVertical: 6,
    borderWidth: 1, borderColor: theme.colors.border,
  },
  pillText: { fontFamily: theme.fonts.bold, color: theme.colors.white, fontSize: 14 },
  header: { paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.sm },
  headerRow: { flexDirection: "row", alignItems: "center", gap: theme.spacing.sm },
  backBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center", borderRadius: theme.radius.full, backgroundColor: theme.colors.bgLight },
  headerTitle: { fontFamily: theme.fonts.display, fontSize: 24, color: theme.colors.white },
  headerSub: { fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.muted },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: theme.spacing.xl },
});
