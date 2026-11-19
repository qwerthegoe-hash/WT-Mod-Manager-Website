"use strict";
// No private accounts, tokens, secrets or telemetry. GitHub's public API only.
const API="https://api.github.com/repos/qwerthegoe-hash/WT-Mod-Manager-Website/releases?per_page=12";
const PREFIX="https://github.com/qwerthegoe-hash/WT-Mod-Manager-Website/";
const $=(id)=>document.getElementById(id);
function make(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=String(text);if(cls)el.className=cls;return el}
function link(url,text){
  const a=make("a",text);
  if(typeof url==="string"&&url.startsWith(PREFIX+"releases/")){
    a.href=url;a.target="_blank";a.rel="noopener noreferrer";
  }else a.removeAttribute("href");
  return a;
}
function digestText(asset){
  const value=String(asset?.digest||"");
  return /^sha256:[a-f0-9]{64}$/i.test(value)?value.slice(7).toLowerCase():null;
}
function render(releases){
  $("releases").replaceChildren();
  for(const release of releases){
    const card=make("article",undefined,"card");
    card.append(make("h3",release.tag_name),make("span",release.prerelease?"Beta · тестовая версия":"Stable · выпуск","pill"));
    card.append(make("p",release.published_at?new Date(release.published_at).toLocaleDateString("ru-RU"):"Дата не указана","meta"));
    const files=Array.isArray(release.assets)?release.assets:[];
    const installer=files.find(item=>item.name==="WTModManager-Setup.exe");
    const portable=files.find(item=>item.name==="WTModManager.exe");
    const evidence=files.find(item=>item.name==="build-info.json");
    const sums=files.find(item=>item.name==="SHA256SUMS.txt");
    for(const [label,asset] of [["Установщик",installer],["Portable",portable]]){
      card.append(make("p",label+": "+(asset?"Опубликован":"Отсутствует")));
      if(asset){
        const digest=digestText(asset);
        card.append(make("div",digest||"SHA-256 пока не предоставлен GitHub","hash"));
      }
    }
    // Signature status is NOT inferred from a SHA, file extension or release name.
    card.append(make("p",evidence?"Сведения об Authenticode: смотри build-info.json.":"Нет проверяемого описания подписи.","meta"));
    const actions=make("div",undefined,"actions");
    actions.append(link(release.html_url,"Открыть выпуск"));
    if(evidence)actions.append(link(evidence.browser_download_url,"build-info.json"));
    if(sums)actions.append(link(sums.browser_download_url,"SHA256SUMS.txt"));
    card.append(actions);
    $("releases").append(card);
  }
  if(!releases.length)$("releases").append(make("p","Публичных релизов пока нет."));
}
async function refresh(){
  $("refresh").disabled=true;$("status").textContent="Проверяем официальные релизы GitHub…";
  try{
    const response=await fetch(API,{cache:"no-store",headers:{Accept:"application/vnd.github+json"}});
    if(!response.ok)throw Error("GitHub HTTP "+response.status);
    const json=await response.json();
    if(!Array.isArray(json))throw Error("Некорректный ответ GitHub");
    const releases=json.filter(x=>!x.draft&&/^v\d+\.\d+\.\d+(?:-[\w.]+)?$/.test(x.tag_name||"")).slice(0,10);
    render(releases);
    $("status").textContent="Найдено официальных выпусков: "+releases.length;
  }catch(error){
    $("status").textContent="Не удалось загрузить сведения: "+String(error.message||"ошибка");
  }finally{$("refresh").disabled=false}
}
$("refresh").addEventListener("click",()=>void refresh());
void refresh();
