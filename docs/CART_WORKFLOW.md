# Cart (Корзина) Workflow

Новый сценарий корзины повторяет мобильные макеты (Skeleton → Filled Cart → Checkout → Empty). Он построен на тех же сущностях, что и остальные workflow в MongoDB, и использует публичное API `kotlin-avito-api`.

## Быстрый старт

1. **Соберите JSON описания**
   ```bash
   python api/cart_workflow.py
   ```
   После запуска появится файл `cart_workflow.json` и сводка о количестве состояний.

2. **Сохраните workflow в стенд**
   ```bash
   curl -X POST http://localhost:8080/workflow/save \
        -H "Content-Type: application/json" \
        -d @cart_workflow.json
   ```
   Ответ содержит `wf_description_id` – его же используйте в `/client/workflow`.

3. **Создайте клиентскую сессию**
   ```bash
   curl -X POST http://localhost:8080/client/workflow \
        -H "Content-Type: application/json" \
        -d '{
              "client_session_id": "cart-demo-session",
              "client_workflow_id": "<wf_description_id>",
              "context": {}
            }'
   ```
   Первый ответ вернёт экран `CartSkeletonScreen` с авто-переходом к загрузке корзины.

## Структура состояний

| Блок | Состояние | Описание |
|------|-----------|----------|
| Загрузка | `CartSkeletonScreen` → `FetchCartSnapshot` → `FetchStoresCatalog` → `ProcessStoresCatalog` → `FetchRecommendedProducts` → `ProcessRecommendedProducts` | Skeleton → запрос корзины → загрузка магазинов и рекомендаций с сервера, нормализация ответов. |
| UI корзины | `CartOverviewScreen` | Отрисовка магазинов, товаров, уведомлений и суммы. |
| Операции | `AddItemToCart`, `RemoveItemFromCart`, `ClearCart` + `*Decision`/`Mark*` | Запросы в API, обработка ошибок, обновление контекста и сообщений. |
| Checkout | `ResetCheckoutError` → `FetchPaymentMethods` → `FetchShippingMethods` → `CheckoutDataDecision` → `CheckoutSummaryScreen` → (`DeliveryMethodsScreen`/`EditRecipientScreen` + `Apply*Selection`/`SaveRecipientInfo`) → `ResetCheckoutErrorBeforeCreate` → `CreateOrder` → `CheckoutCreateDecision` → `CheckoutSuccessScreen` | Раскрывает сводку оформления, модальные окна выбора доставки и редактирования получателя, затем создаёт заказ. |
| Ошибки/пустое состояние | `CartNetworkErrorScreen`, `CartOperationErrorScreen`, `CheckoutErrorScreen`, `CartEmptyScreen`, `CartFarewellScreen` | Покрывают сетевые ошибки, ошибки операций и финал. |

Всего: **37 состояний** (12 screen, 9 integration, 16 technical).

## Интеграции и API

| State | Метод | Endpoint |
|-------|-------|----------|
| `FetchCartSnapshot` | GET | `{{base_url}}/carts/{{cart_id}}/with-advertisements` |
| `FetchStoresCatalog` | GET | `{{base_url}}/stores` |
| `FetchRecommendedProducts` | GET | `{{base_url}}/advertisements?page=0&size=8` |
| `AddItemToCart` | POST | `{{base_url}}/carts/add-advertisement` |
| `RemoveItemFromCart` | DELETE | `{{base_url}}/carts/{{cart_id}}/advertisements/{{target_advertisement_id}}` |
| `ClearCart` | DELETE | `{{base_url}}/carts/{{cart_id}}` |
| `FetchPaymentMethods` | GET | `{{base_url}}/payment-methods` |
| `FetchShippingMethods` | GET | `{{base_url}}/shipping-methods` |
| `CreateOrder` | POST | `{{base_url}}/ships` |

Все URL интерполируются через контекстную переменную `base_url` (по умолчанию `http://localhost:8080/backservices/api`).

## Контекст по умолчанию

`cart_predefined_context()` (сохраняется в Mongo наряду со states) содержит:

- `base_url`: базовый адрес внешнего API;
- `user_id`/`cart_id`: идентификаторы демо-пользователя и корзины;
- `selected_items` и `selected_items_count`: текущее выделение и количество;
- `cart_snapshot`: fallback-данные для мгновенного отображения макета;
- `cart_operation_error_flag`, `checkout_error_flag`: маркеры ошибок для decision-состояний;
- `stores_catalog`, `stores_catalog_source`, `stores_catalog_error_flag`: кэш витрины магазинов и индикатор источника (remote/fallback);
- `recommended_products`, `recommended_products_count`, `recommended_products_source`: подборка товаров, обновляемая после запросов к `{{base_url}}/advertisements`;
- `selected_payment_method`, `selected_payment_method_name`: текущий платёжный способ и подпись.
- `selected_shipping_method`, `selected_shipping_method_name`, `selected_shipping_method_price`, `selected_shipping_method_eta`: выбранный способ доставки и параметры для бейджа.
- `recipient_name`, `recipient_phone`, `recipient_email`: данные получателя для модалки редактирования.

## События на экране корзины

| Event | Описание | Требуемые поля контекста |
|-------|----------|--------------------------|
| `refresh_cart` | Повторно читать корзину | — |
| `add_item` | Увеличить/вернуть товар | `target_advertisement_id` |
| `remove_item` | Удалить товар | `target_advertisement_id` |
| `toggle_item` | Переключить выбор (фронт обновляет `selected_items`) | `target_advertisement_id`, `selected_items`, `selected_items_count` (опционально) |
| `clear_cart` | Очистить корзину | — |
| `checkout` | Запустить checkout пайплайн | — |
| `choose_delivery` | Открыть список способов доставки | — |
| `select_delivery_method` | Применить выбранную доставку | `new_shipping_method_id`, `new_shipping_method_name`, `new_shipping_method_price`, `new_shipping_method_eta` |
| `edit_recipient` | Открыть модалку редактирования получателя | — |
| `save_recipient` | Сохранить контактные данные | `new_recipient_name`, `new_recipient_phone`, `new_recipient_email` |
| `select_payment_method` | Выбрать способ оплаты со сводки | `new_payment_method_id`, `new_payment_method_name` |

## Полезные советы

- При ошибках API (`cart_operation_error`, `checkout_error`) decision-состояния ведут пользователя на соответствующие экраны и не меняют `last_operation`.
- Для undo удаления достаточно повторно отправить `add_item` с `target_advertisement_id = last_removed_advertisement_id`.
- Каталожные данные (`stores_catalog`, `recommended_products`) подгружаются с сервера перед отображением корзины; при сбое запросов автоматически используется fallback из `predefined_context`.
- JSON из `cart_workflow.json` можно отдавать напрямую в `/workflow/save`, либо импортировать через отдельные скрипты.

Документ и Python-модуль синхронизированы: при обновлении `api/cart_workflow.py` обязательно пересоздавайте `cart_workflow.json` и проверяйте endpoint-ы.

## Модальные окна checkout

- **`DeliveryMethodsScreen`** — показывает список опций из `shipping_methods`, каждая кнопка прокидывает в контекст ID, название и ETA; после подтверждения `ApplyDeliverySelection` обновляет карточку в сводке.
- **`EditRecipientScreen`** — предзаполняет форму данными из контекста и, при сохранении, через `SaveRecipientInfo` синхронизирует значения.
- **`ApplyPaymentSelection`** — быстрый селектор внутри `CheckoutSummaryScreen`, меняет подпись кнопки оплаты без возвращения в бэкенд.
