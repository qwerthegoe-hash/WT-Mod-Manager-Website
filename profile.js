"use strict";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { COMMUNITY_CONFIG as config } from "./community-config.js";

const $ = id => document.getElementById(id);
const BUCKET = "community-avatars";
const MAX_FILE_BYTES = 5 * 1024 * 1024;
const COLORS = new Set(["blue", "teal", "purple"]);
const MIME = { "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif" };
const RESERVED = /^(admin|administrator|developer|moderator|system|system bot|wt guardian|wt mod manager)$/i;

let db;
let user;
let currentAvatarPath = null;
let uploadedObjectUrl = null;
let newFile = null;
let removeAvatarRequested = false;
let busy = false;

function status(text, isError = false) {
    const element = $("profileNotice");
    element.textContent = text;
    element.classList.toggle("error", isError);
}
function currentColor() {
    return document.querySelector('input[name="profileAccent"]:checked')?.value || "blue";
}
function previewName() {
    $("userProfileTitle").textContent = $("profileNickname").value.trim() || "Player";
}
function setAccent(value) {
    const color = COLORS.has(value) ? value : "blue";
    document.body.dataset.profileAccent = color;
    const field = document.querySelector('input[name="profileAccent"][value="' + color + '"]');
    if (field) field.checked = true;
}
function setAvatar(url) {
    const image = $("profileAvatarImage");
    const fallback = $("profileAvatarFallback");
    if (url) {
        image.src = url;
        image.hidden = false;
        fallback.hidden = true;
    } else {
        image.hidden = true;
        image.removeAttribute("src");
        fallback.hidden = false;
    }
}
function discardPreview() {
    if (uploadedObjectUrl) URL.revokeObjectURL(uploadedObjectUrl);
    uploadedObjectUrl = null;
}
async function validateImage(file) {
    const extension = MIME[file.type];
    if (!extension || file.size < 16 || file.size > MAX_FILE_BYTES)
        throw new Error("Выбери PNG, JPG, WebP или GIF размером до 5 МБ.");
    const buffer = new Uint8Array(await file.slice(0, 16).arrayBuffer());
    const signature = (...bytes) => bytes.every((b, i) => buffer[i] === b);
    const chars = (offset, n) => String.fromCharCode(...buffer.slice(offset, offset + n));
    const valid = (extension === "jpg" && signature(0xff, 0xd8, 0xff)) ||
        (extension === "png" && signature(137, 80, 78, 71, 13, 10, 26, 10)) ||
        (extension === "gif" && (chars(0, 6) === "GIF87a" || chars(0, 6) === "GIF89a")) ||
        (extension === "webp" && chars(0, 4) === "RIFF" && chars(8, 4) === "WEBP");
    if (!valid) throw new Error("Файл не соответствует формату изображения.");
    return extension;
}
function setBusy(value) {
    busy = value;
    $("saveProfile").disabled = value || !user;
    $("removeAvatar").disabled = value;
    $("avatarFile").disabled = value;
}
async function readCurrentAvatar(path) {
    if (!path) return setAvatar(null);
    const expectedPrefix = user.id + "/";
    if (!path.startsWith(expectedPrefix)) return setAvatar(null);
    const { data, error } = await db.storage.from(BUCKET).createSignedUrl(path, 3600);
    if (error) {
        console.warn("Avatar preview unavailable:", error.message);
        return setAvatar(null);
    }
    setAvatar(data.signedUrl);
}
function readLocalNickname() {
    try { return localStorage.getItem("wtmm-community-nick:" + user.id) || ""; }
    catch { return ""; }
}
function storeLocalNickname(name) {
    try { localStorage.setItem("wtmm-community-nick:" + user.id, name); }
    catch { /* Storage may be disabled. */ }
}
async function getIdentity() {
    const { data: sessionData, error: sessionError } = await db.auth.getSession();
    if (sessionError) throw sessionError;
    if (!sessionData.session) {
        const { error: signInError } = await db.auth.signInAnonymously();
        if (signInError) throw signInError;
    }
    const { data: identity, error } = await db.auth.getUser();
    if (error || !identity.user) throw error || new Error("Не удалось получить аккаунт.");
    return identity.user;
}
async function loadProfile() {
    const { data, error } = await db.from("community_user_profiles")
        .select("nickname,avatar_path,accent").eq("user_id", user.id).maybeSingle();
    if (error) throw error;
    $("profileNickname").value = data?.nickname || readLocalNickname() || "Player_" + user.id.slice(0, 6);
    $("profileUserId").value = user.id;
    previewName();
    setAccent(data?.accent || "blue");
    currentAvatarPath = data?.avatar_path || null;
    await readCurrentAvatar(currentAvatarPath);
}
async function saveProfile(event) {
    event.preventDefault();
    if (busy || !user) return;
    const nickname = $("profileNickname").value.trim();
    if (nickname.length < 2 || nickname.length > 24) {
        status("Никнейм должен содержать от 2 до 24 символов.", true);
        return;
    }
    if (RESERVED.test(nickname)) {
        status("Этот никнейм зарезервирован для администрации.", true);
        return;
    }
    setBusy(true);
    status("Сохранение профиля...");
    const oldPath = currentAvatarPath;
    let newPath = null;
    let pathToSave = removeAvatarRequested ? null : currentAvatarPath;
    try {
        if (newFile) {
            const extension = await validateImage(newFile);
            newPath = user.id + "/" + crypto.randomUUID() + "." + extension;
            const { error: uploadError } = await db.storage.from(BUCKET)
                .upload(newPath, newFile, { contentType: newFile.type, upsert: false, cacheControl: "3600" });
            if (uploadError) throw uploadError;
            pathToSave = newPath;
        }
        const { error } = await db.from("community_user_profiles").upsert({
            user_id: user.id, nickname, avatar_path: pathToSave,
            accent: currentColor(), updated_at: new Date().toISOString()
        }, { onConflict: "user_id" });
        if (error) throw error;
        currentAvatarPath = pathToSave;
        storeLocalNickname(nickname);
        newFile = null;
        removeAvatarRequested = false;
        $("avatarFile").value = "";
        discardPreview();
        if (oldPath && oldPath !== pathToSave) {
            const { error: cleanupError } = await db.storage.from(BUCKET).remove([oldPath]);
            if (cleanupError) console.warn("Old avatar cleanup:", cleanupError.message);
        }
        await readCurrentAvatar(currentAvatarPath);
        previewName();
        status("Профиль сохранён!");
    } catch (error) {
        if (newPath) await db.storage.from(BUCKET).remove([newPath]);
        status("Не удалось сохранить: " + (error?.message || "неизвестная ошибка") +
            ". Если таблица не найдена, выполни supabase/profile_upgrade.sql.", true);
    } finally {
        setBusy(false);
    }
}
function bindControls() {
    $("profileNickname").addEventListener("input", previewName);
    $("profileForm").addEventListener("submit", saveProfile);
    document.querySelectorAll('input[name="profileAccent"]').forEach(input => {
        input.addEventListener("change", () => setAccent(currentColor()));
    });
    $("avatarFile").addEventListener("change", async event => {
        const file = event.target.files?.[0];
        if (!file) return;
        try {
            await validateImage(file);
            discardPreview();
            newFile = file;
            removeAvatarRequested = false;
            uploadedObjectUrl = URL.createObjectURL(file);
            setAvatar(uploadedObjectUrl);
            status("Аватарка выбрана. Нажми «Сохранить профиль».");
        } catch (error) {
            event.target.value = "";
            status(error.message, true);
        }
    });
    $("removeAvatar").addEventListener("click", () => {
        if (busy) return;
        discardPreview();
        newFile = null;
        removeAvatarRequested = true;
        $("avatarFile").value = "";
        setAvatar(null);
        status("Аватарка будет удалена после сохранения.");
    });
    $("copyProfileId").addEventListener("click", async () => {
        if (!user) return;
        try {
            await navigator.clipboard.writeText(user.id);
            status("ID скопирован.");
        } catch {
            $("profileUserId").focus();
            $("profileUserId").select();
            status("ID выделен — скопируй его вручную.");
        }
    });
    window.addEventListener("pagehide", discardPreview);
}
async function init() {
    bindControls();
    try {
        if (!config.supabaseUrl || !config.supabasePublishableKey)
            throw new Error("Не настроено подключение к Supabase.");
        db = createClient(config.supabaseUrl, config.supabasePublishableKey);
        user = await getIdentity();
        await loadProfile();
        setBusy(false);
        status("");
    } catch (error) {
        console.error("Profile initialization failed:", error);
        status("Не удалось загрузить профиль: " + (error?.message || "ошибка") +
            ". Возможно, нужно выполнить supabase/profile_upgrade.sql.", true);
    }
}
init();
