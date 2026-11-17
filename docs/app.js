
"use strict";

// WT Mod Manager Website — Stage 1 Support Integration
// Languages: English, Russian, Ukrainian

const translations = {
    en: {
        navFeatures: "Features",
        navDownload: "Download",
        navHelp: "Help",
        navFeedback: "Feedback",
        navSupport: "Support",
        navProfile: "Profile",
        navMods: "Mods",

        eyebrow: "PUBLIC BETA / VERSION 1.2",
        headline: '<span class="hero-title-main">Manage your War Thunder mods</span> <em>All in one place</em>',
        lead: "Organize custom sights, camouflages, supported audio files and personal preferences in one convenient Windows tool. Free to use and built as an independent project for players.",
        heroDownload: "Get WT Mod Manager",
        learnMore: "Explore features",
        free: "100% free",
        windows: "Windows desktop",
        community: "Independent fan project",

        sights: "Sights",
        camouflages: "Camouflages",
        sounds: "Sounds",
        settings: "Settings",

        previewLabel: "APP PREVIEW",
        previewTitle: "Everything in one place",
        previewDesc: "Quick navigation, flexible appearance and convenient settings.",
        mockCaption: "Illustrative website preview — not an actual screenshot.",

        featuresOverline: "FEATURES",
        featuresTitle: "Made for your setup",
        featuresDesc: "Useful mod management tools in one interface.",
        f1Title: "Custom sights",
        f1Desc: "Keep your aiming setups organized.",
        f2Title: "Camouflages",
        f2Desc: "Manage user-created vehicle appearances.",
        f3Title: "Sounds",
        f3Desc: "Browse and preview supported audio files.",
        f4Title: "Personalization",
        f4Desc: "Themes, languages, fonts and convenient settings.",

        downloadOverline: "DOWNLOAD",
        downloadTitle: "Ready to try the beta?",
        downloadDesc: "Installer downloads will appear here when the first public release is ready. No unfinished downloads or fake links.",
        downloadSoon: "Public installer: coming soon.",
        downloadReady: "The public installer is available.",
        downloadBtn: "Download for Windows",
        releases: "Release notes",

        helpOverline: "HELP CENTER",
        helpTitle: "Need a hand?",
        helpDesc: "Find instructions for using WT Mod Manager.",
        helpSearchPlaceholder: "Search instructions...",
        helpEmpty: "No matching instructions found.",
        helpRead: "Read guide",
        guideLabel: "STEP-BY-STEP GUIDE",
        helpInstallTitle: "Installing the app",
        helpInstallDesc: "Download and install WT Mod Manager.",
        helpSightsTitle: "Custom sights",
        helpSightsDesc: "Learn to manage custom sight files.",
        helpCamoTitle: "Camouflages",
        helpCamoDesc: "Manage user-created camouflages.",
        helpLanguageTitle: "Changing language",
        helpLanguageDesc: "Choose your preferred interface language.",
        helpResetTitle: "Resetting settings",
        helpResetDesc: "Restore default application preferences.",

        feedbackOverline: "COMMUNITY FEEDBACK",
        feedbackTitle: "Help us make it better",
        feedbackDesc: "Your feedback helps improve WT Mod Manager.",
        bugTitle: "Found a bug?",
        bugDesc: "Describe the problem and how to reproduce it.",
        bugButton: "Report a bug",
        ideaTitle: "Have an idea?",
        ideaDesc: "Suggest a useful feature for a future release.",
        ideaButton: "Suggest a feature",
        feedbackNote: "Requests are submitted through our website. No GitHub account is required. Never share passwords or private information.",

        supportOverline: "SUPPORT THE PROJECT",
        supportTitle: "Free to use. Supported by players.",
        supportDesc: "WT Mod Manager is free for everyone. If you find it useful, you can optionally support development through monobank. Contributions help improve features, fix bugs and prepare new releases. Supporting is never required.",
        supportSoon: "Support link is being prepared.",
        supportReady: "Voluntary support via monobank is available.",
        supportBtn: "Support via monobank",

        faqOverline: "GOOD TO KNOW",
        faqTitle: "Your questions, answered",
        q1: "Is WT Mod Manager free?",
        a1: "Yes. WT Mod Manager is designed as a free Windows utility: no subscriptions, mandatory payments or paid access to core tools. The download button will be enabled only when the public installer is actually published. Voluntary development support is separate and does not unlock exclusive functions.",
        q2: "Is this an official War Thunder product?",
        a2: "This is the project website for WT Mod Manager itself, an independent fan-made tool. It is not an official War Thunder or Gaijin Entertainment product, and is not developed, sponsored or approved by them. The website describes our own software and its planned releases; War Thunder trademarks belong to their respective owners.",
        q3: "Where are downloads hosted?",
        a3: "Public Windows installers and release notes are planned for the project's GitHub Releases page after the build is ready. Until then, the site intentionally does not show a non-working download link. Community-submitted mod archives are handled separately through the site's moderated mod library.",

        previewHint: "Select Sights, Camouflages, Sounds or Settings to explore this interactive concept.",
        previewSightsTitle: "Precision where you need it",
        previewSightsDesc: "Explore an illustrative sight layout and keep the aiming presets you use organized.",
        previewCamoTitle: "Your personal visual style",
        previewCamoDesc: "Browse different camouflage looks in an organized space for vehicle appearance files.",
        previewSoundsTitle: "Audio, under control",
        previewSoundsDesc: "Keep supported sound files in order and preview the kind of audio options the manager focuses on.",
        previewSettingsTitle: "A setup that feels yours",
        previewSettingsDesc: "Personalize the interface, appearance and preferences in one clear workspace.",
        previewSightsNote1: "Preset", previewSightsNote2: "Sight view", previewSightsNote3: "Organization",
        previewCamoNote1: "Patterns", previewCamoNote2: "Collections", previewCamoNote3: "Vehicles",
        previewSoundsNote1: "Audio", previewSoundsNote2: "Playback", previewSoundsNote3: "Profiles",
        previewSettingsNote1: "Themes", previewSettingsNote2: "Languages", previewSettingsNote3: "Preferences",
        contactTitle: "Contact the developer",
        contactDesc: "Have a project question, an improvement idea or feedback? Reach out through our Support Center.",
        contactButton: "Get in touch",
        q4: "What does WT Mod Manager help organize?",
        a4: "The goal is to bring supported custom sights, camouflage files, audio resources and personal settings into one Windows interface. The website illustration shows the idea of these sections; it is not a live screenshot of the application. Check the release notes for what each public version actually supports.",
        q5: "How can I reach the developer?",
        a5: "Open the Support Center to report a technical problem, propose a feature or send a question. If a direct developer email is configured, you will also see a contact option there. Please do not include passwords, account tokens or sensitive personal information.",
        footerNote: "Independent fan-made project. War Thunder is a trademark of its respective owner."
    },

    ru: {
        navFeatures: "Возможности",
        navDownload: "Скачать",
        navHelp: "Помощь",
        navFeedback: "Обратная связь",
        navSupport: "Поддержать",
        navProfile: "Профиль",
        navMods: "Моды",

        eyebrow: "ПУБЛИЧНАЯ БЕТА / ВЕРСИЯ 1.2",
        headline: '<span class="hero-title-main">Управляй модами War Thunder</span> <em>Всё под контролем</em>',
        lead: "Управляй прицелами, камуфляжами, поддерживаемыми звуковыми файлами и настройками в одной удобной программе для Windows. Бесплатно, понятно и создано для игроков.",
        heroDownload: "Скачать WT Mod Manager",
        learnMore: "Посмотреть возможности",
        free: "Полностью бесплатно",
        windows: "Для Windows",
        community: "Независимый проект",

        sights: "Прицелы",
        camouflages: "Камуфляжи",
        sounds: "Звуки",
        settings: "Настройки",

        previewLabel: "ПРЕДПРОСМОТР",
        previewTitle: "Всё в одном месте",
        previewDesc: "Удобная навигация, гибкое оформление и сохранение настроек.",
        mockCaption: "Иллюстрация интерфейса — не настоящий скриншот приложения.",

        featuresOverline: "ВОЗМОЖНОСТИ",
        featuresTitle: "Всё для твоих модов",
        featuresDesc: "Удобные инструменты для управления модификациями.",
        f1Title: "Пользовательские прицелы",
        f1Desc: "Упорядочивай свои прицелы.",
        f2Title: "Камуфляжи",
        f2Desc: "Управляй пользовательскими камуфляжами техники.",
        f3Title: "Звуки",
        f3Desc: "Просматривай и прослушивай поддерживаемые аудиофайлы.",
        f4Title: "Персонализация",
        f4Desc: "Темы оформления, языки, шрифты и настройки.",

        downloadOverline: "СКАЧАТЬ",
        downloadTitle: "Готов попробовать бета-версию?",
        downloadDesc: "Установщик появится после первого публичного релиза. Никаких поддельных ссылок для скачивания.",
        downloadSoon: "Публичный установщик: скоро будет доступен.",
        downloadReady: "Публичный установщик доступен.",
        downloadBtn: "Скачать для Windows",
        releases: "История версий",

        helpOverline: "ЦЕНТР ПОМОЩИ",
        helpTitle: "Нужна помощь?",
        helpDesc: "Найди нужную инструкцию по использованию WT Mod Manager.",
        helpSearchPlaceholder: "Поиск по инструкциям...",
        helpEmpty: "Ничего не найдено. Попробуй другой запрос.",
        helpRead: "Читать инструкцию",
        guideLabel: "ПОШАГОВАЯ ИНСТРУКЦИЯ",
        helpInstallTitle: "Установка программы",
        helpInstallDesc: "Как скачать и установить WT Mod Manager.",
        helpSightsTitle: "Пользовательские прицелы",
        helpSightsDesc: "Как работать с файлами прицелов.",
        helpCamoTitle: "Камуфляжи",
        helpCamoDesc: "Как управлять пользовательскими камуфляжами.",
        helpLanguageTitle: "Изменение языка",
        helpLanguageDesc: "Как выбрать язык интерфейса программы.",
        helpResetTitle: "Сброс настроек",
        helpResetDesc: "Как восстановить стандартные настройки.",

        feedbackOverline: "ОБРАТНАЯ СВЯЗЬ",
        feedbackTitle: "Помоги сделать проект лучше",
        feedbackDesc: "Нашёл ошибку или придумал полезную функцию? Расскажи об этом.",
        bugTitle: "Нашли ошибку?",
        bugDesc: "Опиши проблему, шаги её появления и версию программы.",
        bugButton: "Сообщить об ошибке",
        ideaTitle: "Есть идея?",
        ideaDesc: "Предложи функцию, которую хотелось бы увидеть в следующих версиях.",
        ideaButton: "Предложить функцию",
        feedbackNote: "Обращения отправляются через наш сайт. Аккаунт GitHub не нужен. Не отправляй пароли, ключи и личные данные.",

        supportOverline: "ПОДДЕРЖАТЬ ПРОЕКТ",
        supportTitle: "Бесплатно для всех. При поддержке игроков.",
        supportDesc: "WT Mod Manager остаётся бесплатным приложением. При желании можно добровольно поддержать его разработку через monobank. Помощь способствует улучшению функций, исправлению ошибок и выпуску обновлений. Поддержка не обязательна.",
        supportSoon: "Ссылка на поддержку готовится.",
        supportReady: "Добровольная поддержка через monobank доступна.",
        supportBtn: "Поддержать через monobank",

        faqOverline: "ПОЛЕЗНО ЗНАТЬ",
        faqTitle: "Задаваемые вопросы вами",
        q1: "WT Mod Manager — бесплатная программа?",
        a1: "Да. WT Mod Manager — бесплатная программа для Windows: подписка, обязательные платежи и платный доступ к основным инструментам не требуются. Кнопка скачивания заработает после публикации готового установщика. Добровольная поддержка через monobank никак не влияет на доступные функции.",
        q2: "Это официальный продукт War Thunder?",
        a2: "Это официальный сайт нашего собственного проекта WT Mod Manager, но сама программа — независимая фанатская утилита, а не официальный продукт War Thunder или Gaijin Entertainment. Мы не представляем разработчиков игры, не финансируемся и не одобрены ими. Здесь публикуется информация только о нашем менеджере; права на War Thunder принадлежат правообладателям.",
        q3: "Где размещаются файлы для скачивания?",
        a3: "Готовые установщики WT Mod Manager и заметки об обновлениях планируется размещать в GitHub Releases нашего проекта. Пока релиз не опубликован, сайт не подменяет его фальшивой ссылкой. Моды, которые загружают участники сообщества, хранятся отдельно в библиотеке сайта и проходят модерацию перед публикацией.",

        previewHint: "Нажми на прицелы, камуфляжи, звуки или настройки — демонстрационная панель переключится.",
        previewSightsTitle: "Точность в твоих руках",
        previewSightsDesc: "Наглядный пример раздела прицелов: порядок в вариантах прицеливания и быстрый доступ к нужным файлам.",
        previewCamoTitle: "Свой стиль для техники",
        previewCamoDesc: "Переключай варианты оформления и представляй, как удобно хранить коллекции пользовательских камуфляжей.",
        previewSoundsTitle: "Звуки под контролем",
        previewSoundsDesc: "Демонстрация раздела для поддерживаемых аудиофайлов, их организации и доступных настроек.",
        previewSettingsTitle: "Интерфейс под себя",
        previewSettingsDesc: "Представление раздела с темами оформления, выбором языка и индивидуальными параметрами программы.",
        previewSightsNote1: "Варианты", previewSightsNote2: "Прицел", previewSightsNote3: "Порядок",
        previewCamoNote1: "Узоры", previewCamoNote2: "Коллекции", previewCamoNote3: "Техника",
        previewSoundsNote1: "Звуки", previewSoundsNote2: "Просмотр", previewSoundsNote3: "Профили",
        previewSettingsNote1: "Темы", previewSettingsNote2: "Языки", previewSettingsNote3: "Параметры",
        contactTitle: "Связаться с разработчиком",
        contactDesc: "Есть вопрос по проекту, идея для новой функции или предложение? Напиши нам через Центр поддержки.",
        contactButton: "Написать разработчику",
        q4: "Что помогает организовывать WT Mod Manager?",
        a4: "Цель проекта — собрать в удобном интерфейсе Windows пользовательские прицелы, файлы камуфляжей, поддерживаемые аудиоматериалы и личные настройки. Иллюстрация на главной показывает концепцию разделов, а не живой скриншот. Фактические возможности каждой публичной версии будут указаны в её описании.",
        q5: "Как связаться с разработчиком?",
        a5: "Перейди в Центр поддержки: там можно описать ошибку, предложить улучшение или задать вопрос о проекте. Если указан прямой адрес разработчика, он появится в разделе контактов. Не отправляй пароли, коды и другие личные данные.",
        footerNote: "Независимый фанатский проект. War Thunder — товарный знак соответствующего правообладателя."
    },

    uk: {
        navFeatures: "Можливості",
        navDownload: "Завантажити",
        navHelp: "Допомога",
        navFeedback: "Зворотний зв'язок",
        navSupport: "Підтримати",
        navProfile: "Профіль",
        navMods: "Моди",

        eyebrow: "ПУБЛІЧНА БЕТА / ВЕРСІЯ 1.2",
        headline: '<span class="hero-title-main">Керуй модами War Thunder</span> <em>Усе під контролем</em>',
        lead: "Керуй прицілами, камуфляжами, підтримуваними звуковими файлами й налаштуваннями в одній зручній програмі для Windows. Безкоштовно та створено для гравців.",
        heroDownload: "Завантажити WT Mod Manager",
        learnMore: "Переглянути можливості",
        free: "Повністю безкоштовно",
        windows: "Для Windows",
        community: "Незалежний проєкт",

        sights: "Приціли",
        camouflages: "Камуфляжі",
        sounds: "Звуки",
        settings: "Налаштування",

        previewLabel: "ПОПЕРЕДНІЙ ПЕРЕГЛЯД",
        previewTitle: "Усе в одному місці",
        previewDesc: "Зручна навігація, гнучке оформлення та збереження налаштувань.",
        mockCaption: "Ілюстрація інтерфейсу — не справжній знімок застосунку.",

        featuresOverline: "МОЖЛИВОСТІ",
        featuresTitle: "Усе для твоїх модів",
        featuresDesc: "Зручні інструменти для керування модифікаціями.",
        f1Title: "Користувацькі приціли",
        f1Desc: "Впорядковуй свої приціли.",
        f2Title: "Камуфляжі",
        f2Desc: "Керуй користувацькими камуфляжами техніки.",
        f3Title: "Звуки",
        f3Desc: "Переглядай і прослуховуй підтримувані аудіофайли.",
        f4Title: "Персоналізація",
        f4Desc: "Теми оформлення, мови, шрифти та налаштування.",

        downloadOverline: "ЗАВАНТАЖЕННЯ",
        downloadTitle: "Готовий спробувати бета-версію?",
        downloadDesc: "Інсталятор з'явиться після першого публічного релізу. Жодних вигаданих посилань.",
        downloadSoon: "Публічний інсталятор: незабаром.",
        downloadReady: "Публічний інсталятор доступний.",
        downloadBtn: "Завантажити для Windows",
        releases: "Історія версій",

        helpOverline: "ЦЕНТР ДОПОМОГИ",
        helpTitle: "Потрібна допомога?",
        helpDesc: "Знайди потрібну інструкцію з використання WT Mod Manager.",
        helpSearchPlaceholder: "Пошук інструкцій...",
        helpEmpty: "Нічого не знайдено. Спробуй інший запит.",
        helpRead: "Читати інструкцію",
        guideLabel: "ПОКРОКОВА ІНСТРУКЦІЯ",
        helpInstallTitle: "Встановлення програми",
        helpInstallDesc: "Як завантажити та встановити WT Mod Manager.",
        helpSightsTitle: "Користувацькі приціли",
        helpSightsDesc: "Як працювати з файлами прицілів.",
        helpCamoTitle: "Камуфляжі",
        helpCamoDesc: "Як керувати користувацькими камуфляжами.",
        helpLanguageTitle: "Зміна мови",
        helpLanguageDesc: "Як вибрати мову інтерфейсу програми.",
        helpResetTitle: "Скидання налаштувань",
        helpResetDesc: "Як повернути стандартні налаштування.",

        feedbackOverline: "ЗВОРОТНИЙ ЗВ'ЯЗОК",
        feedbackTitle: "Допоможи зробити проєкт кращим",
        feedbackDesc: "Знайшов помилку або придумав корисну функцію? Розкажи нам.",
        bugTitle: "Знайшли помилку?",
        bugDesc: "Опиши проблему, кроки її відтворення та версію програми.",
        bugButton: "Повідомити про помилку",
        ideaTitle: "Є ідея?",
        ideaDesc: "Запропонуй функцію, яку хотілося б побачити в наступних версіях.",
        ideaButton: "Запропонувати функцію",
        feedbackNote: "Звернення надсилаються через наш сайт. Обліковий запис GitHub не потрібен. Не надсилай паролі, ключі й особисті дані.",

        supportOverline: "ПІДТРИМАТИ ПРОЄКТ",
        supportTitle: "Безкоштовно для всіх. Завдяки підтримці гравців.",
        supportDesc: "WT Mod Manager залишається безкоштовною програмою. За бажанням можна добровільно підтримати розробку через monobank. Внески допомагають покращувати функції, виправляти помилки та випускати оновлення. Підтримка не обов'язкова.",
        supportSoon: "Посилання для підтримки готується.",
        supportReady: "Добровільна підтримка через monobank доступна.",
        supportBtn: "Підтримати через monobank",

        faqOverline: "КОРИСНО ЗНАТИ",
        faqTitle: "Запитання, які ставите ви",
        q1: "WT Mod Manager — безкоштовна програма?",
        a1: "Так. WT Mod Manager — безкоштовна програма для Windows: підписка й обов'язкові платежі не потрібні. Кнопка завантаження запрацює після появи готового публічного інсталятора. Добровільна підтримка через monobank не відкриває окремих платних функцій.",
        q2: "Це офіційний продукт War Thunder?",
        a2: "Це офіційна сторінка нашого власного проєкту WT Mod Manager, але програма є незалежною фанатською утилітою, а не офіційним продуктом War Thunder або Gaijin Entertainment. Ми не представляємо розробників гри й не маємо їхнього схвалення. Торговельні марки War Thunder належать відповідним правовласникам.",
        q3: "Де розміщуються файли для завантаження?",
        a3: "Готові інсталятори WT Mod Manager та нотатки про оновлення планується розміщувати в GitHub Releases нашого проєкту. До появи релізу сайт не показує несправжнє посилання. Моди учасників спільноти зберігаються окремо в бібліотеці сайту й проходять модерацію перед публікацією.",

        previewHint: "Натисни на приціли, камуфляжі, звуки або налаштування — демонстраційна панель перемкнеться.",
        previewSightsTitle: "Точність у твоїх руках",
        previewSightsDesc: "Наочний приклад розділу прицілів: порядок у варіантах прицілювання та зручний доступ до потрібних файлів.",
        previewCamoTitle: "Власний стиль для техніки",
        previewCamoDesc: "Переглядай варіанти оформлення й уявляй, як зручно зберігати колекції користувацьких камуфляжів.",
        previewSoundsTitle: "Звуки під контролем",
        previewSoundsDesc: "Демонстрація розділу для підтримуваних аудіофайлів, їх організації та доступних налаштувань.",
        previewSettingsTitle: "Інтерфейс під себе",
        previewSettingsDesc: "Уявлення розділу з темами оформлення, вибором мови та особистими параметрами програми.",
        previewSightsNote1: "Варіанти", previewSightsNote2: "Приціл", previewSightsNote3: "Порядок",
        previewCamoNote1: "Візерунки", previewCamoNote2: "Колекції", previewCamoNote3: "Техніка",
        previewSoundsNote1: "Звуки", previewSoundsNote2: "Перегляд", previewSoundsNote3: "Профілі",
        previewSettingsNote1: "Теми", previewSettingsNote2: "Мови", previewSettingsNote3: "Параметри",
        contactTitle: "Зв'язатися з розробником",
        contactDesc: "Маєш запитання щодо проєкту, ідею нової функції чи пропозицію? Напиши через Центр підтримки.",
        contactButton: "Написати розробнику",
        q4: "Що допомагає впорядковувати WT Mod Manager?",
        a4: "Мета проєкту — поєднати в одному інтерфейсі Windows користувацькі приціли, файли камуфляжів, підтримувані аудіоматеріали та власні налаштування. Ілюстрація на головній показує концепцію, а не живий знімок програми. Фактичні можливості публічних версій будуть описані в нотатках до випуску.",
        q5: "Як зв'язатися з розробником?",
        a5: "Перейди в Центр підтримки, щоб описати проблему, запропонувати покращення чи поставити запитання. Якщо доступна пряма електронна адреса розробника, її буде показано в розділі контактів. Не надсилай паролі або особисті дані.",
        footerNote: "Незалежний фанатський проєкт. War Thunder — торгова марка відповідного правовласника."
    }
};

