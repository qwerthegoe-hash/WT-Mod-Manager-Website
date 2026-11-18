
"""WT Mod Manager 1.2 — seven-language localization.

Languages:
Russian, English, Ukrainian, German, French, Spanish, Polish.

Functions:
    tr(key, language)
    translate_ui(text, language)
    translate_dynamic(message, language)

All translations are stored locally.
"""

LANGUAGES = {
    "ru": "Русский",
    "en": "English",
    "uk": "Українська",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "pl": "Polski",
}

_CODES = ("en", "uk", "de", "fr", "es", "pl")

# Settings text:
# Russian, English, Ukrainian, German, French, Spanish, Polish.
_SETTINGS = {
    'always_on_top': ('Поверх остальных окон', 'Always on top', 'Поверх інших вікон', 'Immer im Vordergrund', 'Toujours au premier plan', 'Siempre visible', 'Zawsze na wierzchu'),
    'always_on_top_desc': ('Окно всегда сверху.', 'Keep window on top.', 'Поверх інших вікон', 'Fenster bleibt oben.', 'Garder la fenêtre au premier plan.', 'Mantener la ventana encima.', 'Okno zawsze na wierzchu.'),
    'appearance_mode': ('Режим оформления', 'Appearance mode', 'Режим оформлення', 'Darstellungsmodus', 'Mode d’apparence', 'Modo de apariencia', 'Tryb wyglądu'),
    'audio': ('Предпросмотр аудио', 'Audio preview', 'Прослуховування аудіо', 'Audiovorschau', 'Aperçu audio', 'Vista previa de audio', 'Podgląd dźwięku'),
    'auto_open': ('Открывать автоматически', 'Open automatically', 'Відкривати автоматично', 'Automatisch öffnen', 'Ouvrir automatiquement', 'Abrir automáticamente', 'Otwieraj automatycznie'),
    'auto_open_desc': ('После обнаружения игры.', 'When the game is detected.', 'Після виявлення гри.', 'Bei Spielerkennung.', 'Lorsque le jeu est détecté.', 'Al detectar el juego.', 'Po wykryciu gry.'),
    'back': ('← Назад', '← Back', '← Назад', '← Zurück', '← Retour', '← Volver', '← Wstecz'),
    'black': ('Тёмная', 'Dark', 'Темна', 'Dunkel', 'Sombre', 'Oscuro', 'Ciemny'),
    'close': ('Назад', 'Back', 'Назад', 'Zurück', 'Retour', 'Volver', 'Wstecz'),
    'color_blue': ('Синий', 'Blue', 'Синій', 'Blau', 'Bleu', 'Azul', 'Niebieski'),
    'color_green': ('Зелёный', 'Green', 'Зелений', 'Grün', 'Vert', 'Verde', 'Zielony'),
    'color_orange': ('Оранжевый', 'Orange', 'Помаранчевий', 'Orange', 'Orange', 'Naranja', 'Pomarańczowy'),
    'color_purple': ('Фиолетовый', 'Purple', 'Фіолетовий', 'Violett', 'Violet', 'Morado', 'Fioletowy'),
    'color_red': ('Красный', 'Red', 'Червоний', 'Rot', 'Rouge', 'Rojo', 'Czerwony'),
    'customize': ('Кастомизация', 'Customization', 'Кастомізація', 'Anpassen', 'Personnaliser', 'Personalizar', 'Dostosuj'),
    'customize_desc': ('Темы и шрифты.', 'Themes and fonts.', 'Теми й шрифти.', 'Themen und Schriftarten.', 'Thèmes et polices.', 'Temas y fuentes.', 'Motywy i czcionki.'),
    'customize_subtitle': ('Выберите оформление.', 'Choose appearance.', 'Оберіть оформлення.', 'Darstellung wählen.', 'Choisir l’apparence.', 'Elige apariencia.', 'Wybierz wygląd.'),
    'customize_title': ('Кастомизация', 'Customization', 'Кастомізація', 'Anpassen', 'Personnalisation', 'Personalización', 'Dostosowanie'),
    'detection': ('Обнаружение War Thunder', 'War Thunder detection', 'Виявлення War Thunder', 'War Thunder Erkennung', 'Détection de War Thunder', 'Detección de War Thunder', 'Wykrywanie War Thunder'),
    'error_message': ('Не удалось сохранить настройки:', 'Could not save settings:', 'Не вдалося зберегти:', 'Speichern fehlgeschlagen:', 'Impossible d’enregistrer :', 'No se pudo guardar:', 'Nie można zapisać:'),
    'error_title': ('Ошибка сохранения', 'Save error', 'Помилка збереження', 'Speicherfehler', 'Erreur d’enregistrement', 'Error al guardar', 'Błąd zapisu'),
    'font': ('Шрифт', 'Font', 'Шрифт', 'Schriftart', 'Police', 'Fuente', 'Czcionka'),
    'interface': ('Интерфейс', 'Interface', 'Інтерфейс', 'Oberfläche', 'Interface', 'Interfaz', 'Interfejs'),
    'language': ('Смена языка', 'Change language', 'Зміна мови', 'Sprache ändern', 'Changer de langue', 'Cambiar idioma', 'Zmień język'),
    'language_desc': ('7 языков.', '7 languages.', '7 мов.', '7 Sprachen.', '7 langues.', '7 idiomas.', '7 języków.'),
    'language_note': ('Сохраняется автоматически.', 'Saved automatically.', 'Зберігається автоматично.', 'Automatisch gespeichert.', 'Enregistré automatiquement.', 'Se guarda automáticamente.', 'Zapis automatyczny.'),
    'language_option': ('Язык интерфейса', 'Interface language', 'Мова інтерфейсу', 'Sprache der Oberfläche', 'Langue de l’interface', 'Idioma de interfaz', 'Język interfejsu'),
    'language_subtitle': ('Выберите язык.', 'Choose language.', 'Оберіть мову.', 'Sprache wählen.', 'Choisissez une langue.', 'Elige un idioma.', 'Wybierz język.'),
    'language_title': ('Смена языка', 'Change language', 'Зміна мови', 'Sprache ändern', 'Changer de langue', 'Cambiar idioma', 'Zmień język'),
    'minimize_tray': ('Сворачивать в трей', 'Minimize to tray', 'Згортати у трей', 'In Infobereich minimieren', 'Réduire dans la zone de notification', 'Minimizar a la bandeja', 'Minimalizuj do zasobnika'),
    'minimize_tray_desc': ('Вместо закрытия окна.', 'Instead of closing.', 'Замість закриття.', 'Statt das Fenster zu schließen.', 'Au lieu de fermer la fenêtre.', 'En lugar de cerrar.', 'Zamiast zamykać okno.'),
    'notifications': ('Уведомления', 'Notifications', 'Сповіщення', 'Benachrichtigungen', 'Notifications', 'Notificaciones', 'Powiadomienia'),
    'notifications_desc': ('Сообщения в трее.', 'System tray alerts.', 'Сповіщення у треї.', 'Meldungen im Infobereich.', 'Alertes de la zone de notification.', 'Avisos en la bandeja.', 'Powiadomienia w zasobniku.'),
    'off': ('Выключено', 'Disabled', 'Вимкнено', 'Deaktiviert', 'Désactivé', 'Desactivado', 'Wyłączone'),
    'on': ('Включено', 'Enabled', 'Увімкнено', 'Aktiviert', 'Activé', 'Activado', 'Włączone'),
    'personalization': ('Персонализация', 'Personalization', 'Персоналізація', 'Personalisierung', 'Personnalisation', 'Personalización', 'Personalizacja'),
    'personalization_desc': ('Внешний вид и язык.', 'Appearance and language.', 'Вигляд і мова.', 'Aussehen und Sprache.', 'Apparence et langue.', 'Apariencia e idioma.', 'Wygląd i język.'),
    'popup': ('Предлагать открыть менеджер', 'Show launch prompt', 'Пропонувати відкрити менеджер', 'Startdialog anzeigen', 'Proposer d’ouvrir le gestionnaire', 'Mostrar aviso de inicio', 'Pokaż okno uruchamiania'),
    'popup_desc': ('При запуске игры.', 'When the game starts.', 'Під час запуску гри.', 'Beim Spielstart.', 'Au lancement du jeu.', 'Al iniciar el juego.', 'Gdy gra się uruchamia.'),
    'preview_button': ('Пример кнопки', 'Sample button', 'Приклад кнопки', 'Beispielschaltfläche', 'Bouton exemple', 'Botón de ejemplo', 'Przykładowy przycisk'),
    'preview_text': ('Пример оформления', 'Appearance preview', 'Зразок оформлення', 'Designvorschau', 'Aperçu du thème', 'Vista previa', 'Podgląd wyglądu'),
    'preview_title': ('Предпросмотр', 'Preview', 'Перегляд', 'Vorschau', 'Aperçu', 'Vista previa', 'Podgląd'),
    'remember_tab': ('Запоминать вкладку', 'Remember last tab', 'Запам’ятовувати вкладку', 'Letzten Tab merken', 'Mémoriser le dernier onglet', 'Recordar última pestaña', 'Zapamiętaj kartę'),
    'remember_tab_desc': ('Открывать прошлую вкладку.', 'Restore the last tab.', 'Відновлювати вкладку.', 'Letzten Tab wieder öffnen.', 'Restaurer le dernier onglet.', 'Restaurar la última pestaña.', 'Przywracaj ostatnią kartę.'),
    'reset': ('Сбросить настройки', 'Reset settings', 'Скинути налаштування', 'Einstellungen zurücksetzen', 'Réinitialiser les paramètres', 'Restablecer ajustes', 'Zresetuj ustawienia'),
    'reset_complete': ('Настройки восстановлены', 'Settings restored', 'Налаштування відновлено', 'Einstellungen wiederhergestellt', 'Paramètres restaurés', 'Ajustes restaurados', 'Ustawienia przywrócone'),
    'reset_question': ('Сбросить все настройки?', 'Reset all settings?', 'Скинути всі налаштування?', 'Alle Einstellungen zurücksetzen?', 'Réinitialiser tous les paramètres ?', '¿Restablecer todos los ajustes?', 'Zresetować wszystkie ustawienia?'),
    'reset_title': ('Сброс настроек', 'Reset settings', 'Скидання налаштувань', 'Einstellungen zurücksetzen', 'Réinitialiser', 'Restablecer ajustes', 'Resetuj ustawienia'),
    'saved': ('Сохранено', 'Saved', 'Збережено', 'Gespeichert', 'Enregistré', 'Guardado', 'Zapisano'),
    'service': ('Сервис', 'Maintenance', 'Сервіс', 'Wartung', 'Maintenance', 'Mantenimiento', 'Narzędzia'),
    'service_desc': ('Настройки сохраняются автоматически.', 'Settings save automatically.', 'Налаштування зберігаються автоматично.', 'Einstellungen werden automatisch gespeichert.', 'Les paramètres sont enregistrés automatiquement.', 'Los ajustes se guardan automáticamente.', 'Ustawienia zapisują się automatycznie.'),
    'subtitle': ('Настройки WT Mod Manager', 'WT Mod Manager settings', 'Налаштування WT Mod Manager', 'WT Mod Manager Einstellungen', 'Paramètres de WT Mod Manager', 'Ajustes de WT Mod Manager', 'Ustawienia WT Mod Manager'),
    'system': ('Как в системе', 'Follow system', 'Як у системі', 'Systemeinstellung', 'Comme le système', 'Seguir sistema', 'Jak w systemie'),
    'theme': ('Цвет акцента', 'Accent color', 'Колір акценту', 'Akzentfarbe', 'Couleur d’accent', 'Color de acento', 'Kolor akcentu'),
    'title': ('Настройки приложения', 'Application settings', 'Налаштування програми', 'App-Einstellungen', 'Paramètres de l’application', 'Ajustes de la aplicación', 'Ustawienia aplikacji'),
    'volume': ('Громкость', 'Volume', 'Гучність', 'Lautstärke', 'Volume', 'Volumen', 'Głośność'),
    'white': ('Светлая', 'Light', 'Світла', 'Hell', 'Clair', 'Claro', 'Jasny'),
}

