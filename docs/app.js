'use strict';

// Text for the three supported languages. Keep translations in this file.
const translations = {
  "en": {
    "navFeatures": "Features",
    "navDownload": "Download",
    "navSupport": "Support",
    "eyebrow": "PUBLIC BETA · 1.2",
    "headline": "Manage your War Thunder mods. <em>Simply.</em>",
    "lead": "A free community-made desktop manager for sights, camouflages, sounds and personal settings. Built for players, not paywalls.",
    "heroDownload": "Get WT Mod Manager",
    "learnMore": "Explore features",
    "free": "100% free",
    "windows": "Windows desktop",
    "community": "Independent community project",
    "sights": "Sights",
    "camouflages": "Camouflages",
    "sounds": "Sounds",
    "settings": "Settings",
    "previewLabel": "APP PREVIEW",
    "previewTitle": "Everything in one place",
    "previewDesc": "Quick navigation, flexible appearance, and settings that stay with you.",
    "mockCaption": "Illustrative website preview — not a screenshot of the application.",
    "featuresOverline": "FEATURES",
    "featuresTitle": "Made for your setup",
    "featuresDesc": "Common mod management tasks, together in a clean interface.",
    "f1Title": "Custom sights",
    "f1Desc": "Keep your aiming setups organized.",
    "f2Title": "Camouflages",
    "f2Desc": "Manage user-created vehicle appearances.",
    "f3Title": "Sounds",
    "f3Desc": "Browse and preview supported audio files.",
    "f4Title": "Personalization",
    "f4Desc": "Themes, languages, fonts and convenient settings.",
    "downloadOverline": "DOWNLOAD",
    "downloadTitle": "Ready to try the beta?",
    "downloadDesc": "Installer downloads will appear here when the first public release is published. No unfinished downloads or fake links.",
    "downloadSoon": "Public installer: coming soon.",
    "downloadReady": "The public installer is available.",
    "downloadBtn": "Download for Windows",
    "releases": "View release notes",
    "supportOverline": "SUPPORT THE PROJECT",
    "supportTitle": "Free to use. Supported by players.",
    "supportDesc": "WT Mod Manager remains free for everyone. If you enjoy the project, you may voluntarily support its development through monobank. Contributions help us improve features, fix issues, and work on future releases. Supporting is never required to use the application.",
    "supportSoon": "Support link is being prepared.",
    "supportReady": "Voluntary support via monobank is available.",
    "supportBtn": "Support via monobank",
    "faqOverline": "GOOD TO KNOW",
    "faqTitle": "Frequently asked questions",
    "q1": "Is WT Mod Manager free?",
    "a1": "Yes. WT Mod Manager is free to download and use. Core features, appearance settings, and future updates do not require payment. Contributions through monobank are entirely optional and do not unlock paid features.",
    "q2": "Is this an official War Thunder product?",
    "a2": "No. WT Mod Manager is an independent fan-made project that helps players organize user-created War Thunder modifications. It is not developed, supported, affiliated with, or endorsed by Gaijin Entertainment. War Thunder and associated trademarks belong to their respective owners.",
    "q3": "Where are downloads hosted?",
    "a3": "Installers are planned to be published through GitHub Releases when ready.",
    "footerNote": "Independent fan-made project. War Thunder is a trademark of its respective owner."
  },
  "ru": {
    "navFeatures": "Возможности",
    "navDownload": "Скачать",
    "navSupport": "Поддержать",
    "eyebrow": "ПУБЛИЧНАЯ БЕТА · 1.2",
    "headline": "Управляй модами War Thunder. <em>Просто.</em>",
    "lead": "Бесплатный менеджер пользовательских прицелов, камуфляжей, звуков и настроек. Создан для игроков.",
    "heroDownload": "Скачать WT Mod Manager",
    "learnMore": "Посмотреть возможности",
    "free": "Полностью бесплатно",
    "windows": "Для Windows",
    "community": "Независимый проект",
    "sights": "Прицелы",
    "camouflages": "Камуфляжи",
    "sounds": "Звуки",
    "settings": "Настройки",
    "previewLabel": "ПРЕДПРОСМОТР",
    "previewTitle": "Всё в одном месте",
    "previewDesc": "Удобная навигация, гибкое оформление и сохранение настроек.",
    "mockCaption": "Иллюстрация интерфейса — не настоящий скриншот приложения.",
    "featuresOverline": "ВОЗМОЖНОСТИ",
    "featuresTitle": "Всё для твоих модов",
    "featuresDesc": "Популярные действия с модификациями в удобном интерфейсе.",
    "f1Title": "Пользовательские прицелы",
    "f1Desc": "Упорядочивай свои прицелы.",
    "f2Title": "Камуфляжи",
    "f2Desc": "Управляй пользовательскими камуфляжами техники.",
    "f3Title": "Звуки",
    "f3Desc": "Просматривай и прослушивай поддерживаемые звуковые файлы.",
    "f4Title": "Персонализация",
    "f4Desc": "Темы, языки, шрифты и удобные настройки.",
    "downloadOverline": "ЗАГРУЗКА",
    "downloadTitle": "Готов попробовать бету?",
    "downloadDesc": "Установщик появится после публикации первого публичного релиза. Неактивных или выдуманных ссылок на загрузку здесь не будет.",
    "downloadSoon": "Публичный установщик: скоро.",
    "downloadReady": "Публичный установщик доступен.",
    "downloadBtn": "Скачать для Windows",
    "releases": "История версий",
    "supportOverline": "ПОДДЕРЖАТЬ ПРОЕКТ",
    "supportTitle": "Бесплатно для всех. При поддержке игроков.",
    "supportDesc": "WT Mod Manager остаётся бесплатной программой для всех игроков. Если проект оказался полезным, можно добровольно поддержать разработку через monobank: помощь пойдёт на развитие функций, исправление ошибок и улучшение будущих версий. Пожертвования не обязательны и не влияют на доступ к программе.",
    "supportSoon": "Ссылка на поддержку готовится.",
    "supportReady": "Добровольная поддержка через monobank доступна.",
    "supportBtn": "Поддержать через monobank",
    "faqOverline": "ЧАСТЫЕ ВОПРОСЫ",
    "faqTitle": "Полезно знать",
    "q1": "WT Mod Manager бесплатный?",
    "a1": "Да. WT Mod Manager можно использовать бесплатно: установка, основные возможности, темы оформления и будущие обновления не требуют оплаты. Поддержка через monobank — только добровольная благодарность разработке и не открывает платные функции.",
    "q2": "Это официальная программа War Thunder?",
    "a2": "Нет. WT Mod Manager — независимый фанатский проект для удобной работы с пользовательскими модификациями War Thunder. Он не разработан компанией Gaijin Entertainment, не является её официальным приложением и не поддерживается или одобряется ею. Все права на War Thunder и связанные обозначения принадлежат их правообладателям.",
    "q3": "Где будут файлы для скачивания?",
    "a3": "Мы планируем публиковать установщики через GitHub Releases.",
    "footerNote": "Независимый фанатский проект. War Thunder — товарный знак соответствующего правообладателя."
  },
  "uk": {
    "navFeatures": "Можливості",
    "navDownload": "Завантажити",
    "navSupport": "Підтримати",
    "eyebrow": "ПУБЛІЧНА БЕТА · 1.2",
    "headline": "Керуй модами War Thunder. <em>Просто.</em>",
    "lead": "Безкоштовний менеджер користувацьких прицілів, камуфляжів, звуків і налаштувань. Створений для гравців.",
    "heroDownload": "Завантажити WT Mod Manager",
    "learnMore": "Переглянути можливості",
    "free": "Повністю безкоштовно",
    "windows": "Для Windows",
    "community": "Незалежний проєкт",
    "sights": "Приціли",
    "camouflages": "Камуфляжі",
    "sounds": "Звуки",
    "settings": "Налаштування",
    "previewLabel": "ПОПЕРЕДНІЙ ПЕРЕГЛЯД",
    "previewTitle": "Усе в одному місці",
    "previewDesc": "Зручна навігація, гнучке оформлення та збереження налаштувань.",
    "mockCaption": "Ілюстрація інтерфейсу — не справжній знімок застосунку.",
    "featuresOverline": "МОЖЛИВОСТІ",
    "featuresTitle": "Усе для твоїх модів",
    "featuresDesc": "Поширені дії з модифікаціями в зручному інтерфейсі.",
    "f1Title": "Користувацькі приціли",
    "f1Desc": "Впорядковуй свої приціли.",
    "f2Title": "Камуфляжі",
    "f2Desc": "Керуй користувацькими камуфляжами техніки.",
    "f3Title": "Звуки",
    "f3Desc": "Переглядай і прослуховуй підтримувані звукові файли.",
    "f4Title": "Персоналізація",
    "f4Desc": "Теми, мови, шрифти та зручні налаштування.",
    "downloadOverline": "ЗАВАНТАЖЕННЯ",
    "downloadTitle": "Готовий спробувати бету?",
    "downloadDesc": "Інсталятор з’явиться після публікації першого публічного релізу. Жодних вигаданих посилань на завантаження.",
    "downloadSoon": "Публічний інсталятор: незабаром.",
    "downloadReady": "Публічний інсталятор доступний.",
    "downloadBtn": "Завантажити для Windows",
    "releases": "Історія версій",
    "supportOverline": "ПІДТРИМАТИ ПРОЄКТ",
    "supportTitle": "Безкоштовно для всіх. Завдяки підтримці гравців.",
    "supportDesc": "WT Mod Manager залишається безкоштовною програмою для всіх. Якщо проєкт вам корисний, ви можете добровільно підтримати його розробку через monobank. Внески допомагають розвивати можливості, виправляти помилки та готувати нові версії. Підтримка не обов’язкова для користування програмою.",
    "supportSoon": "Посилання для підтримки готується.",
    "supportReady": "Добровільна підтримка через monobank доступна.",
    "supportBtn": "Підтримати через monobank",
    "faqOverline": "ПОШИРЕНІ ЗАПИТАННЯ",
    "faqTitle": "Корисно знати",
    "q1": "WT Mod Manager безкоштовний?",
    "a1": "Так. WT Mod Manager можна завантажувати й використовувати безкоштовно. Основні можливості, налаштування оформлення та майбутні оновлення не потребують оплати. Підтримка через monobank повністю добровільна й не відкриває платних функцій.",
    "q2": "Це офіційна програма War Thunder?",
    "a2": "Ні. WT Mod Manager — незалежний фанатський проєкт для впорядкування користувацьких модифікацій War Thunder. Його не розробляє, не підтримує і не схвалює Gaijin Entertainment; він не пов’язаний з компанією офіційно. War Thunder та пов’язані торговельні марки належать їхнім правовласникам.",
    "q3": "Де будуть файли для завантаження?",
    "a3": "Плануємо публікувати інсталятори через GitHub Releases.",
    "footerNote": "Незалежний фанатський проєкт. War Thunder — торгова марка відповідного власника."
  }
};

