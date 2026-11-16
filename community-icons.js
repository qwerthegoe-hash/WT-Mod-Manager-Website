"use strict";
/*
 * WT Mod Manager — custom icon artwork supplied by the project owner.
 * Transparent silhouettes are hosted in assets/community-icons.svg.
 * The DOM decoration is idempotent and safe for dynamically added controls.
 */
(() => {
    const SPRITE = "assets/community-icons.svg";
    const CHANNELS = {
        general: "chat",
        updates: "updates",
        news: "news",
        ideas: "ideas",
        help: "help"
    };

    function icon(name) {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
        svg.classList.add("wt-custom-icon");
        svg.dataset.iconName = name;
        svg.setAttribute("viewBox", "0 0 512 512");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("focusable", "false");
        use.setAttribute("href", SPRITE + "#" + name);
        svg.append(use);
        return svg;
    }

    function buttonIcon(node, name, label) {
        if (!node || node.dataset.customIcon === name) return;
        node.dataset.customIcon = name;
        node.classList.add("wt-custom-action");
        node.replaceChildren(icon(name), document.createTextNode(label));
    }

    function applyIcons() {
        document.querySelectorAll(".channel[data-channel]").forEach(button => {
            const name = CHANNELS[button.dataset.channel];
            if (!name || button.dataset.customIcon === name) return;
            const label = button.textContent.replace(/^[^\p{L}\p{N}]+/u, "").trim();
            const chip = document.createElement("span");
            chip.className = "wt-custom-chip";
            chip.append(icon(name));
            button.dataset.customIcon = name;
            button.replaceChildren(chip, document.createTextNode(label));
        });

        const guardianAvatar = document.querySelector(".guardian-avatar");
        if (guardianAvatar && guardianAvatar.dataset.customIcon !== "guardian") {
            guardianAvatar.dataset.customIcon = "guardian";
            guardianAvatar.replaceChildren(icon("guardian"));
        }

        buttonIcon(document.querySelector("#emojiToggle"), "emoji", "");
        const emojiButton = document.querySelector("#emojiToggle");
        if (emojiButton) emojiButton.setAttribute("aria-label", "Выбрать эмодзи");

        const photo = document.querySelector("label.attach-button[for='mediaInput']");
        buttonIcon(photo, "photo", "Фото / GIF");

        document.querySelectorAll(".composer-tools .attach-button").forEach(button => {
            if (button.matches("label[for='mediaInput']")) return;
            if (button.textContent.includes("Проверенные фото") ||
                button.dataset.customIcon === "approved") {
                buttonIcon(button, "approved", "Проверенные фото");
            }
        });

        buttonIcon(document.querySelector("#mediaReviewButton"), "moderation", "Модерация фото");
        buttonIcon(document.querySelector("#guardianAdminButton"), "settings", "WT Guardian — настройки");

        document.querySelectorAll(".guardian-system-notice strong").forEach(title => {
            if (title.dataset.customIcon === "guardian") return;
            title.dataset.customIcon = "guardian";
            const label = title.textContent.replace(/^\s*🛡️\s*/, "").trim();
            title.replaceChildren(icon("guardian"), document.createTextNode(label));
        });
    }

    function start() {
        applyIcons();
        let scheduled = false;
        const observer = new MutationObserver(records => {
            if (!records.some(record => record.addedNodes.length)) return;
            if (scheduled) return;
            scheduled = true;
            queueMicrotask(() => {
                scheduled = false;
                applyIcons();
            });
        });
        observer.observe(document.body, {childList: true, subtree: true});
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start, {once: true});
    } else {
        start();
    }
})();
