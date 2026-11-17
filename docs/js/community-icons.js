"use strict";
/*
 * WT Mod Manager — custom icon artwork supplied by the project owner.
 * Transparent silhouettes are hosted in assets/community-icons.svg.
 * The DOM decoration is idempotent and safe for dynamically added controls.
 */
(() => {
    // Reuse the owner's original PNG artwork. Resolve relative to this script,
    // not the document, so nested pages never break icon URLs.
    const ASSET_ROOT = new URL("../assets/", document.currentScript.src);
    const IMAGES = {
        chat: "Chat.png", updates: "updates.png", news: "news.png",
        ideas: "ideas.png", help: "help.png", profile: "profile.png",
        guardian: "guardian.png", emoji: "emoji.png", photo: "photo.png",
        approved: "approved.png", moderation: "moderation.png",
        settings: "settings.png"
    };
    const CHANNELS = {
        general: "chat",
        updates: "updates",
        news: "news",
        ideas: "ideas",
        help: "help"
    };

    function icon(name) {
        const img = document.createElement("img");
        img.classList.add("wt-custom-icon");
        img.dataset.iconName = name;
        img.src = new URL(IMAGES[name] || "help.png", ASSET_ROOT).href;
        img.alt = "";
        img.decoding = "async";
        img.setAttribute("aria-hidden", "true");
        return img;
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