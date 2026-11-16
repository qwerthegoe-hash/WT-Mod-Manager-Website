"use strict";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { COMMUNITY_CONFIG as config } from "./community-config.js";

const $ = id => document.getElementById(id);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const CATEGORIES = {
    sights: "Игровые прицелы", camouflage: "Камуфляжи", sounds: "Звуки",
    interface: "Интерфейс", other: "Другое"
};

function textNode(tag, value, className = "") {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = value || "";
    return el;
}
function setImage(imageId, fallbackId, url) {
    const img = $(imageId), fallback = $(fallbackId);
    if (!url) { img.hidden = true; fallback.hidden = false; return; }
    img.src = url;
    img.hidden = false;
    fallback.hidden = true;
}
async function signed(db, bucket, path) {
    if (!path) return null;
    const { data, error } = await db.storage.from(bucket).createSignedUrl(path, 1800);
    if (error) { console.warn("Image unavailable:", error.message); return null; }
    return data?.signedUrl || null;
}
async function session(db) {
    const { data, error } = await db.auth.getSession();
    if (error) throw error;
    if (!data.session) {
        const { error: authError } = await db.auth.signInAnonymously();
        if (authError) throw authError;
    }
}
async function renderMod(db, item) {
    const card = textNode("article", "", "mod-card");
    const cover = textNode("div", "WT", "mod-card-cover");
    const url = await signed(db, "wtmm-mod-previews", item.cover_path);
    if (url) {
        const image = document.createElement("img");
        image.src = url;
        image.loading = "lazy";
        image.alt = "Обложка мода " + item.title;
        cover.replaceChildren(image);
    }
    const content = textNode("div", "", "mod-card-content");
    content.append(
        textNode("h3", item.title),
        textNode("div", (CATEGORIES[item.category] || "Другое") + " · v" + item.version, "mod-card-meta"),
        textNode("p", item.description.slice(0, 135), "mod-card-copy")
    );
    const end = textNode("div", "", "mod-card-end");
    const link = textNode("a", "Подробнее", "mod-card-button");
    link.href = "mods.html?mod=" + encodeURIComponent(item.id);
    end.append(link);
    content.append(end);
    card.append(cover, content);
    return card;
}
async function init() {
    const userId = new URLSearchParams(location.search).get("id") || "";
    if (!UUID.test(userId)) {
        $("creatorNotice").textContent = "Некорректная ссылка на профиль.";
        return;
    }
    try {
        const db = createClient(config.supabaseUrl, config.supabasePublishableKey);
        await session(db);
        const { data: player, error } = await db.from("community_user_profiles")
            .select("user_id,nickname,bio,avatar_path,banner_path,is_public,accent")
            .eq("user_id", userId).maybeSingle();
        if (error) throw error;
        if (!player || player.is_public === false) {
            $("creatorNotice").textContent = "Этот профиль скрыт или пока не создан.";
            return;
        }
        $("creatorName").textContent = player.nickname;
        $("creatorBio").textContent = player.bio || "Игрок сообщества WT Mod Manager";
        document.title = player.nickname + " — WT Mod Manager";
        document.body.dataset.profileAccent = player.accent || "blue";
        const [avatarUrl, bannerUrl] = await Promise.all([
            signed(db, "community-avatars", player.avatar_path),
            signed(db, "community-banners", player.banner_path)
        ]);
        setImage("creatorAvatarImage", "creatorAvatarFallback", avatarUrl);
        setImage("creatorBannerImage", "creatorBannerFallback", bannerUrl);

        const { data: mods, error: modError } = await db.from("wtmm_mods")
            .select("id,title,description,category,version,cover_path,created_at")
            .eq("owner_id", userId).eq("status", "approved")
            .order("created_at", { ascending: false }).limit(100);
        if (modError) throw modError;
        const items = mods || [];
        $("creatorModCount").textContent = "Одобренных модов: " + items.length;
        $("creatorHeader").hidden = false;
        $("creatorModsHeading").hidden = false;
        const cards = await Promise.all(items.map(mod => renderMod(db, mod)));
        $("creatorModsGrid").replaceChildren(...cards);
        $("creatorNotice").textContent = items.length ? "" : "У автора пока нет опубликованных модификаций.";
    } catch (error) {
        console.error("Creator page:", error);
        $("creatorNotice").textContent = "Не удалось загрузить профиль: " + error.message +
            ". Проверь настройки Supabase и SQL-скрипты.";
    }
}
init();
