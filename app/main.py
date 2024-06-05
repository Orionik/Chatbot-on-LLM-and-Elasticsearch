from fastapi import FastAPI
from elasticsearch import Elasticsearch
from pydantic import BaseModel
from openai import OpenAI




# Импорт моделей данных
class Doc(BaseModel):
    """
    Модель данных для документа.

    - id: Строковый идентификатор документа.
    - text: Текст документа (необязательный).
    """
    id: str
    text: str | None = None


class Searcher(BaseModel):
    """
    Модель данных для поиска.

    - text: Строковый запрос для поиска документа.
    """
    text: str | None = None




# Создание клиентов для Elasticsearch и OpenAI
client = Elasticsearch("http://localhost:9200")
lm_client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

app = FastAPI() # Создаем экземпляр FastAPI




# API-эндпоинт для поиска документа
@app.get("/find_doc")
async def find_doc(promt: Searcher):
    """
    API-эндпоинт для поиска документа по запросу пользователя.

    - promt: Объект типа Searcher, содержащий текстовый запрос пользователя.

    Выполняет поиск документа в Elasticsearch по полю "text" на основе запроса пользователя.
    Использует LM Studio для генерации ответа на основе найденных документов.

    Возвращает сгенерированный ответ.
    """

    # Поиск документов в Elasticsearch
    resp = await client.search(index="my_index", # Имя индекса в Elasticsearch
                               query={"match": {"text": {"query": promt.text}}}, # Запрос для поиска
                               min_score=10 # Минимальный рейтинг документа для попадания в результат
    )

    # Обработка результатов поиска
    val = []    # Список найденных документов
    resp.body["hits"]["max_score"]
    for doc in resp.body["hits"]["hits"]:
        if doc["_score"] >= resp.body["hits"]["max_score"]*0.75:    # Фильтрация по минимальному рейтингу
            val.append("".join(doc["_source"]["text"])) # Добавление текста документа в список
            print(doc["_id"])   # Печать ID документа (для отладки)
            val.append("\n")    # Добавление переноса строки между документами

    # Формирование истории взаимодействия (контекста) для LM Studio
    history = [
        {"role": "system", "content": f"Сейчас пользователь задаст тебе вопрос. Отвечай на вопрос, используя только этот текст: {"".join(val)}"},   # Инструкции для LM Studio
        {"role": "user", "content": promt.text},
        ]

    # Генерация ответа с помощью LM Studio
    completion = await lm_client.chat.completions.create(
            model="local-model",    # Модель LM Studio (может быть не использовано)
            messages=history,
            temperature=0.7,    # Температура LM Studio (контролирует креативность ответа)
            stream=True,    # Потоковая передача результатов
            max_tokens=500  # Максимальное количество токенов для ответа
        )

    # Сбор сгенерированного ответа
    new_message = await {"role": "assistant", "content": ""}
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)   # Печать ответа (для отладки)
            new_message["content"] += chunk.choices[0].delta.content    # Добавление ответа в словарь

    return await new_message["content"] # Возврат сгенерированного ответа


# API-эндпоинт для добавления документа
@app.post("/add_doc")
async def add_do(doc: Doc):
    """
    API-эндпоинт для добавления документа в Elasticsearch.

    - doc: Объект типа Doc, содержащий информацию о документе.

    Добавляет документ в индекс "my_index" Elasticsearch.

    Возвращает подтверждение добавления документа.
    """
    print(doc)
    client.index(
    index="my_index",
    id=doc.id,
    document={"text": doc.text}
)
    return await {"All": "Is good"}




#uvicorn bd_service.app.main:app --reload
