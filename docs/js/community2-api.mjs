// WT Mod Manager Community 2.0 — Supabase client operations.
// Every table has owner-bound RLS. This module does not store user secrets,
// bypass security, or cache personal data across signed-in accounts.
const isUuid = value => typeof value === "string" &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
function result(response) {
  if (response.error) throw response.error;
  return response.data;
}
export function createCommunity2(db,user) {
  if(!db || !isUuid(user?.id)) throw new Error("Community 2.0 requires a verified account");
  const id = user.id;
  const api = {
    userId:id,
    async favorites() {
      return result(await db.from("wtmm_mod_favorites")
        .select("mod_id").eq("user_id",id).limit(1000)) || [];
    },
    async toggleFavorite(modId, favorite) {
      if(!isUuid(modId)) throw new Error("Invalid mod ID");
      if(favorite) {
        result(await db.from("wtmm_mod_favorites").delete()
          .eq("user_id",id).eq("mod_id",modId));
        return false;
      }
      result(await db.from("wtmm_mod_favorites").insert({user_id:id,mod_id:modId}));
      return true;
    },
    async collections() {
      return result(await db.from("wtmm_collections")
        .select("id,name,description,created_at").eq("owner_id",id)
        .order("created_at",{ascending:false}).limit(30)) || [];
    },
    async newCollection(name, description = "") {
      const title=String(name||"").trim();
      if(title.length<2 || title.length>60 || description.length>400)
        throw new Error("Collection name must be 2–60 characters");
      return result(await db.from("wtmm_collections")
        .insert({owner_id:id,name:title,description}).select("id,name").single());
    },
    async deleteCollection(collectionId) {
      if(!isUuid(collectionId)) throw new Error("Invalid collection");
      result(await db.from("wtmm_collections").delete()
        .eq("owner_id",id).eq("id",collectionId));
    },
    async collectionItems(collectionId) {
      if(!isUuid(collectionId)) throw new Error("Invalid collection");
      return result(await db.from("wtmm_collection_items").select("mod_id,created_at")
        .eq("collection_id",collectionId).limit(200)) || [];
    },
    async collectionAdd(collectionId,modId) {
      if(!isUuid(collectionId)||!isUuid(modId)) throw new Error("Invalid mod or collection");
      result(await db.from("wtmm_collection_items")
        .insert({collection_id:collectionId,mod_id:modId}));
    },
    async collectionRemove(collectionId,modId) {
      if(!isUuid(collectionId)||!isUuid(modId)) throw new Error("Invalid mod or collection");
      result(await db.from("wtmm_collection_items").delete()
        .eq("collection_id",collectionId).eq("mod_id",modId));
    },
    async follows() {
      return result(await db.from("wtmm_author_follows")
        .select("author_id").eq("follower_id",id).limit(300)) || [];
    },
    async toggleFollow(authorId,following) {
      if(!isUuid(authorId)||authorId===id) throw new Error("Cannot follow this account");
      if(following) {
        result(await db.from("wtmm_author_follows").delete()
          .eq("follower_id",id).eq("author_id",authorId));
        return false;
      }
      result(await db.from("wtmm_author_follows")
        .insert({follower_id:id,author_id:authorId}));
      return true;
    },
    async notifications() {
      return result(await db.from("wtmm_notifications")
        .select("id,kind,title,body,url,created_at,read_at")
        .eq("user_id",id).order("created_at",{ascending:false}).limit(50)) || [];
    },
    async markRead(notificationId) {
      if(!isUuid(notificationId)) throw new Error("Invalid notification");
      result(await db.from("wtmm_notifications")
        .update({read_at:new Date().toISOString()})
        .eq("user_id",id).eq("id",notificationId));
    },
    async tickets() {
      return result(await db.from("wtmm_support_tickets")
        .select("id,kind,title,message,status,created_at,updated_at")
        .eq("user_id",id).order("created_at",{ascending:false}).limit(50)) || [];
    },
    async dashboardStats() {
      const [modCount,favorites,follows,collections,notifications] = await Promise.all([
        db.from("wtmm_mods").select("id",{head:true,count:"exact"})
          .eq("owner_id",id).eq("status","approved"),
        api.favorites(),api.follows(),api.collections(),api.notifications()
      ]);
      if(modCount.error) throw modCount.error;
      return {publishedMods:modCount.count||0,favorites:favorites.length,
        following:follows.length,collections:collections.length,
        unread:notifications.filter(n=>!n.read_at).length};
    }
  };
  return api;
}
export function safeCommunityLink(path) {
  if(typeof path!=="string" || path.length>300) return null;
  // Database-generated relative links only; never open untrusted external URL.
  if(!/^\.\.\/(?:mods\/mods\.html|profile\/profile\.html)(?:\?[a-zA-Z0-9=&-]{0,100}|#[a-zA-Z0-9-]{1,50})?$/.test(path))
    return null;
  return path;
}
