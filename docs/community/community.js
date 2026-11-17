
"use strict";

/*
 * WT Mod Manager Community
 * Frontend version 4.0
 *
 * Requires:
 * - community.html
 * - community.css
 * - community-config.js
 * - Supabase Community Database 3.0
 * - media_upgrade.sql
 * - Edge Function: community-media
 *
 * Features:
 * - Persistent chat messages
 * - Five community channels
 * - Administrator-only news
 * - Realtime synchronization
 * - Message pagination
 * - Emoji picker
 * - Reports and moderation
 * - Hidden message synchronization
 * - Safe text rendering
 * - Anti-spam checks
 * - Private media quarantine
 * - Media moderation queue
 * - Approved image selection
 * - Image/GIF validation
 */

import { createClient } from
    "https://esm.sh/@supabase/supabase-js@2.119.0";

import { COMMUNITY_CONFIG as config } from
    "../js/community-config.js";


// ============================================================
// CONFIGURATION
// ============================================================

const CHANNELS = {
    general: {
        title: "Общий чат",
        description: "Свободное общение игроков"
    },

    updates: {
        title: "Обсуждение обновлений",
        description: "Новые версии, изменения и отзывы"
    },

    news: {
        title: "Новости",
        description: "Официальные объявления разработчика"
    },

    ideas: {
        title: "Идеи и предложения",
        description: "Обсуждение новых возможностей"
    },

    help: {
        title: "Помощь",
        description: "Вопросы по WT Mod Manager"
    }
};

const ALLOWED_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif"
};

const REPORT_REASONS = {
    spam: "Спам",
    harassment: "Оскорбления или травля",
    scam: "Мошенничество",
    unsafe_content: "Опасный контент",
    other: "Другое"
};

const MEDIA_BUCKETS = {
    pending: "community-pending",
    published: "community-media"
};

const MEDIA_FUNCTION = "community-media";

const REFRESH_INTERVAL = 30000;
const MIN_SEND_INTERVAL = 3500;
const MAX_MESSAGE_LENGTH = 1500;

const PAGE_SIZE = Math.min(
    Math.max(Number(config.messagesPerPage) || 60, 10),
    100
);

const MAX_IMAGE_BYTES = Math.min(
    Number(config.maxImageBytes) || 5242880,
    5242880
);

const MEDIA_PATH_PATTERN =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png|webp|gif)$/;

const $ = id => document.getElementById(id);


// ============================================================
// APPLICATION STATE
// ============================================================

let db = null;
let user = null;
let isAdmin = false;

let activeChannel = "general";
let nickname = "";

let selectedFile = null;
let selectedApprovedPath = null;

let sending = false;
let isLoadingOlder = false;
let initialized = false;

let realtimeSubscription = null;

let oldestMessageDate = null;
let oldestMessageId = null;
let canLoadOlder = false;

let generation = 0;
let realtimeGeneration = 0;
let refreshTimer = null;

let lastSendAttempt = 0;
let refreshBusy = false;

let reportDialog = null;
let reportMessageId = null;

let mediaReviewDialog = null;
let mediaPickerDialog = null;

let mediaSelectionBusy = false;

const visibleMessages = new Map();


// ============================================================
// NOTIFICATIONS
// ============================================================

function notice(message, error = false) {
    const element = $("chatNotice");

    if (!element) {
        return;
    }

    element.textContent = message;
    element.classList.toggle("error", error);
}

function connection(message, online = false) {
    // No online badge is displayed. Connection errors remain in the chat notice.
    const el = $("connectionStatus");
    if (el) { el.textContent = ""; el.hidden = true; }
}

function showError(prefix, error) {
    const message =
        error instanceof Error
            ? error.message
            : String(error || "Неизвестная ошибка");

    console.error(prefix, error);

    notice(`${prefix}: ${message}`, true);
}


// ============================================================
// COMPOSER ACCESS
// ============================================================

function setEnabled(enabled) {
    $("sendMessage").disabled = !enabled;
    $("messageInput").disabled = !enabled;
    $("mediaInput").disabled = !enabled;
}

function canWriteInChannel() {
    return Boolean(
        user &&
        !sending &&
        (activeChannel !== "news" || isAdmin)
    );
}

function updateComposer() {
    const allowed = canWriteInChannel();

    setEnabled(allowed);

    $("sendMessage").textContent = sending
        ? "Отправка..."
        : "Отправить";

    $("messageInput").placeholder =
        activeChannel === "news" && !isAdmin
            ? "Только администратор может публиковать новости"
            : "Напиши сообщение...";
}


// ============================================================
// CONFIGURATION VALIDATION
// ============================================================

function isConfigured() {
    const url = String(
        config.supabaseUrl || ""
    ).trim();

    const key = String(
        config.supabasePublishableKey || ""
    ).trim();

    return (
        /^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/i.test(url) &&
        key.length > 10
    );
}


// ============================================================
// LOCAL STORAGE
// ============================================================

function readNickname() {
    if (!user?.id) return "";
    try { return localStorage.getItem("wtmm-community-nick:" + user.id) || ""; }
    catch { return ""; }
}

function storeNickname(value) {
    if (!user?.id) return;
    try { localStorage.setItem("wtmm-community-nick:" + user.id, value); }
    catch { /* Local storage unavailable. */ }
}

// ============================================================
// USERNAME VALIDATION
// ============================================================

function prepareNickname() {
    if (!user) return false;
    let value = String(nickname || "").trim();
    if (!value) value = "Player_" + user.id.slice(0, 6);
    if (value.length < 2 || value.length > 24) {
        notice("Никнейм должен содержать от 2 до 24 символов.", true);
        return false;
    }
    const reservedPattern =
        /^(admin|administrator|developer|moderator|system|system bot|wt guardian|wt mod manager)$/i;
    if (!isAdmin && reservedPattern.test(value)) {
        notice("Этот никнейм зарезервирован администрацией.", true);
        return false;
    }
    nickname = value;
    storeNickname(value);
    return true;
}


// ============================================================
// PROFILE SYNC
// ============================================================

// Keep the chat nickname in sync when the profile is saved in another tab.
window.addEventListener("storage", event => {
    if (!user?.id || event.key !== "wtmm-community-nick:" + user.id) return;
    if (typeof event.newValue !== "string") return;
    nickname = event.newValue;
    prepareNickname();
});

async function loadAccountNickname() {
    // The standalone profile page owns profile editing and avatar uploads.
    // Messages keep their author snapshots; a rename applies to new messages.
    const fallback = readNickname() || "Player_" + user.id.slice(0, 6);
    const { data, error } = await db
        .from("community_user_profiles")
        .select("nickname")
        .eq("user_id", user.id)
        .maybeSingle();
    if (error) {
        console.warn("Profile migration unavailable; using local nickname:", error.message);
    }
    nickname = String(data?.nickname || fallback);
    prepareNickname();
}

// ============================================================
// TEXT PRE-MODERATION
// ============================================================

function containsBlockedLink(value) {
    return (
        /(https?:\/\/|www\.|discord\.gg\/|discord\.com\/invite\/|t\.me\/)/i.test(value) ||
        /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(value) ||
        /[a-z0-9-]+\.(com|net|org|io|gg|ru|ua|me|xyz|app|dev|site|link|click|top)(\/|\s|$)/i.test(value)
    );
}

function validateText(value) {
    if (value.length > MAX_MESSAGE_LENGTH) {
        return "Сообщение слишком длинное.";
    }

    // Link and spam filtering must reach the server-side Guardian RPC.
    // Browser-only filtering cannot reliably record warnings or prevent bypass.
    return null;
}


// ============================================================
// IMAGE VALIDATION
// ============================================================

