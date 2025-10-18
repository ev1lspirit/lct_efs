import re


def _is_valid_session_id(session_id: str) -> bool:
    """
    Validate session_id format to prevent injection attacks

    Accepts:
    - UUID format (with or without hyphens)
    - Alphanumeric strings with hyphens/underscores (max 128 chars)

    Args:
        session_id: Session identifier to validate

    Returns:
        True if valid, False otherwise
    """
    if not session_id or not isinstance(session_id, str):
        return False

    # Проверка длины (защита от DOS)
    if len(session_id) > 128:
        return False

    # Разрешаем UUID или буквенно-цифровые строки с дефисами/подчеркиваниями
    # Запрещаем символы, которые могут быть использованы для инъекций
    pattern = r"^[a-zA-Z0-9_-]+$"

    return bool(re.match(pattern, session_id))
