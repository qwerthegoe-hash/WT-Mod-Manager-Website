// Community 2.0 controls shared by catalog cards and the detail viewer.
import { createCommunity2 } from "./community2-api.mjs";
import { uiText } from "./site-language.mjs";

const element=(tag,cls,text)=>{
  const node=document.createElement(tag);
  if(cls)node.className=cls;
  if(text)node.textContent=uiText(text);
  return node;
};
function button(text,cls="community2-small") {
  const node=element("button",cls,text);
  node.type="button";
  return node;
}
export async function createModCommunity(db,user,notify) {
  const api=createCommunity2(db,user);
  const stored=await api.favorites();
  const favorites=new Set(stored.map(x=>x.mod_id));
  const report=typeof notify==="function"?notify:()=>{};
  async function toggle(row,control){
    control.disabled=true;
    try {
      const wasFavorite=favorites.has(row.id);
      const now=await api.toggleFavorite(row.id,wasFavorite);
      if(now)favorites.add(row.id);else favorites.delete(row.id);
      row.is_favorite=now;
      if(Number.isFinite(Number(row.favorites_count)))
        row.favorites_count=Math.max(0,Number(row.favorites_count)+(now?1:-1));
      updateHeart(control,row);
      report(now?"Мод добавлен в избранное.":"Мод удалён из избранного.");
    }catch(e){report("Не удалось изменить избранное: "+e.message,true);}
    finally{control.disabled=false;}
  }
  function updateHeart(control,row) {
    const saved=favorites.has(row.id);
    control.setAttribute("aria-pressed",String(saved));
    control.textContent=uiText(saved?"♥ В избранном":"♡ В избранное")+
      (Number.isFinite(Number(row.favorites_count))?" · "+Number(row.favorites_count):"");
    control.setAttribute("aria-label",uiText(saved?"Убрать из избранного":"Добавить в избранное"));
  }
  function addFavoriteButton(row,container){
    if(row.status!=="approved")return null;
    const heart=button("♡ В избранное","community2-small community2-heart");
    updateHeart(heart,row);
    heart.addEventListener("click",()=>void toggle(row,heart));
    container.append(heart);
    return heart;
  }
  async function addCollectionPicker(row,container) {
    if(row.status!=="approved")return;
    const area=element("div","community2-collection-picker");
    const title=element("label","", "Добавить мод в коллекцию");
    const select=element("select","community2-select");
    select.setAttribute("aria-label",uiText("Выбери коллекцию"));
    const line=element("div","community2-actions");
    const add=button("Добавить в коллекцию");
    const create=button("Новая коллекция");
    const feedback=element("p","community2-muted");
    async function load(){
      select.replaceChildren();
      const collections=await api.collections();
      for(const collection of collections){
        const option=element("option","",collection.name);
        option.value=collection.id;
        select.append(option);
      }
      add.disabled=!collections.length;
      if(!collections.length)feedback.textContent=uiText("Сначала создай коллекцию.");
    }
    add.addEventListener("click",async()=>{
      if(!select.value)return;
      add.disabled=true;
      try{
        await api.collectionAdd(select.value,row.id);
        feedback.textContent=uiText("Мод добавлен в коллекцию.");
      }catch(e){
        feedback.textContent=uiText("Не удалось добавить мод: ")+e.message;
      }finally{add.disabled=false;}
    });
    create.addEventListener("click",async()=>{
      const name=window.prompt(uiText("Название новой коллекции (2–60 символов):"));
      if(name===null)return;
      create.disabled=true;
      try{
        const newCollection=await api.newCollection(name.trim());
        await load();select.value=newCollection.id;
        feedback.textContent=uiText("Коллекция создана.");
      }catch(e){feedback.textContent=uiText("Не удалось создать коллекцию: ")+e.message;}
      finally{create.disabled=false;}
    });
    line.append(select,add,create);
    area.append(title,line,feedback);
    container.append(area);
    try{await load();}catch(e){feedback.textContent=uiText("Коллекции недоступны: ")+e.message;}
  }
  async function addComparison(row,content,signImage){
    if(row.status!=="approved"||!row.before_image_path||!row.after_image_path)return;
    const [before,after]=await Promise.all([
      signImage({cover_path:row.before_image_path}),
      signImage({cover_path:row.after_image_path})
    ]);
    if(!before||!after)return;
    const section=element("section","community2-comparison");
    section.setAttribute("aria-label",uiText("Интерактивное сравнение мода"));
    section.append(element("h3","","Сравнение «До / После»"));
    const frame=element("div","community2-compare-frame");
    const beforeImg=element("img","before");
    beforeImg.src=before;beforeImg.alt=uiText("До установки мода");
    const afterImg=element("img","after");
    afterImg.src=after;afterImg.alt=uiText("После установки мода");
    const divider=element("div","divider");divider.setAttribute("aria-hidden","true");
    frame.append(beforeImg,afterImg,divider);
    const slider=element("input");
    slider.type="range";slider.min="0";slider.max="100";slider.value="50";
    slider.setAttribute("aria-label",uiText("Положение границы сравнения"));
    const labels=element("div","community2-comparison-labels");
    labels.append(element("span","","До"),element("span","","После"));
    slider.addEventListener("input",()=>{
      const value=Math.max(0,Math.min(100,Number(slider.value)||0));
      afterImg.style.clipPath="inset(0 "+(100-value)+"% 0 0)";
      divider.style.left=value+"%";
    });
    section.append(frame,slider,labels);
    content.append(section);
  }
  return {api,favorites,addFavoriteButton,addCollectionPicker,addComparison};
}
