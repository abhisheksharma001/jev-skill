import { complete } from "./llm";
// Writes the reply the agent reviews before sending.
export async function draftReply(thread: string, kbArticles: string[]) {
  return complete(
    "Write a friendly, concise reply to the customer using the knowledge base articles. Summarize next steps. Do not promise refunds.",
    `${thread}\n\nKB:\n${kbArticles.join("\n---\n")}`,
    { maxTokens: 600 },
  );
}
