
"use strict";

// WT Mod Manager Support Center
// Stage 1: Formspree, field help, modal, developer contact
// Languages: EN / RU / UA

const texts = {
    en: {
        home: "← Home",
        eyebrow: "COMMUNITY SUPPORT",
        title: "How can we help?",
        subtitle: "Report a problem or share an idea for WT Mod Manager. No GitHub account required.",
        category: "Request type",
        bugTab: "Report a bug",
        bugTabDesc: "Something isn't working",
        ideaTab: "Suggest a feature",
        ideaTabDesc: "Help improve the app",
        privacy: "Do not send passwords, access tokens, personal documents or private files.",
        overline: "NEW REQUEST",
        bugTitle: "Report a problem",
        bugDescription: "Tell us what happened. More details help us investigate.",
        ideaTitle: "Suggest a new feature",
        ideaDescription: "Share your idea and explain why it would help players.",
        name: "Name or nickname",
        email: "Email for a reply",
        problemTitle: "Problem title",
        ideaSubject: "Idea title",
        version: "Application version (optional)",
        bugMessage: "Describe the problem",
        ideaMessage: "Describe your idea",
        messageHint: "Please include enough details.",
        bugSteps: "What did you do before the problem appeared? (optional)",
        ideaSteps: "How would this help players? (optional)",
        bugStepsNote: "Describe your actions in order, if possible.",
        ideaStepsNote: "Explain how the new feature would be useful.",
        reference: "Screenshot or reference URL (optional)",
        readyNote: "Your request will be sent to the developer. We can reply to the email address you provided.",
        setupNote: "Sending is not configured yet. The form is available for preview.",
        send: "Send request",
        sending: "Sending...",
        success: "Your request was sent successfully. Thank you!",
        error: "The request could not be sent. Please try again later.",
        invalid: "Please check the required fields and enter a valid email address.",
        notReady: "The support service has not been connected yet.",
        mainHelp: "How to complete the form?",
        modalOverline: "SUPPORT GUIDE",
        modalExample: "EXAMPLE",
        modalDone: "Got it",
        modalClose: "Close help",
        contactOverline: "DIRECT CONTACT",
        contactTitle: "Contact the developer",
        contactDescription: "You can send the form above or write directly to the developer. Sending the form does not require entering our email manually.",
        developerEmailLabel: "DEVELOPER EMAIL",
        copyEmail: "Copy email",
        writeEmail: "Write an email",
        copied: "Email address copied.",
        copyFailed: "Could not copy automatically. Select and copy the address above.",
        privacyFooter: "Independent fan-made project. Not affiliated with Gaijin Entertainment."
    },

    ru: {
        home: "← На главную",
        eyebrow: "ПОДДЕРЖКА СООБЩЕСТВА",
        title: "Чем мы можем помочь?",
        subtitle: "Сообщи об ошибке или предложи новую функцию WT Mod Manager. Аккаунт GitHub не нужен.",
        category: "Тип обращения",
        bugTab: "Сообщить об ошибке",
        bugTabDesc: "Что-то работает неправильно",
        ideaTab: "Предложить функцию",
        ideaTabDesc: "Помоги улучшить приложение",
        privacy: "Не отправляй пароли, токены доступа, личные документы и приватные файлы.",
        overline: "НОВОЕ ОБРАЩЕНИЕ",
        bugTitle: "Сообщить о проблеме",
        bugDescription: "Опиши, что произошло. Подробности помогут разобраться в ошибке.",
        ideaTitle: "Предложить новую функцию",
        ideaDescription: "Расскажи о своей идее и о том, чем она будет полезна игрокам.",
        name: "Имя или никнейм",
        email: "Email для ответа",
        problemTitle: "Название проблемы",
        ideaSubject: "Название идеи",
        version: "Версия программы (необязательно)",
        bugMessage: "Опиши проблему",
        ideaMessage: "Опиши свою идею",
        messageHint: "Пожалуйста, добавь достаточно подробностей.",
        bugSteps: "Что вы делали перед появлением ошибки? (необязательно)",
        ideaSteps: "Чем это поможет игрокам? (необязательно)",
        bugStepsNote: "По возможности опиши свои действия по порядку.",
        ideaStepsNote: "Объясни, как новая функция будет использоваться.",
        reference: "Ссылка на скриншот или пример (необязательно)",
        readyNote: "Обращение будет отправлено разработчику. Мы сможем ответить на указанный email.",
        setupNote: "Отправка пока не настроена. Сейчас форму можно просмотреть.",
        send: "Отправить обращение",
        sending: "Отправка...",
        success: "Обращение успешно отправлено. Спасибо!",
        error: "Не удалось отправить обращение. Попробуй позже.",
        invalid: "Проверь обязательные поля и правильность email.",
        notReady: "Сервис поддержки ещё не подключён.",
        mainHelp: "Как правильно заполнить форму?",
        modalOverline: "СПРАВКА ПО ЗАПОЛНЕНИЮ",
        modalExample: "ПРИМЕР ЗАПОЛНЕНИЯ",
        modalDone: "Понятно",
        modalClose: "Закрыть подсказку",
        contactOverline: "ПРЯМАЯ СВЯЗЬ",
        contactTitle: "Связаться с разработчиком",
        contactDescription: "Ты можешь отправить обращение через форму выше или написать разработчику напрямую. При отправке формы вводить наш email вручную не нужно.",
        developerEmailLabel: "EMAIL РАЗРАБОТЧИКА",
        copyEmail: "Скопировать email",
        writeEmail: "Написать письмо",
        copied: "Email скопирован.",
        copyFailed: "Не удалось скопировать автоматически. Выдели и скопируй адрес выше.",
        privacyFooter: "Независимый фанатский проект. Не связан с Gaijin Entertainment."
    },

    uk: {
        home: "← На головну",
        eyebrow: "ПІДТРИМКА СПІЛЬНОТИ",
        title: "Чим ми можемо допомогти?",
        subtitle: "Повідом про помилку або запропонуй нову функцію WT Mod Manager. Обліковий запис GitHub не потрібен.",
        category: "Тип звернення",
        bugTab: "Повідомити про помилку",
        bugTabDesc: "Щось працює неправильно",
        ideaTab: "Запропонувати функцію",
        ideaTabDesc: "Допоможи покращити програму",
        privacy: "Не надсилай паролі, токени доступу, особисті документи та приватні файли.",
        overline: "НОВЕ ЗВЕРНЕННЯ",
        bugTitle: "Повідомити про проблему",
        bugDescription: "Опиши, що сталося. Подробиці допоможуть дослідити помилку.",
        ideaTitle: "Запропонувати нову функцію",
        ideaDescription: "Розкажи про свою ідею та її користь для гравців.",
        name: "Ім'я або нікнейм",
        email: "Email для відповіді",
        problemTitle: "Назва проблеми",
        ideaSubject: "Назва ідеї",
        version: "Версія програми (необов'язково)",
        bugMessage: "Опиши проблему",
        ideaMessage: "Опиши свою ідею",
        messageHint: "Будь ласка, додай достатньо подробиць.",
        bugSteps: "Що ви робили перед появою помилки? (необов'язково)",
        ideaSteps: "Чим це допоможе гравцям? (необов'язково)",
        bugStepsNote: "За можливості опиши свої дії по черзі.",
        ideaStepsNote: "Поясни, як буде використовуватися нова функція.",
        reference: "Посилання на знімок екрана або приклад (необов'язково)",
        readyNote: "Звернення буде надіслано розробнику. Ми зможемо відповісти на зазначений email.",
        setupNote: "Надсилання ще не налаштовано. Зараз форму можна переглянути.",
        send: "Надіслати звернення",
        sending: "Надсилання...",
        success: "Звернення успішно надіслано. Дякуємо!",
        error: "Не вдалося надіслати звернення. Спробуй пізніше.",
        invalid: "Перевір обов'язкові поля та правильність email.",
        notReady: "Сервіс підтримки ще не підключений.",
        mainHelp: "Як правильно заповнити форму?",
        modalOverline: "ДОВІДКА ЩОДО ЗАПОВНЕННЯ",
        modalExample: "ПРИКЛАД ЗАПОВНЕННЯ",
        modalDone: "Зрозуміло",
        modalClose: "Закрити підказку",
        contactOverline: "ПРЯМИЙ ЗВ'ЯЗОК",
        contactTitle: "Зв'язатися з розробником",
        contactDescription: "Ти можеш надіслати звернення через форму вище або написати розробнику напряму. Під час надсилання форми вводити наш email вручну не потрібно.",
        developerEmailLabel: "EMAIL РОЗРОБНИКА",
        copyEmail: "Скопіювати email",
        writeEmail: "Написати листа",
        copied: "Email скопійовано.",
        copyFailed: "Не вдалося скопіювати автоматично. Виділи та скопіюй адресу вище.",
        privacyFooter: "Незалежний фанатський проєкт. Не пов'язаний із Gaijin Entertainment."
    }
};

