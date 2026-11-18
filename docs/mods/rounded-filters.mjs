// Enhanced select controls for the mod catalog filters.
// The original <select> remains the single source of truth: changing a custom
// option dispatches the native 'change' event, preserving search, filtering,
// sorting and the five language variants from the existing application.
export function nextFilterIndex(current, key, length) {
  if (!length) return -1;
  if (key === "Home") return 0;
  if (key === "End") return length - 1;
  if (key === "ArrowDown") return (current + 1 + length) % length;
  if (key === "ArrowUp") return (current - 1 + length) % length;
  return current;
}

let activeDropdown = null;

export function upgradeModFilterSelects() {
  for (const id of ["modsCategory", "modsSort"]) {
    const select = document.getElementById(id);
    if (!select || select.dataset.roundedFilterReady === "true") continue;

    const field = select.parentElement;
    const label = field?.querySelector("span[id]");
    if (!field || !label) continue; // Keep the native control as a safe fallback.

    const root = document.createElement("div");
    root.className = "mods-select-root";
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "mods-select-trigger";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", id + "-menu");

    const text = document.createElement("span");
    text.className = "mods-select-value";
    text.id = id + "-selected";
    trigger.setAttribute("aria-labelledby", label.id + " " + text.id);
    const chevron = document.createElement("span");
    chevron.className = "mods-select-chevron";
    chevron.setAttribute("aria-hidden", "true");
    trigger.append(text, chevron);

    const menu = document.createElement("div");
    menu.id = id + "-menu";
    menu.className = "mods-select-menu";
    menu.setAttribute("role", "listbox");
    menu.setAttribute("aria-labelledby", label.id);
    menu.hidden = true;
    root.append(trigger, menu);

    let buttons = [];
    let focusedIndex = 0;
    let isOpen = false;
    let observer = null;
    const currentIndex = () => Math.max(0, [...select.options].findIndex(o => o.value === select.value));

    function syncOptions() {
      const chosen = select.selectedOptions[0];
      text.textContent = chosen ? chosen.textContent.trim() : "";
      const options = [...select.options];
      // Rebuild only when labels/values change; translations update native
      // option text via the site's localization observer.
      const updated = options.length !== buttons.length ||
        options.some((o, index) =>
          buttons[index]?.textContent !== o.textContent.trim() ||
          buttons[index]?.dataset.value !== o.value ||
          buttons[index]?.disabled !== o.disabled);
      if (updated) {
        const nodes = options.map((option, index) => {
          const item = document.createElement("button");
          item.type = "button";
          item.className = "mods-select-option";
          item.setAttribute("role", "option");
          item.id = id + "-choice-" + index;
          item.dataset.value = option.value;
          item.tabIndex = -1;
          item.disabled = option.disabled;
          item.textContent = option.textContent.trim();
          item.addEventListener("click", () => choose(index));
          return item;
        });
        menu.replaceChildren(...nodes);
        buttons = nodes;
      }
      buttons.forEach((item, index) => {
        const selected = options[index]?.value === select.value;
        item.classList.toggle("is-selected", selected);
        item.setAttribute("aria-selected", String(selected));
      });
      if (isOpen && document.activeElement !== trigger &&
          !menu.contains(document.activeElement)) {
        focusOption(currentIndex());
      }
    }

    function focusOption(index) {
      if (!buttons.length) return;
      focusedIndex = Math.max(0, Math.min(index, buttons.length - 1));
      const button = buttons[focusedIndex];
      if (!button || button.disabled) return;
      button.focus({preventScroll: true});
      button.scrollIntoView?.({block: "nearest"});
    }

    function closeMenu(restoreFocus = false) {
      if (!isOpen) return;
      isOpen = false;
      menu.hidden = true;
      root.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
      if (activeDropdown === closeMenu) activeDropdown = null;
      if (restoreFocus) trigger.focus({preventScroll: true});
    }

    function openMenu(move = 0) {
      if (activeDropdown && activeDropdown !== closeMenu) activeDropdown();
      syncOptions();
      if (!buttons.length || select.disabled) return;
      isOpen = true;
      root.classList.add("is-open");
      menu.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
      activeDropdown = closeMenu;
      let index = currentIndex();
      if (move !== 0) index = nextFilterIndex(index, move > 0 ? "ArrowDown" : "ArrowUp", buttons.length);
      focusOption(index);
    }

    function choose(index) {
      const option = select.options[index];
      if (!option || option.disabled) return;
      const changed = select.value !== option.value;
      select.value = option.value;
      syncOptions();
      closeMenu(true);
      // The original mods.js change listener re-runs the real server search.
      if (changed) select.dispatchEvent(new Event("change", {bubbles: true}));
    }

    trigger.addEventListener("click", () => {
      if (isOpen) closeMenu(true);
      else openMenu();
    });
    trigger.addEventListener("keydown", event => {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
        event.preventDefault();
        openMenu(event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0);
      }
    });
    menu.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMenu(true);
      } else if (event.key === "Tab") {
        closeMenu();
      } else if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
        event.preventDefault();
        focusOption(nextFilterIndex(focusedIndex, event.key, buttons.length));
      } else if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        choose(focusedIndex);
      }
    });
    document.addEventListener("pointerdown", event => {
      if (isOpen && !root.contains(event.target)) closeMenu();
    });
    window.addEventListener("resize", () => closeMenu());
    select.addEventListener("change", syncOptions);
    field.append(root);
    syncOptions();
    select.classList.add("mods-select-native");
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");
    select.dataset.roundedFilterReady = "true";
    if (typeof MutationObserver !== "undefined") {
      observer = new MutationObserver(() => {
        const focused = isOpen && menu.contains(document.activeElement);
        syncOptions();
        if (focused) focusOption(focusedIndex);
      });
      observer.observe(select, {childList: true, subtree: true, characterData: true, attributes: true,
        attributeFilter: ["disabled", "label"]});
    }
  }
}
