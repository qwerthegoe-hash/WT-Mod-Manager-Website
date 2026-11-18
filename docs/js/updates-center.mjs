"use strict";
// No administrator credentials, tokens or private file URLs in this page.
import {createClient} from "https://esm.sh/@supabase/supabase-js@2.119.0";
import {COMMUNITY_CONFIG as config} from "./community-config.js";
import {ensureAuthenticatedUser} from "./supabase-session.mjs";
const db=createClient(config.supabaseUrl,config.supabasePublishableKey);
const $=id=>document.getElementById(id);
let account=null, active=true;
const github="https://api.github.com/repos/qwerthegoe-hash/WT-Mod-Manager-Website/releases?per_page=12";
function el(tag,cls,text){
  const n=document.createElement(tag);if(cls)n.className=cls;
  if(text)n.textContent=String(text);return n;
}
function safeLink(url, text){
  const link=el("a","action",text);
  if(typeof url!=="string" || !url.startsWith("https://github.com/qwerthegoe-hash/WT-Mod-Manager-Website/releases/")){
    link.removeAttribute("href");
    return link;
  }
  link.href=url;link.target="_blank";link.rel="noopener noreferrer";return link;
}
async function loadReleases(){
  $("releaseStatus").textContent="Проверяем GitHub Releases...";
  try{
    const response=await fetch(github,{cache:"no-store",headers:{"Accept":"application/vnd.github+json"}});
    if(!response.ok)throw Error("GitHub HTTP "+response.status);
    const data=await response.json();
    if(!Array.isArray(data))throw Error("Некорректный ответ сервера");
    const list=data.filter(x=>!x.draft&&x.tag_name).slice(0,10);
    const host=$("releases");host.replaceChildren();
    if(!list.length){host.textContent="Выпуски пока отсутствуют.";}
    for(const release of list){
      const item=el("article","item"),head=el("h3","",release.name||release.tag_name);
      const meta=el("p","",new Date(release.published_at||release.created_at).toLocaleDateString("ru-RU"));
      const status=el("span","pill",release.prerelease?"Beta / тестирование":"Stable");
      const info=el("p","",(release.body||"Без описания изменений.").slice(0,550));
      const action=safeLink(release.html_url,"Посмотреть версию и скачать");
      item.append(head,status,meta,info,action);host.append(item);
    }
    $("releaseStatus").textContent="Выпусков найдено: "+list.length;
  }catch(error){$("releaseStatus").textContent="Не удалось загрузить релизы: "+error.message;}
}
async function loadNotifications(){
  if(!account)return;
  const {data,error}=await db.from("wtmm_notifications")
    .select("id,kind,title,body,url,created_at,read_at")
    .eq("user_id",account.id).order("created_at",{ascending:false}).limit(70);
  if(error){$("notificationStatus").textContent="Ошибка: "+error.message;return;}
  const host=$("notifications");host.replaceChildren();
  const valid=data||[];$("notificationStatus").textContent="Уведомлений: "+valid.length;
  if(!valid.length){host.append(el("p","muted","Пока нет уведомлений этого аккаунта."));return;}
  for(const notice of valid){
    const card=el("article","item"),title=el("h3","",notice.title||"Уведомление");
    if(!notice.read_at)title.prepend(el("span","pill","Новое "));
    card.append(title,el("p","",notice.body||""),el("small","",new Date(notice.created_at).toLocaleString("ru-RU")));
    const target=String(notice.url||"");
    if(/^(?:\.\.\/)?mods\/mods\.html\?mod=[a-f0-9-]{36}$/i.test(target)){
      const id=target.split("mod=")[1];
      const link=el("a","action","Открыть мод");
      link.href="mods/mods.html?mod="+encodeURIComponent(id);card.append(link);
    }
    host.append(card);
  }
}
async function init(){
  await loadReleases();
  try{account=await ensureAuthenticatedUser(db);await loadNotifications();}
  catch(error){$("notificationStatus").textContent="Невозможно проверить аккаунт: "+error.message;}
}
$("refreshReleases").addEventListener("click",loadReleases);
$("markRead").addEventListener("click",async()=>{
  if(!account)return;
  $("markRead").disabled=true;
  try{
    const {error}=await db.from("wtmm_notifications")
      .update({read_at:new Date().toISOString()})
      .eq("user_id",account.id).is("read_at",null);
    if(error)throw error;
    await loadNotifications();
  }catch(error){$("notificationStatus").textContent="Не удалось отметить уведомления: "+error.message;}
  finally{$("markRead").disabled=false;}
});
document.addEventListener("visibilitychange",()=>{
  if(document.visibilityState==="visible"&&account)void loadNotifications();
});
setInterval(()=>{if(document.visibilityState==="visible"&&account)void loadNotifications();},30000);
void init();
