"use strict";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { COMMUNITY_CONFIG as config } from "./community-config.js";

const $ = id => document.getElementById(id);
const FILE_BUCKET = "wtmm-mod-packages";
const COVER_BUCKET = "wtmm-mod-previews";
const FILE_LIMIT = 20 * 1024 * 1024;
const COVER_LIMIT = 5 * 1024 * 1024;
const CATEGORIES = {
    sights: "Игровые прицелы", camouflage: "Камуфляжи",
    sounds: "Звуки", interface: "Интерфейс", other: "Другое"
};
const IMAGE_MIMES = {
    "image/png": "png", "image/jpeg": "jpg",
    "image/webp": "webp", "image/gif": "gif"
};

let db, user, isAdmin = false, records = [], profiles = new Map();
let currentView = new URLSearchParams(location.search).get("mine") === "1" ? "mine" : "catalog";
let currentModId = null, sending = false;
const coverCache = new Map();

function say(message, error = false, target = "modsNotice") {
    const element = $(target);
    element.textContent = message || "";
    element.classList.toggle("error", error);
}
function node(tag, className = "", text = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
}
function link(href, text, className = "") {
    const a = node("a", className, text);
    a.href = href;
    return a;
}
async function ensureSession() {
    const { data, error } = await db.auth.getSession();
    if (error) throw error;
    if (!data.session) {
        const result = await db.auth.signInAnonymously();
        if (result.error) throw result.error;
    }
    const { data: identity, error: userError } = await db.auth.getUser();
    if (userError || !identity.user) throw userError || new Error("Нет аккаунта.");
    return identity.user;
}
async function getAdminStatus() {
    const { data, error } = await db.from("community_admins")
        .select("user_id").eq("user_id", user.id).maybeSingle();
    if (error) console.warn("Admin check:", error.message);
    return Boolean(data);
}
function modLabel(row) {
    return CATEGORIES[row.category] || CATEGORIES.other;
}
function profile(row) {
    return profiles.get(row.owner_id) || null;
}
function authorName(row) {
    return profile(row)?.nickname || (row.owner_id === user?.id ? "Я" : "Автор");
}
function authorLink(row) {
    const publicProfile = profile(row);
    return publicProfile ? "creator.html?id=" + encodeURIComponent(row.owner_id) : null;
}
async function coverUrl(row) {
    if (!row.cover_path) return null;
    if (coverCache.has(row.cover_path)) return coverCache.get(row.cover_path);
    const { data, error } = await db.storage.from(COVER_BUCKET)
        .createSignedUrl(row.cover_path, 1200);
    if (error || !data?.signedUrl) {
        console.warn("Cover URL unavailable:", error?.message);
        return null;
    }
    coverCache.set(row.cover_path, data.signedUrl);
    return data.signedUrl;
}
async function queryAll() {
    const { data, error } = await db.from("wtmm_mods")
        .select("id,owner_id,title,description,category,version,status,file_path,cover_path,rejection_reason,created_at")
        .order("created_at", { ascending: false }).limit(150);
    if (error) throw error;
    records = data || [];
    const ids = [...new Set(records.map(row => row.owner_id))];
    profiles = new Map();
    if (ids.length) {
        const { data: users, error: profileError } = await db
            .from("community_user_profiles")
            .select("user_id,nickname,avatar_path,is_public")
            .in("user_id", ids);
        if (profileError) console.warn("Profile lookup:", profileError.message);
        else for (const item of users || []) {
            if (item.is_public !== false || item.user_id === user.id)
                profiles.set(item.user_id, item);
        }
    }
}
function visibleRecords() {
    const q = $("modsSearch").value.trim().toLocaleLowerCase();
    const category = $("modsCategory").value;
    const view = currentView === "moderation" && !isAdmin ? "catalog" : currentView;
    const rows = records.filter(row => {
        if (view === "catalog" && row.status !== "approved") return false;
        if (view === "mine" && row.owner_id !== user.id) return false;
        if (view === "moderation" && row.status !== "pending") return false;
        if (category !== "all" && row.category !== category) return false;
        if (q && !(row.title + " " + row.description + " " + authorName(row))
            .toLocaleLowerCase().includes(q)) return false;
        return true;
    });
    const sort = $("modsSort").value;
    if (sort === "name") rows.sort((a, b) => a.title.localeCompare(b.title, "ru"));
    else if (sort === "old") rows.reverse();
    return rows;
}
async function makeCard(row) {
    const card = node("article", "mod-card");
    const cover = node("div", "mod-card-cover");
    cover.textContent = "WT";
    const signed = await coverUrl(row);
    if (signed) {
        const img = node("img");
        img.src = signed;
        img.alt = "Обложка: " + row.title;
        img.loading = "lazy";
        cover.replaceChildren(img);
    }
    const content = node("div", "mod-card-content");
    content.append(node("h3", "", row.title));
    content.append(node("div", "mod-card-meta",
        modLabel(row) + " · " + authorName(row) + " · v" + row.version));
    content.append(node("p", "mod-card-copy",
        row.description.slice(0, 140) + (row.description.length > 140 ? "…" : "")));
    const end = node("div", "mod-card-end");
    const details = node("button", "mod-card-button", "Подробнее");
    details.type = "button";
    details.addEventListener("click", () => showModDetails(row.id));
    const status = node("span", "mod-status " + row.status,
        row.status === "approved" ? "Одобрено" :
        row.status === "pending" ? "Проверка" : "Отклонено");
    if (currentView === "catalog") end.append(details);
    else end.append(details, status);
    content.append(end);
    card.append(cover, content);
    return card;
}
let renderVersion = 0;
async function render() {
    const version = ++renderVersion;
    document.querySelectorAll(".mods-tab").forEach(button => {
        const selected = button.dataset.view === currentView;
        button.classList.toggle("active", selected);
        button.setAttribute("aria-pressed", String(selected));
    });
    const rows = visibleRecords();
    $("modsCounter").textContent = rows.length + " модов";
    $("modsEmpty").hidden = rows.length !== 0;
    const fragment = document.createDocumentFragment();
    const cards = await Promise.all(rows.map(makeCard));
    if (version !== renderVersion) return;
    for (const card of cards) fragment.append(card);
    $("modsGrid").replaceChildren(fragment);
}
async function refresh() {
    say("Загружаю модификации...");
    await queryAll();
    await render();
    say("");
}
async function showModDetails(id) {
    const row = records.find(item => item.id === id);
    if (!row) return;
    currentModId = row.id;
    const detail = $("modDetailsContent");
    const dialog = $("modDetailsDialog");
    const content = document.createDocumentFragment();
    const imgUrl = await coverUrl(row);
    if (imgUrl) {
        const img = node("img", "mod-details-cover");
        img.src = imgUrl; img.alt = "Обложка " + row.title;
        content.append(img);
    }
    content.append(node("h2", "mod-details-title", row.title));
    const info = node("div", "mod-details-info");
    info.append(node("span", "", modLabel(row) + " · версия " + row.version));
    const author = authorLink(row);
    info.append(author ? link(author, authorName(row), "mod-details-author") :
        node("span", "", authorName(row)));
    content.append(info);
    content.append(node("p", "mod-details-text", row.description || "Описание отсутствует."));
    if (row.status !== "approved") {
        content.append(node("p", "mod-status " + row.status,
            row.status === "pending" ? "Ожидает модерации" : "Отклонено"));
        if (row.rejection_reason)
            content.append(node("p", "mods-review-note", "Причина: " + row.rejection_reason));
    }
    const actions = node("div", "mod-details-actions");
    if (row.status === "approved") {
        const button = node("button", "mods-primary", "Получить ссылку для скачивания");
        button.type = "button";
        const downloadBox = node("div", "mods-review-link");
        button.addEventListener("click", async () => {
            button.disabled = true;
            try {
                const { data, error } = await db.storage.from(FILE_BUCKET)
                    .createSignedUrl(row.file_path, 90);
                if (error) throw error;
                const a = link(data.signedUrl, "Скачать ZIP (ссылка действует 90 секунд)");
                a.target = "_blank"; a.rel = "noopener noreferrer";
                downloadBox.replaceChildren(a);
            } catch (error) {
                downloadBox.textContent = "Ошибка скачивания: " + error.message;
            } finally { button.disabled = false; }
        });
        actions.append(button, downloadBox);
    }
    if (currentView === "moderation" && isAdmin && row.status === "pending") {
        const warning = node("p", "mods-review-note",
            "Перед публикацией обязательно проверь архив вручную. Не запускай неизвестные файлы.");
        content.append(warning);
        const preview = node("button", "mods-secondary", "Сформировать ссылку на ZIP");
        preview.type = "button";
        const previewArea = node("div", "mods-review-link");
        const approve = node("button", "mods-primary", "Одобрить");
        approve.type = "button"; approve.disabled = true;
        const reject = node("button", "mods-secondary", "Отклонить");
        reject.type = "button";
        preview.addEventListener("click", async () => {
            preview.disabled = true;
            try {
                const { data, error } = await db.storage.from(FILE_BUCKET)
                    .createSignedUrl(row.file_path, 120);
                if (error) throw error;
                const a = link(data.signedUrl, "Открыть/скачать архив для ручной проверки");
                a.target = "_blank"; a.rel = "noopener noreferrer";
                a.addEventListener("click", () => { approve.disabled = false; });
                previewArea.replaceChildren(a);
            } catch (error) {
                previewArea.textContent = "Не удалось открыть архив: " + error.message;
            } finally { preview.disabled = false; }
        });
        approve.addEventListener("click", () => decideMod(row, "approved"));
        reject.addEventListener("click", () => decideMod(row, "rejected"));
        actions.append(preview, previewArea, approve, reject);
    }
    if (currentView === "mine" && row.owner_id === user.id &&
        row.status !== "approved") {
        const remove = node("button", "mods-secondary", "Удалить заявку");
        remove.type = "button";
        remove.addEventListener("click", () => deleteSubmission(row));
        actions.append(remove);
    }
    content.append(actions);
    detail.replaceChildren(content);
    if (!dialog.open) dialog.showModal();
}
async function decideMod(row, status) {
    if (!isAdmin || !user || row.status !== "pending") return;
    if (status === "approved" && !confirm("Архив проверен вручную? Опубликовать мод?")) return;
    if (status === "rejected" && !confirm("Отклонить эту заявку?")) return;
    const reason = status === "rejected" ? "Отклонено администратором" : null;
    const { data, error } = await db.from("wtmm_mods")
        .update({
            status, rejection_reason: reason,
            reviewed_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        }).eq("id", row.id).eq("status", "pending").select("id");
    if (error || !data?.length) {
        say("Не удалось изменить статус: " + (error?.message || "заявка уже обработана"), true);
        return;
    }
    $("modDetailsDialog").close();
    try { await refresh(); } catch (error) { say("Ошибка обновления: " + error.message, true); }
}
async function deleteSubmission(row) {
    if (row.owner_id !== user.id || row.status === "approved") return;
    if (!confirm("Удалить заявку на публикацию?")) return;
    const { error } = await db.from("wtmm_mods").delete().eq("id", row.id);
    if (error) { say("Ошибка удаления: " + error.message, true); return; }
    await Promise.all([
        db.storage.from(FILE_BUCKET).remove([row.file_path]),
        row.cover_path ? db.storage.from(COVER_BUCKET).remove([row.cover_path]) : Promise.resolve()
    ]);
    $("modDetailsDialog").close();
    await refresh();
}
function zipLooksValid(bytes) {
    return bytes.length >= 4 && bytes[0] === 80 && bytes[1] === 75 &&
        ((bytes[2] === 3 && bytes[3] === 4) || (bytes[2] === 5 && bytes[3] === 6));
}
async function imageExtension(file) {
    const ext = IMAGE_MIMES[file?.type];
    if (!file || !ext || file.size < 16 || file.size > COVER_LIMIT)
        throw new Error("Обложка должна быть PNG, JPG, GIF или WebP до 5 МБ.");
    const bytes = new Uint8Array(await file.slice(0, 16).arrayBuffer());
    const at = (start, len) => String.fromCharCode(...bytes.slice(start, start + len));
    const valid = (ext === "png" && at(1, 3) === "PNG") ||
        (ext === "jpg" && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) ||
        (ext === "gif" && ["GIF87a", "GIF89a"].includes(at(0, 6))) ||
        (ext === "webp" && at(0, 4) === "RIFF" && at(8, 4) === "WEBP");
    if (!valid) throw new Error("Неверная сигнатура изображения.");
    return ext;
}
async function uploadMod(event) {
    event.preventDefault();
    if (sending || !user) return;
    const form = event.currentTarget;
    const title = form.elements.title.value.trim();
    const description = form.elements.description.value.trim();
    const category = form.elements.category.value;
    const version = form.elements.version.value.trim();
    const pack = form.elements.package.files[0];
    const cover = form.elements.cover.files[0];
    if (title.length < 3 || title.length > 90 || !CATEGORIES[category] ||
        !version || version.length > 32 || description.length > 2500) {
        say("Проверь название, категорию, версию и описание.", true, "submitNotice"); return;
    }
    if (!pack || !pack.name.toLowerCase().endsWith(".zip") ||
        pack.size < 4 || pack.size > FILE_LIMIT) {
        say("Нужен ZIP-архив размером до 20 МБ.", true, "submitNotice"); return;
    }
    const prefix = new Uint8Array(await pack.slice(0, 4).arrayBuffer());
    if (!zipLooksValid(prefix)) {
        say("Файл не похож на ZIP-архив.", true, "submitNotice"); return;
    }
    let coverExt = null;
    try { if (cover) coverExt = await imageExtension(cover); }
    catch (error) { say(error.message, true, "submitNotice"); return; }
    const id = crypto.randomUUID();
    const path = user.id + "/" + id + "/" + crypto.randomUUID() + ".zip";
    const coverPath = cover ? user.id + "/" + id + "/" + crypto.randomUUID() + "." + coverExt : null;
    sending = true;
    $("submitModButton").disabled = true;
    const uploaded = [];
    try {
        say("Загружаю архив в закрытое хранилище...", false, "submitNotice");
        const { error: fileError } = await db.storage.from(FILE_BUCKET).upload(path, pack, {
            contentType: "application/zip", upsert: false
        });
        if (fileError) throw fileError;
        uploaded.push({ bucket: FILE_BUCKET, path });
        if (cover) {
            say("Загружаю обложку...", false, "submitNotice");
            const { error: coverError } = await db.storage.from(COVER_BUCKET).upload(
                coverPath, cover, { contentType: cover.type, upsert: false }
            );
            if (coverError) throw coverError;
            uploaded.push({ bucket: COVER_BUCKET, path: coverPath });
        }
        const { error: dbError } = await db.from("wtmm_mods").insert({
            id, owner_id: user.id, title, description, category, version,
            status: "pending", file_path: path, cover_path: coverPath
        });
        if (dbError) throw dbError;
        form.reset();
        say("Мод успешно отправлен на ручную модерацию!", false, "submitNotice");
        currentView = "mine";
        await refresh();
    } catch (error) {
        await Promise.all(uploaded.map(x => db.storage.from(x.bucket).remove([x.path])));
        say("Не удалось отправить мод: " + error.message +
            ". Если таблицы ещё нет, выполни SQL-скрипт community_platform_upgrade.sql.", true, "submitNotice");
    } finally {
        sending = false;
        $("submitModButton").disabled = false;
    }
}
function bind() {
    document.querySelectorAll(".mods-tab").forEach(button => {
        button.addEventListener("click", async () => {
            currentView = button.dataset.view;
            await render();
        });
    });
    for (const id of ["modsSearch", "modsCategory", "modsSort"]) {
        $(id).addEventListener(id === "modsSearch" ? "input" : "change", () => render());
    }
    $("showSubmit").addEventListener("click", () => {
        $("submitPanel").hidden = false;
        $("submitPanel").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    $("closeSubmit").addEventListener("click", () => { $("submitPanel").hidden = true; });
    $("modSubmitForm").addEventListener("submit", uploadMod);
    $("closeModDetails").addEventListener("click", () => $("modDetailsDialog").close());
    $("modDetailsDialog").addEventListener("click", e => {
        if (e.target === $("modDetailsDialog")) $("modDetailsDialog").close();
    });
}
async function init() {
    bind();
    try {
        db = createClient(config.supabaseUrl, config.supabasePublishableKey);
        user = await ensureSession();
        isAdmin = await getAdminStatus();
        $("moderationTab").hidden = !isAdmin;
        await refresh();
    } catch (error) {
        console.error("Mod library initialization:", error);
        say("Ошибка подключения библиотеки: " + error.message +
            ". Проверь, выполнен ли SQL-файл community_platform_upgrade.sql.", true);
    }
}
init();
