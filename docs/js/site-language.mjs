// Centralized internal-page localization for WT Mod Manager.
// The only language selector is on docs/index.html. Other pages read its
// localStorage preference and never write a different language to storage.
// Static interface strings are translated; usernames, messages, mod content,
// private IDs, file names and text typed by visitors are never translated.
const LANGUAGES = new Set(["ru", "uk", "en", "pl", "de"]);
const TABLE = [
  // Common navigation and states
  ["Главная", "Home", "Головна", "Strona główna", "Startseite"],
  ["← На главную", "← Back to home", "← На головну", "← Do strony głównej", "← Zur Startseite"],
  ["Мой профиль", "My profile", "Мій профіль", "Mój profil", "Mein Profil"],
  ["Библиотека модов", "Mod library", "Бібліотека модів", "Biblioteka modów", "Mod-Bibliothek"],
  ["Community", "Community", "Спільнота", "Społeczność", "Community"],
  ["Загрузка...", "Loading...", "Завантаження...", "Ładowanie...", "Wird geladen..."],
  ["Закрыть", "Close", "Закрити", "Zamknij", "Schließen"],
  ["Подробнее", "Details", "Докладніше", "Szczegóły", "Details"],
  ["Автор", "Author", "Автор", "Autor", "Autor"],
  ["Я", "Me", "Я", "Ja", "Ich"],
  ["Копировать", "Copy", "Копіювати", "Kopiuj", "Kopieren"],

  // Profile: account, media, editing, authentication, 2FA
  ["Мой профиль — WT Mod Manager", "My profile — WT Mod Manager", "Мій профіль — WT Mod Manager", "Mój profil — WT Mod Manager", "Mein Profil — WT Mod Manager"],
  ["Мой профиль", "My profile", "Мій профіль", "Mój profil", "Mein Profil"],
  ["Твои настройки, твоя аватарка и личный ID пользователя.", "Your settings, avatar and personal user ID.", "Твої налаштування, аватар і особистий ID користувача.", "Twoje ustawienia, awatar i osobisty identyfikator użytkownika.", "Deine Einstellungen, dein Avatar und deine persönliche Benutzer-ID."],
  ["Твой баннер профиля", "Your profile banner", "Твій банер профілю", "Twój baner profilu", "Dein Profilbanner"],
  ["Твоя аватарка", "Your avatar", "Твоя аватарка", "Twój awatar", "Dein Avatar"],
  ["Личный аккаунт", "Personal account", "Особистий акаунт", "Konto osobiste", "Persönliches Konto"],
  ["Никнейм", "Nickname", "Нікнейм", "Pseudonim", "Benutzername"],
  ["От 2 до 24 символов. Не используй имена администрации.", "2–24 characters. Do not use staff names.", "Від 2 до 24 символів. Не використовуй імена адміністрації.", "Od 2 do 24 znaków. Nie używaj nazw administracji.", "2–24 Zeichen. Verwende keine Namen der Administration."],
  ["Никнейм можно менять раз в 7 дней. Отсчёт идёт по времени сервера.", "You can change your nickname every 7 days, based on server time.", "Нікнейм можна змінювати раз на 7 днів за серверним часом.", "Pseudonim można zmieniać co 7 dni według czasu serwera.", "Du kannst deinen Benutzernamen alle 7 Tage ändern (Serverzeit)."],
  ["Никнейм можно менять не чаще одного раза в 7 дней.", "Nickname changes are limited to once every 7 days.", "Нікнейм можна змінювати не частіше одного разу на 7 днів.", "Pseudonim można zmieniać najwyżej raz na 7 dni.", "Der Benutzername kann höchstens einmal alle 7 Tage geändert werden."],
  ["О себе", "About me", "Про себе", "O mnie", "Über mich"],
  ["Расскажи, какие моды и темы тебе интересны...", "Share which mods and topics interest you...", "Розкажи, які моди та теми тобі цікаві...", "Opowiedz, jakie mody i tematy Cię interesują...", "Welche Mods und Themen interessieren dich?..."],
  ["До 320 символов. Это описание увидят посетители публичного профиля.", "Up to 320 characters. Visitors to your public profile can see this description.", "До 320 символів. Цей опис бачитимуть відвідувачі публічного профілю.", "Do 320 znaków. Opis zobaczą odwiedzający Twój profil publiczny.", "Bis zu 320 Zeichen. Besucher deines öffentlichen Profils sehen diese Beschreibung."],
  ["Аватарка", "Avatar", "Аватарка", "Awatar", "Avatar"],
  ["Выбрать изображение", "Choose image", "Вибрати зображення", "Wybierz obraz", "Bild auswählen"],
  ["Убрать аватарку", "Remove avatar", "Прибрати аватарку", "Usuń awatar", "Avatar entfernen"],
  ["PNG, JPG, WebP или GIF, до 5 МБ.", "PNG, JPG, WebP or GIF, up to 5 MB.", "PNG, JPG, WebP або GIF, до 5 МБ.", "PNG, JPG, WebP lub GIF, do 5 MB.", "PNG, JPG, WebP oder GIF, bis 5 MB."],
  ["Обложка профиля", "Profile banner", "Обкладинка профілю", "Baner profilu", "Profilbanner"],
  ["Выбрать баннер", "Choose banner", "Вибрати банер", "Wybierz baner", "Banner auswählen"],
  ["Убрать баннер", "Remove banner", "Прибрати банер", "Usuń baner", "Banner entfernen"],
  ["PNG, JPG, WebP или GIF до 5 МБ. Лучше горизонтальное изображение.", "PNG, JPG, WebP or GIF, up to 5 MB. A landscape image works best.", "PNG, JPG, WebP або GIF до 5 МБ. Краще горизонтальне зображення.", "PNG, JPG, WebP lub GIF, do 5 MB. Najlepiej w orientacji poziomej.", "PNG, JPG, WebP oder GIF, bis 5 MB. Ein Querformat eignet sich am besten."],
  ["Цвет профиля", "Profile color", "Колір профілю", "Kolor profilu", "Profilfarbe"],
  ["Голубой", "Blue", "Блакитний", "Niebieski", "Blau"],
  ["Бирюзовый", "Teal", "Бірюзовий", "Turkusowy", "Türkis"],
  ["Фиолетовый", "Purple", "Фіолетовий", "Fioletowy", "Violett"],
  ["Публичный профиль — другие игроки смогут видеть мой никнейм, описание, аватарку, баннер и одобренные моды.", "Public profile — other players can see my nickname, description, avatar, banner and approved mods.", "Публічний профіль — інші гравці зможуть бачити мій нікнейм, опис, аватар, банер і схвалені моди.", "Profil publiczny — inni gracze zobaczą mój pseudonim, opis, awatar, baner i zatwierdzone mody.", "Öffentliches Profil — andere Spieler können meinen Benutzernamen, Beschreibung, Avatar, Banner und genehmigte Mods sehen."],
  ["ID пользователя", "User ID", "ID користувача", "ID użytkownika", "Benutzer-ID"],
  ["Твой ID", "Your ID", "Твій ID", "Twój ID", "Deine ID"],
  ["Посмотреть публичный профиль", "View public profile", "Переглянути публічний профіль", "Zobacz profil publiczny", "Öffentliches Profil ansehen"],
  ["Мои моды", "My mods", "Мої моди", "Moje mody", "Meine Mods"],
  ["Сохранить профиль", "Save profile", "Зберегти профіль", "Zapisz profil", "Profil speichern"],
  ["Доступ к аккаунту", "Account access", "Доступ до акаунта", "Dostęp do konta", "Kontozugriff"],
  ["Привяжи email и подтверди его через письмо. После подтверждения можно установить пароль и входить с другого устройства без потери профиля.", "Link your email and confirm it through the verification message. Then set a password to sign in on another device without losing your profile.", "Прив'яжи email та підтвердь його листом. Потім встанови пароль, щоб входити з іншого пристрою без втрати профілю.", "Połącz i potwierdź adres e-mail. Następnie ustaw hasło, aby logować się na innym urządzeniu bez utraty profilu.", "Verknüpfe deine E-Mail-Adresse und bestätige sie per Nachricht. Lege dann ein Passwort fest, um dich auf einem anderen Gerät anzumelden."],
  ["Привязать email", "Link email", "Прив'язати email", "Połącz e-mail", "E-Mail verknüpfen"],
  ["Пароль (после подтверждения email)", "Password (after email verification)", "Пароль (після підтвердження email)", "Hasło (po potwierdzeniu e-maila)", "Passwort (nach E-Mail-Bestätigung)"],
  ["Не менее 10 символов", "At least 10 characters", "Не менш ніж 10 символів", "Co najmniej 10 znaków", "Mindestens 10 Zeichen"],
  ["Сохранить пароль", "Save password", "Зберегти пароль", "Zapisz hasło", "Passwort speichern"],
  ["Уже есть аккаунт? Войти", "Already have an account? Sign in", "Уже маєш акаунт? Увійти", "Masz już konto? Zaloguj się", "Du hast bereits ein Konto? Anmelden"],
  ["Пароль", "Password", "Пароль", "Hasło", "Passwort"],
  ["Войти в существующий профиль", "Sign in to an existing account", "Увійти до наявного профілю", "Zaloguj się na istniejące konto", "Bei bestehendem Konto anmelden"],
  ["Внимание: вход в другой аккаунт переключит текущий профиль. Данные анонимного профиля не будут перенесены автоматически.", "Warning: signing into another account switches your current profile. Anonymous profile data will not be transferred automatically.", "Увага: вхід до іншого акаунта перемкне поточний профіль. Дані анонімного профілю не перенесуться автоматично.", "Uwaga: zalogowanie na inne konto zmieni bieżący profil. Dane anonimowego profilu nie zostaną przeniesione automatycznie.", "Achtung: Die Anmeldung bei einem anderen Konto wechselt das aktuelle Profil. Anonyme Profildaten werden nicht automatisch übertragen."],
  ["Двухфакторная защита (2FA)", "Two-factor authentication (2FA)", "Двофакторний захист (2FA)", "Uwierzytelnianie dwuskładnikowe (2FA)", "Zwei-Faktor-Authentifizierung (2FA)"],
  ["Подключи приложение-аутентификатор к аккаунту с подтверждённой почтой. После входа по паролю ты сможешь дополнительно подтверждать личность кодом. Не включай 2FA, если не сможешь сохранить доступ к приложению-аутентификатору.", "Connect an authenticator app to an account with a verified email. After signing in with a password, you can verify your identity with a code. Do not enable 2FA if you might lose access to your authenticator.", "Підключи застосунок-аутентифікатор до акаунта з підтвердженою поштою. Після входу з паролем підтверджуй особу кодом. Не вмикай 2FA, якщо можеш втратити доступ до застосунку.", "Połącz aplikację uwierzytelniającą z kontem z potwierdzonym e-mailem. Po zalogowaniu hasłem potwierdź tożsamość kodem. Nie włączaj 2FA, jeśli możesz utracić dostęp do aplikacji.", "Verbinde eine Authenticator-App mit einem Konto mit bestätigter E-Mail-Adresse. Nach der Passwortanmeldung kannst du deine Identität mit einem Code bestätigen. Aktiviere 2FA nicht, wenn du den Zugriff auf die App verlieren könntest."],
  ["Проверяем настройки безопасности…", "Checking security settings…", "Перевіряємо налаштування безпеки…", "Sprawdzanie ustawień bezpieczeństwa…", "Sicherheitseinstellungen werden überprüft…"],
  ["Подключить 2FA", "Enable 2FA", "Підключити 2FA", "Włącz 2FA", "2FA aktivieren"],
  ["1. Добавь аккаунт в приложение-аутентификатор", "1. Add the account to your authenticator app", "1. Додай акаунт у застосунок-аутентифікатор", "1. Dodaj konto do aplikacji uwierzytelniającej", "1. Konto zur Authenticator-App hinzufügen"],
  ["QR-код для подключения двухфакторной защиты", "QR code for enabling 2FA", "QR-код для підключення двофакторного захисту", "Kod QR do włączenia 2FA", "QR-Code zur Aktivierung von 2FA"],
  ["Если QR не открывается, введи секрет вручную в приложении:", "If the QR code cannot be scanned, enter the secret manually in the app:", "Якщо QR-код не відкривається, введи секрет у застосунку вручну:", "Jeśli kod QR nie działa, wpisz sekret ręcznie w aplikacji:", "Falls der QR-Code nicht funktioniert, gib das Geheimnis manuell in der App ein:"],
  ["2. Код из приложения (6 цифр)", "2. Code from the app (6 digits)", "2. Код із застосунку (6 цифр)", "2. Kod z aplikacji (6 cyfr)", "2. Code aus der App (6 Ziffern)"],
  ["Код для подключения 2FA", "2FA setup code", "Код підключення 2FA", "Kod konfiguracji 2FA", "2FA-Einrichtungscode"],
  ["Подтвердить подключение", "Confirm setup", "Підтвердити підключення", "Potwierdź konfigurację", "Einrichtung bestätigen"],
  ["Отмена", "Cancel", "Скасувати", "Anuluj", "Abbrechen"],
  ["Подтверди вход", "Verify sign-in", "Підтвердь вхід", "Potwierdź logowanie", "Anmeldung bestätigen"],
  ["Код из приложения-аутентификатора", "Code from your authenticator app", "Код із застосунку-аутентифікатора", "Kod z aplikacji uwierzytelniającej", "Code aus der Authenticator-App"],
  ["Код 2FA для входа", "2FA sign-in code", "Код 2FA для входу", "Kod 2FA do logowania", "2FA-Anmeldecode"],
  ["Подтвердить код", "Verify code", "Підтвердити код", "Potwierdź kod", "Code bestätigen"],
  ["Отключить 2FA", "Disable 2FA", "Вимкнути 2FA", "Wyłącz 2FA", "2FA deaktivieren"],
  ["Анонимный профиль зависит от данных этого браузера. Привяжи email, подтверди его и установи пароль, чтобы иметь возможность войти снова.", "An anonymous profile depends on this browser's data. Link and verify an email address, then set a password so you can sign in again.", "Анонімний профіль залежить від даних браузера. Прив'яжи та підтвердь email, а потім встанови пароль, щоб мати змогу ввійти знову.", "Profil anonimowy zależy od danych tej przeglądarki. Połącz i potwierdź e-mail oraz ustaw hasło, aby móc zalogować się ponownie.", "Ein anonymes Profil hängt von den Daten dieses Browsers ab. Verknüpfe und bestätige deine E-Mail-Adresse und lege ein Passwort fest, damit du dich erneut anmelden kannst."],

  // Mod catalog / upload controls
  ["Библиотека модов — WT Mod Manager", "Mod library — WT Mod Manager", "Бібліотека модів — WT Mod Manager", "Biblioteka modów — WT Mod Manager", "Mod-Bibliothek — WT Mod Manager"],
  ["Пользовательские модификации, опубликованные после проверки администратором.", "Community mods published after administrator review.", "Модифікації користувачів, опубліковані після перевірки адміністратором.", "Mody użytkowników publikowane po zatwierdzeniu przez administratora.", "Community-Mods, die nach Prüfung durch die Administration veröffentlicht wurden."],
  ["Загрузить свой мод", "Upload your mod", "Завантажити свій мод", "Prześlij swój mod", "Deinen Mod hochladen"],
  ["Разделы модификаций", "Mod sections", "Розділи модифікацій", "Sekcje modów", "Mod-Bereiche"],
  ["Каталог", "Catalog", "Каталог", "Katalog", "Katalog"],
  ["На проверке", "Pending review", "На перевірці", "Do weryfikacji", "Wird überprüft"],
  ["Поиск", "Search", "Пошук", "Szukaj", "Suche"],
  ["Название или автор", "Title or author", "Назва або автор", "Nazwa lub autor", "Titel oder Autor"],
  ["Категория", "Category", "Категорія", "Kategoria", "Kategorie"],
  ["Все категории", "All categories", "Усі категорії", "Wszystkie kategorie", "Alle Kategorien"],
  ["Графика и эффекты", "Visuals & effects", "Графіка та ефекти", "Grafika i efekty", "Grafik und Effekte"],
  ["Камуфляжи", "Camouflages", "Камуфляжі", "Kamuflaże", "Tarnanstriche"],
  ["Звуки", "Sounds", "Звуки", "Dźwięki", "Sounds"],
  ["Интерфейс", "Interface", "Інтерфейс", "Interfejs", "Oberfläche"],
  ["Другое", "Other", "Інше", "Inne", "Sonstiges"],
  ["Сортировка", "Sort by", "Сортування", "Sortowanie", "Sortierung"],
  ["Сначала новые", "Newest first", "Спочатку нові", "Najpierw najnowsze", "Neueste zuerst"],
  ["Сначала старые", "Oldest first", "Спочатку старі", "Najpierw najstarsze", "Älteste zuerst"],
  ["По названию", "By title", "За назвою", "Według nazwy", "Nach Titel"],
  ["Модификации", "Mods", "Модифікації", "Mody", "Mods"],
  ["Здесь пока пусто", "Nothing here yet", "Тут поки порожньо", "Tutaj na razie pusto", "Hier ist noch nichts"],
  ["Выбери другую категорию или добавь свою первую модификацию.", "Choose another category or upload your first mod.", "Вибери іншу категорію або додай свій перший мод.", "Wybierz inną kategorię lub dodaj pierwszy mod.", "Wähle eine andere Kategorie oder lade deinen ersten Mod hoch."],
  ["Загрузить модификацию", "Upload a mod", "Завантажити модифікацію", "Prześlij mod", "Mod hochladen"],
  ["Файлы сначала попадают на проверку. После одобрения они станут доступны в каталоге. Не публикуй чужие материалы без разрешения и не загружай исполняемые программы.", "Uploads are reviewed first and appear in the catalog after approval. Do not upload other people's content without permission or executable programs.", "Файли спочатку проходять перевірку й з'являються в каталозі після схвалення. Не публікуй чужі матеріали без дозволу та не завантажуй виконувані програми.", "Pliki najpierw trafiają do weryfikacji i po zatwierdzeniu pojawiają się w katalogu. Nie przesyłaj cudzych materiałów bez zgody ani plików wykonywalnych.", "Dateien werden zuerst überprüft und nach Freigabe im Katalog angezeigt. Lade keine fremden Inhalte ohne Erlaubnis oder ausführbare Programme hoch."],
  ["Название мода", "Mod title", "Назва мода", "Nazwa moda", "Mod-Titel"],
  ["Например: Clean HUD", "For example: Clean HUD", "Наприклад: Clean HUD", "Na przykład: Clean HUD", "Zum Beispiel: Clean HUD"],
  ["Версия", "Version", "Версія", "Wersja", "Version"],
  ["Описание", "Description", "Опис", "Opis", "Beschreibung"],
  ["Что меняет мод? Как установить?", "What does this mod change? How is it installed?", "Що змінює мод? Як його встановити?", "Co zmienia mod? Jak go zainstalować?", "Was ändert der Mod? Wie wird er installiert?"],
  ["ZIP-архив модификации (до 20 МБ)", "Mod ZIP archive (up to 20 MB)", "ZIP-архів мода (до 20 МБ)", "Archiwum ZIP moda (do 20 MB)", "Mod-ZIP-Archiv (bis 20 MB)"],
  ["Обложка (необязательно, до 5 МБ)", "Cover image (optional, up to 5 MB)", "Обкладинка (необов'язково, до 5 МБ)", "Okładka (opcjonalnie, do 5 MB)", "Vorschaubild (optional, bis 5 MB)"],
  ["Отправить на модерацию", "Submit for review", "Надіслати на модерацію", "Prześlij do weryfikacji", "Zur Prüfung einreichen"],
  ["Графика и эффекты", "Visuals & effects", "Графіка та ефекти", "Grafika i efekty", "Grafik und Effekte"],
  ["Отправка...", "Sending...", "Надсилання...", "Wysyłanie...", "Wird gesendet..."],
  ["Ожидает проверки", "Awaiting review", "Очікує перевірки", "Oczekuje na weryfikację", "Wartet auf Prüfung"],
  ["Одобрено", "Approved", "Схвалено", "Zatwierdzono", "Freigegeben"],
  ["Отклонено", "Rejected", "Відхилено", "Odrzucono", "Abgelehnt"],
  ["Удалить", "Delete", "Видалити", "Usuń", "Löschen"],
  ["Скачать ZIP", "Download ZIP", "Завантажити ZIP", "Pobierz ZIP", "ZIP herunterladen"],

  // Community: fixed navigation, channel controls and composer
  ["Community — WT Mod Manager", "Community — WT Mod Manager", "Спільнота — WT Mod Manager", "Społeczność — WT Mod Manager", "Community — WT Mod Manager"],
  ["Открыть библиотеку модов", "Open mod library", "Відкрити бібліотеку модів", "Otwórz bibliotekę modów", "Mod-Bibliothek öffnen"],
  ["Открыть свой профиль", "Open your profile", "Відкрити свій профіль", "Otwórz swój profil", "Dein Profil öffnen"],
  ["Community Hub", "Community Hub", "Центр спільноти", "Centrum społeczności", "Community-Zentrale"],
  ["Чаты, новости, обсуждения и идеи игроков.", "Player chats, news, discussions and ideas.", "Чати, новини, обговорення та ідеї гравців.", "Czaty, wiadomości, dyskusje i pomysły graczy.", "Chats, Neuigkeiten, Diskussionen und Ideen der Spieler."],
  ["Каналы сообщества", "Community channels", "Канали спільноти", "Kanały społeczności", "Community-Kanäle"],
  ["Общий чат", "General chat", "Загальний чат", "Czat ogólny", "Allgemeiner Chat"],
  ["Обновления", "Updates", "Оновлення", "Aktualizacje", "Updates"],
  ["Новости", "News", "Новини", "Wiadomości", "Neuigkeiten"],
  ["Идеи", "Ideas", "Ідеї", "Pomysły", "Ideen"],
  ["Помощь", "Help", "Допомога", "Pomoc", "Hilfe"],
  ["Свободное общение игроков", "Open discussion for players", "Вільне спілкування гравців", "Swobodne rozmowy graczy", "Offener Austausch zwischen Spielern"],
  ["BOT · ЗАКРЕПЛЕНО", "BOT · PINNED", "БОТ · ЗАКРІПЛЕНО", "BOT · PRZYPIĘTO", "BOT · ANGEHEFTET"],
  ["Добро пожаловать! Общайся уважительно. Разрешены текст, эмодзи, фотографии и GIF. Ссылки и другие файлы запрещены.", "Welcome! Be respectful. Text, emoji, photos and GIFs are allowed. Links and other files are not allowed.", "Ласкаво просимо! Спілкуйся ввічливо. Дозволено текст, емодзі, фото й GIF. Посилання та інші файли заборонено.", "Witamy! Rozmawiaj z szacunkiem. Dozwolone są tekst, emoji, zdjęcia i GIF-y. Linki oraz inne pliki są zabronione.", "Willkommen! Sei respektvoll. Text, Emojis, Fotos und GIFs sind erlaubt. Links und andere Dateien sind nicht gestattet."],
  ["Загрузить старые сообщения", "Load older messages", "Завантажити старі повідомлення", "Wczytaj starsze wiadomości", "Ältere Nachrichten laden"],
  ["Сообщения участников", "Member messages", "Повідомлення учасників", "Wiadomości uczestników", "Nachrichten der Mitglieder"],
  ["Удалить вложение", "Remove attachment", "Видалити вкладення", "Usuń załącznik", "Anhang entfernen"],
  ["Напиши сообщение...", "Write a message...", "Напиши повідомлення...", "Napisz wiadomość...", "Nachricht schreiben..."],
  ["Текст сообщения", "Message text", "Текст повідомлення", "Treść wiadomości", "Nachrichtentext"],
  ["Эмодзи", "Emoji", "Емодзі", "Emoji", "Emoji"],
  ["Фото или GIF", "Photo or GIF", "Фото або GIF", "Zdjęcie lub GIF", "Foto oder GIF"],
  ["Фото / GIF", "Photo / GIF", "Фото / GIF", "Zdjęcie / GIF", "Foto / GIF"],
  ["Отправить", "Send", "Надіслати", "Wyślij", "Senden"],
  ["Прикрепить", "Attach", "Прикріпити", "Dołącz", "Anhängen"],
  ["Отправить жалобу", "Send report", "Надіслати скаргу", "Wyślij zgłoszenie", "Meldung senden"],
  ["Причина жалобы", "Reason for report", "Причина скарги", "Powód zgłoszenia", "Grund der Meldung"],

  // Creator
  ["Профиль автора — WT Mod Manager", "Creator profile — WT Mod Manager", "Профіль автора — WT Mod Manager", "Profil autora — WT Mod Manager", "Erstellerprofil — WT Mod Manager"],
  ["Профиль автора", "Creator profile", "Профіль автора", "Profil autora", "Erstellerprofil"],
  ["Публичная страница игрока и его одобренные модификации.", "A player's public profile and approved mods.", "Публічна сторінка гравця та його схвалені модифікації.", "Publiczny profil gracza i jego zatwierdzone mody.", "Öffentliches Spielerprofil und freigegebene Mods."],
  ["Баннер автора", "Creator banner", "Банер автора", "Baner autora", "Banner des Erstellers"],
  ["Аватар автора", "Creator avatar", "Аватар автора", "Awatar autora", "Avatar des Erstellers"],
  ["Модификации автора", "Creator's mods", "Модифікації автора", "Mody autora", "Mods des Erstellers"],
  ["Некорректная ссылка на профиль.", "Invalid profile link.", "Некоректне посилання на профіль.", "Nieprawidłowy link do profilu.", "Ungültiger Profillink."],
  ["Профиль скрыт.", "Profile is private.", "Профіль приховано.", "Profil jest ukryty.", "Profil ist privat."],
  ["Нет доступных модов", "No mods available", "Немає доступних модів", "Brak dostępnych modów", "Keine Mods verfügbar"],
];

