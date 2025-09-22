"""
Файл для примера выполнения запросов
с помощью адаптера
"""

from commonAdapter import CommonAdapter

ca = CommonAdapter("https://sandkittens.me/api/v1")

# Пример для отправки GET запроса
print(ca.get("user"))

# Пример для отправки POST запроса
print(ca.post("user", json={
    "role": "USER",
    "email": "testFromPython@mail.ru",
    "password": "testFromPython",
    "lastName": "zmeya",
    "firstName": "gaduka",
    "address": "tehnohab",
    "rating": 1.5
}))

# Пример для отправки PUT запроса
print(ca.put("user", json={
    "id": 3,
    "role": "USER",
    "email": "UPDATEDtestFromPython@mail.ru",
    "password": "UPDATEDtestFromPython",
    "lastName": "Uzmeya",
    "firstName": "Ugaduka",
    "address": "Utehnohab",
    "rating": 1.8
}))

# Пример для отправки DELETE запроса
print(ca.delete("user/4"))