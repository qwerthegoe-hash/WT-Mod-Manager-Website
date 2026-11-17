"use strict";
import { normalizeContactTopic, validateContact } from "./contact-core.mjs";
import { getContactBridge } from "../js/contact-bridge.mjs";
import { contactLocalesExtra } from "./contact-extra-i18n.mjs";

const copy = {
  ru: {
    skip:"Перейти к форме", navHome:"Главная", navCommunity:"Сообщество", navSupport:"Центр поддержки",
    languageLabel:"Язык", eyebrow:"СВЯЗЬ С КОМАНДОЙ",
    heading:"Связаться с <em>разработчиком</em>",
    intro:"Есть вопрос по WT Mod Manager, идея для сотрудничества или предложение? Напиши напрямую через отдельную форму. Мы получим сообщение в нашем канале обращений.",
    sidebarLabel:"ЦЕНТР КОНТАКТОВ",sidebarTitle:"Выбери тему",sidebarDesc:"Так мы сможем быстрее понять, зачем ты пишешь.",
    topicQuestion:"Общий вопрос",topicQuestionDesc:"О проекте или приложении",
    topicCooperation:"Сотрудничество",topicCooperationDesc:"Партнёрство и предложения",
    topicFeedback:"Отзыв или идея",topicFeedbackDesc:"Мнение и пожелания",
    topicOther:"Другое",topicOtherDesc:"Любое обращение по делу",
    helpTitle:"НУЖНА ТЕХНИЧЕСКАЯ ПОМОЩЬ?",
    helpText:"Для ошибки или проблемы установки у нас есть отдельная форма, где можно описать шаги воспроизведения.",
    helpLink:"Сообщить об ошибке",
    formOverline:"НОВОЕ СООБЩЕНИЕ",formHeading:"Напиши нам",
    formDesc:"Обращение попадёт разработчику через действующую систему сообщений. Регистрация не требуется.",
    nameLabel:"Твоё имя или никнейм",emailLabel:"Email для ответа",emailOptionalLabel:"Email (необязательно)",
    titleLabel:"Тема письма",titlePlaceholder:"Вопрос о WT Mod Manager",
    messageLabel:"Сообщение разработчику",messagePlaceholder:"Расскажи подробнее, что хочешь обсудить...",
    optionsTitle:"Дополнительные настройки сообщения",replyLabel:"Нужен ответ?",
    replyEmail:"Да, ответьте на мой email",replyNone:"Нет, просто передаю сообщение",
    referenceLabel:"Ссылка на пример (необязательно)",
    optionsNote:"Не прикрепляй пароли, токены, документы и приватные файлы. Пожалуйста, не публикуй чужие личные данные.",
    consentText:"Я согласен отправить указанные данные для обработки моего обращения.",
    loading:"Подключение к службе обращений…",ready:"Форма готова к отправке.",
    unavailable:"Служба отправки временно недоступна. Можно использовать электронную почту, если она указана.",cooldown:"Сообщение уже отправлено. Повтори попытку немного позже.",
    invalid:"Проверь заполнение полей и согласие на отправку.",
    sending:"Отправляем сообщение…",send:"Отправить сообщение",
    sendError:"Не удалось отправить сообщение. Проверь подключение и попробуй ещё раз.",
    successTitle:"Сообщение отправлено!",successText:"Сервис принял обращение. Если ты запросил ответ, мы сможем связаться через указанный email.",
    again:"Написать ещё",emailFallback:"Написать через почтовое приложение",
    privacy:"WT Mod Manager — независимый фанатский проект. Сообщения обрабатываются через Formspree. Не передавай конфиденциальную информацию.",
    backHome:"Вернуться на главную"
  },
  uk: {
    skip:"Перейти до форми",navHome:"Головна",navCommunity:"Спільнота",navSupport:"Центр підтримки",
    languageLabel:"Мова",eyebrow:"ЗВ'ЯЗОК ІЗ КОМАНДОЮ",
    heading:"Зв'язатися з <em>розробником</em>",
    intro:"Маєш запитання про WT Mod Manager, ідею співпраці чи пропозицію? Напиши через окрему форму, і звернення надійде до нашої служби повідомлень.",
    sidebarLabel:"ЦЕНТР КОНТАКТІВ",sidebarTitle:"Обери тему",sidebarDesc:"Це допоможе швидше зрозуміти твоє звернення.",
    topicQuestion:"Загальне питання",topicQuestionDesc:"Про проєкт або програму",
    topicCooperation:"Співпраця",topicCooperationDesc:"Партнерство та пропозиції",
    topicFeedback:"Відгук або ідея",topicFeedbackDesc:"Думки та побажання",
    topicOther:"Інше",topicOtherDesc:"Інші питання щодо проєкту",
    helpTitle:"ПОТРІБНА ТЕХНІЧНА ДОПОМОГА?",
    helpText:"Для повідомлень про помилки та проблеми встановлення є окрема форма з описом кроків відтворення.",
    helpLink:"Повідомити про помилку",
    formOverline:"НОВЕ ПОВІДОМЛЕННЯ",formHeading:"Напиши нам",
    formDesc:"Повідомлення надійде розробнику через чинну систему звернень. Реєстрація не потрібна.",
    nameLabel:"Твоє ім'я або нікнейм",emailLabel:"Email для відповіді",emailOptionalLabel:"Email (необов'язково)",
    titleLabel:"Тема листа",titlePlaceholder:"Питання про WT Mod Manager",
    messageLabel:"Повідомлення розробнику",messagePlaceholder:"Опиши детальніше, що хотів би обговорити...",
    optionsTitle:"Додаткові налаштування повідомлення",replyLabel:"Потрібна відповідь?",
    replyEmail:"Так, дайте відповідь на мій email",replyNone:"Ні, просто надсилаю повідомлення",
    referenceLabel:"Посилання на приклад (необов'язково)",
    optionsNote:"Не додавай паролі, токени, документи та приватні файли. Не поширюй чужі особисті дані.",
    consentText:"Я погоджуюся на передавання вказаних даних для опрацювання звернення.",
    loading:"Підключення до служби звернень…",ready:"Форма готова до надсилання.",
    unavailable:"Служба надсилання тимчасово недоступна. За наявності адреси можна написати електронною поштою.",cooldown:"Повідомлення вже надіслано. Повтори спробу трохи пізніше.",
    invalid:"Перевір заповнення полів і згоду на надсилання.",
    sending:"Надсилаємо повідомлення…",send:"Надіслати повідомлення",
    sendError:"Не вдалося надіслати повідомлення. Перевір з'єднання та спробуй ще раз.",
    successTitle:"Повідомлення надіслано!",successText:"Сервіс прийняв звернення. Якщо ти попросив відповідь, ми зможемо написати на вказаний email.",
    again:"Написати ще",emailFallback:"Написати через поштовий застосунок",
    privacy:"WT Mod Manager — незалежний фанатський проєкт. Повідомлення обробляє Formspree. Не передавай конфіденційної інформації.",
    backHome:"Повернутися на головну"
  },
  en: {
    skip:"Skip to form",navHome:"Home",navCommunity:"Community",navSupport:"Support Center",
    languageLabel:"Language",eyebrow:"GET IN TOUCH",
    heading:"Contact the <em>developer</em>",
    intro:"Have a question about WT Mod Manager, a collaboration proposal or feedback? Send a message through our dedicated contact page.",
    sidebarLabel:"CONTACT CENTER",sidebarTitle:"Choose a topic",sidebarDesc:"Help us understand the reason for your message.",
    topicQuestion:"General question",topicQuestionDesc:"About the project or app",
    topicCooperation:"Collaboration",topicCooperationDesc:"Partnerships and proposals",
    topicFeedback:"Feedback or idea",topicFeedbackDesc:"Suggestions and thoughts",
    topicOther:"Other",topicOtherDesc:"Another project-related question",
    helpTitle:"NEED TECHNICAL SUPPORT?",
    helpText:"For bugs or installation problems, use our separate support form with steps to reproduce the issue.",
    helpLink:"Report a bug",
    formOverline:"NEW MESSAGE",formHeading:"Write to us",
    formDesc:"Your message goes through our existing contact service to the developer. No registration required.",
    nameLabel:"Your name or nickname",emailLabel:"Reply email",emailOptionalLabel:"Email (optional)",
    titleLabel:"Message subject",titlePlaceholder:"Question about WT Mod Manager",
    messageLabel:"Message to the developer",messagePlaceholder:"Tell us what you'd like to discuss...",
    optionsTitle:"Additional message options",replyLabel:"Would you like a reply?",
    replyEmail:"Yes, reply to my email",replyNone:"No, I'm just sharing this",
    referenceLabel:"Reference link (optional)",
    optionsNote:"Never include passwords, access tokens, documents, or private files. Do not share anyone else's personal data.",
    consentText:"I agree to send the provided information so my message can be processed.",
    loading:"Connecting to the contact service…",ready:"Ready to send.",
    unavailable:"The contact service is unavailable. You can use email if a developer address is configured.",cooldown:"Your message was just sent. Please try again shortly.",
    invalid:"Please check the required fields and consent.",
    sending:"Sending your message…",send:"Send message",
    sendError:"The message could not be sent. Check your connection and try again.",
    successTitle:"Message sent!",successText:"The service accepted your request. If you asked for a reply, we can contact you at the email you entered.",
    again:"Write another message",emailFallback:"Write via email app",
    privacy:"WT Mod Manager is an independent fan project. Formspree processes messages. Do not share confidential information.",
    backHome:"Back to homepage"
  }
};