_SETTINGS.update({
    'color_custom': ('Свой цвет', 'Custom color', 'Власний колір', 'Eigene Farbe', 'Couleur personnalisée', 'Color personalizado', 'Własny kolor'),
    'intensity': ('Интенсивность темы', 'Theme intensity', 'Інтенсивність теми', 'Farbintensität', 'Intensité du thème', 'Intensidad del tema', 'Intensywność motywu'),
    'custom_hex': ('Цвет HEX', 'HEX color', 'Колір HEX', 'HEX-Farbe', 'Couleur HEX', 'Color HEX', 'Kolor HEX'),
    'apply_hex': ('Применить цвет', 'Apply color', 'Застосувати колір', 'Farbe anwenden', 'Appliquer', 'Aplicar color', 'Zastosuj kolor'),
    'invalid_hex': ('Введите цвет вида #AABBCC', 'Enter a color like #AABBCC', 'Введіть колір #AABBCC', 'Farbe wie #AABBCC eingeben', 'Saisir une couleur #AABBCC', 'Introduce un color #AABBCC', 'Wpisz kolor #AABBCC'),
    'animation_section': ('Анимации', 'Animations', 'Анімації', 'Animationen', 'Animations', 'Animaciones', 'Animacje'),
    'animations_enabled': ('Включить анимации', 'Enable animations', 'Увімкнути анімації', 'Animationen aktivieren', 'Activer les animations', 'Activar animaciones', 'Włącz animacje'),
    'animation_speed': ('Скорость анимаций', 'Animation speed', 'Швидкість анімацій', 'Animationsgeschwindigkeit', 'Vitesse des animations', 'Velocidad de animación', 'Prędkość animacji'),
    'presets': ('Пресеты оформления', 'Appearance presets', 'Пресети оформлення', 'Designvorlagen', 'Préréglages', 'Ajustes guardados', 'Presety wyglądu'),
    'preset_name': ('Название пресета', 'Preset name', 'Назва пресета', 'Name der Vorlage', 'Nom du préréglage', 'Nombre del ajuste', 'Nazwa presetu'),
    'save_preset': ('Сохранить пресет', 'Save preset', 'Зберегти пресет', 'Vorlage speichern', 'Enregistrer', 'Guardar ajuste', 'Zapisz preset'),
    'apply_preset': ('Применить', 'Apply', 'Застосувати', 'Anwenden', 'Appliquer', 'Aplicar', 'Zastosuj'),
    'delete_preset': ('Удалить пресет', 'Delete preset', 'Видалити пресет', 'Vorlage löschen', 'Supprimer', 'Eliminar ajuste', 'Usuń preset'),
    'preset_placeholder': ('Моя тема', 'My theme', 'Моя тема', 'Mein Design', 'Mon thème', 'Mi tema', 'Mój motyw'),
    'preset_choose': ('Выберите пресет', 'Choose a preset', 'Оберіть пресет', 'Vorlage auswählen', 'Choisir un préréglage', 'Elige un ajuste', 'Wybierz preset'),
    'preset_error': ('Не удалось сохранить пресет', 'Could not save preset', 'Не вдалося зберегти пресет', 'Vorlage konnte nicht gespeichert werden', 'Impossible d’enregistrer', 'No se pudo guardar', 'Nie można zapisać presetu'),

    # Reset buttons below intensity and animation speed sliders.
    'reset_slider': ('Сбросить', 'Reset', 'Скинути', 'Zurücksetzen', 'Réinitialiser', 'Restablecer', 'Zresetuj'),
    'reset_value': ('Сбросить', 'Reset', 'Скинути', 'Zurücksetzen', 'Réinitialiser', 'Restablecer', 'Zresetuj'),
})


