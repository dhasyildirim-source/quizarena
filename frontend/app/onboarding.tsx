import React, { useState } from "react";
import { View, Text, StyleSheet, Dimensions } from "react-native";
import { useRouter } from "expo-router";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";

import { theme } from "@/src/theme";
import { GButton } from "@/src/components/ui";

const { width } = Dimensions.get("window");

const SLIDES = [
  {
    icon: "flash" as const,
    title: "Gerçek Zamanlı Düellolar",
    desc: "Rakiplerinle 10 soruluk kıyasıya bilgi savaşına gir. Hız ve doğruluk her şeydir!",
    color: theme.colors.gold,
  },
  {
    icon: "trophy" as const,
    title: "Ligde Yüksel",
    desc: "Bronz'dan Şampiyon'a kadar yüksel. Puanlarını topla, sezon ödüllerini kap.",
    color: theme.colors.blue,
  },
  {
    icon: "sparkles" as const,
    title: "Koleksiyonunu Yap",
    desc: "Kazandığın altınlarla çerçeveler, ünvanlar ve rozetler satın al.",
    color: theme.colors.green,
  },
];

export default function Onboarding() {
  const router = useRouter();
  const [index, setIndex] = useState(0);
  const slide = SLIDES[index];
  const isLast = index === SLIDES.length - 1;

  return (
    <LinearGradient colors={["#0D1B3E", "#132347"]} style={{ flex: 1 }}>
      <SafeAreaView style={styles.container}>
        <Animated.View key={index} entering={FadeInDown.duration(400)} style={styles.content}>
          <View style={[styles.iconWrap, { shadowColor: slide.color, borderColor: slide.color }]}>
            <Ionicons name={slide.icon} size={72} color={slide.color} />
          </View>
          <Text style={styles.title}>{slide.title}</Text>
          <Text style={styles.desc}>{slide.desc}</Text>
        </Animated.View>

        <View style={styles.footer}>
          <View style={styles.dots}>
            {SLIDES.map((_, i) => (
              <View key={i} style={[styles.dot, i === index && styles.dotActive]} />
            ))}
          </View>
          <GButton
            testID="onboarding-next-button"
            title={isLast ? "Hadi Başlayalım" : "Devam Et"}
            icon={isLast ? "rocket" : undefined}
            onPress={() => (isLast ? router.replace("/signin") : setIndex(index + 1))}
          />
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: theme.spacing.lg, justifyContent: "space-between" },
  content: { flex: 1, alignItems: "center", justifyContent: "center", gap: theme.spacing.lg },
  iconWrap: {
    width: 160, height: 160, borderRadius: 44, backgroundColor: theme.colors.bgCard,
    alignItems: "center", justifyContent: "center", borderWidth: 2,
    shadowOpacity: 0.4, shadowRadius: 24, shadowOffset: { width: 0, height: 0 },
  },
  title: { fontFamily: theme.fonts.display, fontSize: 28, color: theme.colors.white, textAlign: "center" },
  desc: { fontFamily: theme.fonts.body, fontSize: 16, color: theme.colors.muted, textAlign: "center", lineHeight: 24, paddingHorizontal: theme.spacing.md },
  footer: { gap: theme.spacing.lg },
  dots: { flexDirection: "row", justifyContent: "center", gap: 8 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: theme.colors.bgLight },
  dotActive: { width: 24, backgroundColor: theme.colors.gold },
});