async function validateImage(file) {
    if (!file) {
        return null;
    }

    const type = String(
        file.type || ""
    ).toLowerCase();

    if (
        !Object.hasOwn(ALLOWED_TYPES, type)
    ) {
        return null;
    }

    if (
        file.size <= 0 ||
        file.size > MAX_IMAGE_BYTES
    ) {
        return null;
    }

    const bytes = new Uint8Array(
        await file.slice(0, 16).arrayBuffer()
    );

    const matches = (...values) =>
        values.every(
            (value, index) => bytes[index] === value
        );

    const ascii = (start, length) =>
        String.fromCharCode(
            ...bytes.slice(start, start + length)
        );

    if (
        type === "image/jpeg" &&
        matches(255, 216, 255)
    ) {
        return "jpg";
    }

    if (
        type === "image/png" &&
        matches(137, 80, 78, 71, 13, 10, 26, 10)
    ) {
        return "png";
    }

    if (
        type === "image/gif" &&
        (
            ascii(0, 6) === "GIF87a" ||
            ascii(0, 6) === "GIF89a"
        )
    ) {
        return "gif";
    }

    if (
        type === "image/webp" &&
        ascii(0, 4) === "RIFF" &&
        ascii(8, 4) === "WEBP"
    ) {
        return "webp";
    }

    return null;
}


// ============================================================
// MEDIA PATH VALIDATION
// ============================================================

function validMediaPath(path) {
    return (
        typeof path === "string" &&
        MEDIA_PATH_PATTERN.test(path)
    );
}

function getMediaUrl(path) {
    if (!validMediaPath(path)) {
        return null;
    }

    return db.storage
        .from(MEDIA_BUCKETS.published)
        .getPublicUrl(path)
        .data.publicUrl;
}


// ============================================================
// ATTACHMENT STATE
// ============================================================

function clearAttachment() {
    selectedFile = null;
    selectedApprovedPath = null;

    $("mediaInput").value = "";
    $("attachmentPreview").hidden = true;
    $("attachmentName").textContent = "";
}

function showAttachment(label) {
    $("attachmentPreview").hidden = false;
    $("attachmentName").textContent = label;
}

function setSelectedApprovedMedia(path) {
    if (!validMediaPath(path)) {
        notice(
            "Недопустимый путь изображения.",
            true
        );

        return false;
    }

    clearAttachment();

    selectedApprovedPath = path;

    const filename = path.split("/").pop();

    showAttachment(`✓ Проверено: ${filename}`);

    notice("Проверенное изображение выбрано.");

    return true;
}


// ============================================================
// MEDIA QUARANTINE UPLOAD
// ============================================================

async function uploadPendingMedia(file) {
    if (!db || !user) {
        throw new Error(
            "Необходимо подключиться к сообществу."
        );
    }

    const extension = await validateImage(file);

    if (!extension) {
        throw new Error(
            "Разрешены только JPEG, PNG, WebP и GIF до 5 МБ."
        );
    }

    const path =
        `${user.id}/${crypto.randomUUID()}.${extension}`;

    if (!validMediaPath(path)) {
        throw new Error(
            "Не удалось создать безопасный путь файла."
        );
    }

    const { error: uploadError } = await db.storage
        .from(MEDIA_BUCKETS.pending)
        .upload(path, file, {
            contentType: file.type,
            upsert: false,
            cacheControl: "0"
        });

    if (uploadError) {
        throw uploadError;
    }

    const { data: jobId, error: queueError } =
        await db.rpc(
            "queue_community_media",
            {
                p_path: path
            }
        );

    if (queueError) {
        throw new Error(
            "Файл загружен в карантин, но заявка не создана: " +
            queueError.message
        );
    }

    return {
        jobId,
        path
    };
}


// ============================================================
// MEDIA JOBS
// ============================================================

async function fetchMyMediaJobs() {
    if (!db || !user) {
        return [];
    }

    const { data, error } = await db
        .from("community_media_jobs")
        .select(
            "id,user_id,pending_path,published_path,status,reason,created_at,reviewed_at"
        )
        .eq("user_id", user.id)
        .order("created_at", {
            ascending: false
        })
        .limit(50);

    if (error) {
        throw error;
    }

    return data || [];
}

async function fetchApprovedMedia() {
    const jobs = await fetchMyMediaJobs();

    return jobs.filter(job =>
        job.status === "approved" &&
        validMediaPath(job.published_path)
    );
}


// ============================================================
// MEDIA STATUS LABELS
// ============================================================

function mediaStatusText(value) {
    switch (value) {
        case "pending":
            return "Ожидает проверки";

        case "approved":
            return "Одобрено";

        case "rejected":
            return "Отклонено";

        default:
            return "Неизвестный статус";
    }
}


// ============================================================
// MEDIA STATUS DIALOG
// ============================================================

async function openMediaStatus() {
    if (!db || !user) {
        return;
    }

    try {
        const jobs = await fetchMyMediaJobs();

        const dialog = document.createElement("dialog");

        dialog.className = "community-media-dialog";

        Object.assign(dialog.style, {
            width: "min(550px, 94vw)",
            maxWidth: "94vw",
            maxHeight: "85vh",
            overflowY: "auto",
            padding: "22px",
            border: "1px solid #456d98",
            borderRadius: "16px",
            background: "#14263b",
            color: "#ffffff"
        });

        const title = document.createElement("h2");
        title.textContent = "Статус моих фотографий";

        const closeButton = document.createElement("button");

        closeButton.type = "button";
        closeButton.textContent = "Закрыть";

        closeButton.addEventListener("click", () => {
            dialog.close();
        });

        dialog.append(title, closeButton);

        if (!jobs.length) {
            const empty = document.createElement("p");

            empty.textContent =
                "Ты ещё не загружал изображения.";

            dialog.append(empty);
        }

        for (const job of jobs) {
            const row = document.createElement("div");

            Object.assign(row.style, {
                padding: "13px 0",
                borderBottom: "1px solid #36536e"
            });

            const filename = document.createElement("strong");

            filename.textContent =
                job.pending_path.split("/").pop();

            const info = document.createElement("p");

            info.textContent =
                `${mediaStatusText(job.status)} · ` +
                new Date(job.created_at).toLocaleString("ru-RU");

            row.append(filename, info);

            if (job.reason) {
                const reason = document.createElement("p");
                reason.textContent = `Причина: ${job.reason}`;

                row.append(reason);
            }

            if (
                job.status === "approved" &&
                validMediaPath(job.published_path)
            ) {
                const button = document.createElement("button");

                button.type = "button";
                button.textContent = "Выбрать фото";

                button.addEventListener("click", () => {
                    setSelectedApprovedMedia(job.published_path);
                    dialog.close();
                });

                row.append(button);
            }

            dialog.append(row);
        }

        dialog.addEventListener("close", () => {
            dialog.remove();
        });

        document.body.append(dialog);
        dialog.showModal();

    } catch (error) {
        showError("Ошибка загрузки статусов", error);
    }
}


// ============================================================
// APPROVED MEDIA PICKER
// ============================================================

