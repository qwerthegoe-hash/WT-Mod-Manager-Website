
from ui.media_page import MediaPage


class CamouflagesPage(MediaPage):
    def __init__(self):
        super().__init__(
            title="Пользовательские камуфляжи",
            description=(
                "Создавайте локальные камуфляжи для конкретной техники. "
                "Выберите картинку или готовый набор, укажите созданный "
                "в игре шаблон транспорта и подтвердите установку."
            ),
            folder="camouflages",
            item_name="камуфляжи"
        )