Object.assign(copy, contactLocalesExtra);
Object.assign(copy.ru,{
  identityReady:"Отправитель из профиля:",identityMissing:"Сначала установи никнейм в своём профиле.",
  openProfile:"Открыть профиль",rateLimit:"Слишком много обращений. Попробуй позже.",
  formDesc:"Отправка через твой профиль WT Mod Manager. Никнейм и подтверждённый email добавляются автоматически.",
  successText:"Служба приняла обращение. Ответ возможен, если к профилю привязан подтверждённый email."
});
Object.assign(copy.uk,{
  identityReady:"Відправник із профілю:",identityMissing:"Спочатку встанови нікнейм у профілі.",
  openProfile:"Відкрити профіль",rateLimit:"Забагато звернень. Спробуй пізніше.",
  formDesc:"Повідомлення надсилається з твого профілю WT Mod Manager. Нікнейм і підтверджений email підставляються автоматично.",
  successText:"Служба прийняла звернення. Відповідь можлива за наявності підтвердженого email."
});
Object.assign(copy.en,{
  identityReady:"Sender from profile:",identityMissing:"Set a nickname in your profile before sending.",
  openProfile:"Open profile",rateLimit:"Too many requests. Please try later.",
  formDesc:"Messages are sent through your WT Mod Manager profile. Nickname and verified email are filled automatically.",
  successText:"The service accepted your message. A reply is possible if a verified email is linked to your profile."
});

