from typing import Optional, Dict, Any
import logging
from .client import MongoDBClient

logger = logging.getLogger(__name__)


class ScreenService:
    def __init__(self):
        self.mongo_client = MongoDBClient(database="lct_efs", collection="screens")

    def save_screen(self, screen_name: str, screen_data: Dict[str, Any]) -> Optional[str]:
        """
        Сохраняет экран в MongoDB
        Args:
            screen_name: Название экрана (уникальный идентификатор)
            screen_data: JSON данные экрана
        Returns:
            ID сохраненного документа или None в случае ошибки
        """
        try:
            # Проверяем, существует ли уже экран с таким именем
            existing_screen = self.mongo_client.collection.find_one({"screen_name": screen_name})

            if existing_screen:
                # Обновляем существующий экран
                logger.info(f"Updating existing screen: {screen_name}")
                result = self.mongo_client.collection.update_one(
                    {"screen_name": screen_name},
                    {"$set": {"screen_data": screen_data}}
                )
                return str(existing_screen["_id"]) if result.modified_count > 0 else None
            else:
                # Создаем новый экран
                logger.info(f"Creating new screen: {screen_name}")
                document = {
                    "screen_name": screen_name,
                    "screen_data": screen_data
                }
                return self.mongo_client.insert_description(document)

        except Exception as e:
            logger.error(f"Error saving screen {screen_name}: {e}")
            return None

    def get_screen(self, screen_name: str) -> Optional[Dict[str, Any]]:
        """
        Получает экран из MongoDB по названию
        Args:
            screen_name: Название экрана
        Returns:
            JSON данные экрана или None если не найден
        """
        try:
            logger.info(f"Loading screen from MongoDB: {screen_name}")
            document = self.mongo_client.collection.find_one({"screen_name": screen_name})

            if document:
                logger.info(f"Screen {screen_name} found in MongoDB")
                return document.get("screen_data")
            else:
                logger.warning(f"Screen {screen_name} not found in MongoDB")
                return None

        except Exception as e:
            logger.error(f"Error retrieving screen {screen_name}: {e}")
            return None

    def delete_screen(self, screen_name: str) -> bool:
        """
        Удаляет экран из MongoDB
        Args:
            screen_name: Название экрана
        Returns:
            True если удаление успешно, False в противном случае
        """
        try:
            result = self.mongo_client.collection.delete_one({"screen_name": screen_name})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting screen {screen_name}: {e}")
            return False

    def list_screens(self) -> list[str]:
        """
        Возвращает список всех названий экранов
        Returns:
            Список названий экранов
        """
        try:
            screens = self.mongo_client.collection.find({}, {"screen_name": 1, "_id": 0})
            return [screen["screen_name"] for screen in screens]
        except Exception as e:
            logger.error(f"Error listing screens: {e}")
            return []

    def __del__(self):
        """Закрывает соединение с MongoDB"""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.__del__()


# Синглтон для переиспользования соединения
_screen_service_instance = None

def get_screen_service() -> ScreenService:
    """Возвращает экземпляр ScreenService (синглтон)"""
    global _screen_service_instance
    if _screen_service_instance is None:
        _screen_service_instance = ScreenService()
    return _screen_service_instance