// Help guides in three languages.

const guides = {
    en: {
        install: [
            "Open the Download section of this website.",
            "When the public release is ready, use the official GitHub Releases download.",
            "Check the downloaded file's source and follow the installer instructions.",
            "Open WT Mod Manager after installation."
        ],
        sights: [
            "Open the Sights section in WT Mod Manager.",
            "Review the available sight files.",
            "Use the import or file selection options provided in your version.",
            "Back up original files before making changes."
        ],
        camouflages: [
            "Open the Camouflages section.",
            "Select a user camouflage using the available controls.",
            "Review the selected files before making changes.",
            "Keep backups and follow supported War Thunder modification rules."
        ],
        language: [
            "Open WT Mod Manager and go to Settings.",
            "Find the language selection control.",
            "Choose your preferred supported language.",
            "Check that the interface and saved preferences update."
        ],
        reset: [
            "Open the application's Settings section.",
            "Find the reset option if your version provides one.",
            "Review which preferences will be affected.",
            "Confirm only after making a backup of important settings."
        ]
    },

    ru: {
        install: [
            "Открой раздел «Скачать» на этом сайте.",
            "После выхода публичного релиза скачай установщик из официального GitHub Releases.",
            "Проверь источник загруженного файла и следуй инструкциям установщика.",
            "После установки открой WT Mod Manager."
        ],
        sights: [
            "Открой раздел «Прицелы» в WT Mod Manager.",
            "Посмотри доступные прицелы и файлы.",
            "Используй импорт или выбор файлов, если такая функция есть в твоей версии.",
            "Перед заменой файлов создай резервные копии."
        ],
        camouflages: [
            "Открой раздел «Камуфляжи».",
            "Выбери пользовательский камуфляж с помощью доступных элементов управления.",
            "Проверь выбранные файлы перед изменениями.",
            "Сохраняй резервные копии и соблюдай правила пользовательских модификаций War Thunder."
        ],
        language: [
            "Открой WT Mod Manager и перейди в раздел «Настройки».",
            "Найди пункт выбора языка интерфейса.",
            "Выбери нужный язык из доступных вариантов.",
            "Проверь, что интерфейс изменился и выбранный язык сохранился."
        ],
        reset: [
            "Открой вкладку «Настройки» в приложении.",
            "Найди функцию сброса, если она есть в установленной версии.",
            "Проверь, какие настройки будут возвращены к стандартным.",
            "Перед подтверждением сохрани важные пользовательские настройки."
        ]
    },

    uk: {
        install: [
            "Відкрий розділ «Завантажити» на цьому сайті.",
            "Після виходу публічного релізу завантаж інсталятор з офіційного GitHub Releases.",
            "Перевір джерело файлу та дотримуйся інструкцій встановлення.",
            "Після встановлення відкрий WT Mod Manager."
        ],
        sights: [
            "Відкрий розділ «Приціли» у WT Mod Manager.",
            "Переглянь доступні приціли та файли.",
            "Скористайся імпортом або вибором файлів, якщо така функція є у твоїй версії.",
            "Перед змінами збережи резервні копії."
        ],
        camouflages: [
            "Відкрий розділ «Камуфляжі».",
            "Вибери користувацький камуфляж за допомогою доступних елементів керування.",
            "Перевір вибрані файли перед змінами.",
            "Зберігай резервні копії та дотримуйся правил модифікацій War Thunder."
        ],
        language: [
            "Відкрий WT Mod Manager і перейди в «Налаштування».",
            "Знайди пункт вибору мови інтерфейсу.",
            "Вибери потрібну мову з доступних варіантів.",
            "Перевір, що інтерфейс оновився, а вибрана мова збереглася."
        ],
        reset: [
            "Відкрий вкладку «Налаштування» у програмі.",
            "Знайди функцію скидання, якщо вона доступна у встановленій версії.",
            "Перевір, які параметри повернуться до стандартних значень.",
            "Перед підтвердженням збережи важливі користувацькі налаштування."
        ]
    }
};

