// Pure validation for developer messages; usable in browser and CI tests.
// Public form ID is not a secret. Server-side Formspree anti-spam is independent.
export const CONTACT_TOPICS = Object.freeze(["question","cooperation","feedback","other"]);

export function normalizeContactTopic(value) {
  return CONTACT_TOPICS.includes(value) ? value : "question";
}

export function validFormspreeId(value) {
  return typeof value === "string" && /^[A-Za-z0-9]{4,30}$/.test(value);
}

export function validDeveloperEmail(value) {
  return typeof value === "string" &&
    value.length <= 160 &&
    /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(value.trim());
}

export function validateContact(values) {
  if (!values || typeof values !== "object") return "invalid";
  if (String(values.website || "").trim()) return "honeypot";
  const name = String(values.name || "").trim();
  const email = String(values.email || "").trim();
  const title = String(values.title || "").trim();
  const message = String(values.message || "").trim();
  const url = String(values.reference || "").trim();
  if (name.length < 2 || name.length > 60) return "invalid";
  if (values.reply !== "email" && values.reply !== "none") return "invalid";
  if (values.reply === "email" && !validDeveloperEmail(email)) return "invalid";
  if (email && !validDeveloperEmail(email)) return "invalid";
  if (title.length < 5 || title.length > 120) return "invalid";
  if (message.length < 15 || message.length > 4000) return "invalid";
  if (url) {
    if (url.length > 500) return "invalid";
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return "invalid";
    } catch { return "invalid"; }
  }
  if (!values.consent) return "invalid";
  return "valid";
}