// Detailed explanation for every form field.
// Each entry: title, description, example, additional note.

const helpTexts = {
    en: {
        overview: {
            title: "How to send a request",
            description:
                "1. Select Report a bug if something is broken, or Suggest a feature if you have an idea.\n\n" +
                "2. Enter your nickname and a working email address.\n\n" +
                "3. Write a short title and a clear description.\n\n" +
                "4. If possible, provide the app version, steps and a screenshot link.\n\n" +
                "5. Click Send request. Your message will be delivered through Formspree.",
            example:
                "Type: Report a bug\n" +
                "Title: Settings window freezes\n" +
                "Description: The app stops responding when I select a theme.",
            extra:
                "You do not need a GitHub account. Fields marked optional may be left empty."
        },
        name: {
            title: "Name or nickname",
            description:
                "This is how the developer can address you when replying. You may use your gaming nickname instead of your real name.",
            example: "Player_123",
            extra: "Do not enter your password or other private information."
        },
        email: {
            title: "Email for a reply",
            description:
                "Enter your own working email address. The developer can use it to respond to your request and ask for extra details.",
            example: "player@example.com",
            extra:
                "This is your email, not the developer's. The form automatically sends your message to the support service."
        },
        bugTitle: {
            title: "Problem title",
            description:
                "Summarize what is not working in a few words. A clear title makes the report easier to understand.",
            example: "App freezes when opening Settings",
            extra: "Avoid vague titles such as 'Help' or 'Does not work'."
        },
        ideaTitle: {
            title: "Idea title",
            description:
                "Give your suggested feature a short, descriptive name.",
            example: "Add a search bar for camouflages",
            extra: "The title should help the developer understand the idea at a glance."
        },
        version: {
            title: "Application version",
            description:
                "Enter the version of WT Mod Manager you are using. It helps the developer determine which release has the issue. You can check the version displayed by the app.",
            example: "Beta 1.2",
            extra: "If you cannot find the version, leave this field empty."
        },
        bugMessage: {
            title: "Describe the problem",
            description:
                "Explain what you expected the app to do and what actually happened. Mention the affected section and any visible error messages.",
            example:
                "I open Settings and select Dark Theme. I expect the theme to change, but the window stops responding.",
            extra:
                "Please avoid including passwords, private files or secret keys."
        },
        ideaMessage: {
            title: "Describe your idea",
            description:
                "Explain what you would like to add, where it should appear and how it should work.",
            example:
                "I would like a search field in the Camouflages section so I can find items by name without scrolling.",
            extra:
                "Describe the feature in your own words. Technical knowledge is not required."
        },
        bugSteps: {
            title: "What did you do before the problem appeared?",
            description:
                "List the actions that caused the problem in order. This helps the developer try the same actions and find the cause.",
            example:
                "1. Open WT Mod Manager.\n" +
                "2. Go to Settings.\n" +
                "3. Open the theme selector.\n" +
                "4. Select Dark Theme.\n" +
                "5. The window stops responding.",
            extra:
                "This field is optional. If the problem happens randomly, describe what you remember."
        },
        ideaSteps: {
            title: "How would this feature help?",
            description:
                "Explain what players could do with the new feature and why it would be useful.",
            example:
                "Players could quickly find a specific camouflage in a large collection instead of browsing the entire list.",
            extra:
                "This field is optional but helps us prioritize useful improvements."
        },
        reference: {
            title: "Screenshot or reference URL",
            description:
                "If you have a screenshot or an example hosted online, paste a link to it. Images can help explain bugs and design ideas.",
            example: "https://example.com/my-screenshot.png",
            extra:
                "This field accepts a URL, not a file upload. Check that the link does not reveal private information."
        }
    },

    ru: {
        overview: {
            title: "Как отправить обращение",
            description:
                "1. Выбери «Сообщить об ошибке», если программа работает неправильно, или «Предложить функцию», если у тебя есть идея.\n\n" +
                "2. Укажи никнейм и работающий email.\n\n" +
                "3. Придумай короткое название и подробно опиши обращение.\n\n" +
                "4. По возможности добавь версию программы, последовательность действий и ссылку на скриншот.\n\n" +
                "5. Нажми «Отправить обращение». Сообщение будет передано через Formspree.",
            example:
                "Тип: Сообщить об ошибке\n" +
                "Название: Программа зависает в настройках\n" +
                "Описание: При выборе темы окно перестаёт отвечать.",
            extra:
                "Аккаунт GitHub не нужен. Необязательные поля можно оставить пустыми."
        },
        name: {
            title: "Имя или никнейм",
            description:
                "Напиши, как разработчик может к тебе обращаться. Можно указать игровой никнейм — настоящее имя необязательно.",
            example: "Player_123",
            extra:
                "Не вводи пароль от аккаунта и другие личные данные."
        },
        email: {
            title: "Email для ответа",
            description:
                "Укажи свой действующий адрес электронной почты. Разработчик сможет ответить на обращение или попросить дополнительную информацию.",
            example: "player@example.com",
            extra:
                "Здесь нужен именно твой email, а не email разработчика. Форма сама отправит сообщение в службу поддержки."
        },
        bugTitle: {
            title: "Название проблемы",
            description:
                "Коротко напиши, что именно не работает. По названию разработчик должен примерно понять суть ошибки.",
            example: "Программа зависает при открытии настроек",
            extra:
                "Лучше не писать просто «Помогите» или «Ничего не работает»."
        },
        ideaTitle: {
            title: "Название идеи",
            description:
                "Дай новой функции короткое и понятное название.",
            example: "Поиск камуфляжей по названию",
            extra:
                "По названию должно быть понятно, что именно ты предлагаешь добавить."
        },
        version: {
            title: "Версия программы",
            description:
                "Укажи версию WT Mod Manager, в которой возникла ошибка. Это поможет определить, какой выпуск программы нужно проверить. Версию можно посмотреть в самом приложении.",
            example: "Beta 1.2",
            extra:
                "Если не знаешь версию, оставь поле пустым."
        },
        bugMessage: {
            title: "Описание проблемы",
            description:
                "Подробно расскажи, что должно было произойти и что произошло на самом деле. Укажи раздел программы и текст ошибки, если он появился.",
            example:
                "Открываю настройки и выбираю тёмную тему. Ожидаю, что оформление изменится, но вместо этого окно перестаёт реагировать.",
            extra:
                "Не добавляй пароли, секретные ключи и приватные файлы."
        },
        ideaMessage: {
            title: "Описание новой функции",
            description:
                "Объясни, какую функцию хочешь добавить, где она должна находиться и как работать.",
            example:
                "Хочу добавить строку поиска в раздел «Камуфляжи», чтобы можно было находить нужный камуфляж по названию.",
            extra:
                "Необязательно разбираться в программировании. Просто опиши свою задумку."
        },
        bugSteps: {
            title: "Что вы делали перед появлением ошибки?",
            description:
                "Здесь нужно по порядку перечислить действия, после которых появилась ошибка. Так разработчик сможет попробовать повторить проблему и найти её причину.",
            example:
                "1. Запустил WT Mod Manager.\n" +
                "2. Открыл «Настройки».\n" +
                "3. Перешёл к выбору темы.\n" +
                "4. Нажал «Тёмная тема».\n" +
                "5. Программа перестала реагировать.",
            extra:
                "Поле необязательное. Если ошибка появляется случайно, опиши то, что помнишь."
        },
        ideaSteps: {
            title: "Чем новая функция поможет игрокам?",
            description:
                "Расскажи, для чего нужна предложенная функция и какую проблему она решит.",
            example:
                "Игроки смогут быстро находить определённый камуфляж среди большого количества файлов, не просматривая весь список.",
            extra:
                "Это необязательное поле, но оно поможет понять пользу твоей идеи."
        },
        reference: {
            title: "Ссылка на скриншот или пример",
            description:
                "Если у тебя есть скриншот ошибки или изображение с примером новой функции, можешь разместить его в интернете и вставить сюда ссылку.",
            example: "https://example.com/my-screenshot.png",
            extra:
                "Здесь нужна ссылка, а не сам файл. Не используй ссылки, открывающие доступ к личным данным."
        }
    },

    uk: {
        overview: {
            title: "Як надіслати звернення",
            description:
                "1. Вибери «Повідомити про помилку», якщо програма працює неправильно, або «Запропонувати функцію», якщо маєш ідею.\n\n" +
                "2. Вкажи нікнейм і робочу email-адресу.\n\n" +
                "3. Напиши коротку назву та докладний опис.\n\n" +
                "4. За можливості додай версію програми, послідовність дій і посилання на знімок екрана.\n\n" +
                "5. Натисни «Надіслати звернення». Повідомлення буде передано через Formspree.",
            example:
                "Тип: Повідомити про помилку\n" +
                "Назва: Програма зависає в налаштуваннях\n" +
                "Опис: Під час вибору теми вікно перестає відповідати.",
            extra:
                "Обліковий запис GitHub не потрібен. Необов'язкові поля можна залишити порожніми."
        },
        name: {
            title: "Ім'я або нікнейм",
            description:
                "Напиши, як розробник може до тебе звертатися. Можна вказати ігровий нікнейм замість справжнього імені.",
            example: "Player_123",
            extra:
                "Не вводь пароль від облікового запису та інші особисті дані."
        },
        email: {
            title: "Email для відповіді",
            description:
                "Вкажи свою дійсну адресу електронної пошти. Розробник зможе відповісти на звернення або уточнити подробиці.",
            example: "player@example.com",
            extra:
                "Потрібна саме твоя адреса, а не email розробника. Форма сама надішле повідомлення службі підтримки."
        },
        bugTitle: {
            title: "Назва проблеми",
            description:
                "Коротко напиши, що саме не працює. Назва має допомогти розробнику зрозуміти суть помилки.",
            example: "Програма зависає під час відкриття налаштувань",
            extra:
                "Краще не використовувати загальні назви на кшталт «Допоможіть»."
        },
        ideaTitle: {
            title: "Назва ідеї",
            description:
                "Дай новій функції коротку та зрозумілу назву.",
            example: "Пошук камуфляжів за назвою",
            extra:
                "Із назви має бути зрозуміло, що саме пропонується додати."
        },
        version: {
            title: "Версія програми",
            description:
                "Вкажи версію WT Mod Manager, у якій виникла помилка. Це допоможе розробнику визначити потрібний випуск. Версію можна переглянути в самій програмі.",
            example: "Beta 1.2",
            extra:
                "Якщо не знаєш версію, залиш поле порожнім."
        },
        bugMessage: {
            title: "Опис проблеми",
            description:
                "Розкажи, що мало статися і що відбулося насправді. Вкажи розділ програми та текст помилки, якщо він з'явився.",
            example:
                "Відкриваю налаштування та вибираю темну тему. Очікую зміни оформлення, але вікно перестає реагувати.",
            extra:
                "Не додавай паролі, секретні ключі та приватні файли."
        },
        ideaMessage: {
            title: "Опис нової функції",
            description:
                "Поясни, яку функцію хочеш додати, де вона повинна бути та як працювати.",
            example:
                "Хочу додати пошуковий рядок до розділу «Камуфляжі», щоб знаходити потрібний камуфляж за назвою.",
            extra:
                "Необов'язково розбиратися в програмуванні. Просто опиши свою ідею."
        },
        bugSteps: {
            title: "Що ви робили перед появою помилки?",
            description:
                "Перелічи дії, після яких з'явилася помилка, у правильному порядку. Це допоможе розробнику спробувати відтворити проблему.",
            example:
                "1. Запустив WT Mod Manager.\n" +
                "2. Відкрив «Налаштування».\n" +
                "3. Перейшов до вибору теми.\n" +
                "4. Натиснув «Темна тема».\n" +
                "5. Програма перестала реагувати.",
            extra:
                "Поле необов'язкове. Якщо помилка виникає випадково, опиши те, що пам'ятаєш."
        },
        ideaSteps: {
            title: "Чим нова функція допоможе гравцям?",
            description:
                "Розкажи, для чого потрібна функція і яку проблему вона вирішить.",
            example:
                "Гравці зможуть швидко знаходити певний камуфляж серед великої кількості файлів, не переглядаючи весь список.",
            extra:
                "Це необов'язкове поле, але воно допоможе зрозуміти користь ідеї."
        },
        reference: {
            title: "Посилання на знімок екрана або приклад",
            description:
                "Якщо маєш знімок екрана з помилкою або приклад нової функції, можеш розмістити його в інтернеті та додати сюди посилання.",
            example: "https://example.com/my-screenshot.png",
            extra:
                "У цьому полі потрібне посилання, а не файл. Не надсилай посилання на особисті дані."
        }
    }
};