async function chooseApprovedMedia() {
    if (
        !db ||
        !user ||
        sending ||
        mediaSelectionBusy
    ) {
        return;
    }

    mediaSelectionBusy = true;

    try {
        const approved = await fetchApprovedMedia();

        if (!approved.length) {
            notice(
                "Нет одобренных изображений. " +
                "Загрузи фотографию и дождись проверки."
            );

            return;
        }

        const dialog = document.createElement("dialog");

        mediaPickerDialog = dialog;

        Object.assign(dialog.style, {
            width: "min(650px, 94vw)",
            maxHeight: "85vh",
            overflowY: "auto",
            padding: "24px",
            background: "#14263b",
            color: "#ffffff",
            border: "1px solid #456d98",
            borderRadius: "16px"
        });

        const title = document.createElement("h2");
        title.textContent = "Проверенные фотографии";

        const subtitle = document.createElement("p");

        subtitle.textContent =
            "Выбери изображение, которое уже одобрил модератор.";

        const close = document.createElement("button");

        close.type = "button";
        close.textContent = "Закрыть";

        close.addEventListener("click", () => {
            dialog.close();
        });

        dialog.append(title, subtitle, close);

        for (const job of approved) {
            const row = document.createElement("div");

            row.style.cssText = `
                display:flex;
                align-items:center;
                justify-content:space-between;
                flex-wrap:wrap;
                gap:12px;
                padding:14px 0;
                border-bottom:1px solid #39536d;
            `;

            const image = document.createElement("img");

            image.src = getMediaUrl(job.published_path);
            image.alt = "Одобренное изображение";
            image.loading = "lazy";

            Object.assign(image.style, {
                maxWidth: "150px",
                maxHeight: "110px",
                objectFit: "contain",
                borderRadius: "9px"
            });

            const filename = document.createElement("span");

            filename.textContent =
                job.published_path.split("/").pop();

            const select = document.createElement("button");

            select.type = "button";
            select.textContent = "Прикрепить";

            select.addEventListener("click", () => {
                setSelectedApprovedMedia(job.published_path);
                dialog.close();
            });

            row.append(image, filename, select);
            dialog.append(row);
        }

        dialog.addEventListener("close", () => {
            dialog.remove();

            if (mediaPickerDialog === dialog) {
                mediaPickerDialog = null;
            }
        });

        document.body.append(dialog);
        dialog.showModal();

    } catch (error) {
        showError("Ошибка выбора фотографии", error);
    } finally {
        mediaSelectionBusy = false;
    }
}


// ============================================================
// SERVER MEDIA ACTIONS
// ============================================================

async function mediaAdminAction(action, jobId = null) {
    if (!db || !user || !isAdmin) {
        throw new Error("Модерация доступна только администратору.");
    }
    const { data, error } = await db.functions.invoke(MEDIA_FUNCTION, {
        body: { action, jobId }
    });
    if (error) {
        const status = error.context?.status;
        const original = String(error.message || "Неизвестная ошибка");
        let detail = original;
        if (error.name === "FunctionsFetchError" ||
            /failed to send a request|failed to fetch|networkerror/i.test(original)) {
            detail = "Не удалось связаться с функцией community-media в Supabase. " +
                "Проверь, опубликована ли функция (Deploy), и посмотри Logs " +
                "в Edge Functions. Если логов нет — проверь доступ к Supabase " +
                "из браузера и расширения, блокирующие сетевые запросы.";
        } else if (status === 404) {
            detail = "Функция community-media не найдена (HTTP 404). Проверь имя и Deploy.";
        } else if (status === 401 || status === 403) {
            detail = "Ошибка авторизации модератора (HTTP " + status + "). " +
                "Проверь сессию и права community_admins.";
        } else if (status >= 500) {
            detail = "Ошибка сервера модерации (HTTP " + status + "). Проверь Logs в Supabase.";
        } else if (status) {
            detail += " (HTTP " + status + ")";
        }
        console.warn("Community media request failed", {
            action, status: status || null, error: original
        });
        throw new Error(detail);
    }
    if (!data || typeof data !== "object") {
        throw new Error("Функция модерации вернула пустой ответ.");
    }
    if (data.error) throw new Error(String(data.error));
    return data;
}

// ============================================================
// MEDIA MODERATION QUEUE
// ============================================================

async function openMediaReview() {
    if (!isAdmin) {
        return;
    }

    try {
        const result = await mediaAdminAction("list");
        const jobs = result.jobs || [];

        const dialog = document.createElement("dialog");

        mediaReviewDialog = dialog;

        Object.assign(dialog.style, {
            width: "min(700px, 94vw)",
            maxWidth: "94vw",
            maxHeight: "85vh",
            overflowY: "auto",
            padding: "24px",
            background: "#14263b",
            color: "#ffffff",
            border: "1px solid #456d98",
            borderRadius: "16px"
        });

        const heading = document.createElement("h2");
        heading.textContent = "Модерация фотографий";

        const description = document.createElement("p");

        description.textContent =
            "Просматривай изображения перед одобрением. " +
            "Непроверенные файлы остаются в закрытом карантине.";

        const close = document.createElement("button");

        close.type = "button";
        close.textContent = "Закрыть";

        close.addEventListener("click", () => {
            dialog.close();
        });

        dialog.append(heading, description, close);

        if (!jobs.length) {
            const empty = document.createElement("p");
            empty.textContent = "Очередь проверки пуста.";

            dialog.append(empty);
        }

        for (const job of jobs) {
            const row = document.createElement("div");

            Object.assign(row.style, {
                padding: "15px 0",
                borderTop: "1px solid #405b77",
                marginTop: "12px"
            });

            const label = document.createElement("p");

            label.textContent =
                `${job.pending_path} · ` +
                new Date(job.created_at).toLocaleString("ru-RU");

            const actions = document.createElement("div");

            actions.style.cssText = `
                display:flex;
                flex-wrap:wrap;
                gap:8px;
                margin-top:12px;
            `;

            const preview = document.createElement("button");
            preview.type = "button";
            preview.textContent = "Посмотреть";

            const approve = document.createElement("button");
            approve.type = "button";
            approve.textContent = "Одобрить";
            approve.disabled = true;

            const reject = document.createElement("button");
            reject.type = "button";
            reject.textContent = "Отклонить";

            let previewOpened = false;
            let busy = false;

            preview.addEventListener("click", async () => {
                if (busy) return;

                busy = true;
                preview.disabled = true;

                try {
                    const result = await mediaAdminAction(
                        "preview",
                        job.id
                    );

                    const link = document.createElement("a");

                    link.href = result.url;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    link.textContent = "Открыть изображение";
                    link.style.color = "#91caff";

                    row.append(link);

                    previewOpened = true;
                    approve.disabled = false;

                } catch (error) {
                    showError("Ошибка просмотра", error);
                } finally {
                    busy = false;
                    preview.disabled = false;
                }
            });

            async function applyDecision(action) {
                if (busy) return;

                if (
                    action === "approve" &&
                    !previewOpened
                ) {
                    notice(
                        "Сначала открой изображение для просмотра.",
                        true
                    );

                    return;
                }

                const confirmed = confirm(
                    action === "approve"
                        ? "Одобрить изображение и сделать его доступным в чате?"
                        : "Отклонить изображение?"
                );

                if (!confirmed) {
                    return;
                }

                busy = true;
                approve.disabled = true;
                reject.disabled = true;

                try {
                    await mediaAdminAction(
                        action,
                        job.id
                    );

                    row.remove();

                    notice(
                        action === "approve"
                            ? "Изображение одобрено."
                            : "Изображение отклонено."
                    );

                } catch (error) {
                    showError("Ошибка модерации", error);
                } finally {
                    busy = false;
                    reject.disabled = false;
                }
            }

            approve.addEventListener("click", () => {
                applyDecision("approve");
            });

            reject.addEventListener("click", () => {
                applyDecision("reject");
            });

            actions.append(
                preview,
                approve,
                reject
            );

            row.append(label, actions);
            dialog.append(row);
        }

        dialog.addEventListener("close", () => {
            dialog.remove();

            if (mediaReviewDialog === dialog) {
                mediaReviewDialog = null;
            }
        });

        document.body.append(dialog);
        dialog.showModal();

    } catch (error) {
        showError("Не удалось открыть модерацию", error);
    }
}


// ============================================================
// MEDIA USER CONTROLS
// ============================================================

function setupMediaControls() {
    const tools = document.querySelector(
        ".composer-tools"
    );

    if (!tools) {
        return;
    }

    const approvedButton = document.createElement("button");

    approvedButton.type = "button";
    approvedButton.className = "attach-button";
    approvedButton.textContent = "✓ Проверенные фото";

    approvedButton.addEventListener(
        "click",
        chooseApprovedMedia
    );

    tools.append(approvedButton);
}


