import { z } from "zod";
import { complete } from "./llm";
export const Category = z.enum(["billing", "scheduling", "technical", "complaint", "sales", "spam"]);
// Runs on every inbound ticket (~40k/day).
export async function classifyTicket(subject: string, body: string) {
  const out = await complete(
    "Classify the support ticket. Respond with one of the following: billing, scheduling, technical, complaint, sales, spam. Respond with the category only.",
    `Subject: ${subject}\n\n${body}`,
    { maxTokens: 5 },
  );
  return Category.parse(out.trim().toLowerCase());
}