const $ = id => document.getElementById(id);
const form = $("contactForm");
const submit = $("contactSubmit");
const status = $("contactNotice");
const success = $("contactSuccess");
const topicButtons = Array.from(document.querySelectorAll("[data-topic]"));
const TOPIC_NAMES = {question:"General question",cooperation:"Collaboration",feedback:"Feedback or idea",other:"Other"};
let lang = "ru";
let topic = "question";
let bridge = null;
let busy = false;
let lastSentAt = 0;

function t(key) { return (copy[lang] && copy[lang][key]) || copy.ru[key] || key; }
function setStatus(message, isError = false) {
  status.textContent = message;
  status.classList.toggle("is-error", isError);
  status.classList.toggle("is-success", !isError && message === t("ready"));
}
function applyLanguage(next) {
  if (!Object.prototype.hasOwnProperty.call(copy, next)) next = "ru";
  lang = next;
  document.documentElement.lang = next;
  $("contactLanguage").value = next;
  try { localStorage.setItem("wtmm-language", next); } catch { /* optional */ }
  for (const element of document.querySelectorAll("[data-t]")) {
    const key = element.dataset.t;
    if (key === "heading") {
      // Hardcoded localized templates; no user input or remote HTML is inserted.
      const parts = t("heading").split(/<em>|<\/em>/);
      element.replaceChildren(
        document.createTextNode(parts[0] || ""),
        Object.assign(document.createElement("em"), { textContent: parts[1] || "" })
      );
    } else {
      element.textContent = t(key);
    }
  }
  for (const element of document.querySelectorAll("[data-placeholder]")) {
    element.placeholder = t(element.dataset.placeholder);
  }
  syncReplySetting();
  $("contactCounter").textContent = $("contactMessage").value.length + " / 4000";
  if (bridge) $("contactIdentityNotice").textContent = t("identityReady") + " " + bridge.nickname;
  // Keep errors from getting overwritten while switching language.
  if (status.dataset.mode === "ready") setStatus(t("ready"));
  else if (status.dataset.mode === "unavailable") setStatus(t("unavailable"), true);
  $("contactSubmit").querySelector("[data-t=send]").textContent = busy ? t("sending") : t("send");
}
function selectTopic(next) {
  topic = normalizeContactTopic(next);
  $("contactTopic").value = topic;
  $("contactSubject").value = "WT Mod Manager — Developer contact — " + TOPIC_NAMES[topic];
  for (const button of topicButtons) {
    const selected = button.dataset.topic === topic;
    button.classList.toggle("is-current", selected);
    button.setAttribute("aria-pressed", String(selected));
  }
}
function syncReplySetting() {
  const hasReplyEmail = Boolean(bridge?.hasReplyEmail);
  const choice = $("contactReply");
  const emailOption = choice.querySelector('option[value="email"]');
  if(emailOption) emailOption.disabled = !hasReplyEmail;
  if(!hasReplyEmail) choice.value = "none";
}
async function loadService() {
  const notice = $("contactIdentityNotice");
  try {
    bridge = await getContactBridge();
    notice.textContent = t("identityReady") + " " + bridge.nickname;
    syncReplySetting();
    submit.disabled = false;
    status.dataset.mode = "ready";
    setStatus(t("ready"));
  } catch(error) {
    bridge = null;
    submit.disabled = true;
    status.dataset.mode = "unavailable";
    setStatus(error?.message === "PROFILE_REQUIRED" ? t("identityMissing") : t("unavailable"),true);
    notice.textContent = t("identityMissing") + " ";
    const link = document.createElement("a");
    link.href = "../profile/profile.html";
    link.textContent = t("openProfile");
    notice.append(link);
  }
}
function readValues() {
  return {
    website: $("contactWebsite").value,
    title: $("contactTitle").value,
    message: $("contactMessage").value,
    reference: $("contactReference").value,
    reply: $("contactReply").value,
    consent: $("contactConsent").checked
  };
}
async function sendMessage(event) {
  event.preventDefault();
  if (busy || !bridge) return;
  if (Date.now() - lastSentAt < 60000) {
    setStatus(t("cooldown"), true);
    return;
  }
  const values = readValues();
  const validation = validateContact(values);
  if (validation === "honeypot") return;
  if (validation !== "valid" || !form.checkValidity()) {
    setStatus(t("invalid"), true);
    form.reportValidity();
    return;
  }
  busy = true;
  submit.disabled = true;
  submit.querySelector("[data-t=send]").textContent = t("sending");
  status.dataset.mode = "sending";
  setStatus(t("sending"));
  try {
    await bridge.send({
      kind:"contact",topic,title:values.title,message:values.message,
      reference:values.reference,reply:values.reply,language:lang,website:values.website
    });
    lastSentAt = Date.now();
    form.reset();
    selectTopic("question");
    syncReplySetting();
    $("contactCounter").textContent = "0 / 4000";
    form.hidden = true;
    success.hidden = false;
    success.focus();
  } catch(error) {
    console.warn("Developer message send failed:", error?.message || "request error");
    status.dataset.mode = "error";
    setStatus(error?.message === "RATE_LIMIT" ? t("rateLimit") : t("sendError"),true);
  } finally {
    busy = false;
    submit.disabled = !bridge;
    submit.querySelector("[data-t=send]").textContent = t("send");
  }
}
function detectLanguage() {
  try {
    const saved = localStorage.getItem("wtmm-language");
    if (Object.prototype.hasOwnProperty.call(copy, saved)) return saved;
  } catch { /* storage may be unavailable */ }
  const locale = (navigator.language || "").toLowerCase();
  if(locale.startsWith("uk")) return "uk";
  if(locale.startsWith("ru")) return "ru";
  if(locale.startsWith("pl")) return "pl";
  if(locale.startsWith("de")) return "de";
  return "en";
}
function init() {
  $("contactYear").textContent = String(new Date().getFullYear());
  applyLanguage(detectLanguage());
  selectTopic("question");
  topicButtons.forEach(button => button.addEventListener("click", () => selectTopic(button.dataset.topic)));
  $("contactLanguage").addEventListener("change", event => applyLanguage(event.target.value));
  $("contactReply").addEventListener("change", syncReplySetting);
  $("contactMessage").addEventListener("input", () => {
    $("contactCounter").textContent = $("contactMessage").value.length + " / 4000";
  });
  form.addEventListener("submit", sendMessage);
  $("contactAgain").addEventListener("click", () => {
    if (Date.now() - lastSentAt < 60000) {
      // Restore a blank form but keep cooldown (prevents accidental duplicate sends).
      status.dataset.mode = "cooldown";
    }
    success.hidden = true;
    form.hidden = false;
    $("contactTitle").focus();
  });
  loadService();
}
init();