# Russian UI text -> English, Ukrainian, German, French, Spanish, Polish.
_UI = {
    'WAR THUNDER ОБНАРУЖЕН': ('WAR THUNDER DETECTED', 'WAR THUNDER ВИЯВЛЕНО', 'WAR THUNDER ERKANNT', 'WAR THUNDER DÉTECTÉ', 'WAR THUNDER DETECTADO', 'WYKRYTO WAR THUNDER'),
    'Автоматически открывать менеджер': ('Open manager automatically', 'Відкривати менеджер автоматично', 'Manager automatisch öffnen', 'Ouvrir automatiquement le gestionnaire', 'Abrir gestor automáticamente', 'Otwieraj menedżer automatycznie'),
    'Аудио': ('Audio', 'Аудіо', 'Audio', 'Audio', 'Audio', 'Audio'),
    'Аудио не выбрано': ('No audio selected', 'Аудіо не вибрано', 'Kein Audio ausgewählt', 'Aucun audio sélectionné', 'Ningún audio seleccionado', 'Nie wybrano dźwięku'),
    'Аудиофайл не найден': ('Audio file not found', 'Аудіофайл не знайдено', 'Kein Audio ausgewählt', 'Aucun audio sélectionné', 'Ningún audio seleccionado', 'Nie znaleziono pliku audio'),
    'Библиотека звуков': ('Sound library', 'Бібліотека звуків', 'Soundbibliothek', 'Bibliothèque de sons', 'Biblioteca de sonidos', 'Biblioteka dźwięków'),
    'Воспроизведение остановлено': ('Playback stopped', 'Відтворення зупинено', 'Wiedergabe gestoppt', 'Lecture arrêtée', 'Reproducción detenida', 'Odtwarzanie'),
    'Воспроизводится': ('Playing', 'Відтворюється', 'Wiedergabe', 'Lecture', 'Reproduciendo', 'Odtwarzanie'),
    'Восстановить все стандартные настройки?': ('Restore all default settings?', 'Відновити всі типові налаштування?', 'Alle Standardeinstellungen wiederherstellen?', 'Restaurer tous les paramètres par défaut ?', '¿Restaurar todos los ajustes predeterminados?', 'Przywrócić wszystkie ustawienia domyślne?'),
    'Восстановить стандартные настройки': ('Restore default settings', 'Відновити типові налаштування', 'Standardeinstellungen wiederherstellen', 'Restaurer les paramètres par défaut', 'Restaurar ajustes predeterminados', 'Przywróć ustawienia domyślne'),
    'Восстановить стандартные настройки?': ('Restore default settings?', 'Відновити стандартні налаштування?', 'Standardeinstellungen wiederherstellen?', 'Restaurer les paramètres par défaut ?', '¿Restaurar ajustes predeterminados?', 'Przywrócić ustawienia domyślne?'),
    'Выберите аудиофайл': ('Select audio file', 'Виберіть аудіофайл', 'Audiodatei wählen', 'Choisir un fichier audio', 'Seleccionar archivo de audio', 'Wybierz plik audio'),
    'Выберите файл': ('Select file', 'Виберіть файл', 'Datei wählen', 'Choisir un fichier', 'Seleccionar archivo', 'Wybierz plik'),
    'Выберите файл для предпросмотра': ('Select a file to preview', 'Виберіть файл для перегляду', 'Datei für Vorschau wählen', 'Sélectionnez un fichier', 'Selecciona un archivo', 'Wybierz plik do podglądu'),
    'Выберите файл для прослушивания': ('Select an audio file', 'Виберіть аудіофайл', 'Audiodatei auswählen', 'Choisissez un fichier audio', 'Elige un archivo de audio', 'Wybierz plik audio'),
    'Выбранный файл больше не существует.': ('The selected file no longer exists.', 'Вибраного файлу більше немає.', 'Die Datei existiert nicht mehr.', 'Le fichier n’existe plus.', 'El archivo ya no existe.', 'Wybrany plik już nie istnieje.'),
    'Выбрать изображение прицела': ('Select sight image', 'Виберіть зображення прицілу', 'Visierbild wählen', 'Sélectionner une image de viseur', 'Seleccionar imagen de mira', 'Wybierz obraz celownika'),
    'Выход': ('Exit', 'Вихід', 'Beenden', 'Quitter', 'Salir', 'Wyjdź'),
    'Готово к воспроизведению': ('Ready to play', 'Готово до відтворення', 'Bereit zur Wiedergabe', 'Prêt à lire', 'Listo para reproducir', 'Gotowe do odtwarzania'),
    'Громкость': ('Volume', 'Гучність', 'Lautstärke', 'Volume', 'Volumen', 'Głośność'),
    'Да, открыть': ('Yes, open', 'Так, відкрити', 'Ja, öffnen', 'Oui, ouvrir', 'Sí, abrir', 'Tak, otwórz'),
    'Добавить': ('Add', 'Додати', 'Hinzufügen', 'Ajouter', 'Añadir', 'Dodaj'),
    'Добавляйте звуковые файлы, прослушивайте их и управляйте своей библиотекой.': ('Import, preview and manage sounds.', 'Додавайте та прослуховуйте звуки.', 'Sounds importieren und anhören.', 'Ajoutez et écoutez vos sons.', 'Añade y escucha tus sonidos.', 'Dodawaj i odsłuchuj dźwięki.'),
    'Добавляйте камуфляжи и текстуры, просматривайте изображения и управляйте своей библиотекой.': ('Import and preview camouflage textures.', 'Імпортуйте й переглядайте камуфляжі.', 'Tarntexturen importieren und ansehen.', 'Importez et visualisez les camouflages.', 'Importa y visualiza camuflajes.', 'Importuj i przeglądaj kamuflaże.'),
    'Загружай изображения прицелов, выбирай их и смотри предпросмотр.': ('Import and preview custom sight images.', 'Імпортуйте та переглядайте приціли.', 'Visierbilder importieren und ansehen.', 'Importez et prévisualisez vos viseurs.', 'Importa y previsualiza miras.', 'Importuj i przeglądaj celowniki.'),
    'Замена файла': ('Replace file', 'Замінити файл', 'Datei ersetzen', 'Remplacer le fichier', 'Reemplazar archivo', 'Zastąp plik'),
    'Запоминать последнюю вкладку': ('Remember last tab', 'Запам’ятовувати останню вкладку', 'Letzten Tab merken', 'Mémoriser le dernier onglet', 'Recordar última pestaña', 'Zapamiętaj ostatnią kartę'),
    'Запустить менеджер модификаций?\nСохранённые настройки останутся без изменений.': ('Open the mod manager?\nYour settings will be preserved.', 'Відкрити менеджер модів?\nНалаштування збережуться.', 'Mod-Manager öffnen?\nEinstellungen bleiben erhalten.', 'Ouvrir le gestionnaire de mods ?\nVos paramètres seront conservés.', '¿Abrir el gestor de mods?\nSe conservarán tus ajustes.', 'Otworzyć menedżera modów?\nUstawienia zostaną zachowane.'),
    'Звуки': ('Sounds', 'Звуки', 'Sounds', 'Sons', 'Sonidos', 'Dźwięki'),
    'Звуковые модификации': ('Sound modifications', 'Звукові модифікації', 'Sound-Modifikationen', 'Modifications sonores', 'Modificaciones de sonido', 'Modyfikacje dźwięku'),
    'Здесь будет предпросмотр прицела': ('Sight preview appears here', 'Тут буде перегляд прицілу', 'Visiervorschau erscheint hier', 'Aperçu du viseur ici', 'Vista previa de la mira', 'Tutaj podgląd celownika'),
    'Здесь можно будет создавать, сохранять, загружать и удалять пользовательские конфигурации.': ('Create and manage profiles here.', 'Тут можна створювати й керувати профілями.', 'Hier Profile erstellen und verwalten.', 'Créez et gérez les profils ici.', 'Crea y administra perfiles aquí.', 'Twórz i zarządzaj profilami tutaj.'),
    'Интерфейс': ('Interface', 'Інтерфейс', 'Oberfläche', 'Interface', 'Interfaz', 'Interfejs'),
    'Исходный файл не найден.': ('Source file not found.', 'Вихідний файл не знайдено.', 'Quelldatei nicht gefunden.', 'Fichier source introuvable.', 'Archivo de origen no encontrado.', 'Nie znaleziono pliku źródłowego.'),
    'Камуфляжи': ('Camouflages', 'Камуфляжі', 'Tarnungen', 'Camouflages', 'Camuflajes', 'Kamuflaże'),
    'Кастомизация': ('Customization', 'Налаштування вигляду', 'Anpassung', 'Personnalisation', 'Personalización', 'Personalizacja'),
    'Конфигурации': ('Configurations', 'Конфігурації', 'Konfigurationen', 'Configurations', 'Configuraciones', 'Konfiguracje'),
    'Настройки': ('Settings', 'Налаштування', 'Einstellungen', 'Paramètres', 'Ajustes', 'Ustawienia'),
    'Настройки приложения': ('Application settings', 'Налаштування програми', 'App-Einstellungen', 'Paramètres de l’application', 'Ajustes de la aplicación', 'Ustawienia aplikacji'),
    'Настройки сохранены': ('Settings saved', 'Налаштування збережено', 'Einstellungen gespeichert', 'Paramètres enregistrés', 'Ajustes guardados', 'Ustawienia zapisane'),
    'Не удалось воспроизвести файл.': ('Could not play file.', 'Не вдалося відтворити файл.', 'Datei konnte nicht abgespielt werden.', 'Lecture du fichier impossible.', 'No se pudo reproducir el archivo.', 'Nie można odtworzyć pliku.'),
    'Не удалось загрузить изображение': ('Could not load image', 'Не вдалося завантажити зображення', 'Bild konnte nicht geladen werden', 'Impossible de charger l’image', 'No se pudo cargar la imagen', 'Nie można wczytać obrazu'),
    'Не удалось открыть изображение': ('Could not open image', 'Не вдалося відкрити зображення', 'Bild konnte nicht geöffnet werden', 'Impossible d’ouvrir l’image', 'No se pudo abrir la imagen', 'Nie można otworzyć obrazu'),
    'Неподдерживаемый или повреждённый файл': ('Unsupported or damaged file', 'Непідтримуваний або пошкоджений файл', 'Nicht unterstützte oder beschädigte Datei', 'Fichier non pris en charge ou endommagé', 'Archivo no compatible o dañado', 'Nieobsługiwany lub uszkodzony plik'),
    'Неподдерживаемый формат аудио.': ('Unsupported audio format.', 'Непідтримуваний формат аудіо.', 'Audioformat nicht unterstützt.', 'Format audio non pris en charge.', 'Formato de audio no compatible.', 'Nieobsługiwany format audio.'),
    'Нет выбранного файла': ('No selected file', 'Файл не вибрано', 'Keine Datei ausgewählt', 'Aucun fichier sélectionné', 'Ningún archivo seleccionado', 'Nie wybrano pliku'),
    'Нет доступных прицелов': ('No sights available', 'Немає прицілів', 'Keine Visiere vorhanden', 'Aucun viseur disponible', 'No hay miras disponibles', 'Brak celowników'),
    'Нет, пропустить': ('No, skip', 'Ні, пропустити', 'Nein, überspringen', 'Non, ignorer', 'No, omitir', 'Nie, pomiń'),
    'Обнаружение War Thunder': ('War Thunder detection', 'Виявлення War Thunder', 'War Thunder-Erkennung', 'Détection de War Thunder', 'Detección de War Thunder', 'Wykrywanie War Thunder'),
    'Обновить': ('Refresh', 'Оновити', 'Aktualisieren', 'Actualiser', 'Actualizar', 'Odśwież'),
    'Открыть менеджер': ('Open manager', 'Відкрити менеджер', 'Manager öffnen', 'Ouvrir le gestionnaire', 'Abrir gestor', 'Otwórz menedżer'),
    'Ошибка': ('Error', 'Помилка', 'Fehler', 'Erreur', 'Error', 'Błąd'),
    'Ошибка аудио': ('Audio error', 'Помилка аудіо', 'Audiofehler', 'Erreur audio', 'Error de audio', 'Błąd audio'),
    'Ошибка воспроизведения': ('Playback error', 'Помилка відтворення', 'Wiedergabefehler', 'Erreur de lecture', 'Error de reproducción', 'Błąd odtwarzania'),
    'Ошибка импорта': ('Import error', 'Помилка імпорту', 'Importfehler', 'Erreur d’importation', 'Error de importación', 'Błąd importu'),
    'Ошибка удаления': ('Deletion error', 'Помилка видалення', 'Löschfehler', 'Erreur de suppression', 'Error al eliminar', 'Błąd usuwania'),
    'Папка mods/sights пуста': ('The mods/sights folder is empty', 'Папка mods/sights порожня', 'Ordner mods/sights ist leer', 'Dossier mods/sights vide', 'Carpeta mods/sights vacía', 'Folder mods/sights jest pusty'),
    'Пауза': ('Paused', 'Пауза', 'Pause', 'Pause', 'Pausa', 'Pauza'),
    'Поверх остальных окон': ('Always on top', 'Поверх інших вікон', 'Immer im Vordergrund', 'Toujours au premier plan', 'Siempre visible', 'Zawsze na wierzchu'),
    'Поддерживаемые форматы: WAV, MP3, OGG, FLAC': ('Supported formats: WAV, MP3, OGG, FLAC', 'Формати: WAV, MP3, OGG, FLAC', 'Formate: WAV, MP3, OGG, FLAC', 'Formats : WAV, MP3, OGG, FLAC', 'Formatos: WAV, MP3, OGG, FLAC', 'Formaty: WAV, MP3, OGG, FLAC'),
    'Подтверждение': ('Confirmation', 'Підтвердження', 'Bestätigung', 'Confirmation', 'Confirmación', 'Potwierdź usunięcie'),
    'Подтверждение удаления': ('Confirm deletion', 'Підтвердження видалення', 'Löschen bestätigen', 'Confirmer la suppression', 'Confirmar eliminación', 'Potwierdź usunięcie'),
    'Показывать предложение запуска': ('Show launch prompt', 'Показувати запит запуску', 'Startabfrage anzeigen', 'Afficher la demande de lancement', 'Mostrar aviso de inicio', 'Pokaż monit uruchomienia'),
    'Показывать уведомления в трее': ('Show tray notifications', 'Показувати сповіщення в треї', 'Tray-Benachrichtigungen anzeigen', 'Afficher les notifications système', 'Mostrar notificaciones de bandeja', 'Pokaż powiadomienia w zasobniku'),
    'Пользовательские камуфляжи': ('Custom camouflages', 'Користувацькі камуфляжі', 'Eigene Tarnungen', 'Camouflages personnalisés', 'Camuflajes personalizados', 'Kamuflaże użytkownika'),
    'Пользовательские прицелы': ('Custom sights', 'Користувацькі приціли', 'Benutzerdefinierte Visiere', 'Viseurs personnalisés', 'Miras personalizadas', 'Celowniki niestandardowe'),
    'Предпросмотр': ('Preview', 'Попередній перегляд', 'Vorschau', 'Aperçu', 'Vista previa', 'Podgląd'),
    'Предпросмотр аудио': ('Audio preview', 'Прослуховування аудіо', 'Audiovorschau', 'Aperçu audio', 'Vista previa de audio', 'Podgląd audio'),
    'Прицелы': ('Sights', 'Приціли', 'Visiere', 'Viseurs', 'Miras', 'Celowniki'),
    'Профили и конфигурации': ('Profiles and configurations', 'Профілі та конфігурації', 'Profile und Konfigurationen', 'Profils et configurations', 'Perfiles y configuraciones', 'Profile i konfiguracje'),
    'Сброс настроек': ('Reset settings', 'Скинути налаштування', 'Einstellungen zurücksetzen', 'Réinitialiser les paramètres', 'Restablecer ajustes', 'Resetuj ustawienia'),
    'Сворачивать в трей при закрытии': ('Minimize to tray on close', 'Згортати в трей під час закриття', 'Beim Schließen in Tray minimieren', 'Réduire dans la zone de notification', 'Minimizar a bandeja al cerrar', 'Minimalizuj do zasobnika przy zamknięciu'),
    'Сервис': ('Maintenance', 'Обслуговування', 'Wartung', 'Maintenance', 'Mantenimiento', 'Konserwacja'),
    'Скрыть менеджер': ('Hide manager', 'Приховати менеджер', 'Manager ausblenden', 'Masquer le gestionnaire', 'Ocultar gestor', 'Ukryj menedżer'),
    'Смена языка': ('Change language', 'Змінити мову', 'Sprache ändern', 'Changer de langue', 'Cambiar idioma', 'Zmień język'),
    'Сначала выбери прицел из списка.': ('Select a sight first.', 'Спочатку виберіть приціл.', 'Bitte zuerst Visier wählen.', 'Choisissez d’abord un viseur.', 'Primero elige una mira.', 'Najpierw wybierz celownik.'),
    'Сначала выберите звук.': ('Select a sound first.', 'Спочатку виберіть звук.', 'Bitte zuerst Sound wählen.', 'Choisissez d’abord un son.', 'Primero selecciona un sonido.', 'Najpierw wybierz dźwięk.'),
    'Сначала выберите звуковой файл.': ('Select an audio file first.', 'Спочатку виберіть аудіофайл.', 'Zuerst Audiodatei wählen.', 'Choisissez d’abord un fichier audio.', 'Primero selecciona un archivo de audio.', 'Najpierw wybierz plik audio.'),
    'Сначала выберите файл.': ('Select a file first.', 'Спочатку виберіть файл.', 'Bitte zuerst Datei wählen.', 'Choisissez d’abord un fichier.', 'Primero selecciona un archivo.', 'Najpierw wybierz plik.'),
    'Список прицелов': ('Sight library', 'Список прицілів', 'Visierliste', 'Liste des viseurs', 'Lista de miras', 'Lista celowników'),
    'Список: ': ('Library: ', 'Список: ', 'Liste: ', 'Liste : ', 'Lista: ', 'Lista: '),
    'Список: камуфляжи': ('Camouflage library', 'Список камуфляжів', 'Tarnungsliste', 'Liste des camouflages', 'Lista de camuflajes', 'Lista kamuflaży'),
    'Текущий выбранный прицел: ': ('Selected sight: ', 'Обраний приціл: ', 'Ausgewähltes Visier: ', 'Viseur sélectionné : ', 'Mira seleccionada: ', 'Wybrany celownik: '),
    'Текущий выбранный прицел: нет': ('Selected sight: none', 'Обраний приціл: немає', 'Ausgewähltes Visier: keines', 'Viseur sélectionné : aucun', 'Mira seleccionada: ninguna', 'Wybrany celownik: brak'),
    'Удаление': ('Delete', 'Видалення', 'Löschen', 'Suppression', 'Eliminar', 'Usuwanie'),
    'Удалить': ('Delete', 'Видалити', 'Löschen', 'Supprimer', 'Eliminar', 'Usuń'),
    'Файл не выбран': ('No file selected', 'Файл не вибрано', 'Keine Datei ausgewählt', 'Aucun fichier sélectionné', 'Ningún archivo seleccionado', 'Nie wybrano pliku'),
    'Файл не найден': ('File not found', 'Файл не знайдено', 'Datei nicht gefunden', 'Fichier introuvable', 'Archivo no encontrado', 'Nie znaleziono pliku'),
    'Файл не является поддерживаемым изображением.': ('Unsupported image.', 'Непідтримуване зображення.', 'Nicht unterstütztes Bild.', 'Image non prise en charge.', 'Imagen no compatible.', 'Nieobsługiwany obraz.'),
    'Ⅱ Пауза': ('Ⅱ Pause', 'Ⅱ Пауза', 'Ⅱ Pause', 'Ⅱ Pause', 'Ⅱ Pausa', 'Ⅱ Pauza'),
    '■ Стоп': ('■ Stop', '■ Стоп', '■ Stopp', '■ Arrêter', '■ Detener', '■ Stop'),
    '▶ Играть': ('▶ Play', '▶ Відтворити', '▶ Abspielen', '▶ Lire', '▶ Reproducir', '▶ Odtwórz'),
    '▶ Продолжить': ('▶ Resume', '▶ Продовжити', '▶ Fortsetzen', '▶ Reprendre', '▶ Continuar', '▶ Wznów'),
    '● MANAGER READY': ('● MANAGER READY', '● МЕНЕДЖЕР ГОТОВИЙ', '● MANAGER BEREIT', '● GESTIONNAIRE PRÊT', '● GESTOR LISTO', '● MENEDŻER GOTOWY'),
    '● WT MOD MANAGER READY': ('● WT MOD MANAGER READY', '● WT MOD MANAGER ГОТОВИЙ', '● WT MOD MANAGER BEREIT', '● WT MOD MANAGER PRÊT', '● WT MOD MANAGER LISTO', '● WT MOD MANAGER GOTOWY'),
}

