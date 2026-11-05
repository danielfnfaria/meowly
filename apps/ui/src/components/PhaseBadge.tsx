import { Badge } from "@mantine/core";
import type { TaskPhase } from "@/api/client";

const COLORS: Record<TaskPhase, string> = {
  pending: "gray",
  running: "blue",
  succeeded: "green",
  failed: "red",
  cancelled: "orange",
};

export function PhaseBadge({ phase }: { phase: TaskPhase }) {
  return <Badge color={COLORS[phase]}>{phase}</Badge>;
}
