
from ui.media_page import MediaPage


class CamouflagesPage(MediaPage):
    def __init__(self):
        super().__init__(
            title="Пользовательские камуфляжи",
            description=(
                "Добавляйте камуфляжи и текстуры, "
                "просматривайте изображения и "
                "управляйте своей библиотекой."
            ),
            folder="camouflages",
            item_name="камуфляжи"
        )
