"use strict";
/*
 * WT Mod Manager: procedural vector icons.
 * All shapes are drawn from SVG paths in code; no image downloads or libraries.
 * Decorative emoji in the interface are replaced. User messages and the
 * emoji picker remain unchanged.
 */
(() => {
    const SVG_NS = "http://www.w3.org/2000/svg";
    const ICONS = {
        chat: ["M20 11.5a8.5 8.5 0 0 1-8.5 8.5 9 9 0 0 1-4-.9L3 21l1.7-4.3A8.5 8.5 0 1 1 20 11.5Z", "M8 11.5h8M8 14.5h5"],
        updates: ["M20 7v5h-5", "M4 17v-5h5", "M5.7 9A7.5 7.5 0 0 1 19 7l1 5M4 12l1 5a7.5 7.5 0 0 0 13.3-2"],
        news: ["M4 3.5h14v17H4z", "M18 8h2a1 1 0 0 1 1 1v9a2.5 2.5 0 0 1-2.5 2.5H7", "M7.5 8h7M7.5 11.5h7M7.5 15h3M12 15h2.5"],
        ideas: ["M9 18h6M9.5 21h5", "M9 15.5c-.5-1.6-3.5-3.4-3.5-7A6.5 6.5 0 0 1 12 2a6.5 6.5 0 0 1 6.5 6.5c0 3.6-3 5.4-3.5 7V18H9v-2.5Z", "M10 10.5 12 12l2-1.5"],
        help: ["M12 3 3.5 7.5v9L12 21l8.5-4.5v-9L12 3Z", "M9.6 9a2.4 2.4 0 1 1 4 1.9c-.9.7-1.6 1.2-1.6 2.6M12 16.7h.01"],
        shield: ["M12 2.5 20 6v5.6c0 5-3.1 8.2-8 10-4.9-1.8-8-5-8-10V6l8-3.5Z", "m8.2 12 2.5 2.6 5-5.2"],
        smile: ["M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z", "M8 14.5c1 1.4 2.3 2.1 4 2.1s3-.7 4-2.1M8.4 9h.1M15.4 9h.1"],
        camera: ["M4.5 7.5H8l1.5-2h5l1.5 2h3.5A1.5 1.5 0 0 1 21 9v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18V9a1.5 1.5 0 0 1 1.5-1.5Z", "M12 9.8a3.2 3.2 0 1 0 0 6.4 3.2 3.2 0 0 0 0-6.4Z"],
        list: ["M5 4h14v17H5z", "M9 4V2.5h6V4M9 9h6M9 13h6M9 17h4"],
        approved: ["M3.5 4.5h17v15h-17z", "m6.5 15 4-4 3 3 2-2 2 2M8.5 9h.01", "m15.5 7 1.5 1.5 3-3"]
    };
    const CHANNELS = {
        general: "chat",
        updates: "updates",
        news: "news",
        ideas: "ideas",
        help: "help"
    };

    function icon(name) {
        const svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("class", "wt-procedural-icon");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("focusable", "false");
        for (const d of ICONS[name] || ICONS.chat) {
            const path = document.createElementNS(SVG_NS, "path");
            path.setAttribute("d", d);
            svg.append(path);
        }
        return svg;
    }

    function setButtonIcon(node, name, label, className = "wt-procedural-action") {
        if (!node || node.dataset.proceduralIcon === name) return;
        node.dataset.proceduralIcon = name;
        node.classList.add(className);
        node.replaceChildren(icon(name), document.createTextNode(label));
    }

    function applyIcons() {
        document.querySelectorAll(".channel[data-channel]").forEach(button => {
            const type = CHANNELS[button.dataset.channel];
            if (!type || button.dataset.proceduralIcon === type) return;
            const label = button.textContent.trim();
            const span = document.createElement("span");
            span.className = "wt-procedural-chip";
            span.append(icon(type));
            button.dataset.proceduralIcon = type;
            button.replaceChildren(span, document.createTextNode(" " + label.replace(/^[^\p{L}\p{N}]+/u, "")));
        });

        const avatar = document.querySelector(".guardian-avatar");
        if (avatar && !avatar.dataset.proceduralIcon) {
            avatar.dataset.proceduralIcon = "shield";
            avatar.replaceChildren(icon("shield"));
        }

        setButtonIcon(document.querySelector("#emojiToggle"), "smile", "");
        const emojiButton = document.querySelector("#emojiToggle");
        if (emojiButton) emojiButton.setAttribute("aria-label", "Выбрать эмодзи");

        const attach = document.querySelector("label.attach-button[for='mediaInput']");
        if (attach && !attach.dataset.proceduralIcon) {
            attach.dataset.proceduralIcon = "camera";
            attach.classList.add("wt-procedural-action");
            attach.replaceChildren(icon("camera"), document.createTextNode("Фото / GIF"));
        }

        document.querySelectorAll(".composer-tools .attach-button").forEach(button => {
            if (button.matches("label[for='mediaInput']")) return;
            const label = button.textContent.trim();
            if (label.includes("Проверенные фото")) {
                setButtonIcon(button, "approved", "Проверенные фото");
            } else if (label.includes("Статус фото")) {
                setButtonIcon(button, "list", "Статус фото");
            }
        });

        document.querySelectorAll(".community-sidebar .channel:not([data-channel])").forEach(button => {
            if (button.id === "guardianAdminButton" || button.textContent.includes("WT Guardian")) {
                setButtonIcon(button, "shield", "WT Guardian — настройки");
            } else if (button.textContent.includes("Модерация фото")) {
                setButtonIcon(button, "shield", "Модерация фото");
            }
        });

        document.querySelectorAll(".guardian-system-notice strong").forEach(title => {
            if (title.dataset.proceduralIcon) return;
            title.dataset.proceduralIcon = "shield";
            title.textContent = title.textContent.replace(/^\s*🛡️\s*/, "");
            title.prepend(icon("shield"));
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
