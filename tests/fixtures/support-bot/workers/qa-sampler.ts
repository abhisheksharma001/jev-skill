import { complete } from "../src/llm";
// Nightly: grades 2% of sent replies (we can't afford more). Returns a score from 1-5 plus a one-paragraph explanation for the coach.
export async function gradeReply(thread: string, reply: string) {
  const out = await complete(
    'Rate the reply on a scale of 1-5 for accuracy, tone and completeness, then explain your reasoning in one paragraph. Return JSON {"score": number, "explanation": string}.',
    `THREAD:\n${thread}\n\nREPLY:\n${reply}`,
    { maxTokens: 400, json: true },
  );
  return JSON.parse(out) as { score: number; explanation: string };
}
