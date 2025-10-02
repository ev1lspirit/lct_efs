from functools import partial
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
from typing import Optional, Dict, Any
import logging

import pymongo
import pymongo.errors
from config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self, database: str, collection: str):
        self.client = MongoClient(settings.mongo_url)
        self.db = self.client[database]
        self.collection = self.db[collection]
        logger.info(f"MongoDB client initialized: database='{database}', collection='{collection}'")

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        try:
            logger.debug(f"Fetching document with id={id} from {self.db.name}.{self.collection.name}")
            document = self.collection.find_one({"_id": ObjectId(id)})
            if document:
                document = dict(document)  # ensure mutable copy
                document["_id"] = str(document["_id"])
                logger.debug(f"Document found: {id}")
            else:
                logger.warning(f"Document not found: {id} in {self.db.name}.{self.collection.name}")
            return document
        except Exception as e:
            logger.error(f"Error retrieving document {id} from {self.db.name}.{self.collection.name}: {e}", exc_info=True)
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
            logger.debug(f"Retrieving description with id={description_id} from {self.db.name}.{self.collection.name}")
            document = self.collection.find_one({"_id": ObjectId(description_id)})
            if document:
                document = dict(document)
                document["_id"] = str(document["_id"])
                logger.debug(f"Description found: {description_id}")
            else:
                logger.warning(f"Description not found: {description_id} in {self.db.name}.{self.collection.name}")
            return document
        except Exception as e:
            logger.error(f"Error retrieving description {description_id} from {self.db.name}.{self.collection.name}: {e}", exc_info=True)
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
            logger.debug(f"Updating description {description_id} in {self.db.name}.{self.collection.name}")
            result = self.collection.update_one(
                {"_id": ObjectId(description_id)}, {"$set": update_data}
            )
            if result.modified_count > 0:
                logger.info(f"Description {description_id} updated successfully")
            else:
                logger.warning(f"Description {description_id} not modified (already up to date or not found)")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating description {description_id}: {e}", exc_info=True)
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
                logger.debug(f"Inserting description with custom ID: {overriden_id}")
            result = self.collection.insert_one(description_data)
            logger.info(f"Description inserted successfully with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except pymongo.errors.DuplicateKeyError as e:
            logger.error(f"Duplicate key error when inserting description: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inserting description: {e}", exc_info=True)
            return None

    def upsert_screen(self, workflow_id: str, state_id: str, screen_json: Dict[str, Any]) -> str:
        """Upsert JSON экрана по уникальной паре (workflow_id, state_id).
        Создаёт уникальный индекс при первом вызове.
        Returns _id документа.
        """
        if self.collection.name != settings.SCREENS_MONGO_COLLECTION:
            raise ValueError("MongoDBClient: неверная коллекция для upsert_screen")
        # Гарантируем уникальный индекс
        try:
            self.collection.create_index(
                [("workflow_id", ASCENDING), ("state_id", ASCENDING)],
                name="uniq_workflow_state",
                unique=True,
            )
        except pymongo.errors.PyMongoError:
            pass
        filter_ = {"workflow_id": workflow_id, "state_id": state_id}
        update_doc = {"$set": {"workflow_id": workflow_id, "state_id": state_id, "screen": screen_json}}
        result = self.collection.update_one(filter_, update_doc, upsert=True)
        if result.upserted_id:
            return str(result.upserted_id)
        existing = self.collection.find_one(filter_, {"_id": 1})
        return str(existing["_id"]) if existing else ""

    def get_screen_by_keys(self, workflow_id: str, state_id: str) -> Optional[Dict[str, Any]]:
        """Получить документ экрана по (workflow_id, state_id)."""
        if self.collection.name != settings.SCREENS_MONGO_COLLECTION:
            raise ValueError("MongoDBClient: неверная коллекция для get_screen_by_keys")
        doc = self.collection.find_one({"workflow_id": workflow_id, "state_id": state_id})
        if not doc:
            return None
        doc = dict(doc)
        doc["_id"] = str(doc["_id"])
        return doc

    def insert_workflow_with_format_validation(self, workflow_data: Dict[str, Any]) -> Optional[str]:
        """Добавляет workflow с валидацией нового формата.
        
        Новый формат поддерживает:
        - 'body' вместо 'params' для POST/PUT/PATCH запросов в integration states
        - Сохранение screens отдельно в коллекции screens
        - predefined_context в отдельной коллекции
        
        Args:
            workflow_data: Полные данные workflow включая states и predefined_context
            
        Returns:
            ID вставленного документа или None в случае ошибки
        """
        try:
            # Валидируем структуру
            if "states" not in workflow_data:
                logger.error("Workflow data must contain 'states' key")
                return None
            
            # Валидируем integration states
            for state in workflow_data.get("states", []):
                if state.get("state_type") == "integration":
                    for expr in state.get("expressions", []):
                        method = expr.get("method", "").lower()
                        has_body = "body" in expr
                        has_params = "params" in expr
                        
                        # POST/PUT/PATCH должны использовать body
                        if method in ["post", "put", "patch"]:
                            if has_params and not has_body:
                                logger.warning(
                                    f"State '{state.get('name')}': POST/PUT/PATCH should use 'body' instead of 'params'. "
                                    "Consider updating to new format."
                                )
                            elif has_body:
                                logger.debug(f"State '{state.get('name')}': Using new format with 'body'")
            
            # Сохраняем только states (без screens и predefined_context)
            states_only = {"states": workflow_data["states"]}
            result = self.insert_description(states_only)
            
            if result:
                logger.info(f"Workflow saved with new format support. ID: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error inserting workflow with format validation: {e}", exc_info=True)
            return None

    def get_workflow_with_context(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Получает workflow со всеми связанными данными.
        
        Args:
            workflow_id: ID workflow документа
            
        Returns:
            Полный workflow с states, screens и context
        """
        try:
            # Получаем states
            workflow_doc = self.get(workflow_id)
            if not workflow_doc:
                logger.warning(f"Workflow {workflow_id} not found")
                return None
            
            # Получаем context из отдельной коллекции
            context_client = MongoDBClient(
                database=self.db.name,
                collection=settings.WORKFLOW_MONGO_COLLECTION
            )
            context_doc = context_client.get(workflow_id)
            
            # Получаем screens из отдельной коллекции
            screens_client = MongoDBClient(
                database=self.db.name,
                collection=settings.SCREENS_MONGO_COLLECTION
            )
            screens_docs = list(screens_client.collection.find({"workflow_id": workflow_id}))
            
            # Формируем полный результат
            result = {
                "_id": workflow_doc["_id"],
                "states": workflow_doc.get("states", []),
                "predefined_context": context_doc if context_doc else {},
                "screens": {
                    screen["state_id"]: screen["screen"]
                    for screen in screens_docs
                }
            }
            
            logger.info(f"Retrieved workflow {workflow_id} with {len(screens_docs)} screens")
            return result
            
        except Exception as e:
            logger.error(f"Error getting workflow with context: {e}", exc_info=True)
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
    mongo_client = MongoDBClient(database=settings.MONGO_DB, collection="states")
    return mongo_client