const LANGUAGE_LABELS = { en: 'EN', ru: 'RU', uk: 'UA' };
let lang = 'en';
let config = {};

function renderLang(next) {
  lang = Object.hasOwn(translations, next) ? next : 'en';
  document.documentElement.lang = lang;
  document.getElementById('selectedLanguage').textContent = LANGUAGE_LABELS[lang];

  for (const button of document.querySelectorAll('.lang-option')) {
    const selected = button.dataset.lang === lang;
    button.classList.toggle('selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  }

  for (const element of document.querySelectorAll('[data-i18n]')) {
    const value = translations[lang][element.dataset.i18n];
    if (value === undefined) continue;
    // Only the headline contains predefined, trusted markup (<em>).
    if (element.dataset.i18n === 'headline') {
      element.innerHTML = value;
    } else {
      element.textContent = value;
    }
  }

  try {
    localStorage.setItem('wtmm-language', lang);
  } catch (error) {
    console.warn('Language preference could not be saved:', error);
  }

  applyStatuses();
}

function approvedUrl(raw, kind) {
  if (typeof raw !== 'string' || !raw.trim()) return '';

  try {
    const url = new URL(raw);
    if (url.protocol !== 'https:') return '';
    const host = url.hostname.toLowerCase();
    if (kind === 'monobank' && host !== 'send.monobank.ua') return '';
    if (kind === 'download' && host !== 'github.com') return '';
    return url.href;
  } catch {
    return '';
  }
}

function activate(link, url) {
  if (!url) return false;
  link.href = url;
  link.classList.remove('disabled');
  link.removeAttribute('aria-disabled');
  link.removeAttribute('tabindex');
  return true;
}

function applyStatuses() {
  const text = translations[lang];
  document.getElementById('downloadStatus').textContent =
    approvedUrl(config.download_url, 'download') ? text.downloadReady : text.downloadSoon;
  document.getElementById('supportStatus').textContent =
    approvedUrl(config.monobank_url, 'monobank') ? text.supportReady : text.supportSoon;
}

function setupLanguageMenu() {
  const toggle = document.getElementById('languageToggle');
  const menu = document.getElementById('languageMenu');
  const options = [...menu.querySelectorAll('.lang-option')];

  function setOpen(open) {
    menu.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.classList.toggle('open', open);
  }

  toggle.addEventListener('click', () => {
    const isOpening = menu.hidden;
    setOpen(isOpening);
    if (isOpening) {
      (options.find(option => option.dataset.lang === lang) || options[0]).focus();
    }
  });

  options.forEach((option, index) => {
    option.addEventListener('click', () => {
      renderLang(option.dataset.lang);
      setOpen(false);
      toggle.focus();
    });

    option.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        const direction = event.key === 'ArrowDown' ? 1 : -1;
        options[(index + direction + options.length) % options.length].focus();
      }
      if (event.key === 'Escape') {
        setOpen(false);
        toggle.focus();
      }
    });
  });

  document.addEventListener('click', event => {
    if (!event.target.closest('.lang-wrap')) setOpen(false);
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !menu.hidden) {
      setOpen(false);
      toggle.focus();
    }
  });
}

async function init() {
  document.getElementById('year').textContent = new Date().getFullYear();
  setupLanguageMenu();

  let initial = '';
  try {
    initial = localStorage.getItem('wtmm-language') || '';
  } catch (error) {
    console.warn('Language preference unavailable:', error);
  }

  if (!Object.hasOwn(translations, initial)) {
    initial = navigator.language?.startsWith('uk') ? 'uk' :
      navigator.language?.startsWith('ru') ? 'ru' : 'en';
  }
  renderLang(initial);

  try {
    const response = await fetch('site-config.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Site config not found');
    config = await response.json();
  } catch (error) {
    console.warn('Site configuration unavailable:', error);
    config = {};
  }

  activate(document.getElementById('downloadBtn'), approvedUrl(config.download_url, 'download'));
  activate(document.getElementById('donateBtn'), approvedUrl(config.monobank_url, 'monobank'));

  const releases = approvedUrl(config.releases_url, 'download');
  if (releases) {
    const link = document.getElementById('releaseNotes');
    link.href = releases;
    link.classList.remove('hidden');
  }
  applyStatuses();
}

document.addEventListener('DOMContentLoaded', init);
