"""
Файл для примера выполнения запросов
с помощью адаптера
"""
from pydantic import BaseModel

from commonAdapter import CommonAdapter


class User(BaseModel):
    id: int
    role: str
    email: str
    password: str
    lastName: str
    firstName: str
    address: str
    rating: float


ca = CommonAdapter("https://sandkittens.me/api/v1")

# Пример для отправки GET запроса
getUsers = ca.get("user", response_model=User)
print(getUsers)

# Пример для отправки GET запроса
getUsers = ca.get("user/2", response_model=User)
print(getUsers)


# Пример для отправки POST запроса
postUser = ca.post("user", response_model=User,
                   json={
                       "role": "USER",
                       "email": "testFromPython@mail.ru",
                       "password": "testFromPython",
                       "lastName": "zmeya",
                       "firstName": "gaduka",
                       "address": "tehnohab",
                       "rating": 1.5
                   })
print(postUser)

#
# Пример для отправки PUT запроса
print(ca.put("user", response_model=User,
             json={
                 "id": 4,
                 "role": "USER",
                 "email": "UPDATEDtestFromPython@mail.ru",
                 "password": "UPDATEDtestFromPython",
                 "lastName": "Uzmeya",
                 "firstName": "Ugaduka",
                 "address": "Utehnohab",
                 "rating": 1.8
             }))

# # Пример для отправки DELETE запроса
print(ca.delete("user/4"))
