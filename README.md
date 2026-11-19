# WT Mod Manager

**WT Mod Manager** — независимый проект для управления пользовательскими модификациями War Thunder.

На официальном сайте доступны новости проекта, библиотека модификаций, информация о возможностях приложения и поддержка пользователей.

## Официальный сайт

**[Открыть сайт WT Mod Manager](https://qwerthegoe-hash.github.io/WT-Mod-Manager-Website/)**

## Полное техническое досье для других чатов и разработчиков

**[WTMM_FULL_PROJECT_HANDOFF_2026-11-19.txt](WTMM_FULL_PROJECT_HANDOFF_2026-11-19.txt)** — основной большой TXT-файл проекта (архитектура, 200+ файлов, назначение скриптов, изменения Beta 12, сайт, Supabase, GitHub Actions, инструкции по тестам, ограничения и следующая работа). **При продолжении проекта в другом чате сначала откройте этот файл, затем проверьте актуальный `main` и последний релиз.**

Основные точки входа:
- Windows-приложение: `src/main.py`, `ui/main_window.py`.
- Система обновлений и восстановления: `src/update_checker.py`, `src/portable_updater.py`, `src/crash_recovery.py`.
- Сайт GitHub Pages: `docs/index.html`; центр доверия: `docs/trust.html`.
- Серверная проверка модов: `supabase/functions/wtmm-mod-scan/index.ts` и `zip.ts`.
- Windows-сборка и релизы: `.github/workflows/build-windows-exe.yml`.
- Последний проверенный релиз на дату досье: [v1.3.0-beta.12](https://github.com/qwerthegoe-hash/WT-Mod-Manager-Website/releases/tag/v1.3.0-beta.12).

Досье описывает снимок состояния проекта на 19 ноября 2026 года. Секреты и private API keys не должны попадать в клиентскую сборку или публичный репозиторий.

---

*WT Mod Manager — независимый фанатский проект, не являющийся официальным продуктом разработчиков War Thunder.*
