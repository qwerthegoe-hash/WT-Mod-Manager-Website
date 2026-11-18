"use strict";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.119.0";
import { COMMUNITY_CONFIG as config } from "./community-config.js";

const status = document.getElementById("result");
const button = document.getElementById("connectApp");
const params = new URLSearchParams(location.search);
const rawPort = params.get("port") || "";
const challenge = params.get("challenge") || "";
const port = Number(rawPort);
const valid = /^\d{4,5}$/.test(rawPort) && Number.isSafeInteger(port) &&
    port >= 1024 && port <= 65535 && /^[a-f0-9]{48}$/.test(challenge);
const db = createClient(config.supabaseUrl, config.supabasePublishableKey);

if (!valid) {
    button.disabled = true;
    status.textContent = "Неверная или устаревшая ссылка. Открой привязку ещё раз из Windows-приложения.";
}
button.addEventListener("click", async () => {
    if (!valid) return;
    button.disabled = true;
    status.textContent = "Проверяю аккаунт...";
    try {
        const {data: sessionData,error: sessionError} = await db.auth.getSession();
        if (sessionError) throw sessionError;
        const session = sessionData?.session;
        if (!session?.access_token || !session?.refresh_token)
            throw new Error("Сначала войди на сайт в этом браузере.");
        const {data: identity,error: userError} = await db.auth.getUser();
        if (userError || !identity?.user?.id)
            throw new Error("Не удалось проверить сеанс сайта.");
        const response = await fetch("http://127.0.0.1:" + port + "/link", {
            method: "POST",
            cache: "no-store",
            headers: {"Content-Type":"application/json","X-WTMM-Pair":challenge},
            body: JSON.stringify({
                access_token:session.access_token,
                refresh_token:session.refresh_token
            })
        });
        if (!response.ok) throw new Error("Приложение отклонило привязку. Проверь, что оно открыто.");
        status.textContent = "Аккаунт связан. Теперь можно нажимать «Добавить в приложение» у скачанных модов.";
    } catch (error) {
        status.textContent = "Не получилось связать: " + (error?.message || "ошибка сети") +
            ". Проверь, что страница открыта в том же браузере и Windows-приложение запущено.";
        button.disabled = false;
    }
});
