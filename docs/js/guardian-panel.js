
"use strict";

/*
 * WT GUARDIAN 2.0
 * Administrator panel + trusted notifications.
 *
 * Requires guardian_upgrade.sql.
 * Does not store administrative secrets.
 * All permissions are checked by PostgreSQL.
 */

const GUARDIAN_OPTIONS = {
    enabled: {
        label: "Включить WT Guardian",
        type: "boolean"
    },

    block_links: {
        label: "Блокировать ссылки",
        type: "boolean"
    },

    detect_obfuscation: {
        label: "Проверять замаскированные ссылки",
        type: "boolean"
    },

    detect_spam: {
        label: "Антиспам",
        type: "boolean"
    },

    detect_duplicates: {
        label: "Проверять повторяющиеся сообщения",
        type: "boolean"
    },

    detect_flood: {
        label: "Проверять флуд и длинные повторы",
        type: "boolean"
    },

    issue_warnings: {
        label: "Выдавать предупреждения",
        type: "boolean"
    },

    min_delay_seconds: {
        label: "Задержка между сообщениями (секунды)",
        type: "number",
        min: 1,
        max: 60
    },

    hourly_limit: {
        label: "Сообщений в час",
        type: "number",
        min: 5,
        max: 500
    },

    duplicate_window_minutes: {
        label: "Период проверки повторов (минуты)",
        type: "number",
        min: 1,
        max: 120
    },

    warning_limit: {
        label: "Предупреждений до ограничения",
        type: "number",
        min: 1,
        max: 10
    },

    mute_minutes: {
        label: "Длительность ограничения (минуты)",
        type: "number",
        min: 1,
        max: 10080
    }
};

const PANEL_STYLE = {
    background: "#14263b",
    color: "#eff6ff",
    border: "1px solid #3c6087",
    borderRadius: "16px",
    padding: "22px",
    boxSizing: "border-box"
};

function element(tag, className = "", text = "") {
    const node = document.createElement(tag);

    if (className) {
        node.className = className;
    }

    node.textContent = text;

    return node;
}

function styledButton(label) {
    const button = element("button", "", label);

    button.type = "button";

    Object.assign(button.style, {
        padding: "10px 14px",
        borderRadius: "9px",
        border: "1px solid #497da9",
        background: "#254c72",
        color: "#ffffff",
        cursor: "pointer",
        font: "inherit"
    });

    return button;
}

function createDialog(titleText) {
    const dialog = document.createElement("dialog");

    Object.assign(dialog.style, {
        ...PANEL_STYLE,
        width: "min(700px, 94vw)",
        maxWidth: "94vw",
        maxHeight: "88vh",
        overflowY: "auto"
    });

    const header = element("h2", "", titleText);

    const close = styledButton("Закрыть");

    close.addEventListener("click", () => {
        dialog.close();
    });

    dialog.append(header, close);

    dialog.addEventListener("close", () => {
        dialog.remove();
    });

    document.body.append(dialog);

    return dialog;
}

function createSettingsInput(name, definition, value) {
    const row = element("label");

    Object.assign(row.style, {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "15px",
        padding: "12px 0",
        borderBottom: "1px solid #304b66",
        color: "#dcecff"
    });

    const caption = element(
        "span",
        "",
        definition.label
    );

    const input = document.createElement("input");

    input.dataset.guardianOption = name;

    if (definition.type === "boolean") {
        input.type = "checkbox";
        input.checked = Boolean(value);
        input.style.width = "18px";
        input.style.height = "18px";
    } else {
        input.type = "number";
        input.min = String(definition.min);
        input.max = String(definition.max);
        input.step = "1";
        input.value = String(value);

        Object.assign(input.style, {
            width: "100px",
            padding: "9px",
            border: "1px solid #426789",
            borderRadius: "8px",
            background: "#101d2d",
            color: "#ffffff"
        });
    }

    row.append(caption, input);

    return row;
}

