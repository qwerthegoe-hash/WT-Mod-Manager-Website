import { createCommunity2,safeCommunityLink } from "./community2-api.mjs";
import { uiText,siteLocale } from "./site-language.mjs";

const $ = id => document.getElementById(id);
const el = (tag, text="", cls="") => {
  const item=document.createElement(tag);
  if(cls)item.className=cls;
  if(text)item.textContent=uiText(text);
  return item;
};
function when(value) {
  const d=new Date(value);
  return Number.isFinite(d.getTime()) ? d.toLocaleString(siteLocale()) : "";
}
function status(target,text,error=false) {
  if(!target)return;
  target.textContent=uiText(text);
  target.classList.toggle("error",error);
}
function linkToMod(row) {
  const a=el("a",row.title,"community2-item-link");
  a.href="../mods/mods.html?mod="+encodeURIComponent(row.id);
  return a;
}
async function renderFavoriteLibrary(api,db) {
  const container=$("community2Favorites");
  const favorites=await api.favorites();
  if(!favorites.length) {
    container.replaceChildren(el("p","Здесь пока нет избранных модов.","community2-muted"));
    return;
  }
  const {data,error}=await db.from("wtmm_mods")
    .select("id,title,category,owner_id")
    .in("id",favorites.map(f=>f.mod_id)).eq("status","approved").limit(100);
  if(error)throw error;
  const list=el("div","","community2-list");
  for(const mod of data||[]) {
    const row=el("div","","community2-list-item");
    row.append(linkToMod(mod));
    const remove=el("button","Убрать из избранного","community2-small");
    remove.type="button";
    remove.addEventListener("click",async()=>{
      remove.disabled=true;
      try {await api.toggleFavorite(mod.id,true);await renderFavoriteLibrary(api,db);}
      catch(e){status($("community2Notice"),"Не удалось изменить избранное: "+e.message,true);}
      finally {remove.disabled=false;}
    });
    row.append(remove);list.append(row);
  }
  container.replaceChildren(list);
}
async function renderCollections(api,db) {
  const root=$("community2Collections");
  const collections=await api.collections();
  const fragment=document.createDocumentFragment();
  if(!collections.length) fragment.append(el("p","Создай свою первую коллекцию модов.","community2-muted"));
  for(const collection of collections) {
    const article=el("article","","community2-collection");
    const title=el("h3",collection.name);
    const actions=el("div","","community2-actions");
    const view=el("button","Открыть коллекцию","community2-small");
    const remove=el("button","Удалить коллекцию","community2-small");
    remove.type=view.type="button";
    const items=el("div","","community2-list");
    items.hidden=true;
    view.addEventListener("click",async()=>{
      if(!items.hidden){items.hidden=true;return;}
      view.disabled=true;
      try {
        const entries=await api.collectionItems(collection.id);
        items.replaceChildren();
        if(entries.length){
          const {data,error}=await db.from("wtmm_mods")
            .select("id,title").in("id",entries.map(x=>x.mod_id))
            .eq("status","approved").limit(200);
          if(error)throw error;
          for(const mod of data||[]) {
            const row=el("div","","community2-list-item");
            const del=el("button","Убрать","community2-small");
            del.type="button";
            del.addEventListener("click",async()=>{
              del.disabled=true;
              try {await api.collectionRemove(collection.id,mod.id);row.remove();}
              catch(e){status($("community2Notice"),"Не удалось убрать мод: "+e.message,true);del.disabled=false;}
            });
            row.append(linkToMod(mod),del);items.append(row);
          }
        }else items.append(el("p","В этой коллекции пока нет модов.","community2-muted"));
        items.hidden=false;
      } catch(e){status($("community2Notice"),"Ошибка коллекции: "+e.message,true);}
      finally{view.disabled=false;}
    });
    remove.addEventListener("click",async()=>{
      if(!window.confirm("Удалить коллекцию «"+collection.name+"»? Избранные моды останутся."))return;
      remove.disabled=true;
      try{await api.deleteCollection(collection.id);await renderCollections(api,db);await renderStats(api);}
      catch(e){status($("community2Notice"),"Не удалось удалить коллекцию: "+e.message,true);}
      finally{remove.disabled=false;}
    });
    actions.append(view,remove);
    article.append(title,actions,items);
    fragment.append(article);
  }
  root.replaceChildren(fragment);
}
async function renderFollowing(api,db) {
  const root=$("community2Following");
  const follows=await api.follows();
  if(!follows.length) {
    root.replaceChildren(el("p","Ты пока ни на кого не подписан.","community2-muted"));
    return;
  }
  const {data,error}=await db.from("community_user_profiles")
    .select("user_id,nickname,is_public").in("user_id",follows.map(f=>f.author_id))
    .eq("is_public",true).limit(300);
  if(error)throw error;
  const block=el("div","","community2-list");
  for(const author of data||[]) {
    const item=el("div","","community2-list-item");
    const a=el("a",author.nickname,"community2-item-link");
    a.href="../creator/creator.html?id="+encodeURIComponent(author.user_id);
    const unfollow=el("button","Отписаться","community2-small");
    unfollow.type="button";
    unfollow.addEventListener("click",async()=>{
      unfollow.disabled=true;
      try {
        await api.toggleFollow(author.user_id,true);
        await Promise.all([renderFollowing(api,db),renderStats(api)]);
      }catch(e){status($("community2Notice"),"Не удалось отписаться: "+e.message,true);unfollow.disabled=false;}
    });
    item.append(a,unfollow);block.append(item);
  }
  root.replaceChildren(block);
}
async function renderNotifications(api) {
  const root=$("community2Notifications");
  const notifications=await api.notifications();
  if(!notifications.length){
    root.replaceChildren(el("p","Пока нет уведомлений.","community2-muted"));
    return;
  }
  const fragment=document.createDocumentFragment();
  for(const n of notifications) {
    const article=el("article","","community2-notification"+(n.read_at?"":" unread"));
    const heading=el("div","","community2-list-item");
    heading.append(el("strong",n.title),el("time",when(n.created_at),"community2-date"));
    article.append(heading);
    if(n.body)article.append(el("p",n.body,"community2-muted"));
    const bottom=el("div","","community2-actions");
    const target=safeCommunityLink(n.url);
    if(target){
      const a=el("a","Подробнее","community2-small");
      a.href=target;bottom.append(a);
    }
    if(!n.read_at) {
      const mark=el("button","Прочитано","community2-small");
      mark.type="button";
      mark.addEventListener("click",async()=>{
        mark.disabled=true;
        try{await api.markRead(n.id);await renderNotifications(api);await renderStats(api);}
        catch(e){status($("community2Notice"),"Не удалось обновить уведомление: "+e.message,true);}
        finally{mark.disabled=false;}
      });
      bottom.append(mark);
    }
    article.append(bottom);fragment.append(article);
  }
  root.replaceChildren(fragment);
}
async function renderTickets(api) {
  const root=$("community2Tickets");
  const tickets=await api.tickets();
  if(!tickets.length){
    root.replaceChildren(el("p","Ты ещё не отправлял обращений.","community2-muted"));
    return;
  }
  const fragment=document.createDocumentFragment();
  const labels={
    sending:"Отправляется",received:"Получено",delivery_failed:"Ошибка доставки",
    in_review:"Рассматривается",resolved:"Решено",closed:"Закрыто"
  };
  for(const ticket of tickets){
    const details=el("details","","community2-ticket");
    const head=el("summary","","community2-list-item");
    const name=el("strong",ticket.title);
    const meta=el("span",(labels[ticket.status]||ticket.status)+" · "+when(ticket.created_at),"community2-date");
    head.append(name,meta);
    details.append(head,el("p",ticket.message,"community2-ticket-body"));
    fragment.append(details);
  }
  root.replaceChildren(fragment);
}
async function renderStats(api) {
  const stats=await api.dashboardStats();
  for(const [key,val] of Object.entries({
    community2ModStat:stats.publishedMods,community2FavStat:stats.favorites,
    community2FollowStat:stats.following,community2CollectionStat:stats.collections,
    community2UnreadStat:stats.unread
  })) if($(key))$(key).textContent=String(val);
  const badge=$("community2NotifyBadge");
  if(badge){badge.textContent=String(stats.unread);badge.hidden=!stats.unread;}
}
export async function mountCommunityDashboard(db,user) {
  const panel=$("communityDashboard");
  if(!panel)return;
  const api=createCommunity2(db,user);
  const newButton=$("community2NewCollection");
  newButton.addEventListener("click",async()=>{
    const name=window.prompt("Название новой коллекции (2–60 символов):");
    if(name===null)return;
    const chosen=name.trim();
    if(chosen.length<2||chosen.length>60){
      status($("community2Notice"),"Название должно содержать от 2 до 60 символов.",true);
      return;
    }
    newButton.disabled=true;
    try {
      await api.newCollection(chosen);
      await Promise.all([renderCollections(api,db),renderStats(api)]);
      status($("community2Notice"),"Коллекция создана.");
    }catch(e){status($("community2Notice"),"Не удалось создать коллекцию: "+e.message,true);}
    finally{newButton.disabled=false;}
  });
  $("community2Refresh").addEventListener("click",()=>void refresh());
  async function refresh(){
    try{
      status($("community2Notice"),"Обновляю личный кабинет...");
      await Promise.all([
        renderStats(api),renderFavoriteLibrary(api,db),renderCollections(api,db),
        renderFollowing(api,db),renderNotifications(api),renderTickets(api)
      ]);
      status($("community2Notice"),"");
    }catch(e){status($("community2Notice"),"Не удалось загрузить личный кабинет: "+e.message,true);}
  }
  panel.hidden=false;
  await refresh();
}