const languageLabels = {
    en: "EN",
    ru: "RU",
    uk: "UA"
};

const guideTitleKeys = {
    install: "helpInstallTitle",
    sights: "helpSightsTitle",
    camouflages: "helpCamoTitle",
    language: "helpLanguageTitle",
    reset: "helpResetTitle"
};

const guideDescKeys = {
    install: "helpInstallDesc",
    sights: "helpSightsDesc",
    camouflages: "helpCamoDesc",
    language: "helpLanguageDesc",
    reset: "helpResetDesc"
};

let currentLanguage = "en";
let siteConfig = {};

// Translation helper.

function tr(key) {
    return translations[currentLanguage][key]
        ?? translations.en[key]
        ?? key;
}

// Only allow expected external hosts for download/donation links.

function approvedUrl(raw, kind) {
    if (typeof raw !== "string" || !raw.trim()) {
        return "";
    }

    try {
        const url = new URL(raw);

        if (url.protocol !== "https:") {
            return "";
        }

        if (url.username || url.password) {
            return "";
        }

        const host = url.hostname.toLowerCase();

        if (kind === "monobank" && host !== "send.monobank.ua") {
            return "";
        }

        if (kind === "github" && host !== "github.com") {
            return "";
        }

        return url.href;
    } catch {
        return "";
    }
}

