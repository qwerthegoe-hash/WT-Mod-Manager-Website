// WTMM optional TOTP 2FA UI. All challenge/verify/enroll calls go to Supabase Auth.
// Never persists TOTP secrets/codes in browser storage or sends them to diagnostics.
export function setupProfileMfa(auth, root = document) {
  const $ = id => root.getElementById(id);
  const els = {
    begin: $("mfaBegin"), cancel: $("mfaCancel"), setup: $("mfaSetup"),
    qr: $("mfaQr"), secret: $("mfaSecret"), setupCode: $("mfaSetupCode"),
    confirm: $("mfaConfirm"), challenge: $("mfaChallenge"),
    loginCode: $("mfaLoginCode"), verify: $("mfaVerify"),
    remove: $("mfaRemove"), status: $("mfaStatus"), note: $("mfaNotice"),
  };
  if (Object.values(els).some(x => !x)) throw new Error("Missing MFA profile controls");
  let pendingFactorId = null;
  let verifiedFactorId = null;
  let busy = false;

  function say(message, error = false) {
    els.note.textContent = message;
    els.note.classList.toggle("error", error);
  }
  function forgetEnrollment() {
    pendingFactorId = null;
    els.setupCode.value = "";
    els.qr.removeAttribute("src");
    els.secret.textContent = "";
    els.setup.hidden = true;
  }
  async function check(result) {
    if (result.error) throw result.error;
    return result.data;
  }
  async function verifyFactor(factorId, code) {
    if (!/^\d{6}$/.test(code)) throw new Error("Введи 6 цифр из приложения-аутентификатора.");
    const challenge = await check(await auth.mfa.challenge({ factorId }));
    await check(await auth.mfa.verify({ factorId, challengeId: challenge.id, code }));
  }
  async function run(action) {
    if (busy) return;
    busy = true;
    for (const id of ["begin", "cancel", "confirm", "verify", "remove"]) els[id].disabled = true;
    try { await action(); }
    catch (error) { say("Не удалось выполнить действие: " + (error?.message || "ошибка сети"), true); }
    finally {
      busy = false;
      for (const id of ["begin", "cancel", "confirm", "verify", "remove"]) els[id].disabled = false;
    }
  }
  async function refresh() {
    const [factorData, assurance] = await Promise.all([
      check(await auth.mfa.listFactors()),
      check(await auth.mfa.getAuthenticatorAssuranceLevel()),
    ]);
    const verified = (factorData?.totp || []).find(x => x.status === "verified");
    verifiedFactorId = verified?.id || null;
    const requiresCode = Boolean(verifiedFactorId) &&
      assurance?.currentLevel !== "aal2" && assurance?.nextLevel === "aal2";
    els.begin.hidden = Boolean(verifiedFactorId);
    els.remove.hidden = !verifiedFactorId || requiresCode;
    els.challenge.hidden = !requiresCode;
    els.status.textContent = verifiedFactorId
      ? requiresCode
        ? "Для входа с двухфакторной защитой подтверди код из приложения."
        : "Двухфакторная защита подключена."
      : "Двухфакторная защита ещё не подключена.";
    return { requiresCode, enrolled: Boolean(verifiedFactorId) };
  }

  els.begin.addEventListener("click", () => run(async () => {
    const identity = await check(await auth.getUser());
    if (!identity?.user?.email || identity.user.is_anonymous) {
      throw new Error("Сначала привяжи и подтверди email.");
    }
    const data = await check(await auth.mfa.enroll({
      factorType: "totp", friendlyName: "WT Mod Manager"
    }));
    pendingFactorId = data.id;
    const source = String(data.totp?.qr_code || "");
    // The QR is an image returned by the trusted Supabase Auth endpoint, not arbitrary HTML.
    if (!/^data:image\/svg\+xml(?:;|,)/i.test(source) || source.length > 50000)
      throw new Error("Сервер вернул неожиданный формат QR-кода.");
    els.qr.src = source;
    els.secret.textContent = String(data.totp?.secret || "");
    els.setup.hidden = false;
    say("Добавь код в приложение-аутентификатор и введи 6 цифр.");
  }));

  els.cancel.addEventListener("click", () => run(async () => {
    const id = pendingFactorId;
    if (id) {
      await check(await auth.mfa.unenroll({ factorId: id }));
    }
    forgetEnrollment();
    say("Подключение отменено.");
  }));

  els.confirm.addEventListener("click", () => run(async () => {
    if (!pendingFactorId) throw new Error("Сначала начни подключение.");
    await verifyFactor(pendingFactorId, els.setupCode.value.trim());
    forgetEnrollment();
    await refresh();
    say("Двухфакторная защита активирована. Сохрани доступ к своему приложению-аутентификатору.");
  }));

  els.verify.addEventListener("click", () => run(async () => {
    if (!verifiedFactorId) throw new Error("Нет подключённого фактора.");
    await verifyFactor(verifiedFactorId, els.loginCode.value.trim());
    els.loginCode.value = "";
    await refresh();
    say("Код подтверждён. Вход защищён.");
  }));

  els.remove.addEventListener("click", () => run(async () => {
    if (!verifiedFactorId) return;
    // Explicit confirmation prevents accidental removal of account protection.
    if (!window.confirm("Отключить двухфакторную защиту этого аккаунта?")) return;
    await check(await auth.mfa.unenroll({ factorId: verifiedFactorId }));
    verifiedFactorId = null;
    await refresh();
    say("Двухфакторная защита отключена.");
  }));

  window.addEventListener("pagehide", () => {
    // Sensitive material should not remain in page elements after navigation.
    forgetEnrollment();
    els.loginCode.value = "";
  });
  return { refresh };
}