// ============================================================
// MEDIA ADMIN CONTROLS
// ============================================================

function setupMediaAdmin() {
    if (!isAdmin) return;
    const sidebar = document.querySelector(".community-sidebar");
    if (!sidebar || $("mediaReviewButton")) return;
    const button = document.createElement("button");
    button.type = "button";
    button.id = "mediaReviewButton";
    button.className = "channel";
    button.textContent = "🛡️ Модерация фото";
    button.addEventListener("click", openMediaReview);
    sidebar.append(button);
}

// ============================================================
// ATTACHMENT INPUT
// ============================================================

function setupAttachments() {
    $("mediaInput").addEventListener(
        "change",
        async event => {
            const file = event.target.files?.[0];

            if (!file) {
                return;
            }

            const extension = await validateImage(file);

            if (!extension) {
                clearAttachment();

                notice(
                    "Разрешены только JPEG, PNG, WebP и GIF до 5 МБ.",
                    true
                );

                return;
            }

            selectedFile = file;
            selectedApprovedPath = null;

            showAttachment(
                `📷 ${file.name} — ` +
                `${(file.size / 1048576).toFixed(2)} МБ`
            );

            notice(
                "Изображение готово к отправке на проверку."
            );
        }
    );

    $("removeAttachment").addEventListener(
        "click",
        clearAttachment
    );
}


// ============================================================
// EMOJI
// ============================================================

function setupEmoji() {
    $("emojiToggle").addEventListener(
        "click",
        () => {
            $("emojiPanel").hidden =
                !$("emojiPanel").hidden;
        }
    );

    document.querySelectorAll(
        "[data-emoji]"
    ).forEach(button => {
        button.addEventListener("click", () => {
            const textarea = $("messageInput");

            if (textarea.disabled) {
                return;
            }

            textarea.setRangeText(
                button.dataset.emoji,
                textarea.selectionStart,
                textarea.selectionEnd,
                "end"
            );

            textarea.focus();
        });
    });
}


// ============================================================
// MESSAGE ELEMENT
// ============================================================

function createMessageElement(message) {
    const article = document.createElement("article");

    article.className = "chat-message";
    article.dataset.messageId = message.id;

    if (message.user_id === user?.id) {
        article.classList.add("own");
    }

    const header = document.createElement("div");
    header.className = "message-header";

    const author = document.createElement("span");
    author.className = "message-author";

    author.textContent = String(
        message.nickname || "Player"
    );

    // Show only the author; keep created_at in data for ordering.
    header.append(author);
    article.append(header);

    if (message.body) {
        const textElement = document.createElement("p");

        textElement.className = "message-text";

        // User input is never parsed as HTML.
        textElement.textContent = message.body;

        article.append(textElement);
    }

    if (
        message.attachment_path &&
        validMediaPath(message.attachment_path)
    ) {
        const image = document.createElement("img");

        image.className = "message-media";
        image.src = getMediaUrl(
            message.attachment_path
        );
        image.alt = "Изображение участника";
        image.loading = "lazy";
        image.referrerPolicy = "no-referrer";

        article.append(image);
    }

    if (message.user_id !== user?.id) {
        const reportButton = document.createElement("button");

        reportButton.type = "button";
        reportButton.textContent = "⚑ Пожаловаться";
        reportButton.className = "community-report-button";

        Object.assign(reportButton.style, {
            marginTop: "12px",
            padding: "6px 10px",
            border: "1px solid #405b77",
            borderRadius: "8px",
            background: "#172a40",
            color: "#a9c2de",
            fontSize: "11px",
            cursor: "pointer"
        });

        reportButton.addEventListener("click", () => {
            openReportDialog(message.id);
        });

        article.append(reportButton);
    }

    return article;
}


// ============================================================
// MESSAGE ORDERING
// ============================================================

function compareMessages(a, b) {
    const timeA = Date.parse(a.created_at);
    const timeB = Date.parse(b.created_at);

    if (timeA !== timeB) {
        return timeA - timeB;
    }

    return String(a.id).localeCompare(
        String(b.id)
    );
}


// ============================================================
// RENDER MESSAGES
// ============================================================

function renderMessages({
    preserveScroll = false
} = {}) {
    const list = $("messages");

    const oldScrollHeight = list.scrollHeight;
    const oldScrollTop = list.scrollTop;

    const nearBottom =
        list.scrollHeight -
        list.scrollTop -
        list.clientHeight < 100;

    const sorted = [...visibleMessages.values()]
        .filter(message =>
            message.channel === activeChannel &&
            !message.is_hidden
        )
        .sort(compareMessages);

    const fragment = document.createDocumentFragment();

    for (const message of sorted) {
        fragment.append(
            createMessageElement(message)
        );
    }

    list.replaceChildren(fragment);

    if (preserveScroll) {
        list.scrollTop =
            oldScrollTop +
            list.scrollHeight -
            oldScrollHeight;
    } else if (nearBottom) {
        list.scrollTop = list.scrollHeight;
    }
}


// ============================================================
// ADD REALTIME MESSAGE
// ============================================================

function addMessage(message) {
    if (
        !message ||
        !message.id ||
        message.channel !== activeChannel
    ) {
        return;
    }

    if (message.is_hidden) {
        visibleMessages.delete(message.id);
        renderMessages();
        return;
    }

    visibleMessages.set(
        message.id,
        message
    );

    renderMessages();
}


// ============================================================
// LOAD MESSAGE HISTORY
// ============================================================

async function loadMessages(older = false) {
    if (!db || !user) {
        return;
    }

    if (older && isLoadingOlder) {
        return;
    }

    const currentGeneration = generation;
    const requestedChannel = activeChannel;

    if (older) {
        isLoadingOlder = true;
        $("loadOlder").disabled = true;
    }

    try {
        let query = db
            .from("community_messages")
            .select(
                "id,user_id,nickname,channel,body,attachment_path,created_at,is_hidden"
            )
            .eq("channel", requestedChannel)
            .order("created_at", {
                ascending: false
            })
            .order("id", {
                ascending: false
            })
            .limit(PAGE_SIZE);

        if (
            older &&
            oldestMessageDate &&
            oldestMessageId
        ) {
            query = query.or(
                `created_at.lt.${oldestMessageDate},` +
                `and(created_at.eq.${oldestMessageDate},id.lt.${oldestMessageId})`
            );
        }

        const { data, error } = await query;

        if (error) {
            throw error;
        }

        if (
            currentGeneration !== generation ||
            requestedChannel !== activeChannel
        ) {
            return;
        }

        const rows = data || [];

        for (const message of rows) {
            if (message.is_hidden) {
                visibleMessages.delete(message.id);
            } else {
                visibleMessages.set(
                    message.id,
                    message
                );
            }
        }

        if (rows.length > 0 && older) {
            const last = rows[rows.length - 1];

            oldestMessageDate = last.created_at;
            oldestMessageId = last.id;
        }

        if (
            rows.length > 0 &&
            !oldestMessageDate
        ) {
            const last = rows[rows.length - 1];

            oldestMessageDate = last.created_at;
            oldestMessageId = last.id;
        }

        if (older || visibleMessages.size <= PAGE_SIZE) {
            canLoadOlder = rows.length === PAGE_SIZE;
        }

        $("loadOlder").hidden = !canLoadOlder;

        renderMessages({
            preserveScroll: older
        });

        if (
            !older &&
            visibleMessages.size === 0
        ) {
            notice(
                "Пока сообщений нет. Можешь написать первым."
            );
        }

    } catch (error) {
        if (currentGeneration === generation) {
            showError(
                "Ошибка загрузки чата",
                error
            );
        }
    } finally {
        isLoadingOlder = false;
        $("loadOlder").disabled = false;
    }
}


