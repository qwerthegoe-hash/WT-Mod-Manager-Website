// Keep key user-facing capabilities present after security and performance changes.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..", "docs");
const read = name => fs.readFileSync(path.join(root, name), "utf8");
const pages = [
  ["index.html", ["community/community.html", "mods/mods.html", "profile/profile.html"]],
  ["community/community.html", ['id="messages"', 'id="sendMessage"', 'id="loadOlder"', 'id="messageInput"']],
  ["profile/profile.html", ['id="profileForm"', 'id="profileNickname"', 'id="saveProfile"', 'id="profileIsPublic"']],
  ["mods/mods.html", ['id="modsGrid"', 'id="modSubmitForm"', 'id="moderationTab"']],
  ["support/support.html", ['id="supportForm"', 'id="formStatus"']],
  ["creator/creator.html", ['id="creatorHeader"', 'id="creatorModsGrid"']],
];
for (const [file, expected] of pages) {
  const text = read(file);
  for (const phrase of expected) assert.ok(text.includes(phrase), `Lost capability ${file}: ${phrase}`);
}
const community = read("community/community.js");
for (const channel of ["general", "updates", "news", "ideas", "help"]) {
  assert.ok(new RegExp(`\\b${channel}:\\s*\\{`).test(community), `Missing community channel ${channel}`);
}
const mods = read("mods/mods.js");
for (const required of ["validateModZip", "modReviewReady", "mapWithConcurrency", "modAdminOverview"]) {
  assert.ok(mods.includes(required), `Missing mod capability ${required}`);
}
console.log("PASS: critical public routes, Community channels, profiles and mods remain present");
