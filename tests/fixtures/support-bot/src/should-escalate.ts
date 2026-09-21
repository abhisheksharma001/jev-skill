import { complete } from "./llm";
// Pages the on-call human if true. Runs on every ticket after classification.
export async function shouldEscalate(thread: string): Promise<boolean> {
  const out = await complete(
    "You are a triage assistant. Answer yes or no: does this customer need a human urgently (safety issue, legal threat, repeated failed contact, or threatens to cancel)?",
    thread,
    { maxTokens: 3 },
  );
  return out.trim().toLowerCase().startsWith("yes");
}