// ============================================================
// RECONCILE MODERATED MESSAGES
// ============================================================

async function reconcileVisibleMessages() {
    if (
        !db ||
        !user ||
        visibleMessages.size === 0
    ) {
        return;
    }

    const currentGeneration = generation;
    const requestedChannel = activeChannel;

    const ids = [...visibleMessages.keys()];
    const CHUNK_SIZE = 50;

    try {
        for (
            let start = 0;
            start < ids.length;
            start += CHUNK_SIZE
        ) {
            const chunk = ids.slice(
                start,
                start + CHUNK_SIZE
            );

            const { data, error } = await db
                .from("community_messages")
                .select("id,is_hidden")
                .eq("channel", requestedChannel)
                .in("id", chunk);

            if (error) {
                throw error;
            }

            if (
                currentGeneration !== generation ||
                requestedChannel !== activeChannel
            ) {
                return;
            }

            const available = new Set(
                (data || [])
                    .filter(row => !row.is_hidden)
                    .map(row => row.id)
            );

            for (const id of chunk) {
                if (!available.has(id)) {
                    visibleMessages.delete(id);
                }
            }
        }

        if (
            currentGeneration === generation &&
            requestedChannel === activeChannel
        ) {
            renderMessages();
        }

    } catch (error) {
        console.warn(
            "Message visibility check failed:",
            error
        );
    }
}


// ============================================================
// REALTIME UNSUBSCRIBE
// ============================================================

async function unsubscribe() {
    const oldSubscription = realtimeSubscription;

    realtimeSubscription = null;

    if (oldSubscription && db) {
        await db.removeChannel(oldSubscription);
    }
}


// ============================================================
// REALTIME SUBSCRIBE
// ============================================================

async function subscribeToChannel() {
    const currentChannel = activeChannel;
    const myGeneration = ++realtimeGeneration;

    await unsubscribe();

    if (
        currentChannel !== activeChannel ||
        myGeneration !== realtimeGeneration
    ) {
        return;
    }

    const subscription = db
        .channel(
            `wtmm-community-${currentChannel}-${crypto.randomUUID()}`
        )
        .on(
            "postgres_changes",
            {
                event: "INSERT",
                schema: "public",
                table: "community_messages",
                filter: `channel=eq.${currentChannel}`
            },
            payload => {
                if (
                    currentChannel !== activeChannel ||
                    myGeneration !== realtimeGeneration
                ) {
                    return;
                }

                addMessage(payload.new);
            }
        )
        .on(
            "postgres_changes",
            {
                event: "UPDATE",
                schema: "public",
                table: "community_messages",
                filter: `channel=eq.${currentChannel}`
            },
            payload => {
                if (
                    currentChannel !== activeChannel ||
                    myGeneration !== realtimeGeneration
                ) {
                    return;
                }

                const message = payload.new;

                if (message?.is_hidden) {
                    visibleMessages.delete(message.id);
                    renderMessages();
                } else if (
                    message?.id &&
                    visibleMessages.has(message.id)
                ) {
                    visibleMessages.set(message.id, message);
                    renderMessages();
                }
            }
        );

    realtimeSubscription = subscription;

    subscription.subscribe(statusValue => {
        if (
            myGeneration !== realtimeGeneration ||
            currentChannel !== activeChannel
        ) {
            return;
        }

        if (statusValue === "SUBSCRIBED") {
            connection("", true);

            loadMessages();
            reconcileVisibleMessages();

        } else if (
            statusValue === "CHANNEL_ERROR" ||
            statusValue === "TIMED_OUT"
        ) {
            connection("Проблема соединения");

        } else if (
            statusValue === "CLOSED"
        ) {
            connection("Отключено");
        }
    });
}


// ============================================================
// CHANNEL SELECTION
// ============================================================

async function selectChannel(next) {
    if (!CHANNELS[next]) {
        return;
    }

    const currentGeneration = ++generation;

    activeChannel = next;
    oldestMessageDate = null;
    oldestMessageId = null;
    canLoadOlder = false;

    visibleMessages.clear();

    $("messages").replaceChildren();
    $("loadOlder").hidden = true;

    document.querySelectorAll(
        ".channel[data-channel]"
    ).forEach(button => {
        const selected =
            button.dataset.channel === next;

        button.classList.toggle(
            "active",
            selected
        );

        button.setAttribute(
            "aria-pressed",
            String(selected)
        );
    });

    $("channelTitle").textContent =
        CHANNELS[next].title;

    $("channelDescription").textContent =
        CHANNELS[next].description;

    clearAttachment();
    notice("");

    connection("Подключение...");
    updateComposer();

    if (!db || !user) {
        return;
    }

    await subscribeToChannel();

    if (
        currentGeneration === generation &&
        visibleMessages.size === 0
    ) {
        await loadMessages();
    }
}


// ============================================================
// SETUP CHANNEL CONTROLS
// ============================================================

function setupChannels() {
    document.querySelectorAll(
        ".channel[data-channel]"
    ).forEach(button => {
        button.addEventListener(
            "click",
            () => {
                selectChannel(
                    button.dataset.channel
                );
            }
        );
    });

    $("loadOlder").addEventListener(
        "click",
        () => {
            if (canLoadOlder) {
                loadMessages(true);
            }
        }
    );
}


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage() {
    if (!db || !user || sending) {
        return;
    }

    if (
        activeChannel === "news" &&
        !isAdmin
    ) {
        notice(
            "Новости доступны только администрации.",
            true
        );

        return;
    }

    if (!prepareNickname()) {
        return;
    }

    const text = $("messageInput").value.trim();
    const file = selectedFile;
    const approvedPath = selectedApprovedPath;
    const targetChannel = activeChannel;

    if (
        !text &&
        !file &&
        !approvedPath
    ) {
        notice(
            "Напиши сообщение или выбери изображение.",
            true
        );

        return;
    }

    const textError = validateText(text);

    if (textError) {
        notice(textError, true);
        return;
    }

    const now = Date.now();

    if (
        now - lastSendAttempt <
        MIN_SEND_INTERVAL
    ) {
        notice(
            "Подожди несколько секунд перед отправкой.",
            true
        );

        return;
    }

    sending = true;
    lastSendAttempt = now;

    updateComposer();
    notice("Обработка сообщения...");

    try {
        // ====================================================
        // QUARANTINE NEW IMAGE
        // ====================================================

        if (file) {
            notice(
                "Загрузка изображения в закрытый карантин..."
            );

            const result = await uploadPendingMedia(file);

            if (selectedFile === file) {
                clearAttachment();
            }

            notice(
                `Изображение отправлено на проверку. ` +
                `ID заявки: ${result.jobId}. ` +
                `После одобрения выбери его через «Проверенные фото».`
            );

            // Draft text remains unchanged.
            // The attachment is NOT published yet.

            return;
        }

        // ====================================================
        // INSERT MESSAGE
        // ====================================================

        if (
            approvedPath &&
            !validMediaPath(approvedPath)
        ) {
            throw new Error(
                "Неверный путь одобренного изображения."
            );
        }

        // WT Guardian 2.0: the server is the only authority for messages.
        // Do not fall back to direct INSERT if the RPC is not installed.
        const { data: guardianResult, error: guardianError } = await db
            .rpc("guardian_send_message", {
                p_channel: targetChannel,
                p_nickname: nickname,
                p_body: text,
                p_attachment_path: approvedPath || null
            });

        if (guardianError) {
            throw guardianError;
        }

        if (!guardianResult || guardianResult.ok !== true) {
            const rejection = guardianRejectionMessage(guardianResult);
            notice(rejection, true);
            await refreshGuardianNotices();
            await refreshGuardianOwnState();
            // Preserve the draft and attachment after a rejection.
            return;
        }

        // ====================================================
        // CLEAR SENT DRAFT
        // ====================================================

        if (
            $("messageInput").value.trim() === text
        ) {
            $("messageInput").value = "";
        }

        if (
            selectedApprovedPath === approvedPath
        ) {
            clearAttachment();
        }

        notice("Сообщение отправлено.");

        if (activeChannel === targetChannel) {
            await loadMessages();
        }

    } catch (error) {
        showError(
            "Не удалось отправить сообщение",
            error
        );

    } finally {
        sending = false;
        updateComposer();
    }
}