export function initGuardianPanel({
    client,
    currentUser,
    isAdmin
}) {
    if (!client || !currentUser) {
        return;
    }

    const db = client;

    let noticeContainer = null;
    let activeAdminDialog = null;
    let loadingNotices = false;

    // ========================================================
    // TRUSTED SYSTEM NOTICES
    // ========================================================

    function setupNotices() {
        const parent = document.querySelector(
            ".guardian-message"
        );

        if (!parent) {
            return;
        }

        const container = element(
            "section",
            "guardian-system-notices"
        );

        Object.assign(container.style, {
            margin: "14px 20px",
            display: "grid",
            gap: "9px"
        });

        container.setAttribute(
            "aria-label",
            "Уведомления WT Guardian"
        );

        parent.insertAdjacentElement(
            "afterend",
            container
        );

        noticeContainer = container;
    }

    async function refreshNotices() {
        if (!noticeContainer || loadingNotices) {
            return;
        }

        loadingNotices = true;

        try {
            const { data, error } = await db
                .from("guardian_notices")
                .select(
                    "id,recipient_id,notice_type,body,created_at"
                )
                .order("created_at", {
                    ascending: false
                })
                .limit(5);

            if (error) {
                throw error;
            }

            const fragment =
                document.createDocumentFragment();

            for (const item of data || []) {
                const box = element(
                    "div",
                    "guardian-system-notice"
                );

                Object.assign(box.style, {
                    padding: "12px 15px",
                    border: "1px solid #3b6288",
                    borderRadius: "11px",
                    background: "#19334c",
                    color: "#d8eaff",
                    fontSize: "12px",
                    lineHeight: "1.6"
                });

                const header = element(
                    "strong",
                    "",
                    "🛡️ WT Guardian"
                );

                const body = element(
                    "p",
                    "",
                    item.body
                );

                body.style.margin = "6px 0";

                const time = element(
                    "small",
                    "",
                    new Date(
                        item.created_at
                    ).toLocaleString("ru-RU")
                );

                box.append(header, body, time);
                fragment.append(box);
            }

            noticeContainer.replaceChildren(fragment);

        } catch (error) {
            console.warn(
                "Guardian notices:",
                error.message
            );

        } finally {
            loadingNotices = false;
        }
    }

    // ========================================================
    // ADMIN SETTINGS
    // ========================================================

    async function loadSettings() {
        const { data, error } = await db
            .from("guardian_settings")
            .select("*")
            .eq("id", 1)
            .single();

        if (error) {
            throw error;
        }

        return data;
    }

    async function showSettings(container) {
        const settings = await loadSettings();

        const section = element("section");

        const heading = element(
            "h3",
            "",
            "Настройки фильтрации"
        );

        section.append(heading);

        const form = document.createElement("form");

        for (
            const [name, definition]
            of Object.entries(GUARDIAN_OPTIONS)
        ) {
            form.append(
                createSettingsInput(
                    name,
                    definition,
                    settings[name]
                )
            );
        }

        const save = styledButton(
            "Сохранить настройки"
        );

        save.type = "submit";
        save.style.marginTop = "18px";

        const feedback = element("p");

        form.addEventListener(
            "submit",
            async event => {
                event.preventDefault();

                const patch = {};

                for (
                    const [name, definition]
                    of Object.entries(GUARDIAN_OPTIONS)
                ) {
                    const input = form.querySelector(
                        `[data-guardian-option="${name}"]`
                    );

                    if (!input) {
                        continue;
                    }

                    patch[name] =
                        definition.type === "boolean"
                            ? input.checked
                            : Number(input.value);
                }

                save.disabled = true;

                try {
                    const { error } = await db.rpc(
                        "guardian_set_settings",
                        {
                            p_settings: patch
                        }
                    );

                    if (error) {
                        throw error;
                    }

                    feedback.textContent =
                        "Настройки WT Guardian сохранены.";

                    feedback.style.color = "#8de0b7";

                } catch (error) {
                    feedback.textContent =
                        "Ошибка: " + error.message;

                    feedback.style.color = "#ffadb4";

                } finally {
                    save.disabled = false;
                }
            }
        );

        form.append(save, feedback);
        section.append(form);
        container.append(section);
    }

    // ========================================================
    // MODERATION LOG
    // ========================================================

    async function showLog(container) {
        const heading = element(
            "h3",
            "",
            "Последние события модерации"
        );

        container.append(heading);

        const { data, error } = await db
            .from("guardian_events")
            .select(
                "user_id,event_type,details,warning_count,created_at"
            )
            .order("created_at", {
                ascending: false
            })
            .limit(30);

        if (error) {
            throw error;
        }

        if (!data?.length) {
            container.append(
                element(
                    "p",
                    "",
                    "Пока нарушений нет."
                )
            );

            return;
        }

        for (const event of data) {
            const row = element("div");

            Object.assign(row.style, {
                padding: "10px 0",
                borderBottom: "1px solid #304b66",
                fontSize: "12px"
            });

            const label = element(
                "strong",
                "",
                event.event_type
            );

            const description = element(
                "p",
                "",
                `Пользователь: ${event.user_id}\n` +
                `Причина: ${event.details}\n` +
                `Предупреждений: ${event.warning_count}`
            );

            description.style.whiteSpace = "pre-line";

            const timestamp = element(
                "small",
                "",
                new Date(
                    event.created_at
                ).toLocaleString("ru-RU")
            );

            row.append(
                label,
                description,
                timestamp
            );

            container.append(row);
        }
    }

    // ========================================================
    // ADMIN ANNOUNCEMENTS
    // ========================================================

    function showAnnouncementForm(container) {
        const heading = element(
            "h3",
            "",
            "Объявление от WT Guardian"
        );

        const textarea =
            document.createElement("textarea");

        textarea.rows = 3;
        textarea.maxLength = 1000;

        textarea.placeholder =
            "Текст официального объявления...";

        Object.assign(textarea.style, {
            width: "100%",
            boxSizing: "border-box",
            padding: "12px",
            border: "1px solid #426789",
            borderRadius: "9px",
            background: "#101d2d",
            color: "#ffffff",
            resize: "vertical"
        });

        const send = styledButton(
            "Опубликовать объявление"
        );

        send.style.marginTop = "10px";

        const feedback = element("p");

        send.addEventListener(
            "click",
            async () => {
                const body = textarea.value.trim();

                if (!body) {
                    feedback.textContent =
                        "Введите текст объявления.";

                    return;
                }

                send.disabled = true;

                try {
                    const { error } = await db.rpc(
                        "guardian_announce",
                        {
                            p_body: body
                        }
                    );

                    if (error) {
                        throw error;
                    }

                    textarea.value = "";

                    feedback.textContent =
                        "Объявление опубликовано.";

                    await refreshNotices();

                } catch (error) {
                    feedback.textContent =
                        "Ошибка: " + error.message;

                } finally {
                    send.disabled = false;
                }
            }
        );

        container.append(
            heading,
            textarea,
            send,
            feedback
        );
    }

    // ========================================================
    // OPEN ADMIN PANEL
    // ========================================================

    async function openAdminPanel() {
        if (!isAdmin) {
            return;
        }

        if (
            activeAdminDialog &&
            activeAdminDialog.open
        ) {
            return;
        }

        const dialog = createDialog(
            "🛡️ WT Guardian — Управление"
        );

        activeAdminDialog = dialog;

        const content = element("div");

        dialog.append(content);
        dialog.showModal();

        try {
            await showSettings(content);

            const divider = element("hr");
            divider.style.margin = "25px 0";

            content.append(divider);

            showAnnouncementForm(content);

            const nextDivider = element("hr");
            nextDivider.style.margin = "25px 0";

            content.append(nextDivider);

            await showLog(content);

        } catch (error) {
            content.append(
                element(
                    "p",
                    "",
                    "Ошибка загрузки панели: " +
                    error.message
                )
            );
        }
    }

    // ========================================================
    // ADMIN SIDEBAR BUTTON
    // ========================================================

    function setupAdminButton() {
        if (!isAdmin) {
            return;
        }

        const sidebar =
            document.querySelector(".community-sidebar");

        if (!sidebar) {
            return;
        }

        const button = styledButton(
            "🛡️ WT Guardian — настройки"
        );

        button.classList.add("channel");

        button.style.width = "100%";
        button.style.marginTop = "10px";

        button.addEventListener(
            "click",
            openAdminPanel
        );

        sidebar.append(button);
    }

    // ========================================================
    // INITIALIZE
    // ========================================================

    setupNotices();
    setupAdminButton();

    refreshNotices();

    setInterval(() => {
        if (!document.hidden) {
            refreshNotices();
        }
    }, 30000);

    document.addEventListener(
        "visibilitychange",
        () => {
            if (!document.hidden) {
                refreshNotices();
            }
        }
    );
}
