"use client";

import { RecommendationBadge } from "@/components/recruitment/recommendation-badge";
import { ScoreGauge } from "@/components/recruitment/score-gauge";
import { Button } from "@/components/ui/button";
import type { ResumeAnalysis } from "@/types/api";

function toSkillList(value: string[] | Record<string, unknown> | null | undefined): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.map(String);
  return Object.values(value).map(String);
}

export function AiAnalysisCard({
  analysis,
  onOverride,
}: {
  analysis: ResumeAnalysis;
  onOverride?: () => void;
}) {
  const matched = toSkillList(analysis.matched_skills);
  const missing = toSkillList(analysis.missing_skills);
  const explanation =
    typeof analysis.explanation === "string"
      ? analysis.explanation
      : JSON.stringify(analysis.explanation ?? {}, null, 2);

  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">AI Analysis</h3>
          <p className="text-sm text-muted-foreground">Status: {analysis.analysis_status}</p>
        </div>
        <ScoreGauge score={Number(analysis.score)} />
      </div>

      <div className="mt-4 flex items-center gap-2">
        <span className="text-sm font-medium">Recommendation:</span>
        <RecommendationBadge recommendation={analysis.recommendation} />
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <p className="mb-2 text-sm font-medium text-green-700">Matched skills</p>
          <div className="flex flex-wrap gap-2">
            {matched.length ? (
              matched.map((skill) => (
                <span key={skill} className="rounded-full bg-green-100 px-2 py-1 text-xs text-green-800">
                  {skill}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </div>
        </div>
        <div>
          <p className="mb-2 text-sm font-medium text-red-700">Missing skills</p>
          <div className="flex flex-wrap gap-2">
            {missing.length ? (
              missing.map((skill) => (
                <span key={skill} className="rounded-full bg-red-100 px-2 py-1 text-xs text-red-800">
                  {skill}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </div>
        </div>
      </div>

      {explanation ? (
        <pre className="mt-4 overflow-x-auto rounded-lg bg-muted p-3 text-xs whitespace-pre-wrap">
          {explanation}
        </pre>
      ) : null}

      {onOverride ? (
        <div className="mt-4">
          <Button type="button" variant="outline" onClick={onOverride}>
            Override AI Decision
          </Button>
        </div>
      ) : null}
    </div>
  );
}
