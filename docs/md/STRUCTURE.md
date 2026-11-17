# Структура WT Mod Manager Website (GitHub Pages /docs)

Проект организован по твоим папкам. Старые файлы в корне репозитория **не удалены**,
чтобы действующий сайт продолжал работать до переключения GitHub Pages.

```text
docs/
├── .nojekyll
├── index.html             # Главная страница, остается наверху
├── app.js                 # Скрипт главной страницы
├── styles.css             # Общий стиль
├── assets/                # Логотип и изображения
│   └── community-icons.svg
├── community/
│   ├── community.html
│   ├── community.css
│   └── community.js
├── profile/
│   ├── profile.html
│   ├── profile.css
│   └── profile.js
├── mods/
│   ├── mods.html
│   ├── mods.css
│   └── mods.js
├── creator/
│   ├── creator.html
│   └── creator.js
├── support/
│   ├── support.html
│   ├── support.css
│   └── support.js
├── js/
│   ├── community-config.js
│   ├── community-icons.js
│   └── guardian-panel.js
├── json/
│   └── site-config.json
├── database/
│   ├── profile_upgrade.sql
│   └── community_platform_upgrade.sql
└── md/
    ├── COMMUNITY_PLATFORM_SETUP.md
    └── STRUCTURE.md
```

## ВАЖНО: добавь изображения из локального проекта

В подключённом GitHub-репозитории сейчас **нет** `assets/LogotipProject.png`
и файлов `sights.png`, `camouflages.png`, `configurations.png`,
`language.png`, `reset.png`, `heart.png`.
Если они есть в твоём локальном `assets`, загрузи их в **`docs/assets/`**:
их используют все страницы и `styles.css`.
Логотип и картинки не стоит заменять случайными изображениями.

## Как переключить GitHub Pages

В Settings → Pages выбери Deploy from a branch → main → /docs.
Сделай это **после загрузки всех изображений и проверки страниц**.
Если использованы GitHub Actions для Pages, проверь путь публикации в workflow
и не меняй источник без необходимости.

Адреса после переключения:

- Главная: `/WT-Mod-Manager-Website/`
- Community: `/WT-Mod-Manager-Website/community/community.html`
- Профиль: `/WT-Mod-Manager-Website/profile/profile.html`
- Библиотека: `/WT-Mod-Manager-Website/mods/mods.html`
- Автор: `/WT-Mod-Manager-Website/creator/creator.html?id=...`
- Поддержка: `/WT-Mod-Manager-Website/support/support.html`

Небольшие страницы-переадресации `docs/community.html`, `docs/profile.html`,
`docs/mods.html`, `docs/creator.html` и `docs/support.html` сохраняют старые
ссылки и передают параметры адресов (например, `?id=` и `?type=`).

## Supabase

Frontend использует `docs/js/community-config.js`.
SQL-файлы в `docs/database/` предназначены для SQL Editor, не исполняются сайтом.
Для реального деплоя Edge Functions сохраняй исходный `supabase/` на
уровне корня репозитория (или настрой Supabase CLI под новый путь).
Перенос edge-функций в публичный Pages `docs/` сам по себе **не разворачивает** функции.

## Проверка

Проверь навигацию, регистрацию, чат, фото, загрузку модов и модерацию
в работающем браузере после публикации. Статическая проверка путей
не заменяет проверки подключения к Supabase.
