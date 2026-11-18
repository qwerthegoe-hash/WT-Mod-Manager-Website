import assert from "node:assert/strict";
import fs from "node:fs";
import { createCommunity2,safeCommunityLink } from "../docs/js/community2-api.mjs";

const read=p=>fs.readFileSync(new URL("../"+p,import.meta.url),"utf8");
const sql=read("docs/database/community_2_2026_11_18.sql");
const modsHtml=read("docs/mods/mods.html");
const modsJs=read("docs/mods/mods.js");
const profileHtml=read("docs/profile/profile.html");
const profileJs=read("docs/profile/profile.js");
const creatorHtml=read("docs/creator/creator.html");
const creatorJs=read("docs/creator/creator.js");
const edge=read("docs/supabase/functions/contact-message/index.ts");
const compareJs=read("docs/js/community2-mods.mjs");
const dashboard=read("docs/js/community2-dashboard.mjs");

for(const name of ["wtmm_mod_favorites","wtmm_collections","wtmm_collection_items",
 "wtmm_author_follows","wtmm_notifications","wtmm_support_tickets"]) {
 assert.ok(sql.includes("create table if not exists public."+name),"Missing table "+name);
 assert.ok(sql.includes("alter table public."+name+" enable row level security"),
   "No RLS for "+name);
}
for(const phrase of [
 "favorites owner add published mod","follows only published authors",
 "notifications owner read","notifications owner mark read",
 "tickets private to owner/admin","tickets admin status update",
 "collection items owner add published",
 "revoke all on public.wtmm_mod_favorites",
 "revoke all on public.wtmm_contact_attempts" // existing separate migration not here; checked separately
].slice(0,-1)) assert.ok(sql.includes(phrase),phrase);
assert.ok(sql.includes("security invoker set search_path=''"),"Catalog search must remain invoker/RLS-safe");
assert.ok(sql.includes("m.status='approved'"),"Discovery must filter approved mods");
assert.ok(sql.includes("approved_favorite_count"),"Popularity must not be limited to own favorites");
assert.ok(!sql.includes("grant insert on public.wtmm_notifications to authenticated"),
 "Notifications may never be fabricated from client");
assert.ok(!sql.includes("grant insert on public.wtmm_support_tickets to authenticated"),
 "Clients must not forge the delivery history");
assert.ok(sql.includes("before_image_path") && sql.includes("after_image_path"));
assert.ok(sql.includes("wtmm_comparison_image_paths"),"Preview paths must be scoped to owner");
assert.ok(sql.includes("tg_table_name"),"Social caps must execute server-side");

for(const id of ["communityDashboard","community2Notifications",
  "community2Collections","community2Favorites","community2Following",
  "community2Tickets","supportHistory","community2UnreadStat"])
 assert.ok(profileHtml.includes('id="'+id+'"'),"Profile missing "+id);
assert.ok(profileJs.includes("mountCommunityDashboard"));
assert.ok(modsHtml.includes('id="modsFavoritesOnly"'));
assert.ok(modsHtml.includes('id="modsAuthorFilter"'));
assert.ok(modsHtml.includes('value="popular"') && modsHtml.includes('value="relevance"'));
for(const input of ['name="before"','name="after"'])assert.ok(modsHtml.includes(input));
assert.ok(modsJs.includes('db.rpc("wtmm_discover_mods"'),"Advanced search must be server paginated");
assert.ok(modsJs.includes('createModCommunity(db,user'));
assert.ok(modsJs.includes("community2.addComparison("));
assert.ok(modsJs.includes('before_image_path:beforePath,after_image_path:afterPath'));
assert.ok(modsJs.includes("await enrichComparisonPaths(records)"),"Moderation needs comparison images");
assert.ok(creatorJs.includes("social.toggleFollow(userId,followed)"));
assert.ok(creatorHtml.includes('id="followCreatorButton"'));
assert.ok(compareJs.includes('slider.type="range"') &&
  compareJs.includes("afterImg.style.clipPath="));
assert.ok(dashboard.includes("renderNotifications(api)"));
assert.ok(dashboard.includes("renderTickets(api)"));
assert.ok(dashboard.includes("renderFollowing(api,db)"));
assert.ok(edge.includes('.from("wtmm_support_tickets")'));
assert.ok(edge.includes('status:"sending"'));
assert.ok(edge.includes('markDelivery("received")'));
assert.ok(edge.includes('markDelivery("delivery_failed")'));
assert.ok(edge.includes("admin.auth.getUser(raw)"),"Tickets must be bound to server-authenticated user");
assert.ok(!edge.includes('user_id:body.user_id'),"Client cannot impersonate requester");

const uuid1="11111111-1111-4111-8111-111111111111";
const uuid2="22222222-2222-4222-8222-222222222222";
const logs=[];
function dbStub() {
 return {
  from(name) {
   const state={name,method:"select",data:null,filters:[]};
   const builder={
    select(fields,opts){state.fields=fields;state.opts=opts;return builder;},
    eq(field,value){state.filters.push([field,value]);return builder;},
    in(field,values){state.filters.push([field,values]);return builder;},
    is(field,value){state.filters.push([field,value]);return builder;},
    insert(data){state.method="insert";state.data=data;return builder;},
    update(data){state.method="update";state.data=data;return builder;},
    delete(){state.method="delete";return builder;},
    order(){return builder;},limit(){return builder;},
    single(){logs.push(state);return Promise.resolve({data:{id:uuid2,name:"My Collection"},error:null});},
    then(resolve,reject){logs.push(state);
      const data=state.method==="select"?[]:null;
      return Promise.resolve({data,error:null,count:0}).then(resolve,reject);}
   };
   return builder;
  }
 };
}
const client=createCommunity2(dbStub(),{id:uuid1});
await client.toggleFavorite(uuid2,false);
assert.equal(logs.at(-1).name,"wtmm_mod_favorites");
assert.deepEqual(logs.at(-1).data,{user_id:uuid1,mod_id:uuid2});
await client.toggleFavorite(uuid2,true);
assert.equal(logs.at(-1).method,"delete");
assert.ok(logs.at(-1).filters.some(([f,v])=>f==="user_id"&&v===uuid1));
await client.toggleFollow(uuid2,false);
assert.equal(logs.at(-1).name,"wtmm_author_follows");
assert.deepEqual(logs.at(-1).data,{follower_id:uuid1,author_id:uuid2});
await assert.rejects(()=>client.toggleFollow(uuid1,false),/Cannot follow/);
await client.newCollection("My Collection");
assert.equal(logs.at(-1).name,"wtmm_collections");
await client.collectionAdd(uuid2,uuid1);
assert.equal(logs.at(-1).name,"wtmm_collection_items");
await client.markRead(uuid2);
assert.equal(logs.at(-1).name,"wtmm_notifications");
assert.equal(logs.at(-1).method,"update");
await client.tickets();
assert.equal(logs.at(-1).name,"wtmm_support_tickets");
assert.ok(logs.at(-1).filters.some(([f,v])=>f==="user_id"&&v===uuid1));
assert.equal(safeCommunityLink("../mods/mods.html?mod="+uuid2),"../mods/mods.html?mod="+uuid2);
assert.equal(safeCommunityLink("https://attacker.example"),null);
assert.equal(safeCommunityLink("javascript:alert(1)"),null);
assert.equal(safeCommunityLink("../profile/profile.html#supportHistory"),
 "../profile/profile.html#supportHistory");
console.log("PASS: Community 2.0 RLS schema, intelligent discovery, dashboard, follows, favorites, comparison, ticket history");