TABLE.push(
  ["Обсуждение обновлений", "Discuss updates", "Обговорення оновлень", "Dyskusja o aktualizacjach", "Updates diskutieren"],
  ["Новые версии, изменения и отзывы", "New versions, changes and feedback", "Нові версії, зміни та відгуки", "Nowe wersje, zmiany i opinie", "Neue Versionen, Änderungen und Feedback"],
  ["Официальные объявления разработчика", "Official developer announcements", "Офіційні оголошення розробника", "Oficjalne ogłoszenia dewelopera", "Offizielle Ankündigungen des Entwicklers"],
  ["Идеи и предложения", "Ideas and suggestions", "Ідеї та пропозиції", "Pomysły i propozycje", "Ideen und Vorschläge"],
  ["Обсуждение новых возможностей", "Discuss new features", "Обговорення нових можливостей", "Dyskusja o nowych funkcjach", "Diskussion über neue Funktionen"],
  ["Вопросы по WT Mod Manager", "Questions about WT Mod Manager", "Запитання про WT Mod Manager", "Pytania o WT Mod Manager", "Fragen zu WT Mod Manager"],
  ["Загрузить ещё моды", "Load more mods", "Завантажити ще моди", "Wczytaj więcej modów", "Weitere Mods laden"],
  ["Обзор модерации модификаций", "Mod moderation overview", "Огляд модерації модів", "Przegląd moderacji modów", "Mod-Moderation im Überblick"],
  ["Панель модерации", "Moderation panel", "Панель модерації", "Panel moderacji", "Moderationsbereich"],
  ["Ожидают проверки", "Awaiting review", "Очікують перевірки", "Oczekujące na weryfikację", "Warten auf Prüfung"],
  ["Опубликованы", "Published", "Опубліковані", "Opublikowane", "Veröffentlicht"],
  ["Отклонены", "Rejected", "Відхилені", "Odrzucone", "Abgelehnt"],
  ["Проверка", "Review", "Перевірка", "Weryfikacja", "Prüfung"],
  ["Загружаю модификации...", "Loading mods...", "Завантажую модифікації...", "Wczytywanie modów...", "Mods werden geladen..."],
  ["Опубликованные версии", "Published versions", "Опубліковані версії", "Opublikowane wersje", "Veröffentlichte Versionen"],
  ["Описание отсутствует.", "No description provided.", "Опис відсутній.", "Brak opisu.", "Keine Beschreibung vorhanden."],
  ["Ожидает модерации", "Pending moderation", "Очікує модерації", "Oczekuje na moderację", "Wartet auf Moderation"],
  ["Получить ссылку для скачивания", "Get download link", "Отримати посилання для завантаження", "Pobierz link do pobrania", "Downloadlink anfordern"],
  ["Скачать ZIP (ссылка действует 90 секунд)", "Download ZIP (link valid for 90 seconds)", "Завантажити ZIP (посилання діє 90 секунд)", "Pobierz ZIP (link ważny 90 sekund)", "ZIP herunterladen (Link 90 Sekunden gültig)"],
  ["Сформировать ссылку на ZIP", "Generate ZIP link", "Створити посилання на ZIP", "Utwórz link do ZIP", "ZIP-Link erstellen"],
  ["Перед публикацией обязательно проверь архив вручную. Не запускай неизвестные файлы.", "Manually review the archive before publishing. Do not run unknown files.", "Перед публікацією перевір архів вручну. Не запускай невідомі файли.", "Przed publikacją sprawdź archiwum ręcznie. Nie uruchamiaj nieznanych plików.", "Prüfe das Archiv vor der Veröffentlichung manuell. Führe keine unbekannten Dateien aus."],
  ["Мод успешно отправлен на ручную модерацию!", "Mod submitted for manual review!", "Мод надіслано на ручну модерацію!", "Mod wysłany do ręcznej weryfikacji!", "Mod zur manuellen Prüfung eingereicht!"],
  ["Этот профиль скрыт или пока не создан.", "This profile is private or has not been created.", "Цей профіль прихований або ще не створений.", "Ten profil jest ukryty albo jeszcze nie istnieje.", "Dieses Profil ist privat oder wurde noch nicht erstellt."],
  ["Игрок сообщества WT Mod Manager", "WT Mod Manager community player", "Гравець спільноти WT Mod Manager", "Gracz społeczności WT Mod Manager", "Spieler der WT Mod Manager-Community"],
  ["У автора пока нет опубликованных модификаций.", "This creator has no published mods yet.", "Автор ще не має опублікованих модифікацій.", "Autor nie ma jeszcze opublikowanych modów.", "Dieser Ersteller hat noch keine veröffentlichten Mods."],
  ["Спам", "Spam", "Спам", "Spam", "Spam"],
  ["Оскорбления или травля", "Harassment or bullying", "Образи або цькування", "Obraźliwe treści lub nękanie", "Belästigung oder Mobbing"],
  ["Мошенничество", "Scam", "Шахрайство", "Oszustwo", "Betrug"],
  ["Опасный контент", "Unsafe content", "Небезпечний вміст", "Niebezpieczna treść", "Gefährliche Inhalte"],
  ["Подключение...", "Connecting...", "Підключення...", "Łączenie...", "Verbindung wird hergestellt..."]
);