function activateLink(element, url) {
    if (!element || !url) {
        return false;
    }

    element.href = url;
    element.classList.remove("disabled");
    element.removeAttribute("aria-disabled");
    element.removeAttribute("tabindex");

    return true;
}

// Main language system.

function renderLanguage(nextLanguage) {
    currentLanguage = Object.prototype.hasOwnProperty.call(
        translations,
        nextLanguage
    ) ? nextLanguage : "en";

    document.documentElement.lang = currentLanguage;

    const selected = document.getElementById("selectedLanguage");

    if (selected) {
        selected.textContent = languageLabels[currentLanguage];
    }

    document.querySelectorAll("[data-i18n]").forEach(element => {
        const key = element.dataset.i18n;
        const value = tr(key);

        if (key === "headline") {
            // Trusted markup from our local translations.
            element.innerHTML = value;
        } else {
            element.textContent = value;
        }
    });

    document.querySelectorAll(".lang-option").forEach(button => {
        const active = button.dataset.lang === currentLanguage;
        button.classList.toggle("selected", active);
        button.setAttribute("aria-pressed", String(active));
    });

    const search = document.getElementById("helpSearch");

    if (search) {
        search.placeholder = tr("helpSearchPlaceholder");
        search.setAttribute("aria-label", tr("helpSearchPlaceholder"));
    }

    const backToTop = document.getElementById("backToTop");

    const backTitles = {
        en: "Back to top",
        ru: "Наверх",
        uk: "Нагору"
    };

    if (backToTop) {
        backToTop.title = backTitles[currentLanguage];
        backToTop.setAttribute(
            "aria-label",
            backTitles[currentLanguage]
        );
    }

    const closeGuide = document.getElementById("closeGuide");

    const closeTitles = {
        en: "Close guide",
        ru: "Закрыть инструкцию",
        uk: "Закрити інструкцію"
    };

    if (closeGuide) {
        closeGuide.setAttribute(
            "aria-label",
            closeTitles[currentLanguage]
        );
    }

    try {
        localStorage.setItem("wtmm-language", currentLanguage);
    } catch {
        // Site can still work if localStorage is disabled.
    }

    updateStatuses();
    searchHelp();

    const panel = document.getElementById("guidePanel");

    if (
        panel &&
        !panel.classList.contains("hidden") &&
        panel.dataset.guide
    ) {
        showGuide(panel.dataset.guide, false);
    }
}