// DOM and application state.

const form = document.getElementById("supportForm");
const statusElement = document.getElementById("formStatus");
const submitButton = document.getElementById("submitRequest");

let currentLanguage = "en";
let requestKind = "bug";
let formspreeId = "";
let developerEmail = "";
let submitting = false;

let activeHelpKey = null;
let helpOpener = null;

function byId(id) {
    return document.getElementById(id);
}

function translate(key) {
    return texts[currentLanguage][key]
        ?? texts.en[key]
        ?? key;
}

function setText(id, key) {
    const element = byId(id);

    if (element) {
        element.textContent = translate(key);
    }
}

function setStatus(message, type = "") {
    statusElement.textContent = message;
    statusElement.className = "form-status";

    if (type) {
        statusElement.classList.add(type);
    }
}

// Modal help system.

function resolveHelpKey(key) {
    if (key === "title") {
        return requestKind === "bug" ? "bugTitle" : "ideaTitle";
    }

    if (key === "message") {
        return requestKind === "bug" ? "bugMessage" : "ideaMessage";
    }

    if (key === "steps") {
        return requestKind === "bug" ? "bugSteps" : "ideaSteps";
    }

    return key;
}

function renderHelpContent() {
    if (!activeHelpKey) {
        return;
    }

    const resolved = resolveHelpKey(activeHelpKey);

    const help =
        helpTexts[currentLanguage][resolved] ??
        helpTexts.en[resolved];

    if (!help) {
        return;
    }

    byId("helpDialogOverline").textContent =
        translate("modalOverline");

    byId("helpDialogTitle").textContent = help.title;
    byId("helpDialogDescription").textContent = help.description;
    byId("helpExampleLabel").textContent = translate("modalExample");
    byId("helpExampleText").textContent = help.example;
    byId("helpExtraText").textContent = help.extra;

    byId("helpDialogDone").textContent = translate("modalDone");

    byId("closeHelpDialog").setAttribute(
        "aria-label",
        translate("modalClose")
    );
}

