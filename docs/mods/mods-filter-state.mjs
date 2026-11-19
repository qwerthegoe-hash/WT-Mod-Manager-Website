// Pure, browser-independent state helpers used by the existing mod catalogue.
// No user IDs, sessions, searches or filter choices are persisted.
export const DEFAULT_MOD_FILTERS = Object.freeze({
  search: "",
  category: "all",
  sort: "new",
  author: "",
  favoritesOnly: false
});

export function hasActiveModFilters(values) {
  return String(values.search ?? "").trim() !== "" ||
    values.category !== DEFAULT_MOD_FILTERS.category ||
    values.sort !== DEFAULT_MOD_FILTERS.sort ||
    String(values.author ?? "") !== "" ||
    values.favoritesOnly === true;
}

export function emptyModState(view, filtered) {
  if (filtered) return {
    title: "Ничего не найдено",
    description: "Попробуй другой запрос или сбрось фильтры."
  };
  if (view === "downloads") return {
    title: "Пока нет скачанных модов",
    description: "Скачанные тобой моды появятся здесь."
  };
  if (view === "mine") return {
    title: "У тебя пока нет модов",
    description: "Создай мод и отправь его на проверку."
  };
  if (view === "moderation") return {
    title: "Очередь пуста",
    description: "В выбранном статусе сейчас нет модов."
  };
  return {
    title: "Здесь пока пусто",
    description: "Выбери другую категорию или добавь свою первую модификацию."
  };
}
