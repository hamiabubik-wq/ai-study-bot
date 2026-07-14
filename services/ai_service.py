from google import genai
from google.genai import types


class StudyAI:
    def __init__(self, api_key: str, model: str, proxy_url: str | None = None) -> None:
        http_options = None
        if proxy_url:
            # generate_content вызывается синхронно (через asyncio.to_thread),
            # поэтому Gemini SDK использует синхронный httpx-клиент -> client_args.
            http_options = types.HttpOptions(
                client_args={"proxy": proxy_url},
                async_client_args={"proxy": proxy_url},
            )
        self.client = genai.Client(api_key=api_key, http_options=http_options)
        self.model = model

    @staticmethod
    def _prompt(school_class: int, subject: str, task: str | None = None) -> str:
        task_part = task or "Задание находится на приложенной фотографии."
        return f"""
Ты — внимательный школьный преподаватель и репетитор.
Ученик учится в {school_class} классе.
Предмет: {subject}.

Задание:
{task_part}

Требования к ответу:
1. Сначала внимательно определи условие задания. Если на фото часть задания не читается, честно укажи, что именно не видно, и не выдумывай данные.
2. Дай подробное решение по шагам, подходящее ученику {school_class} класса.
3. Используй правила, формулы, определения или грамматику, которые нужны для решения.
4. После решения обязательно добавь отдельный раздел «Ответ».
5. Затем добавь раздел «Объяснение простыми словами», чтобы ученик понял тему, а не просто переписал результат.
6. Для русского и английского языка объясняй правила и исправления. Для литературы и истории отделяй факты от интерпретации. Для точных наук проверяй вычисления.
7. Не используй слишком сложные термины без объяснения.
8. Отвечай на русском языке, кроме тех мест, где по заданию нужен английский текст.

Структура ответа:
📌 Условие
🧩 Подробное решение
✅ Ответ
💡 Объяснение простыми словами
""".strip()

    def solve_text(self, school_class: int, subject: str, task: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=self._prompt(school_class, subject, task),
            config=types.GenerateContentConfig(temperature=0.25),
        )
        return response.text or "Не удалось получить текст ответа."

    def solve_image(
        self,
        school_class: int,
        subject: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                image_part,
                self._prompt(school_class, subject),
            ],
            config=types.GenerateContentConfig(temperature=0.2),
        )
        return response.text or "Не удалось получить текст ответа."