const normalized = text => String(text || "").trim().replace(/\s+/g," ");
const langs = ["ru","en","uk","pl","de"];
const dictionary = new Map(TABLE.map(([ru,en,uk,pl,de]) => [normalized(ru), {ru,en,uk,pl,de}]));
const excluded = [
  "#messages", ".chat-messages", "#creatorBio",
  ".mod-card-copy", ".mod-details-text", ".mod-details-title",
  ".mod-card h3", ".message-author", ".message-body", ".message-content",
  "#creatorName", "#profileUserId", "#attachmentName",
  ".profile-mini-label .custom-name"
].join(",");
let activeLanguage = "ru";
const originals = new WeakMap();

export function readSiteLanguage() {
  try {
    const selected = localStorage.getItem("wtmm-language");
    if (LANGUAGES.has(selected)) return selected;
  } catch { /* Browser storage can be unavailable. */ }
  // Match the homepage browser-locale fallback without writing to storage.
  const browser = String(navigator.language || "en").slice(0, 2).toLowerCase();
  return LANGUAGES.has(browser) ? browser : "en";
}
export function siteLanguage() { return activeLanguage; }
export function siteLocale() {
  return ({ru:"ru-RU",uk:"uk-UA",en:"en-US",pl:"pl-PL",de:"de-DE"})[activeLanguage] || "en-US";
}
export function uiText(raw, language = activeLanguage) {
  return dictionary.get(normalized(raw))?.[language] || String(raw);
}
function skip(node) {
  const parent = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
  return !parent || parent.closest(excluded) ||
    parent.closest("script,style,noscript,code,[contenteditable],svg") ||
    parent.closest("[data-no-site-translation]") ||
    (node.nodeType === Node.TEXT_NODE && Boolean(parent.closest("textarea")));
}
function translateTextNode(node) {
  if(skip(node)) return;
  const before = node.nodeValue || "";
  const current = normalized(before);
  if(!current) return;
  const cached = originals.get(node);
  // If app code replaced a translated UI label with a nickname, file name,
  // profile content or dynamic text, invalidate cached UI state immediately.
  const original = dictionary.has(current) ? current
    : cached?.rendered === current ? cached.source : null;
  if(!original || !dictionary.has(original)) {
    if(cached) originals.delete(node);
    return;
  }
  const target = dictionary.get(original)[activeLanguage];
  if(!target) return;
  const leading = before.match(/^\s*/)?.[0] || "";
  const trailing = before.match(/\s*$/)?.[0] || "";
  const next = leading + target + trailing;
  originals.set(node, {source:original, rendered:normalized(target)});
  if(next !== before) node.nodeValue = next;
}
const attributeOriginals = new WeakMap();
function translateAttributes(element) {
  if(skip(element)) return;
  const originalsForElement = attributeOriginals.get(element) || {};
  for(const attribute of ["placeholder","aria-label","title","alt"]) {
    const value = element.getAttribute(attribute);
    if(!value) continue;
    const existing = originalsForElement[attribute];
    const current = normalized(value);
    const original = dictionary.has(current) ? current
      : existing?.rendered === current ? existing.source : null;
    if(!original || !dictionary.has(original)) {
      delete originalsForElement[attribute];
      continue;
    }
    const target = dictionary.get(original)[activeLanguage];
    if(!target) continue;
    originalsForElement[attribute] = {source:original,rendered:normalized(target)};
    if(target !== value) element.setAttribute(attribute,target);
  }
  attributeOriginals.set(element,originalsForElement);
}
function applyElement(root) {
  if(!root || (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE)) return;
  if(root.nodeType === Node.ELEMENT_NODE && skip(root)) return;
  const tree = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  if(root.nodeType === Node.ELEMENT_NODE) translateAttributes(root);
  let node;
  while((node = tree.nextNode())) {
    if(node.nodeType === Node.TEXT_NODE) translateTextNode(node);
    else translateAttributes(node);
  }
}
let titleMemory = null;
function render(language = readSiteLanguage()) {
  activeLanguage = LANGUAGES.has(language) ? language : "en";
  document.documentElement.lang = activeLanguage;
  const title = normalized(document.title);
  const originalTitle = dictionary.has(title) ? title
    : titleMemory?.rendered === title ? titleMemory.source : null;
  if (originalTitle) {
    const translatedTitle = uiText(originalTitle, activeLanguage);
    titleMemory = {source:originalTitle,rendered:normalized(translatedTitle)};
    document.title = translatedTitle;
  } else {
    // The creator profile may set a personalized title: never overwrite it.
    titleMemory = null;
  }
  applyElement(document.body);
}
export function setupSiteLanguage() {
  if(!document.body) {
    document.addEventListener("DOMContentLoaded", setupSiteLanguage, {once:true});
    return;
  }
  render();
  // Observe interface updates, while skipping chat messages/user authored fields.
  const observer = new MutationObserver(entries => {
    for(const entry of entries) {
      if(entry.type === "characterData") translateTextNode(entry.target);
      for(const child of entry.addedNodes || []) {
        if(child.nodeType === Node.TEXT_NODE) translateTextNode(child);
        else applyElement(child);
      }
    }
  });
  observer.observe(document.body,{subtree:true,childList:true,characterData:true});
  // Selecting language is deliberately never possible from secondary pages.
  window.addEventListener("pageshow", () => render());
  window.addEventListener("storage", event => {
    if(event.key === "wtmm-language") render();
  });
  return activeLanguage;
}