function setupLanguageMenu() {
    const toggle = document.getElementById("languageToggle");
    const menu = document.getElementById("languageMenu");

    if (!toggle || !menu) {
        return;
    }

    const options = [...menu.querySelectorAll(".lang-option")];

    function setOpen(open) {
        menu.hidden = !open;
        toggle.classList.toggle("open", open);
        toggle.setAttribute("aria-expanded", String(open));

        if (open) {
            const selected = options.find(
                option => option.dataset.lang === currentLanguage
            );

            (selected || options[0])?.focus();
        }
    }

    toggle.addEventListener("click", () => {
        setOpen(menu.hidden);
    });

    options.forEach((option, index) => {
        option.addEventListener("click", () => {
            renderLanguage(option.dataset.lang);
            setOpen(false);
            toggle.focus();
        });

        option.addEventListener("keydown", event => {
            if (
                event.key === "ArrowDown" ||
                event.key === "ArrowUp"
            ) {
                event.preventDefault();

                const direction =
                    event.key === "ArrowDown" ? 1 : -1;

                const next =
                    (index + direction + options.length) %
                    options.length;

                options[next].focus();
            }

            if (event.key === "Escape") {
                setOpen(false);
                toggle.focus();
            }
        });
    });

    document.addEventListener("click", event => {
        if (!event.target.closest(".lang-wrap")) {
            setOpen(false);
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !menu.hidden) {
            setOpen(false);
            toggle.focus();
        }
    });
}

