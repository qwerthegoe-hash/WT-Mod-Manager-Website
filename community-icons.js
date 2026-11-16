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
        chat: ["M20 11.5a8 8 0 0 1-8 8 8.7 8.7 0 0 1-3.7-.8L4 20l1.3-4.2A8 8 0 1 1 20 11.5Z", "M8.5 10.5h7M8.5 13.7h4.5"],
        updates: ["M20 7v5h-5", "M4 17v-5h5", "M5 9a7.7 7.7 0 0 1 13.4-2L20 12", "M19 15a7.7 7.7 0 0 1-13.4 2L4 12"],
        news: ["M5 3.5h13v15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-15Z", "M18 8h2a1 1 0 0 1 1 1v8.5a3 3 0 0 1-3 3", "M8.3 7.7h6.4M8.3 11h6.4M8.3 14.5h2.3M13.4 14.5h1.3"],
        ideas: ["M9.5 17.5h5M10 20.5h4", "M8.7 15.5c-.8-1.5-3-3.4-3-6.9a6.3 6.3 0 0 1 12.6 0c0 3.5-2.2 5.4-3 6.9l-.5 2h-5.6l-.5-2Z", "M10 10.4l2 1.7 2-1.7"],
        help: ["M12 3.2 4.2 7.5v9L12 20.8l7.8-4.3v-9L12 3.2Z", "M9.5 9.6a2.55 2.55 0 0 1 5 0c0 1.5-2.5 1.8-2.5 3.3M12 16.5h.01"],
        shield: ["M12 2.7 19.5 6v5.4c0 4.8-2.9 8-7.5 9.8-4.6-1.8-7.5-5-7.5-9.8V6L12 2.7Z", "m8.5 11.9 2.4 2.4 4.8-5"],
        smile: ["M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z", "M8 14.5c1 1.4 2.3 2.1 4 2.1s3-.7 4-2.1M8.4 9h.1M15.4 9h.1"],
        camera: ["M4.5 7h3.2l1.7-2h5.2l1.7 2h3.2A1.5 1.5 0 0 1 21 8.5v9A1.5 1.5 0 0 1 19.5 19h-15A1.5 1.5 0 0 1 3 17.5v-9A1.5 1.5 0 0 1 4.5 7Z", "M12 10a3.1 3.1 0 1 0 0 6.2A3.1 3.1 0 0 0 12 10Z", "M17.6 10h.01"],
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
