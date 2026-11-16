"use strict";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { COMMUNITY_CONFIG as config } from "./community-config.js";

const $ = id => document.getElementById(id);
const COLORS = new Set(["blue", "teal", "purple"]);
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const IMAGE_TYPES = {
    "image/jpeg": "jpg", "image/png": "png",
    "image/webp": "webp", "image/gif": "gif"
};
const RESERVED = /^(admin|administrator|developer|moderator|system|system bot|wt guardian|wt mod manager)$/i;
const MEDIA = {
    avatar: {
        bucket: "community-avatars", input: "avatarFile", image: "profileAvatarImage",
        fallback: "profileAvatarFallback", remove: "removeAvatar", current: null,
        file: null, removeRequested: false, tempUrl: null
    },
    banner: {
        bucket: "community-banners", input: "bannerFile", image: "profileBannerImage",
        fallback: "profileBannerFallback", remove: "removeBanner", current: null,
        file: null, removeRequested: false, tempUrl: null
    }
};
let db;
let user;
let saving = false;

function report(text, error = false, id = "profileNotice") {
    const el = $(id);
    if (!el) return;
    el.textContent = text;
    el.classList.toggle("error", error);
}
function accentValue() {
    return document.querySelector('input[name="profileAccent"]:checked')?.value || "blue";
}
function setAccent(value) {
    const chosen = COLORS.has(value) ? value : "blue";
    document.body.dataset.profileAccent = chosen;
    const field = document.querySelector('input[name="profileAccent"][value="' + chosen + '"]');
    if (field) field.checked = true;
}
function updateHeading() {
    $("userProfileTitle").textContent = $("profileNickname").value.trim() || "Player";
}
function picture(item, url) {
    const img = $(item.image), fallback = $(item.fallback);
    if (url) {
        img.src = url; img.hidden = false; fallback.hidden = true;
    } else {
        img.hidden = true; img.removeAttribute("src"); fallback.hidden = false;
    }
}
function revokePreview(item) {
    if (item.tempUrl) URL.revokeObjectURL(item.tempUrl);
    item.tempUrl = null;
}
async function imageExtension(file) {
    if (!file || !IMAGE_TYPES[file.type] || file.size < 16 || file.size > MAX_IMAGE_BYTES)
        throw new Error("Выбери PNG, JPG, WebP или GIF размером до 5 МБ.");
    const signature = new Uint8Array(await file.slice(0, 16).arrayBuffer());
    const has = (...numbers) => numbers.every((x, i) => signature[i] === x);
    const chars = (from, count) => String.fromCharCode(...signature.subarray(from, from + count));
    const ext = IMAGE_TYPES[file.type];
    const valid = (ext === "jpg" && has(255, 216, 255)) ||
        (ext === "png" && has(137, 80, 78, 71, 13, 10, 26, 10)) ||
        (ext === "gif" && ["GIF87a", "GIF89a"].includes(chars(0, 6))) ||
        (ext === "webp" && chars(0, 4) === "RIFF" && chars(8, 4) === "WEBP");
    if (!valid) throw new Error("Файл не соответствует заявленному формату.");
    return ext;
}
async function signedPicture(item) {
    if (!item.current || !item.current.startsWith(user.id + "/")) {
        picture(item, null); return;
    }
    const { data, error } = await db.storage.from(item.bucket).createSignedUrl(item.current, 3600);
    if (error) {
        console.warn("Private image preview unavailable", error.message);
        picture(item, null); return;
    }
    picture(item, data.signedUrl);
}
function setSaving(value) {
    saving = value;
    $("saveProfile").disabled = value || !user;
    for (const media of Object.values(MEDIA)) {
        $(media.input).disabled = value;
        $(media.remove).disabled = value;
    }
}
function readLocalNickname() {
    try { return localStorage.getItem("wtmm-community-nick:" + user.id) || ""; }
    catch { return ""; }
}
function saveLocalNickname(value) {
    try { localStorage.setItem("wtmm-community-nick:" + user.id, value); }
    catch { /* Browser storage is optional. */ }
}
async function getIdentity() {
    const { data: session, error: sessionError } = await db.auth.getSession();
    if (sessionError) throw sessionError;
    if (!session.session) {
        const { error } = await db.auth.signInAnonymously();
        if (error) throw error;
    }
    const { data, error } = await db.auth.getUser();
    if (error || !data.user) throw error || new Error("Не удалось получить аккаунт.");
    return data.user;
}
async function loadProfile() {
    const { data, error } = await db.from("community_user_profiles")
        .select("nickname,avatar_path,banner_path,bio,accent,is_public")
        .eq("user_id", user.id).maybeSingle();
    if (error) throw error;

    $("profileNickname").value = data?.nickname || readLocalNickname() ||
        "Player_" + user.id.slice(0, 6);
    $("profileBio").value = data?.bio || "";
    $("profileUserId").value = user.id;
    $("profileIsPublic").checked = data?.is_public !== false;
    $("openPublicProfile").href = "creator.html?id=" + encodeURIComponent(user.id);
    $("accountEmail").value = user.email || "";
    setAccent(data?.accent || "blue");
    updateHeading();
    MEDIA.avatar.current = data?.avatar_path || null;
    MEDIA.banner.current = data?.banner_path || null;
    await Promise.all(Object.values(MEDIA).map(signedPicture));
}
async function uploadMedia(item) {
    if (!item.file) return null;
    const ext = await imageExtension(item.file);
    const path = user.id + "/" + crypto.randomUUID() + "." + ext;
    const { error } = await db.storage.from(item.bucket).upload(path, item.file, {
        contentType: item.file.type, upsert: false, cacheControl: "3600"
    });
    if (error) throw error;
    return path;
}
async function saveProfile(event) {
    event.preventDefault();
    if (saving || !user) return;
    const name = $("profileNickname").value.trim();
    const bio = $("profileBio").value.trim();
    if (name.length < 2 || name.length > 24) {
        report("Никнейм должен содержать от 2 до 24 символов.", true); return;
    }
    if (RESERVED.test(name)) {
        report("Этот никнейм зарезервирован для администрации.", true); return;
    }
    if (bio.length > 320) {
        report("Описание слишком длинное (максимум 320 символов).", true); return;
    }

    setSaving(true);
    report("Сохраняю профиль и изображения...");
    const nextPaths = {}, newFiles = [];
    try {
        for (const [kind, item] of Object.entries(MEDIA)) {
            nextPaths[kind] = item.removeRequested ? null : item.current;
            if (item.file) {
                const path = await uploadMedia(item);
                nextPaths[kind] = path;
                newFiles.push({ item, path });
            }
        }
        const { error } = await db.from("community_user_profiles").upsert({
            user_id: user.id, nickname: name, bio,
            avatar_path: nextPaths.avatar,
            banner_path: nextPaths.banner,
            is_public: $("profileIsPublic").checked,
            accent: accentValue(),
            updated_at: new Date().toISOString()
        }, { onConflict: "user_id" });
        if (error) throw error;

        saveLocalNickname(name);
        for (const [kind, item] of Object.entries(MEDIA)) {
            const oldPath = item.current;
            item.current = nextPaths[kind];
            item.file = null;
            item.removeRequested = false;
            $(item.input).value = "";
            revokePreview(item);
            if (oldPath && oldPath !== item.current) {
                const { error: removeError } = await db.storage.from(item.bucket).remove([oldPath]);
                if (removeError) console.warn("Old image cleanup failed", removeError.message);
            }
        }
        await Promise.all(Object.values(MEDIA).map(signedPicture));
        report("Профиль сохранён! Изменения доступны на сайте.");
    } catch (error) {
        for (const file of newFiles) {
            const { error: cleanupError } = await db.storage.from(file.item.bucket).remove([file.path]);
            if (cleanupError) console.warn("Failed to clean upload", cleanupError.message);
        }
        report("Ошибка сохранения: " + (error?.message || String(error)) +
            ". Проверь, выполнены ли SQL-скрипты профиля.", true);
    } finally {
        setSaving(false);
    }
}
async function fileSelected(kind, event) {
    const item = MEDIA[kind], file = event.target.files?.[0];
    if (!file) return;
    try {
        await imageExtension(file);
        revokePreview(item);
        item.file = file;
        item.removeRequested = false;
        item.tempUrl = URL.createObjectURL(file);
        picture(item, item.tempUrl);
        report("Изображение выбрано. Нажми «Сохранить профиль».");
    } catch (error) {
        event.target.value = "";
        report(error.message, true);
    }
}
function removeImage(kind) {
    const item = MEDIA[kind];
    if (saving) return;
    revokePreview(item);
    item.file = null;
    item.removeRequested = true;
    $(item.input).value = "";
    picture(item, null);
    report("Изображение будет удалено после сохранения.");
}
async function runAccountChange(action, payload, message) {
    try {
        report("Отправляю запрос...", false, "accountNotice");
        const { error } = await db.auth.updateUser(payload);
        if (error) throw error;
        report(message, false, "accountNotice");
        if (action === "password") $("accountPassword").value = "";
    } catch (error) {
        report("Не удалось выполнить действие: " + error.message, true, "accountNotice");
    }
}
function bind() {
    $("profileForm").addEventListener("submit", saveProfile);
    $("profileNickname").addEventListener("input", updateHeading);
    document.querySelectorAll('input[name="profileAccent"]').forEach(el =>
        el.addEventListener("change", () => setAccent(accentValue())));
    for (const kind of Object.keys(MEDIA)) {
        const item = MEDIA[kind];
        $(item.input).addEventListener("change", event => fileSelected(kind, event));
        $(item.remove).addEventListener("click", () => removeImage(kind));
    }
    $("copyProfileId").addEventListener("click", async () => {
        if (!user) return;
        try {
            await navigator.clipboard.writeText(user.id);
            report("ID скопирован.");
        } catch {
            $("profileUserId").select();
            report("ID выделен — скопируй вручную.");
        }
    });
    $("linkAccountEmail").addEventListener("click", async () => {
        const email = $("accountEmail").value.trim();
        if (!email || !$("accountEmail").checkValidity()) {
            report("Введи действительный email.", true, "accountNotice"); return;
        }
        await runAccountChange("email", { email },
            "Проверь письмо и подтверди email. После подтверждения установи пароль. " +
            "Для анонимных аккаунтов в Supabase должно быть включено Manual Linking.");
    });
    $("setAccountPassword").addEventListener("click", async () => {
        const password = $("accountPassword").value;
        if (password.length < 10) {
            report("Пароль должен содержать не менее 10 символов.", true, "accountNotice"); return;
        }
        const { data, error } = await db.auth.getUser();
        if (error || !data?.user?.email) {
            report("Сначала привяжи и подтверди email.", true, "accountNotice"); return;
        }
        await runAccountChange("password", { password }, "Пароль установлен. Теперь аккаунт можно использовать для входа.");
    });
    $("loginAccount").addEventListener("click", async () => {
        const email = $("loginEmail").value.trim();
        const password = $("loginPassword").value;
        if (!email || !password) {
            report("Введи email и пароль.", true, "accountNotice"); return;
        }
        try {
            report("Выполняю вход...", false, "accountNotice");
            const { error } = await db.auth.signInWithPassword({ email, password });
            if (error) throw error;
            window.location.reload();
        } catch (error) {
            report("Не удалось войти: " + error.message, true, "accountNotice");
        }
    });
    window.addEventListener("pagehide", () =>
        Object.values(MEDIA).forEach(revokePreview));
}
async function init() {
    bind();
    try {
        if (!config.supabaseUrl || !config.supabasePublishableKey)
            throw new Error("Подключение Supabase не настроено.");
        db = createClient(config.supabaseUrl, config.supabasePublishableKey);
        user = await getIdentity();
        await loadProfile();
        setSaving(false);
        report("");
    } catch (error) {
        console.error("Profile initialization:", error);
        report("Не удалось открыть профиль: " + error.message +
            ". Возможно, требуется выполнить SQL-скрипты profile_upgrade.sql и community_platform_upgrade.sql.", true);
    }
}
init();
