import React from "react";
import { View, Text, StyleSheet } from "react-native";
import Svg, { Circle } from "react-native-svg";
import { theme } from "@/src/theme";

// Circular countdown timer. Parent passes remaining seconds & total.
export function CircularTimer({
  remaining, total, size = 96,
}: {
  remaining: number; total: number; size?: number;
}) {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(1, remaining / total));
  const danger = remaining <= 5;
  const color = danger ? theme.colors.red : theme.colors.gold;
  const offset = circumference * (1 - progress);

  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size} style={{ position: "absolute", transform: [{ rotate: "-90deg" }] }}>
        <Circle cx={size / 2} cy={size / 2} r={radius} stroke={theme.colors.bgLight} strokeWidth={strokeWidth} fill="none" />
        <Circle
          cx={size / 2} cy={size / 2} r={radius} stroke={color} strokeWidth={strokeWidth}
          fill="none" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
        />
      </Svg>
      <Text style={[styles.text, { color }]}>{Math.ceil(remaining)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  text: { fontFamily: theme.fonts.mono, fontSize: 30, color: theme.colors.gold },
});
