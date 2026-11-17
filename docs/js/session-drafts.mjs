// WTMM: session-only drafts. No passwords, tokens or image bytes are ever saved.
// A draft is local to the current browser tab and disappears when the session ends.
const MAX_DRAFT_CHARS = 5000;
const KEY_PATTERN = /^[a-z0-9:_-]{1,120}$/i;

export function createSessionDrafts(storage, namespace) {
  if (!KEY_PATTERN.test(namespace)) throw new TypeError("Invalid draft namespace");
  const key = suffix => {
    if (!KEY_PATTERN.test(suffix)) throw new TypeError("Invalid draft key");
    return "wtmm:draft:" + namespace + ":" + suffix;
  };
  return Object.freeze({
    read(suffix) {
      try {
        const value = storage?.getItem(key(suffix));
        return typeof value === "string" ? value.slice(0, MAX_DRAFT_CHARS) : "";
      } catch { return ""; }
    },
    write(suffix, value) {
      if (typeof value !== "string") return false;
      try {
        if (!value) storage?.removeItem(key(suffix));
        else storage?.setItem(key(suffix), value.slice(0, MAX_DRAFT_CHARS));
        return true;
      } catch { return false; }
    },
    clear(suffix) {
      try { storage?.removeItem(key(suffix)); } catch { /* storage optional */ }
    }
  });
}