// ============================================================
// SETUP COMPOSER
// ============================================================

function setupComposer() {
    $("sendMessage").addEventListener(
        "click",
        sendMessage
    );

    $("messageInput").addEventListener(
        "keydown",
        event => {
            if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.isComposing
            ) {
                event.preventDefault();
                sendMessage();
            }
        }
    );
}


// ============================================================
// REPORT DIALOG
// ============================================================

function createReportDialog() {
    const dialog = document.createElement("dialog");

    dialog.setAttribute(
        "aria-label",
        "Пожаловаться на сообщение"
    );

    Object.assign(dialog.style, {
        width: "min(430px, 92vw)",
        maxWidth: "92vw",
        padding: "24px",
        border: "1px solid #456d98",
        borderRadius: "18px",
        background: "#17273b",
        color: "#ecf5ff",
        boxShadow: "0 25px 80px #0008"
    });

    const title = document.createElement("h2");
    title.textContent = "Пожаловаться на сообщение";
    title.style.margin = "0 0 12px";
    title.style.fontSize = "20px";

    const description = document.createElement("p");

    description.textContent =
        "Выбери причину жалобы. " +
        "Она будет сохранена для проверки модератором.";

    description.style.fontSize = "13px";
    description.style.lineHeight = "1.6";
    description.style.color = "#b8cce2";

    const form = document.createElement("form");
    form.method = "dialog";

    const reasonLabel = document.createElement("label");
    reasonLabel.textContent = "Причина жалобы";
    reasonLabel.htmlFor = "communityReportReason";

    const select = document.createElement("select");
    select.id = "communityReportReason";
    select.required = true;

    Object.entries(REPORT_REASONS).forEach(
        ([value, label]) => {
            const option = document.createElement("option");

            option.value = value;
            option.textContent = label;

            select.append(option);
        }
    );

    const detailsLabel = document.createElement("label");

    detailsLabel.textContent =
        "Дополнительная информация (необязательно)";

    detailsLabel.htmlFor = "communityReportDetails";

    const textarea = document.createElement("textarea");

    textarea.id = "communityReportDetails";
    textarea.rows = 4;
    textarea.maxLength = 1000;

    textarea.placeholder =
        "Кратко объясни, что произошло...";

    for (const field of [select, textarea]) {
        Object.assign(field.style, {
            display: "block",
            width: "100%",
            boxSizing: "border-box",
            marginTop: "8px",
            marginBottom: "15px",
            padding: "11px",
            border: "1px solid #415f7f",
            borderRadius: "9px",
            background: "#101c2e",
            color: "#ffffff",
            font: "inherit"
        });
    }

    const actions = document.createElement("div");

    Object.assign(actions.style, {
        display: "flex",
        gap: "10px",
        justifyContent: "flex-end"
    });

    const cancel = document.createElement("button");

    cancel.type = "button";
    cancel.textContent = "Отмена";

    const submit = document.createElement("button");

    submit.type = "submit";
    submit.textContent = "Отправить жалобу";

    for (const button of [cancel, submit]) {
        Object.assign(button.style, {
            padding: "10px 14px",
            border: "1px solid #4d7295",
            borderRadius: "9px",
            background: "#234565",
            color: "#ffffff",
            cursor: "pointer"
        });
    }

    cancel.addEventListener("click", () => {
        dialog.close();
    });

    form.addEventListener(
        "submit",
        async event => {
            event.preventDefault();

            if (!reportMessageId || !user || !db) {
                return;
            }

            submit.disabled = true;
            submit.textContent = "Отправка...";

            try {
                const { error } = await db
                    .from("community_reports")
                    .insert({
                        message_id: reportMessageId,
                        reporter_id: user.id,
                        reason: select.value,
                        details: textarea.value.trim()
                    });

                if (error) {
                    throw error;
                }

                notice(
                    "Жалоба отправлена модератору."
                );

                dialog.close();

            } catch (error) {
                showError(
                    "Не удалось отправить жалобу",
                    error
                );

            } finally {
                submit.disabled = false;
                submit.textContent = "Отправить жалобу";
            }
        }
    );

    actions.append(
        cancel,
        submit
    );

    form.append(
        reasonLabel,
        select,
        detailsLabel,
        textarea,
        actions
    );

    dialog.append(
        title,
        description,
        form
    );

    dialog.addEventListener("close", () => {
        reportMessageId = null;
        textarea.value = "";
    });

    document.body.append(dialog);

    reportDialog = dialog;
}


// ============================================================
// OPEN REPORT
// ============================================================

function openReportDialog(messageId) {
    if (!user) {
        notice(
            "Необходимо подключиться к чату.",
            true
        );

        return;
    }

    reportMessageId = messageId;

    if (!reportDialog) {
        createReportDialog();
    }

    if (!reportDialog.open) {
        reportDialog.showModal();
    }
}


// ============================================================
// PROFILE
// ============================================================

// ============================================================
// PERIODIC SYNCHRONIZATION
// ============================================================

async function refreshCommunity() {
    if (
        !db ||
        !user ||
        sending ||
        refreshBusy
    ) {
        return;
    }

    refreshBusy = true;

    try {
        await reconcileVisibleMessages();
        await loadMessages();

    } catch (error) {
        console.warn(
            "Community refresh failed:",
            error
        );

    } finally {
        refreshBusy = false;
    }
}


// ============================================================
// REFRESH TIMER
// ============================================================

function startRefreshTimer() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }

    refreshTimer = setInterval(() => {
        if (!document.hidden) {
            refreshCommunity();
        }
    }, REFRESH_INTERVAL);

    document.addEventListener(
        "visibilitychange",
        () => {
            if (!document.hidden) {
                refreshCommunity();
            }
        }
    );

    window.addEventListener(
        "online",
        () => {
            refreshCommunity();
        }
    );
}


// ============================================================
// STARTUP
// ============================================================

async function start() {
    if (initialized) {
        return;
    }

    initialized = true;

    setupChannels();
    setupAttachments();
    setupMediaControls();
    setupEmoji();
    setupComposer();
    createReportDialog();

    setEnabled(false);
    connection("Подключение...");

    if (!isConfigured()) {
        connection("Не настроено");

        notice(
            "Заполни supabaseUrl и " +
            "supabasePublishableKey в community-config.js.",
            true
        );

        return;
    }

    try {
        db = createClient(
            config.supabaseUrl,
            config.supabasePublishableKey
        );

        const {
            data: sessionData,
            error: sessionError
        } = await db.auth.getSession();

        if (sessionError) {
            throw sessionError;
        }

        if (!sessionData.session) {
            const result =
                await db.auth.signInAnonymously();

            if (result.error) {
                throw result.error;
            }
        }

        const result =
            await db.auth.getUser();

        if (
            result.error ||
            !result.data.user
        ) {
            throw result.error || new Error(
                "Не удалось получить профиль."
            );
        }

        user = result.data.user;

        const adminResult = await db
            .from("community_admins")
            .select("user_id")
            .eq("user_id", user.id)
            .maybeSingle();

        if (adminResult.error) {
            console.warn(
                "Could not check administrator status:",
                adminResult.error
            );
        }

        isAdmin = Boolean(
            adminResult.data
        );

        await loadAccountNickname();

        setupMediaAdmin();
        updateComposer();

        // Built-in WT Guardian panel: no separate guardian-panel.js file.
        await initializeGuardian();

        await selectChannel("general");

        startRefreshTimer();

    } catch (error) {
        console.error(
            "Community initialization failed:",
            error
        );

        connection("Ошибка");

        notice(
            `Не удалось подключиться к сообществу: ${error.message}`,
            true
        );
    }
}


