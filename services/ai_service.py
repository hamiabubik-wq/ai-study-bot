import re

from google import genai
from google.genai import types


class StudyAI:
    def __init__(self, api_key: str, model: str, proxy_url: str | None = None) -> None:
        http_options = None
        if proxy_url:
            http_options = types.HttpOptions(
                client_args={"proxy": proxy_url},
                async_client_args={"proxy": proxy_url},
            )
        self.client = genai.Client(api_key=api_key, http_options=http_options)
        self.model = model

    @staticmethod
    def _is_exact_subject(subject: str) -> bool:
        subject = subject.lower()

        return any(
            name in subject
            for name in (
                "математика",
                "физика",
                "химия",
            )
        )

    @staticmethod
    def _prompt(
        school_class: int,
        subject: str,
        task: str | None = None,
    ) -> str:
        task_part = task or (
            "Задание находится на приложенной фотографии. "
            "Сначала внимательно распознай его."
        )

        return f"""
Ты — очень внимательный школьный учитель и репетитор.

Класс ученика: {school_class}
Предмет: {subject}

Задание:
{task_part}

Главные правила:

1. Сначала точно определи условие задания.
2. Не придумывай числа, слова, знаки или данные, которых нет.
3. Если фотография нечёткая или часть задания обрезана, не угадывай.
4. Если не видно хотя бы одного важного символа, попроси прислать новое фото.
5. Решай задание строго по шагам.
6. Не пропускай вычисления и преобразования.
7. После решения обязательно проверь результат.
8. Если первая проверка показала ошибку, исправь решение до отправки.
9. Не пиши уверенный ответ, если не уверен в условии.
10. Объясняй на уровне ученика {school_class} класса.

Правила для математики:

- Проверяй каждое арифметическое действие.
- Отдельно проверяй знаки плюс и минус.
- Проверяй скобки, дроби, степени и корни.
- После решения подставляй ответ обратно, если это возможно.
- Для вычислений используй Python, если он доступен.
- Не округляй результат без необходимости.

Правила для физики:

- Выпиши дано.
- Укажи, что нужно найти.
- Запиши формулу.
- Проверь единицы измерения.
- Переведи величины в систему СИ, если это нужно.
- Подставь числа отдельно.
- Проверь итоговое значение.

Правила для химии:

- Проверяй индексы химических элементов.
- Проверяй коэффициенты уравнения.
- Не путай индексы и коэффициенты.
- Проверяй молярные массы и арифметику.

Правила для русского и английского языка:

- Сначала укажи правило.
- Затем выполни задание.
- Объясни каждое исправление.
- Не исправляй слова без объяснения причины.

Правила для литературы и истории:

- Не придумывай цитаты, даты, авторов и события.
- Не выдавай предположение за факт.
- Если точного ответа нет, честно скажи об этом.

Правила оформления для Telegram:

- Никогда не используй LaTeX.
- Не используй символы $ и $$.
- Не используй команды вида:
  \\vec
  \\sqrt
  \\frac
  \\cdot
  \\times
  \\left
  \\right
  \\begin
  \\end

Формулы пиши обычным текстом.

Примеры правильного оформления:

|a| = √(6² + 8²)

x² + 5x + 6 = 0

a / b

2 · 5 = 10

вектор a

Не пиши формулы внутри символов $.

Формат ответа:

📌 Условие

Кратко и точно перепиши условие.

🧩 Подробное решение

Покажи все шаги решения.

🔍 Проверка

Проверь вычисления, логику, правила или подстановку ответа.

✅ Ответ

Напиши только окончательный ответ.

💡 Объяснение простыми словами

Объясни, почему решение именно такое.
""".strip()

    @staticmethod
    def _clean_ai_text(text: str) -> str:
        if not text:
            return "Не удалось получить текст ответа."

        # Убираем Markdown-разметку формул
        text = text.replace("$$", "")
        text = text.replace("$", "")

        # Заменяем основные LaTeX-команды
        replacements = {
            "\\cdot": "·",
            "\\times": "×",
            "\\div": "÷",
            "\\pm": "±",
            "\\neq": "≠",
            "\\leq": "≤",
            "\\geq": "≥",
            "\\approx": "≈",
            "\\infty": "∞",
            "\\pi": "π",
            "\\degree": "°",
            "\\%": "%",
            "\\,": " ",
            "\\;": " ",
            "\\:": " ",
            "\\!": "",
            "\\(": "",
            "\\)": "",
            "\\[": "",
            "\\]": "",
            "\\left": "",
            "\\right": "",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Векторы: \vec{a} -> вектор a
        text = re.sub(
            r"\\vec\{([^{}]+)\}",
            r"вектор \1",
            text,
        )

        # Корни: \sqrt{100} -> √(100)
        text = re.sub(
            r"\\sqrt\{([^{}]+)\}",
            r"√(\1)",
            text,
        )

        # Степень корня: \sqrt[3]{8} -> ³√(8)
        text = re.sub(
            r"\\sqrt\[3\]\{([^{}]+)\}",
            r"³√(\1)",
            text,
        )

        # Дроби: \frac{a}{b} -> (a) / (b)
        text = re.sub(
            r"\\frac\{([^{}]+)\}\{([^{}]+)\}",
            r"(\1) / (\2)",
            text,
        )

        # Степени
        superscripts = {
            "^2": "²",
            "^3": "³",
            "^4": "⁴",
            "^5": "⁵",
            "^6": "⁶",
            "^7": "⁷",
            "^8": "⁸",
            "^9": "⁹",
        }

        for old, new in superscripts.items():
            text = text.replace(old, new)

        # Убираем команды оформления
        text = re.sub(
            r"\\(?:textbf|mathbf|mathrm|textit|text)\{([^{}]+)\}",
            r"\1",
            text,
        )

        # Убираем оставшиеся простые LaTeX-команды
        text = re.sub(
            r"\\[a-zA-Z]+",
            "",
            text,
        )

        # Убираем лишние фигурные скобки
        text = text.replace("{", "")
        text = text.replace("}", "")

        # Не больше двух пустых строк подряд
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    def _generate(
        self,
        contents,
        subject: str,
    ) -> str:
        config = types.GenerateContentConfig()

        if self._is_exact_subject(subject):
            config = types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        code_execution=types.ToolCodeExecution
                    )
                ]
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        answer = response.text or ""

        return self._clean_ai_text(answer)

    def solve_text(
        self,
        school_class: int,
        subject: str,
        task: str,
    ) -> str:
        prompt = self._prompt(
            school_class=school_class,
            subject=subject,
            task=task,
        )

        return self._generate(
            contents=prompt,
            subject=subject,
        )

    def solve_image(
        self,
        school_class: int,
        subject: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        prompt = self._prompt(
            school_class=school_class,
            subject=subject,
        )

        return self._generate(
            contents=[
                image_part,
                prompt,
            ],
            subject=subject,
        )