_DYNAMIC = {
    'Удалить прицел ': ('Delete sight ', 'Видалити приціл ', 'Visier löschen: ', 'Supprimer le viseur ', 'Eliminar mira ', 'Usunąć celownik '),
    'Удалить файл ': ('Delete file ', 'Видалити файл ', 'Datei löschen: ', 'Supprimer le fichier ', 'Eliminar archivo ', 'Usuń plik '),
    'Удалить ': ('Delete ', 'Видалити ', 'Löschen: ', 'Supprimer ', 'Eliminar ', 'Usuń '),
    ' из библиотеки менеджера?': (' from the manager library?', ' з бібліотеки менеджера?', ' aus der Bibliothek?', ' de la bibliothèque ?', ' de la biblioteca?', ' z biblioteki?'),
    'Файл ': ('File ', 'Файл ', 'Datei ', 'Fichier ', 'Archivo ', 'Plik '),
    ' уже существует.': (' already exists.', ' вже існує.', ' existiert bereits.', ' existe déjà.', ' ya existe.', ' już istnieje.'),
    'Звук ': ('Sound ', 'Звук ', 'Sound ', 'Son ', 'Sonido ', 'Dźwięk '),
}


def _language(language):
    return language if language in LANGUAGES else "ru"


def tr(key, language="ru"):
    """Translate a SettingsPage translation key."""
    language = _language(language)
    variants = _SETTINGS.get(key)

    if variants is None:
        return key

    if language == "ru":
        return variants[0]

    return variants[1 + _CODES.index(language)]