// ============================================================
// WT GUARDIAN 2.0 — BUILT-IN MODERATION FRONTEND
// Database/API: guardian_upgrade.sql
// The browser never creates privileged notices or moderation events.
// ============================================================

const GUARDIAN_SETTINGS_FIELDS = {
    enabled: ["WT Guardian включён", "checkbox"],
    block_links: ["Запрещать ссылки и email", "checkbox"],
    detect_obfuscation: ["Искать замаскированные ссылки", "checkbox"],
    detect_spam: ["Ограничивать частоту сообщений", "checkbox"],
    detect_duplicates: ["Находить повторяющиеся сообщения", "checkbox"],
    detect_flood: ["Обнаруживать флуд", "checkbox"],
    issue_warnings: ["Выдавать предупреждения", "checkbox"],
    min_delay_seconds: ["Пауза между сообщениями (сек)", "number", 1, 60],
    hourly_limit: ["Лимит сообщений в час", "number", 5, 500],
    duplicate_window_minutes: ["Период поиска повторов (мин)", "number", 1, 120],
    warning_limit: ["Предупреждений до ограничения", "number", 1, 10],
    mute_minutes: ["Время ограничения (мин)", "number", 1, 10080]
};

const GUARDIAN_REASONS = {
    blocked_link: "Ссылки и email запрещены.",
    obfuscated_link: "Обнаружена скрытая или изменённая ссылка.",
    sending_too_fast: "Сообщения отправляются слишком часто.",
    hourly_limit: "Достигнут часовой лимит сообщений.",
    duplicate_message: "Это сообщение уже недавно отправлялось.",
    character_flood: "Слишком много одинаковых символов.",
    caps_flood: "Слишком много заглавных букв.",
    muted: "Отправка сообщений временно ограничена.",
    admin_only: "Новости публикует только администрация.",
    unapproved_media: "Изображение ещё не прошло проверку.",
    reserved_nickname: "Этот никнейм зарезервирован.",
    invalid_channel: "Неизвестный канал.",
    invalid_nickname: "Некорректный никнейм.",
    message_too_long: "Сообщение слишком длинное.",
    empty_message: "Нельзя отправить пустое сообщение.",
    authentication: "Сессия авторизации недействительна.",
    configuration: "Правила Guardian ещё не настроены."
};

let guardianReady = false;
let guardianNoticesElement = null;
let guardianNoticesLoading = false;
let guardianNoticesTimer = null;
let guardianDialog = null;
let guardianStateElement = null;

function guardianRejectionMessage(result) {
    const code = String(result?.code || "unknown");
    let message = "🛡️ WT Guardian: " +
        (GUARDIAN_REASONS[code] || "Сообщение отклонено сервером.");

    const count = Number(result?.warning_count);
    if (Number.isInteger(count) && count > 0) {
        message += ` Предупреждений: ${count}.`;
    }

    if (result?.muted_until) {
        const until = new Date(result.muted_until);
        if (Number.isFinite(until.getTime())) {
            message += ` Ограничение до ${until.toLocaleString("ru-RU")}.`;
        }
    }

    if (result?.rate_limited) {
        message += " Дальнейшие попытки временно ограничены.";
    }

    return message;
}

function guardianNode(tag, text = "", className = "") {
    const node = document.createElement(tag);
    node.textContent = text;
    if (className) node.className = className;
    return node;
}

function guardianButton(label) {
    const button = guardianNode("button", label);
    button.type = "button";
    Object.assign(button.style, {
        padding: "10px 13px",
        border: "1px solid #436d96",
        borderRadius: "9px",
        background: "#214261",
        color: "#e3f1ff",
        cursor: "pointer"
    });
    return button;
}

function guardianCreateDialog(title) {
    const dialog = document.createElement("dialog");
    Object.assign(dialog.style, {
        width: "min(730px, 94vw)",
        maxWidth: "94vw",
        maxHeight: "85vh",
        overflowY: "auto",
        padding: "24px",
        color: "#edf6ff",
        background: "#14263b",
        border: "1px solid #436d96",
        borderRadius: "17px"
    });

    dialog.append(guardianNode("h2", title));
    const close = guardianButton("Закрыть");
    close.addEventListener("click", () => dialog.close());
    dialog.append(close);
    dialog.addEventListener("close", () => dialog.remove(), { once: true });
    document.body.append(dialog);
    return dialog;
}

async function refreshGuardianNotices() {
    if (!guardianReady || !db || !user ||
        !guardianNoticesElement || guardianNoticesLoading) return;

    guardianNoticesLoading = true;
    try {
        const { data, error } = await db
            .from("guardian_notices")
            .select("id,recipient_id,notice_type,body,created_at")
            .order("created_at", { ascending: false })
            .limit(8);

        if (error) throw error;
        const fragment = document.createDocumentFragment();
        for (const item of data || []) {
            const box = guardianNode("article", "", "guardian-system-notice");
            Object.assign(box.style, {
                padding: "12px 15px",
                marginBottom: "8px",
                border: "1px solid #3b6387",
                borderRadius: "11px",
                background: "#19334c",
                color: "#e2f1ff"
            });
            const heading = guardianNode("strong", "🛡️ WT Guardian");
            const body = guardianNode("p", item.body);
            body.style.margin = "7px 0";
            body.style.whiteSpace = "pre-wrap";
            const date = guardianNode(
                "small", new Date(item.created_at).toLocaleString("ru-RU")
            );
            box.append(heading, body, date);
            fragment.append(box);
        }
        guardianNoticesElement.replaceChildren(fragment);
    } catch (error) {
        console.warn("Guardian notices unavailable:", error);
    } finally {
        guardianNoticesLoading = false;
    }
}

async function refreshGuardianOwnState() {
    if (!guardianReady || !db || !user || !guardianStateElement) return;
    try {
        const { data, error } = await db
            .from("guardian_user_state")
            .select("warning_count,muted_until")
            .eq("user_id", user.id)
            .maybeSingle();
        if (error) throw error;
        const warnings = Number(data?.warning_count || 0);
        let label = `🛡️ Guardian · предупреждений: ${warnings}`;
        if (data?.muted_until) {
            const until = new Date(data.muted_until);
            if (until.getTime() > Date.now()) {
                label += ` · ограничение до ${until.toLocaleString("ru-RU")}`;
            }
        }
        guardianStateElement.textContent = label;
    } catch (error) {
        console.warn("Guardian state unavailable:", error);
    }
}