// Help center search.

function searchHelp() {
    const search = document.getElementById("helpSearch");

    if (!search) {
        return;
    }

    const query = search.value.trim().toLocaleLowerCase();
    let visibleCount = 0;

    document.querySelectorAll(".help-card").forEach(card => {
        const key = card.dataset.help;

        if (!guideTitleKeys[key] || !guides[currentLanguage][key]) {
            return;
        }

        const content = [
            tr(guideTitleKeys[key]),
            tr(guideDescKeys[key]),
            guides[currentLanguage][key].join(" "),
            key
        ].join(" ").toLocaleLowerCase();

        const matches = !query || content.includes(query);

        card.hidden = !matches;

        if (matches) {
            visibleCount++;
        }
    });

    const empty = document.getElementById("helpEmpty");

    if (empty) {
        empty.classList.toggle("hidden", visibleCount > 0);
    }
}

function showGuide(key, focusPanel = true) {
    const steps = guides[currentLanguage][key];

    if (!steps) {
        return;
    }

    const panel = document.getElementById("guidePanel");
    const content = document.getElementById("guideContent");
    const title = document.getElementById("guideTitle");

    if (!panel || !content || !title) {
        return;
    }

    panel.dataset.guide = key;
    title.textContent = tr(guideTitleKeys[key]);

    content.replaceChildren();

    const list = document.createElement("ol");

    steps.forEach(step => {
        const item = document.createElement("li");
        item.textContent = step;
        list.appendChild(item);
    });

    content.appendChild(list);
    panel.classList.remove("hidden");

    if (focusPanel) {
        panel.scrollIntoView({
            behavior: window.matchMedia(
                "(prefers-reduced-motion: reduce)"
            ).matches ? "auto" : "smooth",
            block: "center"
        });

        panel.focus({ preventScroll: true });
    }
}

