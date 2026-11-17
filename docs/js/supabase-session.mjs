// WT Mod Manager: unified session bootstrap for Community, Mods and Profiles.
// Sessions are always revalidated by the Supabase Auth service.
// Anonymous sign-in remains supported for public community access.
const inflightSessions = new WeakMap();

export async function ensureAuthenticatedUser(client) {
  if (!client?.auth) throw new TypeError("Supabase authentication client missing");
  const existing = inflightSessions.get(client);
  if (existing) return existing;
  const promise = (async () => {
    const { data: sessionData, error: sessionError } = await client.auth.getSession();
    if (sessionError) throw sessionError;
    if (!sessionData?.session) {
      const result = await client.auth.signInAnonymously();
      if (result.error) throw result.error;
    }
    // Do not trust user data from local storage or an unverified session object.
    const { data, error } = await client.auth.getUser();
    if (error || !data?.user?.id) {
      throw error || new Error("Не удалось подтвердить учётную запись.");
    }
    return data.user;
  })();
  inflightSessions.set(client, promise);
  try {
    return await promise;
  } finally {
    inflightSessions.delete(client);
  }
}
