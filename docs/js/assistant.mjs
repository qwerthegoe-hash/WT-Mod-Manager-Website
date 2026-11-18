"use strict";
import {createClient} from "https://esm.sh/@supabase/supabase-js@2.119.0";
import {COMMUNITY_CONFIG as config} from "./community-config.js";
import {ensureAuthenticatedUser} from "./supabase-session.mjs";
const db=createClient(config.supabaseUrl,config.supabasePublishableKey);
const state=document.getElementById("state");
const log=document.getElementById("conversation");
const ask=document.getElementById("question");
const send=document.getElementById("send");
let enabled=false,busy=false;
function add(role,text){
  const p=document.createElement("p");
  const title=document.createElement("strong");title.textContent=role+": ";
  p.append(title,document.createTextNode(String(text)));
  log.append(p);log.scrollTop=log.scrollHeight;
}
async function invoke(action,body={}){
  const {data,error}=await db.functions.invoke("wtmm-desktop-bridge",{body:{action,...body}});
  if(error){
    let reason=error.message||"Сервер недоступен";
    if(error.context && typeof error.context.json==="function"){
      try{const detail=await error.context.json();if(detail?.error)reason=String(detail.error);}
      catch{ /* response may have no JSON */ }
    }
    throw new Error(reason);
  }
  if(data?.error)throw new Error(String(data.error));
  return data;
}
async function init(){
  try{
    const user=await ensureAuthenticatedUser(db);
    if(user.is_anonymous){
      state.textContent="Для GPT-помощника нужен зарегистрированный аккаунт. Войди на сайте через профиль.";
      return;
    }
    const info=await invoke("assistant_status");
    if(!info?.enabled){
      state.textContent="GPT ещё не подключён владельцем сайта: нужен серверный OPENAI_API_KEY.";
      return;
    }
    enabled=true;send.disabled=false;
    state.textContent="GPT подключён. Лимит: до 12 вопросов в час на аккаунт.";
  }catch(err){state.textContent="GPT недоступен: "+err.message;}
}
send.addEventListener("click",async()=>{
  if(!enabled||busy)return;
  const message=ask.value.trim();
  if(message.length<3||message.length>1200){
    state.textContent="Напиши вопрос от 3 до 1200 символов.";return;
  }
  busy=true;send.disabled=true;ask.value="";
  add("Ты",message);
  try{
    const data=await invoke("assistant",{message});
    add("GPT",data.answer||"Ответ не получен.");
    state.textContent="Готово. Помощник не менял файлы.";
  }catch(error){
    add("Ошибка",error.message);
    state.textContent="Попробуй позже или воспользуйся кодовой диагностикой в приложении.";
  }finally{busy=false;send.disabled=!enabled;}
});
void init();