async function guardianOpenAdminPanel() {
    if (!guardianReady || !db || !user || !isAdmin) return;
    if (guardianDialog?.open) return;

    const dialog = guardianCreateDialog("🛡️ WT Guardian — управление");
    guardianDialog = dialog;
    dialog.addEventListener("close", () => {
        if (guardianDialog === dialog) guardianDialog = null;
    });

    const feedback = guardianNode("p", "Загрузка настроек...");
    feedback.setAttribute("role", "status");
    dialog.append(feedback);
    dialog.showModal();

    try {
        const { data: settings, error } = await db
            .from("guardian_settings")
            .select("*")
            .eq("id", 1)
            .single();
        if (error) throw error;
        if (!dialog.open) return;

        feedback.textContent = "";
        const form = document.createElement("form");
        form.append(guardianNode("h3", "Настройки фильтрации"));

        const inputs = new Map();
        for (const [key, definition] of Object.entries(GUARDIAN_SETTINGS_FIELDS)) {
            const [label, type, minimum, maximum] = definition;
            const row = guardianNode("label");
            Object.assign(row.style, {
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "15px",
                padding: "11px 0",
                borderBottom: "1px solid #304b66"
            });
            const caption = guardianNode("span", label);
            const input = document.createElement("input");
            input.type = type;
            if (type === "checkbox") {
                input.checked = Boolean(settings[key]);
            } else {
                input.min = String(minimum);
                input.max = String(maximum);
                input.step = "1";
                input.value = String(settings[key]);
                Object.assign(input.style, {
                    width: "105px",
                    padding: "9px",
                    border: "1px solid #496988",
                    borderRadius: "8px",
                    background: "#0e1b2a",
                    color: "#ffffff"
                });
            }
            inputs.set(key, input);
            row.append(caption, input);
            form.append(row);
        }

        const save = guardianButton("Сохранить правила");
        save.type = "submit";
        save.style.marginTop = "15px";
        const saveFeedback = guardianNode("p");
        form.append(save, saveFeedback);
        form.addEventListener("submit", async event => {
            event.preventDefault();
            if (save.disabled) return;
            const values = {};
            for (const [key, definition] of Object.entries(GUARDIAN_SETTINGS_FIELDS)) {
                const input = inputs.get(key);
                if (definition[1] === "checkbox") {
                    values[key] = input.checked;
                } else {
                    const number = Number(input.value);
                    if (!Number.isInteger(number) ||
                        number < definition[2] || number > definition[3]) {
                        saveFeedback.textContent = `Недопустимое значение: ${definition[0]}`;
                        return;
                    }
                    values[key] = number;
                }
            }
            save.disabled = true;
            try {
                const { error: updateError } = await db
                    .rpc("guardian_set_settings", { p_settings: values });
                if (updateError) throw updateError;
                saveFeedback.textContent = "✓ Правила сохранены на сервере.";
            } catch (error) {
                saveFeedback.textContent = `Ошибка: ${error.message}`;
            } finally {
                save.disabled = false;
            }
        });
        dialog.append(form);

        const announcementSection = guardianNode("section");
        announcementSection.style.marginTop = "28px";
        announcementSection.append(guardianNode("h3", "Официальное объявление"));
        const announcementText = document.createElement("textarea");
        announcementText.rows = 3;
        announcementText.maxLength = 1000;
        announcementText.placeholder = "Текст объявления WT Guardian...";
        Object.assign(announcementText.style, {
            display: "block",
            width: "100%",
            boxSizing: "border-box",
            padding: "12px",
            marginBottom: "10px",
            background: "#101e2d",
            color: "#ffffff",
            border: "1px solid #456787",
            borderRadius: "9px"
        });
        const announce = guardianButton("Опубликовать объявление");
        const announceFeedback = guardianNode("p");
        announce.addEventListener("click", async () => {
            const message = announcementText.value.trim();
            if (!message || announce.disabled) return;
            announce.disabled = true;
            try {
                const { error: announceError } = await db.rpc(
                    "guardian_announce", { p_body: message }
                );
                if (announceError) throw announceError;
                announcementText.value = "";
                announceFeedback.textContent = "✓ Объявление опубликовано.";
                await refreshGuardianNotices();
            } catch (error) {
                announceFeedback.textContent = `Ошибка: ${error.message}`;
            } finally {
                announce.disabled = false;
            }
        });
        announcementSection.append(announcementText, announce, announceFeedback);
        dialog.append(announcementSection);

        const eventsSection = guardianNode("section");
        eventsSection.style.marginTop = "28px";
        eventsSection.append(guardianNode("h3", "Журнал модерации"));
        const refreshEvents = guardianButton("Обновить журнал");
        const eventsList = guardianNode("div");
        eventsSection.append(refreshEvents, eventsList);
        dialog.append(eventsSection);

        async function loadEvents() {
            if (refreshEvents.disabled) return;
            refreshEvents.disabled = true;
            eventsList.textContent = "Загрузка событий...";
            try {
                const { data, error: eventsError } = await db
                    .from("guardian_events")
                    .select("user_id,event_type,details,warning_count,created_at")
                    .order("created_at", { ascending: false })
                    .limit(50);
                if (eventsError) throw eventsError;
                const fragment = document.createDocumentFragment();
                for (const item of data || []) {
                    const row = guardianNode("div");
                    Object.assign(row.style, {
                        padding: "11px 0",
                        borderBottom: "1px solid #38506a",
                        whiteSpace: "pre-wrap",
                        overflowWrap: "anywhere"
                    });
                    const title = guardianNode("strong", item.event_type);
                    const body = guardianNode("p",
                        `ID: ${item.user_id}\nПричина: ${item.details}\nПредупреждений: ${item.warning_count}`
                    );
                    const date = guardianNode("small",
                        new Date(item.created_at).toLocaleString("ru-RU")
                    );
                    row.append(title, body, date);
                    fragment.append(row);
                }
                eventsList.replaceChildren(fragment);
                if (!data?.length) eventsList.textContent = "Событий пока нет.";
            } catch (error) {
                eventsList.textContent = `Ошибка журнала: ${error.message}`;
            } finally {
                refreshEvents.disabled = false;
            }
        }
        refreshEvents.addEventListener("click", loadEvents);
        await loadEvents();
    } catch (error) {
        feedback.textContent = `Ошибка панели: ${error.message}`;
    }
}

async function initializeGuardian() {
    if (!db || !user || guardianReady) return;

    // This verifies the Guardian migration was installed.
    const { error } = await db
        .from("guardian_settings")
        .select("id")
        .eq("id", 1)
        .maybeSingle();

    if (error) {
        console.warn("WT Guardian is not installed yet:", error.message);
        notice("WT Guardian не настроен: сначала выполни guardian_upgrade.sql.", true);
        return;
    }

    guardianReady = true;

    const parent = document.querySelector(".guardian-message");
    if (parent && !document.querySelector(".guardian-system-notices")) {
        guardianNoticesElement = guardianNode(
            "section", "", "guardian-system-notices"
        );
        guardianNoticesElement.setAttribute("aria-label", "Сообщения WT Guardian");
        Object.assign(guardianNoticesElement.style, {
            margin: "13px 20px",
            display: "grid",
            gap: "8px"
        });
        parent.insertAdjacentElement("afterend", guardianNoticesElement);
    }

    const profile = $("guardianProfileState");
    if (profile && !document.querySelector(".guardian-user-status")) {
        guardianStateElement = guardianNode("div", "🛡️ WT Guardian", "guardian-user-status");
        Object.assign(guardianStateElement.style, {
            marginTop: "12px",
            color: "#b5cce3",
            fontSize: "12px",
            overflowWrap: "anywhere"
        });
        profile.append(guardianStateElement);
    }

    if (isAdmin) {
        const sidebar = document.querySelector(".community-sidebar");
        if (sidebar && !document.querySelector("#guardianAdminButton")) {
            const button = guardianButton("🛡️ WT Guardian — настройки");
            button.id = "guardianAdminButton";
            button.classList.add("channel");
            button.style.width = "100%";
            button.style.marginTop = "10px";
            button.addEventListener("click", guardianOpenAdminPanel);
            sidebar.append(button);
        }
    }

    await Promise.all([refreshGuardianNotices(), refreshGuardianOwnState()]);

    if (guardianNoticesTimer) clearInterval(guardianNoticesTimer);
    guardianNoticesTimer = setInterval(() => {
        if (!document.hidden) {
            refreshGuardianNotices();
            refreshGuardianOwnState();
        }
    }, 30000);

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            refreshGuardianNotices();
            refreshGuardianOwnState();
        }
    });
}

start();