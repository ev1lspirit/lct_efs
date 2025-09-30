from functools import partial
from pprint import pprint
from pymongo import MongoClient
from bson.objectid import ObjectId
from typing import Optional, Dict, Any

import pymongo
import pymongo.errors
from config import settings


class MongoDBClient:
    def __init__(self, database: str, collection: str):
        self.client = MongoClient(settings.mongo_url)
        self.db = self.client[database]
        self.collection = self.db[collection]

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        try:
            document = self.collection.find_one({"_id": ObjectId(id)})
            if document:
                # Преобразуем ObjectId в строку для JSON-сериализации
                document["_id"] = str(document["_id"])
            return document
        except Exception as e:
            print(f"Error retrieving document: {e}")
            return None

    def get_all(self, filter: Optional[Dict[str, Any]] = None) -> list:
        """
        Get all items from a collection.

        Args:
            filter (Optional[Dict[str, Any]]): Filter to apply to collection.

        Returns:
            list: List of items.
        """
        return list(self.db[self.collection.name].find(filter))

    def retrieve_description(self, description_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает JSON-описание по ID.
        Args:
            description_id: ID документа в MongoDB
        Returns:
            Словарь с данными или None, если документ не найден
        """
        try:
            document = self.collection.find_one({"_id": ObjectId(description_id)})
            if document:
                # Преобразуем ObjectId в строку для JSON-сериализации
                document["_id"] = str(document["_id"])
            return document
        except Exception as e:
            print(f"Error retrieving document: {e}")
            return None

    def update_description(
        self, description_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """
        Обновляет JSON-описание по ID.
        Args:
            description_id: ID документа в MongoDB
            update_data: Данные для обновления
        Returns:
            True если обновление успешно, False в случае ошибки
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(description_id)}, {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    def insert_description(self, description_data: Dict[str, Any], overriden_id: str = None) -> Optional[str]:
        """
        Добавляет новое JSON-описание в коллекцию.
        Args:
            description_data: Данные для вставки
        Returns:
            ID вставленного документа в виде строки или None в случае ошибки
        """
        try:
            if overriden_id:
                description_data["_id"] = ObjectId(overriden_id)
            result = self.collection.insert_one(description_data)
            return str(result.inserted_id)
        except pymongo.errors.DuplicateKeyError as e:
            print(f"Duplicate key error: {e}")
            return None
        except Exception as e:
            print(f"Error inserting document: {e}")
            return None

    def __del__(self):
        """Закрывает соединение с MongoDB при удалении объекта"""
        if self.client:
            self.client.close()


# Dependency для MongoDB клиента
def get_mongo_client_as_dependency():
    """
    Создает и возвращает MongoDBClient как зависимость.
    Автоматически закрывает соединение после использования.
    """
    mongo_client = partial(
        MongoDBClient,
        database=settings.MONGO_DB,
    )
    yield mongo_client



def get_mongo_client():
    """
    Создает и возвращает MongoDBClient как зависимость.
    Автоматически закрывает соединение после использования.
    """
    mongo_client = MongoDBClient(database="lct_efs", collection="states")
    return mongo_client

