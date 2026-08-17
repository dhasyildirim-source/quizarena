// Simple module store to pass the last match result from Game -> Result screen.
export type MatchResult = {
  matchId: string;
  won: boolean;
  draw: boolean;
  winnerId: string | null;
  finalScores: { player: number; opponent: number };
  xpGained: number;
  coinsGained: number;
  rankPointsChange: number;
  newLevel: number | null;
  leveledUp: boolean;
  newAchievements: { title: string; coinReward: number }[];
  opponent: { displayName: string; avatarUrl?: string | null; league?: string };
  breakdown: {
    questionIndex: number;
    correct: boolean;
    points: number;
    timeMs: number;
    opponentCorrect: boolean;
  }[];
  mode: string;
};

let lastResult: MatchResult | null = null;

export function setMatchResult(r: MatchResult) {
  lastResult = r;
}
export function getMatchResult(): MatchResult | null {
  return lastResult;
}
