export const theme = {
  colors: {
    bg: "#0D1B3E",
    bgCard: "#132347",
    bgLight: "#1A2F5E",
    gold: "#F5C518",
    goldDark: "#C49A0E",
    blue: "#3B82F6",
    green: "#22C55E",
    red: "#EF4444",
    white: "#F0F4FF",
    muted: "#8896B3",
    border: "rgba(255,255,255,0.08)",
  },
  fonts: {
    display: "Nunito-ExtraBold",
    body: "Nunito-Regular",
    bold: "Nunito-Bold",
    mono: "SpaceMono-Regular",
  },
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
  radius: { sm: 8, md: 12, lg: 16, xl: 24, full: 999 },
} as const;

export const LEAGUE_COLORS: Record<string, string> = {
  BRONZE: "#CD7F32",
  SILVER: "#C0C0C0",
  GOLD: "#F5C518",
  PLATINUM: "#5AC8FA",
  DIAMOND: "#4FD1FF",
  MASTER: "#A855F7",
  CHAMPION: "#EF4444",
};

export const CATEGORY_LABELS: Record<string, string> = {
  HISTORY: "Tarih", GEOGRAPHY: "Coğrafya", SCIENCE: "Bilim",
  TECHNOLOGY: "Teknoloji", SPORTS: "Spor", ART_CULTURE: "Sanat",
  MUSIC: "Müzik", CINEMA: "Sinema", LITERATURE: "Edebiyat",
  MYTHOLOGY: "Mitoloji", FOOD: "Yemek", NATURE: "Doğa",
  POLITICS: "Siyaset", ECONOMY: "Ekonomi", GAMING: "Oyun", ANIMATION: "Animasyon",
};
