"use strict";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.119.0";
import { COMMUNITY_CONFIG as config } from "./community-config.js";

const status = document.getElementById("result");
const button = document.getElementById("connectApp");
const params = new URLSearchParams(location.search);
const pairId = params.get("pair_id") || "";
const pairCode = params.get("code") || "";
const valid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(pairId) &&
    /^[a-f0-9]{36}$/.test(pairCode);
const db = createClient(config.supabaseUrl, config.supabasePublishableKey);
if (!valid) {
    button.disabled = true;
    status.textContent = "Неверная или устаревшая ссылка. Начни привязку из Windows-приложения заново.";
}
button.addEventListener("click", async () => {
    if (!valid) return;
    button.disabled = true;
    status.textContent = "Проверяю аккаунт...";
    try {
        // The website never sends its session tokens to the desktop.
        // The Edge Function verifies this browser's user JWT server-side.
        const {data: userResult,error: userError} = await db.auth.getUser();
        if (userError || !userResult?.user?.id)
            throw new Error("Сначала войди на сайт в этом браузере.");
        const {data,error} = await db.functions.invoke("wtmm-desktop-bridge",{
            body:{action:"claim",pair_id:pairId,pair_code:pairCode}
        });
        if (error || !data?.paired) throw error || new Error(data?.error || "Привязка не подтверждена");
        status.textContent = "Готово! Windows-приложение привязано к аккаунту. Теперь открой «Скачанные моды» и нажми «Добавить в приложение».";
    } catch (error) {
        status.textContent = "Не получилось связать: " + (error?.message || "ошибка сети") +
            ". Проверь аккаунт сайта и попробуй создать новую ссылку в приложении.";
        button.disabled = false;
    }
});
