import React, { useEffect } from "react";
import { Dimensions, StyleSheet, View } from "react-native";
import Animated, {
  useAnimatedStyle, useSharedValue, withDelay, withRepeat, withTiming, Easing,
} from "react-native-reanimated";

const { width, height } = Dimensions.get("window");
const COLORS = ["#F5C518", "#3B82F6", "#22C55E", "#EF4444", "#F0F4FF", "#A855F7"];

function Piece({ index }: { index: number }) {
  const startX = Math.random() * width;
  const size = 6 + Math.random() * 8;
  const color = COLORS[index % COLORS.length];
  const duration = 2200 + Math.random() * 1800;
  const delay = Math.random() * 1200;
  const translateY = useSharedValue(-40);
  const rotate = useSharedValue(0);
  const drift = useSharedValue(0);

  useEffect(() => {
    translateY.value = withDelay(delay, withRepeat(withTiming(height + 60, { duration, easing: Easing.linear }), -1, false));
    rotate.value = withRepeat(withTiming(360, { duration: 900, easing: Easing.linear }), -1, false);
    drift.value = withDelay(delay, withRepeat(withTiming((Math.random() - 0.5) * 80, { duration: 1200 }), -1, true));
  }, []);

  const style = useAnimatedStyle(() => ({
    transform: [
      { translateY: translateY.value },
      { translateX: drift.value },
      { rotate: `${rotate.value}deg` },
    ],
  }));

  return (
    <Animated.View
      style={[
        { position: "absolute", left: startX, top: 0, width: size, height: size * 1.6, backgroundColor: color, borderRadius: 2 },
        style,
      ]}
    />
  );
}

export function Confetti({ count = 60 }: { count?: number }) {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      {Array.from({ length: count }).map((_, i) => (
        <Piece key={i} index={i} />
      ))}
    </View>
  );
}