function setupHelpCenter() {
    const search = document.getElementById("helpSearch");
    const panel = document.getElementById("guidePanel");
    const closeButton = document.getElementById("closeGuide");

    if (!search || !panel || !closeButton) {
        return;
    }

    search.addEventListener("input", searchHelp);

    document.querySelectorAll(".help-open").forEach(button => {
        button.addEventListener("click", () => {
            panel.dataset.lastOpener = button.dataset.guide;
            showGuide(button.dataset.guide);
        });
    });

    closeButton.addEventListener("click", () => {
        const openerKey = panel.dataset.lastOpener;

        panel.classList.add("hidden");
        delete panel.dataset.guide;

        const opener = openerKey
            ? document.querySelector(
                `.help-open[data-guide="${openerKey}"]`
            )
            : null;

        if (opener) {
            opener.focus({ preventScroll: true });
        }
    });
}

// Scroll progress and Back to Top.

function setupScrollFeatures() {
    const progress = document.getElementById(
        "scrollProgressFill"
    );

    const backToTop = document.getElementById(
        "backToTop"
    );

    if (!progress || !backToTop) {
        return;
    }

    let scheduled = false;

    function update() {
        const maxScroll =
            document.documentElement.scrollHeight -
            window.innerHeight;

        const fraction = maxScroll > 0
            ? Math.max(
                0,
                Math.min(1, window.scrollY / maxScroll)
            )
            : 0;

        progress.style.transform = `scaleX(${fraction})`;

        const visible = window.scrollY > 450;

        backToTop.classList.toggle("visible", visible);
        backToTop.tabIndex = visible ? 0 : -1;

        scheduled = false;
    }

    function scheduleUpdate() {
        if (scheduled) {
            return;
        }

        scheduled = true;
        requestAnimationFrame(update);
    }

    window.addEventListener(
        "scroll",
        scheduleUpdate,
        { passive: true }
    );

    window.addEventListener(
        "resize",
        scheduleUpdate
    );

    backToTop.addEventListener("click", () => {
        const reducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        window.scrollTo({
            top: 0,
            behavior: reducedMotion ? "auto" : "smooth"
        });
    });

    update();
}