def translate_ui(source, language="ru"):
    """Translate common UI text while preserving filenames."""
    if not isinstance(source, str):
        return source

    language = _language(language)

    if language == "ru":
        return source

    pos = _CODES.index(language)
    variants = _UI.get(source)

    if variants is not None:
        return variants[pos]

    for prefix, variants in _UI.items():
        if prefix.endswith(": ") and source.startswith(prefix):
            return variants[pos] + source[len(prefix):]

    for prefix, variants in _UI.items():
        if source.startswith(prefix + ": "):
            return variants[pos] + ": " + source[len(prefix) + 2:]

    return source


def translate_dynamic(message, language="ru"):
    """Translate messages containing filenames and dynamic values."""
    if not isinstance(message, str):
        return message

    language = _language(language)

    if language == "ru":
        return message

    translated = translate_ui(message, language)

    if translated != message:
        return translated

    pos = _CODES.index(language)

    for source, variants in sorted(
        _DYNAMIC.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        translated = translated.replace(source, variants[pos])

    for source, variants in _UI.items():
        if source.endswith(": ") and source in translated:
            translated = translated.replace(source, variants[pos])

    return translated


def missing_translations():
    """Check that all entries have the required number of translations."""
    return [
        name
        for name, table in (
            ("settings", _SETTINGS),
            ("ui", _UI),
            ("dynamic", _DYNAMIC),
        )
        for key, row in table.items()
        if len(row) != (7 if name == "settings" else 6)
    ]
