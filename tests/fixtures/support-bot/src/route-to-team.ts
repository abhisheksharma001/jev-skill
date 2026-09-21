// Pure rules: maps category -> queue. No LLM.
export const QUEUE: Record<string, string> = { billing: "fin", scheduling: "ops", technical: "tech", complaint: "cx-lead", sales: "sales", spam: "trash" };
export const routeToTeam = (category: string) => QUEUE[category] ?? "ops";
