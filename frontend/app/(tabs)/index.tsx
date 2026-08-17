import React, { useCallback, useState } from "react";
import {
  View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity, Dimensions,
} from "react-native";
import { useRouter } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { Image } from "expo-image";
import { SafeAreaView } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";

import { theme, LEAGUE_COLORS } from "@/src/theme";
import { api } from "@/src/api";
import { useAuth } from "@/src/auth/AuthContext";
import { Avatar, Card, GButton, Pill, ProgressBar, LeagueBadge, Loading } from "@/src/components/ui";

const { width } = Dimensions.get("window");

export default function Home() {
  const { user, refresh } = useAuth();
  const router = useRouter();
  const [summary, setSummary] = useState<any>(null);
  const [quests, setQuests] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [s, q, m] = await Promise.all([
        api("/home/summary"),
        api("/quests"),
        api("/matches/recent"),
      ]);
      setSummary(s);
      setQuests(q);
      setMatches(m);
      await refresh();
    } catch {}
    setLoading(false);
    setRefreshing(false);
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  if (loading || !summary || !user) {
    return <SafeAreaView style={styles.screen}><Loading label="Arena yükleniyor..." /></SafeAreaView>;
  }

  const leagueColor = LEAGUE_COLORS[summary.league] || theme.colors.gold;
  const leagueProgress =
    summary.leagueMax > summary.leagueMin
      ? (summary.rankPoints - summary.leagueMin) / (summary.leagueMax - summary.leagueMin)
      : 0.5;

  return (
    <SafeAreaView style={styles.screen} edges={["top"]}>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={theme.colors.gold} />}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.headerUser} onPress={() => router.push("/(tabs)/profile")} testID="home-profile-shortcut">
            <Avatar uri={user.avatarUrl} size={44} frame={user.activeFrameId} />
            <View>
              <Text style={styles.hello}>Merhaba,</Text>
              <Text style={styles.name}>{user.displayName}</Text>
            </View>
          </TouchableOpacity>
          <View style={styles.headerPills}>
            <Pill icon="logo-bitcoin" value={summary.coins} color={theme.colors.gold} testID="header-coin-counter" />
          </View>
        </View>

        {/* League Hero */}
        <Animated.View entering={FadeInDown.delay(50)}>
          <LinearGradient colors={[theme.colors.bgCard, theme.colors.bgLight]} style={styles.hero}>
            <View style={[styles.heroGlow, { backgroundColor: leagueColor }]} />
            <Ionicons name="shield-half" size={64} color={leagueColor} />
            <Text style={styles.heroLeague}>{summary.league}</Text>
            <Text style={styles.heroPoints}>{summary.rankPoints} <Text style={styles.heroPointsLabel}>RP</Text></Text>
            <Text style={styles.heroRank}>Küresel Sıra #{summary.globalRank}</Text>
            <View style={{ width: "100%", marginTop: theme.spacing.md }}>
              <ProgressBar progress={leagueProgress} color={leagueColor} height={10} />
            </View>
          </LinearGradient>
        </Animated.View>

        {/* Quick stats */}
        <View style={styles.statsRow}>
          <StatBox icon="trophy" label="Bugünkü Galibiyet" value={summary.winsToday} color={theme.colors.green} />
          <StatBox icon="flame" label="Seri" value={summary.currentStreak} color={theme.colors.red} />
          <StatBox icon="star" label="Seviye" value={summary.level} color={theme.colors.gold} />
        </View>

        {/* Featured mode */}
        <Animated.View entering={FadeInDown.delay(100)}>
          <TouchableOpacity activeOpacity={0.9} onPress={() => router.push("/matchmaking?mode=CLASSIC")} testID="home-play-button">
            <LinearGradient colors={["#3B82F6", "#1A2F5E"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.featured}>
              <View style={{ flex: 1 }}>
                <Text style={styles.featuredTag}>ÖNE ÇIKAN MOD</Text>
                <Text style={styles.featuredTitle}>Klasik Düello</Text>
                <Text style={styles.featuredDesc}>10 soru, tek galip. Hazır mısın?</Text>
                <View style={styles.featuredBtn}>
                  <Ionicons name="flash" size={18} color={theme.colors.bg} />
                  <Text style={styles.featuredBtnText}>Hemen Oyna</Text>
                </View>
              </View>
              <Ionicons name="flash" size={72} color="rgba(245,197,24,0.9)" />
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>

        {/* Login streak */}
        <Card style={styles.streakCard}>
          <View style={styles.streakHeader}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <Ionicons name="calendar" size={20} color={theme.colors.gold} />
              <Text style={styles.sectionTitle}>Giriş Serisi</Text>
            </View>
            <Text style={styles.streakDays}>{summary.loginStreak} gün</Text>
          </View>
          <View style={styles.streakDots}>
            {[1, 2, 3, 4, 5, 6, 7].map((d) => {
              const done = d <= summary.loginStreak;
              return (
                <View key={d} style={[styles.streakDay, done && styles.streakDayDone]}>
                  {done ? <Ionicons name="checkmark" size={14} color={theme.colors.bg} /> : <Text style={styles.streakDayNum}>{d}</Text>}
                </View>
              );
            })}
          </View>
          <Text style={styles.streakHint}>7 gün üst üste giriş → +150 altın</Text>
        </Card>

        {/* Daily quests */}
        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>Günlük Görevler</Text>
          <TouchableOpacity onPress={() => router.push("/quests")} testID="home-quests-link">
            <Text style={styles.link}>Tümü</Text>
          </TouchableOpacity>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: theme.spacing.sm }}>
          {quests.filter((q) => q.type === "DAILY").map((q) => (
            <Card key={q.id} style={styles.questCard}>
              <Text style={styles.questTitle} numberOfLines={2}>{q.title}</Text>
              <ProgressBar progress={q.progress / q.target} color={theme.colors.blue} />
              <Text style={styles.questProgress}>{q.progress}/{q.target}</Text>
              {q.status === "COMPLETED" ? (
                <GButton testID={`quest-claim-${q.id}`} title="+Al" variant="success" style={{ minHeight: 34, paddingVertical: 6 }} onPress={async () => { await api(`/quests/${q.id}/claim`, { method: "POST" }); load(); }} />
              ) : (
                <View style={styles.questReward}>
                  <Ionicons name="logo-bitcoin" size={14} color={theme.colors.gold} />
                  <Text style={styles.questRewardText}>{q.coinReward}</Text>
                </View>
              )}
            </Card>
          ))}
        </ScrollView>

        {/* Recent matches */}
        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>Son Maçlar</Text>
        </View>
        {matches.length === 0 ? (
          <Card><Text style={styles.emptyText}>Henüz maç yok. İlk düellona başla!</Text></Card>
        ) : (
          matches.map((m) => (
            <Card key={m.id} style={styles.matchRow}>
              <View style={[styles.matchBadge, { backgroundColor: m.won ? theme.colors.green : theme.colors.red }]}>
                <Text style={styles.matchBadgeText}>{m.won ? "G" : "M"}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.matchOpp}>{m.opponent}</Text>
                <Text style={styles.matchMode}>{m.mode}</Text>
              </View>
              <Text style={styles.matchScore}>{m.myScore} - {m.oppScore}</Text>
            </Card>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function StatBox({ icon, label, value, color }: any) {
  return (
    <View style={styles.statBox}>
      <Ionicons name={icon} size={20} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.bg },
  content: { padding: theme.spacing.md, gap: theme.spacing.md, paddingBottom: theme.spacing.xl },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  headerUser: { flexDirection: "row", alignItems: "center", gap: theme.spacing.sm },
  hello: { fontFamily: theme.fonts.body, color: theme.colors.muted, fontSize: 13 },
  name: { fontFamily: theme.fonts.display, color: theme.colors.white, fontSize: 18 },
  headerPills: { flexDirection: "row", gap: 8 },
  hero: {
    borderRadius: theme.radius.lg, padding: theme.spacing.lg, alignItems: "center",
    borderWidth: 1, borderColor: theme.colors.border, overflow: "hidden",
  },
  heroGlow: { position: "absolute", top: -60, width: 160, height: 160, borderRadius: 80, opacity: 0.12 },
  heroLeague: { fontFamily: theme.fonts.display, fontSize: 26, color: theme.colors.white, marginTop: 8, letterSpacing: 1 },
  heroPoints: { fontFamily: theme.fonts.mono, fontSize: 30, color: theme.colors.gold, marginTop: 2 },
  heroPointsLabel: { fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.muted },
  heroRank: { fontFamily: theme.fonts.body, color: theme.colors.muted, marginTop: 2 },
  statsRow: { flexDirection: "row", gap: theme.spacing.sm },
  statBox: {
    flex: 1, backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.md, padding: theme.spacing.md,
    alignItems: "center", gap: 4, borderWidth: 1, borderColor: theme.colors.border,
  },
  statValue: { fontFamily: theme.fonts.mono, fontSize: 20, color: theme.colors.white },
  statLabel: { fontFamily: theme.fonts.body, fontSize: 10, color: theme.colors.muted, textAlign: "center" },
  featured: {
    borderRadius: theme.radius.lg, padding: theme.spacing.lg, flexDirection: "row",
    alignItems: "center", overflow: "hidden",
  },
  featuredTag: { fontFamily: theme.fonts.bold, fontSize: 10, color: "rgba(240,244,255,0.7)", letterSpacing: 1 },
  featuredTitle: { fontFamily: theme.fonts.display, fontSize: 24, color: theme.colors.white, marginTop: 4 },
  featuredDesc: { fontFamily: theme.fonts.body, fontSize: 13, color: "rgba(240,244,255,0.8)", marginTop: 2 },
  featuredBtn: {
    flexDirection: "row", alignItems: "center", gap: 6, backgroundColor: theme.colors.gold,
    alignSelf: "flex-start", borderRadius: theme.radius.full, paddingHorizontal: 16, paddingVertical: 8, marginTop: theme.spacing.md,
  },
  featuredBtnText: { fontFamily: theme.fonts.bold, color: theme.colors.bg, fontSize: 14 },
  streakCard: { gap: theme.spacing.sm },
  streakHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  streakDays: { fontFamily: theme.fonts.mono, color: theme.colors.gold, fontSize: 16 },
  streakDots: { flexDirection: "row", justifyContent: "space-between", marginTop: 4 },
  streakDay: { width: 34, height: 34, borderRadius: 17, backgroundColor: theme.colors.bgLight, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: theme.colors.border },
  streakDayDone: { backgroundColor: theme.colors.gold, borderColor: theme.colors.gold },
  streakDayNum: { fontFamily: theme.fonts.bold, color: theme.colors.muted, fontSize: 12 },
  streakHint: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.muted },
  sectionHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  sectionTitle: { fontFamily: theme.fonts.bold, fontSize: 18, color: theme.colors.white },
  link: { fontFamily: theme.fonts.bold, fontSize: 14, color: theme.colors.gold },
  questCard: { width: 150, gap: 6 },
  questTitle: { fontFamily: theme.fonts.bold, fontSize: 13, color: theme.colors.white, minHeight: 34 },
  questProgress: { fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.muted },
  questReward: { flexDirection: "row", alignItems: "center", gap: 4 },
  questRewardText: { fontFamily: theme.fonts.bold, color: theme.colors.gold, fontSize: 13 },
  matchRow: { flexDirection: "row", alignItems: "center", gap: theme.spacing.md },
  matchBadge: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  matchBadgeText: { fontFamily: theme.fonts.display, color: theme.colors.white, fontSize: 16 },
  matchOpp: { fontFamily: theme.fonts.bold, color: theme.colors.white, fontSize: 15 },
  matchMode: { fontFamily: theme.fonts.body, color: theme.colors.muted, fontSize: 12 },
  matchScore: { fontFamily: theme.fonts.mono, color: theme.colors.white, fontSize: 16 },
  emptyText: { fontFamily: theme.fonts.body, color: theme.colors.muted, textAlign: "center" },
});