// Reveal-on-scroll animations.

function setupRevealAnimations() {
    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    if (
        reducedMotion ||
        !("IntersectionObserver" in window)
    ) {
        return;
    }

    document.documentElement.classList.add("js");

    const observer = new IntersectionObserver(
        entries => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) {
                    return;
                }

                entry.target.classList.add("revealed");
                observer.unobserve(entry.target);
            });
        },
        {
            threshold: 0.08,
            rootMargin: "0px 0px 25px 0px"
        }
    );

    document.querySelectorAll(".reveal").forEach(element => {
        observer.observe(element);
    });
}

// Download and monobank links.

function updateStatuses() {
    const downloadUrl = approvedUrl(
        siteConfig.download_url,
        "github"
    );

    const supportUrl = approvedUrl(
        siteConfig.monobank_url,
        "monobank"
    );

    const downloadStatus = document.getElementById(
        "downloadStatus"
    );

    const supportStatus = document.getElementById(
        "supportStatus"
    );

    if (downloadStatus) {
        downloadStatus.textContent = downloadUrl
            ? tr("downloadReady")
            : tr("downloadSoon");
    }

    if (supportStatus) {
        supportStatus.textContent = supportUrl
            ? tr("supportReady")
            : tr("supportSoon");
    }
}

async function loadSiteConfig() {
    try {
        const response = await fetch(
            "json/site-config.json",
            { cache: "no-store", signal: AbortSignal.timeout(8000) }
        );

        if (!response.ok) {
            throw new Error(
                "Could not load site-config.json"
            );
        }

        siteConfig = await response.json();
    } catch (error) {
        console.warn(
            "Site configuration unavailable:",
            error
        );

        siteConfig = {};
    }

    activateLink(
        document.getElementById("downloadBtn"),
        approvedUrl(siteConfig.download_url, "github")
    );

    activateLink(
        document.getElementById("donateBtn"),
        approvedUrl(siteConfig.monobank_url, "monobank")
    );

    const releasesUrl = approvedUrl(
        siteConfig.releases_url,
        "github"
    );

    if (releasesUrl) {
        const releaseNotes = document.getElementById(
            "releaseNotes"
        );

        if (releaseNotes) {
            releaseNotes.href = releasesUrl;
            releaseNotes.classList.remove("hidden");
        }
    }

    updateStatuses();
}

// Support Center links.
// They open our own page, not GitHub Issues.

function setupSupportLinks() {
    const bugLink = document.getElementById(
        "bugReportLink"
    );

    const ideaLink = document.getElementById(
        "featureRequestLink"
    );

    if (bugLink) {
        bugLink.href = "support/support.html?type=bug";
        bugLink.removeAttribute("target");
    }

    if (ideaLink) {
        ideaLink.href = "support/support.html?type=idea";
        ideaLink.removeAttribute("target");
    }
}

// Remember the selected language.

function detectInitialLanguage() {
    try {
        const stored = localStorage.getItem(
            "wtmm-language"
        );

        if (
            stored &&
            Object.prototype.hasOwnProperty.call(
                translations,
                stored
            )
        ) {
            return stored;
        }
    } catch {
        // Storage may be unavailable.
    }

    const browserLang = (
        navigator.language || "en"
    ).toLowerCase();

    if (browserLang.startsWith("uk")) {
        return "uk";
    }

    if (browserLang.startsWith("ru")) {
        return "ru";
    }

    return "en";
}

// Initialization.

async function init() {
    const year = document.getElementById("year");

    if (year) {
        year.textContent = String(
            new Date().getFullYear()
        );
    }

    setupLanguageMenu();
    setupHelpCenter();
    setupScrollFeatures();
    setupSupportLinks();

    renderLanguage(detectInitialLanguage());
    setupRevealAnimations();

    await loadSiteConfig();
}

document.addEventListener("DOMContentLoaded", init);