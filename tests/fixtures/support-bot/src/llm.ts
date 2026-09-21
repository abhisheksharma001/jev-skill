import OpenAI from "openai";
export const openai = new OpenAI();
export async function complete(system: string, user: string, opts: { maxTokens?: number; json?: boolean } = {}) {
  const r = await openai.chat.completions.create({
    model: opts.maxTokens && opts.maxTokens > 200 ? "gpt-5.5" : "gpt-5.4-mini",
    temperature: 0,
    max_tokens: opts.maxTokens ?? 20,
    response_format: opts.json ? { type: "json_object" } : undefined,
    messages: [{ role: "system", content: system }, { role: "user", content: user }],
  });
  return r.choices[0].message.content ?? "";
}
