import { complete } from "./llm";
// Decides if a refund request is inside policy: within 30 days of service date AND amount <= $500 AND not already refunded.
export async function refundEligible(ticket: string, serviceDate: string, amount: number, alreadyRefunded: boolean) {
  const out = await complete(
    "Answer true or false. Refund policy: request must be within 30 days of the service date, the amount must be <= $500, and the order must not already be refunded.",
    `Today: ${new Date().toISOString().slice(0, 10)}\nService date: ${serviceDate}\nAmount: $${amount}\nAlready refunded: ${alreadyRefunded}\nTicket: ${ticket}`,
    { maxTokens: 3 },
  );
  return out.trim().toLowerCase() === "true";
}