function getModalFocusableElements() {
    return [
        ...byId("helpDialog").querySelectorAll(
            'button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
    ].filter(element => element.getClientRects().length > 0);
}

function openHelp(key, opener) {
    activeHelpKey = key;
    helpOpener = opener;

    renderHelpContent();

    byId("helpOverlay").hidden = false;
    document.body.classList.add("help-dialog-open");

    // Prevent keyboard navigation into the form.
    byId("helpDialog").focus();
}

function closeHelp() {
    const overlay = byId("helpOverlay");

    if (overlay.hidden) {
        return;
    }

    overlay.hidden = true;
    document.body.classList.remove("help-dialog-open");

    activeHelpKey = null;

    if (helpOpener && helpOpener.isConnected) {
        helpOpener.focus();
    }

    helpOpener = null;
}

function setupHelpModal() {
    document.querySelectorAll("[data-help]").forEach(button => {
        button.addEventListener("click", () => {
            openHelp(button.dataset.help, button);
        });
    });

    byId("closeHelpDialog").addEventListener("click", closeHelp);
    byId("helpDialogDone").addEventListener("click", closeHelp);

    byId("helpOverlay").addEventListener("click", event => {
        if (event.target === byId("helpOverlay")) {
            closeHelp();
        }
    });

    document.addEventListener("keydown", event => {
        if (byId("helpOverlay").hidden) {
            return;
        }

        if (event.key === "Escape") {
            event.preventDefault();
            closeHelp();
            return;
        }

        if (event.key !== "Tab") {
            return;
        }

        const focusable = getModalFocusableElements();

        if (!focusable.length) {
            event.preventDefault();
            byId("helpDialog").focus();
            return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const current = document.activeElement;

        if (event.shiftKey) {
            if (current === first || !focusable.includes(current)) {
                event.preventDefault();
                last.focus();
            }
        } else if (current === last || !focusable.includes(current)) {
            event.preventDefault();
            first.focus();
        }
    });
}

// Language switching.

function applyLanguage(language) {
    currentLanguage = Object.prototype.hasOwnProperty.call(
        texts,
        language
    ) ? language : "en";

    document.documentElement.lang = currentLanguage;

    const languageLabels = {
        en: "EN",
        ru: "RU",
        uk: "UA"
    };

    byId("supportLanguageLabel").textContent =
        languageLabels[currentLanguage];

    const sharedFields = {
        homeLink: "home",
        supportEyebrow: "eyebrow",
        supportTitle: "title",
        supportSubtitle: "subtitle",
        categoryTitle: "category",
        bugTabTitle: "bugTab",
        bugTabDesc: "bugTabDesc",
        ideaTabTitle: "ideaTab",
        ideaTabDesc: "ideaTabDesc",
        privacyNote: "privacy",
        formOverline: "overline",
        nameLabel: "name",
        emailLabel: "email",
        versionLabel: "version",
        messageHint: "messageHint",
        referenceLabel: "reference",
        mainHelpLabel: "mainHelp",
        contactOverline: "contactOverline",
        contactTitle: "contactTitle",
        contactDescription: "contactDescription",
        emailAddressLabel: "developerEmailLabel",
        copyEmailLabel: "copyEmail",
        writeEmailLabel: "writeEmail",
        footerDisclaimer: "privacyFooter"
    };

    Object.entries(sharedFields).forEach(([id, key]) => {
        setText(id, key);
    });

    document.querySelectorAll(".lang-option").forEach(button => {
        const selected =
            button.dataset.lang === currentLanguage;

        button.classList.toggle("selected", selected);
        button.setAttribute("aria-pressed", String(selected));
    });

    const languageLabelsAria = {
        en: "Choose language",
        ru: "Выбрать язык",
        uk: "Вибрати мову"
    };

    byId("supportLanguageToggle").setAttribute(
        "aria-label",
        languageLabelsAria[currentLanguage]
    );

    document.querySelectorAll(".field-help").forEach(button => {
        const helpKey = resolveHelpKey(button.dataset.help);
        const definition = helpTexts[currentLanguage][helpKey];

        if (definition) {
            button.setAttribute(
                "aria-label",
                definition.title
            );
            button.title = definition.title;
        }
    });

    applyRequestKind(requestKind, false);
    renderHelpContent();

    byId("emailCopyStatus").textContent = "";

    try {
        localStorage.setItem("wtmm-language", currentLanguage);
    } catch {
        // Page remains usable without localStorage.
    }
}

function applyRequestKind(kind, clearStatus = true) {
    requestKind = kind === "idea" ? "idea" : "bug";

    const isBug = requestKind === "bug";

    document.querySelectorAll(".support-category").forEach(button => {
        const active = button.dataset.type === requestKind;

        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
    });

    setText("formTitle", isBug ? "bugTitle" : "ideaTitle");
    setText(
        "formDescription",
        isBug ? "bugDescription" : "ideaDescription"
    );
    setText(
        "requestTitleLabel",
        isBug ? "problemTitle" : "ideaSubject"
    );
    setText(
        "messageLabel",
        isBug ? "bugMessage" : "ideaMessage"
    );
    setText(
        "stepsLabel",
        isBug ? "bugSteps" : "ideaSteps"
    );
    setText(
        "stepsNote",
        isBug ? "bugStepsNote" : "ideaStepsNote"
    );

    byId("requestType").value = isBug
        ? "Bug report"
        : "Feature request";

    byId("messageSubject").value = isBug
        ? "WT Mod Manager — Bug report"
        : "WT Mod Manager — Feature request";

    byId("versionField").hidden = !isBug;
    byId("appVersion").disabled = !isBug;

    byId("reproduceSteps").name = isBug
        ? "steps_to_reproduce"
        : "expected_benefit";

    byId("submitLabel").textContent = submitting
        ? translate("sending")
        : translate("send");

    byId("submissionNote").textContent = formspreeId
        ? translate("readyNote")
        : translate("setupNote");

    const titleHelp = helpTexts[currentLanguage][
        isBug ? "bugTitle" : "ideaTitle"
    ];

    const messageHelp = helpTexts[currentLanguage][
        isBug ? "bugMessage" : "ideaMessage"
    ];

    const stepsHelp = helpTexts[currentLanguage][
        isBug ? "bugSteps" : "ideaSteps"
    ];

    byId("requestTitle").placeholder = titleHelp.example;
    byId("requestMessage").placeholder = messageHelp.example;
    byId("reproduceSteps").placeholder = stepsHelp.example;

    document.querySelectorAll(".field-help").forEach(button => {
        const resolved = resolveHelpKey(button.dataset.help);
        const data = helpTexts[currentLanguage][resolved];

        if (data) {
            button.setAttribute("aria-label", data.title);
            button.title = data.title;
        }
    });

    if (clearStatus) {
        setStatus("");
    }

    const params = new URLSearchParams(window.location.search);
    params.set("type", requestKind);

    // Keep the current local or published path.
    history.replaceState(
        null,
        "",
        `${window.location.pathname}?${params.toString()}${window.location.hash}`
    );
}

function setupCategories() {
    document.querySelectorAll(".support-category").forEach(button => {
        button.addEventListener("click", () => {
            if (submitting) {
                return;
            }

            applyRequestKind(button.dataset.type);
        });
    });
}

function setupLanguageDropdown() {
    const toggle = byId("supportLanguageToggle");
    const menu = byId("supportLanguageMenu");
    const options = [...menu.querySelectorAll(".lang-option")];

    function close() {
        menu.hidden = true;
        toggle.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", () => {
        const opening = menu.hidden;

        menu.hidden = !opening;
        toggle.classList.toggle("open", opening);
        toggle.setAttribute("aria-expanded", String(opening));

        if (opening) {
            const selected = options.find(
                option => option.dataset.lang === currentLanguage
            );

            (selected || options[0]).focus();
        }
    });

    options.forEach((button, index) => {
        button.addEventListener("click", () => {
            applyLanguage(button.dataset.lang);
            close();
            toggle.focus();
        });

        button.addEventListener("keydown", event => {
            if (
                event.key === "ArrowDown" ||
                event.key === "ArrowUp"
            ) {
                event.preventDefault();

                const direction = event.key === "ArrowDown" ? 1 : -1;

                const nextIndex =
                    (index + direction + options.length) %
                    options.length;

                options[nextIndex].focus();
            }
        });
    });

    document.addEventListener("click", event => {
        if (!event.target.closest(".lang-wrap")) {
            close();
        }
    });

    document.addEventListener("keydown", event => {
        if (
            event.key === "Escape" &&
            !menu.hidden &&
            byId("helpOverlay").hidden
        ) {
            close();
            toggle.focus();
        }
    });
}

// Message character counter.

function setupCounter() {
    const message = byId("requestMessage");

    message.addEventListener("input", updateCharacterCounter);
    updateCharacterCounter();
}

function updateCharacterCounter() {
    const message = byId("requestMessage");
    byId("characterCount").textContent =
        `${message.value.length} / 5000`;
}

// Developer contact panel.

function validDeveloperEmail(value) {
    if (typeof value !== "string") {
        return "";
    }

    const email = value.trim();

    if (
        email.length > 160 ||
        !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(email)
    ) {
        return "";
    }

    return email;
}

function updateDeveloperContact() {
    const panel = byId("developerContact");

    if (!developerEmail) {
        panel.hidden = true;
        return;
    }

    panel.hidden = false;

    byId("developerEmailLink").textContent = developerEmail;
    byId("developerEmailLink").href = `mailto:${developerEmail}`;
    byId("writeDeveloperEmail").href = `mailto:${developerEmail}`;
}

async function copyDeveloperEmail() {
    if (!developerEmail) {
        return;
    }

    const status = byId("emailCopyStatus");

    try {
        await navigator.clipboard.writeText(developerEmail);
        status.textContent = translate("copied");
    } catch {
        status.textContent = translate("copyFailed");
        byId("developerEmailLink").focus();
    }
}

function setupDeveloperContact() {
    byId("copyDeveloperEmail").addEventListener(
        "click",
        copyDeveloperEmail
    );
}

// Configuration from site-config.json.

async function loadSettings() {
    try {
        const response = await fetch("site-config.json", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Configuration could not be loaded");
        }

        const config = await response.json();

        const candidate = config.formspree_form_id;

        if (
            typeof candidate === "string" &&
            /^[A-Za-z0-9]{4,30}$/.test(candidate)
        ) {
            formspreeId = candidate;
        }

        developerEmail = validDeveloperEmail(
            config.developer_email
        );
    } catch (error) {
        console.warn("Support configuration unavailable:", error);
    }

    submitButton.disabled = !formspreeId;
    updateDeveloperContact();

    byId("submissionNote").textContent = formspreeId
        ? translate("readyNote")
        : translate("setupNote");
}

// Formspree submission.

function setupSubmission() {
    form.addEventListener("submit", async event => {
        event.preventDefault();

        if (submitting) {
            return;
        }

        if (!formspreeId) {
            setStatus(translate("notReady"), "error");
            return;
        }

        const name = byId("visitorName").value.trim();
        const email = byId("visitorEmail").value.trim();
        const title = byId("requestTitle").value.trim();
        const message = byId("requestMessage").value.trim();
        const website = byId("contactWebsite").value.trim();

        if (website) {
            // Spam trap: do not send automated submissions.
            return;
        }

        if (
            name.length < 2 ||
            !email ||
            title.length < 5 ||
            message.length < 15 ||
            !form.checkValidity()
        ) {
            setStatus(translate("invalid"), "error");
            form.reportValidity();
            return;
        }

        const data = new FormData(form);

        data.set("name", name);
        data.set("email", email);
        data.set("title", title);
        data.set("message", message);
        data.set("language", currentLanguage);
        data.set(
            "page",
            window.location.origin + window.location.pathname
        );

        submitting = true;
        submitButton.disabled = true;
        byId("submitLabel").textContent = translate("sending");
        setStatus("");

        try {
            const response = await fetch(
                `https://formspree.io/f/${formspreeId}`,
                {
                    method: "POST",
                    body: data,
                    headers: {
                        Accept: "application/json"
                    }
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Formspree returned HTTP ${response.status}`
                );
            }

            form.reset();
            updateCharacterCounter();
            setStatus(translate("success"), "success");
        } catch (error) {
            console.error("Support submission failed:", error);
            setStatus(translate("error"), "error");
        } finally {
            submitting = false;
            submitButton.disabled = !formspreeId;
            byId("submitLabel").textContent = translate("send");
        }
    });
}

// Initial language.

function detectLanguage() {
    try {
        const saved = localStorage.getItem("wtmm-language");

        if (
            saved &&
            Object.prototype.hasOwnProperty.call(texts, saved)
        ) {
            return saved;
        }
    } catch {
        // Continue without local storage.
    }

    const browserLanguage = (
        navigator.language || "en"
    ).toLowerCase();

    if (browserLanguage.startsWith("uk")) {
        return "uk";
    }

    if (browserLanguage.startsWith("ru")) {
        return "ru";
    }

    return "en";
}

// Startup.

async function initSupport() {
    byId("year").textContent =
        String(new Date().getFullYear());

    setupCategories();
    setupLanguageDropdown();
    setupHelpModal();
    setupCounter();
    setupSubmission();
    setupDeveloperContact();

    applyLanguage(detectLanguage());

    const params = new URLSearchParams(
        window.location.search
    );

    applyRequestKind(params.get("type"), false);

    await loadSettings();
}

document.addEventListener("DOMContentLoaded", initSupport);
