# Промпт: Интеграция мобильного приложения с Workflow Engine Service

## 📋 Обзор системы

Данный сервис представляет собой **Workflow Engine** на базе конечного автомата (FSM), который управляет динамическими пользовательскими сценариями через REST API. Система позволяет создавать сложные многошаговые процессы (workflow) без изменения кода мобильного приложения.

### Основные возможности

- ✅ Динамические экранные потоки без обновления приложения
- ✅ Условная логика на основе данных пользователя
- ✅ Интеграция с внешними API
- ✅ Сохранение состояния сессии пользователя
- ✅ Поддержка сложных многоэтапных процессов (кредитование, опросы, формы)

---

## 🏗️ Архитектура сервиса

### Компоненты системы

```
┌─────────────────────┐
│  Мобильное          │
│  приложение         │
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────┐
│  FastAPI Backend    │
│  (Workflow Engine)  │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│ MongoDB │ │  Redis  │
│ (States)│ │(Session)│
└─────────┘ └─────────┘
```

### Типы состояний (State Types)

| Тип | Описание | Использование |
|-----|----------|---------------|
| **screen** | Отображает экран пользователю | Формы, информационные экраны, кнопки действий |
| **technical** | Выполняет логику/условия | Валидация, расчеты, условные переходы |
| **integration** | Вызывает внешние API | Получение данных, отправка запросов |
| **service** | Служебное состояние | Инициализация, завершение, ошибки |

---

## 🔌 API Endpoints

### 1. **Сохранение Workflow** (Admin Panel → Backend)

**Эндпоинт:** `POST /workflow/save`

**Описание:** Создание нового workflow со всеми состояниями, переходами и экранами.

**Request Body:**

```json
{
  "states": [
    {
      "state_type": "screen",
      "name": "LoginScreen",
      "screen": {
        "title": "Вход в систему",
        "fields": [
          {
            "id": "email",
            "type": "email",
            "label": "Email",
            "required": true,
            "validation": "email"
          },
          {
            "id": "password",
            "type": "password",
            "label": "Пароль",
            "required": true,
            "minLength": 8
          }
        ],
        "buttons": [
          {
            "id": "submit",
            "label": "Войти",
            "event": "submit",
            "style": "primary"
          },
          {
            "id": "forgot",
            "label": "Забыли пароль?",
            "event": "forgot_password",
            "style": "text"
          }
        ]
      },
      "transitions": [
        {
          "case": "submit",
          "state_id": "ValidateCredentials"
        },
        {
          "case": "forgot_password",
          "state_id": "ForgotPasswordScreen"
        }
      ],
      "expressions": [
        {"event_name": "submit"},
        {"event_name": "forgot_password"}
      ],
      "initial_state": true,
      "final_state": false
    },
    {
      "state_type": "technical",
      "name": "ValidateCredentials",
      "transitions": [
        {
          "variable": "is_valid",
          "case": "True",
          "state_id": "DashboardScreen"
        },
        {
          "variable": "is_valid",
          "case": "False",
          "state_id": "LoginScreen"
        }
      ],
      "expressions": [
        {
          "variable": "is_valid",
          "dependent_variables": ["email", "password"],
          "expression": "len(email) > 0 and len(password) >= 8"
        }
      ],
      "initial_state": false,
      "final_state": false
    },
    {
      "state_type": "screen",
      "name": "DashboardScreen",
      "screen": {
        "title": "Главная",
        "components": [
          {
            "type": "text",
            "content": "Добро пожаловать, {{user_name}}!"
          }
        ]
      },
      "transitions": [],
      "expressions": [],
      "initial_state": false,
      "final_state": true
    }
  ],
  "predefined_context": {
    "app_version": "1.0.0",
    "platform": "mobile"
  }
}
```

**Response:**

```json
{
  "status": "success",
  "wf_description_id": "507f1f77bcf86cd799439011",
  "wf_context_id": "507f1f77bcf86cd799439011",
  "screens_saved": 2
}
```

**Важные детали:**

- `wf_description_id` - уникальный ID workflow (используется в мобильном приложении)
- `screen` - произвольный JSON-объект, описывающий UI экрана
- `initial_state: true` - начальное состояние (должно быть ровно одно)
- `final_state: true` - конечное состояние (может быть несколько)

---

### 2. **Выполнение Workflow** (Mobile App → Backend)

**Эндпоинт:** `POST /client/workflow`

**Описание:** Основной эндпоинт для взаимодействия мобильного приложения с workflow.

#### 2.1. Создание новой сессии

**Request:**

```json
{
  "client_session_id": "user_12345_session_abc",
  "client_workflow_id": "507f1f77bcf86cd799439011",
  "context": {
    "user_id": "12345",
    "device_type": "ios",
    "app_version": "1.0.0"
  },
  "event_name": null
}
```

**Response:**

```json
{
  "session_id": "user_12345_session_abc",
  "context": {
    "__workflow_id": "507f1f77bcf86cd799439011",
    "__created_at": "2025-10-02T10:00:00",
    "user_id": "12345",
    "device_type": "ios",
    "app_version": "1.0.0"
  },
  "current_state": "LoginScreen",
  "state_type": "screen",
  "screen": {
    "title": "Вход в систему",
    "fields": [
      {
        "id": "email",
        "type": "email",
        "label": "Email",
        "required": true
      },
      {
        "id": "password",
        "type": "password",
        "label": "Пароль",
        "required": true
      }
    ],
    "buttons": [
      {
        "id": "submit",
        "label": "Войти",
        "event": "submit",
        "style": "primary"
      }
    ]
  }
}
```

#### 2.2. Отправка события (переход между состояниями)

**Request:**

```json
{
  "client_session_id": "user_12345_session_abc",
  "context": {
    "email": "user@example.com",
    "password": "SecurePass123"
  },
  "event_name": "submit"
}
```

**Response (следующий экран):**

```json
{
  "session_id": "user_12345_session_abc",
  "context": {
    "__workflow_id": "507f1f77bcf86cd799439011",
    "__created_at": "2025-10-02T10:00:00",
    "user_id": "12345",
    "email": "user@example.com",
    "password": "SecurePass123",
    "is_valid": true
  },
  "current_state": "DashboardScreen",
  "state_type": "screen",
  "screen": {
    "title": "Главная",
    "components": [
      {
        "type": "text",
        "content": "Добро пожаловать, user@example.com!"
      }
    ]
  }
}
```

**Response (финальное состояние):**

```json
{
  "session_id": "user_12345_session_abc",
  "context": {
    "__workflow_id": "507f1f77bcf86cd799439011",
    "result": "success"
  },
  "current_state": "CompletedState",
  "state_type": "service"
}
```

**Важные детали:**

- `client_session_id` - уникальный ID сессии (генерируется в приложении)
- `client_workflow_id` - обязателен только при первом запросе (создание сессии)
- `context` - данные пользователя, накапливаются между состояниями
- `event_name` - название события, вызывающего переход (из `expressions`)
- `screen` - присутствует только для `state_type: "screen"`

---

## 📱 Интеграция в мобильное приложение

### Архитектура клиента

```
┌──────────────────────────────────────┐
│       Мобильное приложение           │
├──────────────────────────────────────┤
│  UI Layer (Views/Screens)            │
│    ↕                                 │
│  Workflow Manager (State Machine)    │
│    ↕                                 │
│  Network Layer (API Client)          │
│    ↕                                 │
│  Storage Layer (Session Cache)       │
└──────────────────────────────────────┘
```

### Компоненты для реализации

#### 1. **WorkflowManager** (Core)

```kotlin
// Kotlin (Android)
class WorkflowManager(
    private val apiClient: WorkflowApiClient,
    private val sessionStorage: SessionStorage
) {
    private var currentSession: WorkflowSession? = null
    
    /**
     * Начать новый workflow
     */
    suspend fun startWorkflow(
        workflowId: String,
        initialContext: Map<String, Any> = emptyMap()
    ): WorkflowResponse {
        val sessionId = generateSessionId()
        val response = apiClient.executeWorkflow(
            sessionId = sessionId,
            workflowId = workflowId,
            context = initialContext,
            eventName = null
        )
        
        currentSession = WorkflowSession(
            id = sessionId,
            workflowId = workflowId,
            context = response.context
        )
        sessionStorage.save(currentSession!!)
        
        return response
    }
    
    /**
     * Отправить событие и получить следующее состояние
     */
    suspend fun sendEvent(
        eventName: String,
        additionalContext: Map<String, Any> = emptyMap()
    ): WorkflowResponse {
        val session = currentSession ?: throw IllegalStateException("No active session")
        
        val response = apiClient.executeWorkflow(
            sessionId = session.id,
            workflowId = null, // Не нужен для существующей сессии
            context = additionalContext,
            eventName = eventName
        )
        
        // Обновляем контекст сессии
        session.context.putAll(response.context)
        sessionStorage.save(session)
        
        return response
    }
    
    /**
     * Восстановить сессию после закрытия приложения
     */
    suspend fun restoreSession(sessionId: String): WorkflowResponse? {
        currentSession = sessionStorage.get(sessionId)
        return currentSession?.let { session ->
            apiClient.executeWorkflow(
                sessionId = session.id,
                workflowId = null,
                context = emptyMap(),
                eventName = null
            )
        }
    }
    
    /**
     * Завершить сессию
     */
    fun endSession() {
        currentSession?.let { sessionStorage.delete(it.id) }
        currentSession = null
    }
    
    private fun generateSessionId(): String {
        val userId = getUserId() // Получить ID пользователя
        val timestamp = System.currentTimeMillis()
        val random = UUID.randomUUID().toString().take(8)
        return "session_${userId}_${timestamp}_${random}"
    }
}
```

```swift
// Swift (iOS)
class WorkflowManager {
    private let apiClient: WorkflowAPIClient
    private let sessionStorage: SessionStorage
    private var currentSession: WorkflowSession?
    
    init(apiClient: WorkflowAPIClient, sessionStorage: SessionStorage) {
        self.apiClient = apiClient
        self.sessionStorage = sessionStorage
    }
    
    /// Начать новый workflow
    func startWorkflow(
        workflowId: String,
        initialContext: [String: Any] = [:]
    ) async throws -> WorkflowResponse {
        let sessionId = generateSessionId()
        let response = try await apiClient.executeWorkflow(
            sessionId: sessionId,
            workflowId: workflowId,
            context: initialContext,
            eventName: nil
        )
        
        currentSession = WorkflowSession(
            id: sessionId,
            workflowId: workflowId,
            context: response.context
        )
        sessionStorage.save(currentSession!)
        
        return response
    }
    
    /// Отправить событие
    func sendEvent(
        _ eventName: String,
        additionalContext: [String: Any] = [:]
    ) async throws -> WorkflowResponse {
        guard let session = currentSession else {
            throw WorkflowError.noActiveSession
        }
        
        let response = try await apiClient.executeWorkflow(
            sessionId: session.id,
            workflowId: nil,
            context: additionalContext,
            eventName: eventName
        )
        
        // Обновляем контекст
        session.context.merge(response.context) { _, new in new }
        sessionStorage.save(session)
        
        return response
    }
    
    /// Восстановить сессию
    func restoreSession(sessionId: String) async throws -> WorkflowResponse? {
        guard let session = sessionStorage.get(sessionId) else {
            return nil
        }
        
        currentSession = session
        return try await apiClient.executeWorkflow(
            sessionId: session.id,
            workflowId: nil,
            context: [:],
            eventName: nil
        )
    }
    
    private func generateSessionId() -> String {
        let userId = getUserId()
        let timestamp = Date().timeIntervalSince1970
        let random = UUID().uuidString.prefix(8)
        return "session_\(userId)_\(Int(timestamp))_\(random)"
    }
}
```

#### 2. **WorkflowApiClient** (Network Layer)

```kotlin
// Kotlin (Android) с Retrofit
interface WorkflowApiService {
    @POST("/client/workflow")
    suspend fun executeWorkflow(
        @Body request: WorkflowRequest
    ): WorkflowResponse
}

data class WorkflowRequest(
    @SerializedName("client_session_id")
    val clientSessionId: String,
    
    @SerializedName("client_workflow_id")
    val clientWorkflowId: String? = null,
    
    @SerializedName("context")
    val context: Map<String, Any>,
    
    @SerializedName("event_name")
    val eventName: String? = null
)

data class WorkflowResponse(
    @SerializedName("session_id")
    val sessionId: String,
    
    @SerializedName("context")
    val context: Map<String, Any>,
    
    @SerializedName("current_state")
    val currentState: String,
    
    @SerializedName("state_type")
    val stateType: String,
    
    @SerializedName("screen")
    val screen: ScreenData? = null
)

data class ScreenData(
    val title: String?,
    val fields: List<FieldData>? = null,
    val buttons: List<ButtonData>? = null,
    val components: List<ComponentData>? = null
)

class WorkflowApiClient(
    private val apiService: WorkflowApiService
) {
    suspend fun executeWorkflow(
        sessionId: String,
        workflowId: String?,
        context: Map<String, Any>,
        eventName: String?
    ): WorkflowResponse {
        return apiService.executeWorkflow(
            WorkflowRequest(
                clientSessionId = sessionId,
                clientWorkflowId = workflowId,
                context = context,
                eventName = eventName
            )
        )
    }
}
```

```swift
// Swift (iOS) с URLSession
struct WorkflowAPIClient {
    private let baseURL: URL
    private let session: URLSession
    
    init(baseURL: URL) {
        self.baseURL = baseURL
        self.session = URLSession.shared
    }
    
    func executeWorkflow(
        sessionId: String,
        workflowId: String?,
        context: [String: Any],
        eventName: String?
    ) async throws -> WorkflowResponse {
        let url = baseURL.appendingPathComponent("/client/workflow")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "client_session_id": sessionId,
            "client_workflow_id": workflowId as Any,
            "context": context,
            "event_name": eventName as Any
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw WorkflowError.networkError
        }
        
        return try JSONDecoder().decode(WorkflowResponse.self, from: data)
    }
}

struct WorkflowResponse: Codable {
    let sessionId: String
    let context: [String: AnyCodable] // Custom type для Any
    let currentState: String
    let stateType: String
    let screen: ScreenData?
    
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case context
        case currentState = "current_state"
        case stateType = "state_type"
        case screen
    }
}
```

#### 3. **DynamicScreenRenderer** (UI Layer)

```kotlin
// Kotlin (Android) - Jetpack Compose
@Composable
fun DynamicScreen(
    screenData: ScreenData,
    onEvent: (String, Map<String, Any>) -> Unit
) {
    var formState by remember { mutableStateOf<Map<String, Any>>(emptyMap()) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Заголовок
        screenData.title?.let {
            Text(
                text = it,
                style = MaterialTheme.typography.h5,
                modifier = Modifier.padding(bottom = 16.dp)
            )
        }
        
        // Поля формы
        screenData.fields?.forEach { field ->
            DynamicField(
                field = field,
                value = formState[field.id],
                onValueChange = { value ->
                    formState = formState + (field.id to value)
                }
            )
            Spacer(modifier = Modifier.height(8.dp))
        }
        
        // Компоненты
        screenData.components?.forEach { component ->
            when (component.type) {
                "text" -> Text(text = component.content.interpolate(formState))
                "image" -> AsyncImage(model = component.url, contentDescription = null)
                "card" -> Card { /* render card */ }
                // ... другие типы
            }
        }
        
        Spacer(modifier = Modifier.weight(1f))
        
        // Кнопки
        screenData.buttons?.forEach { button ->
            Button(
                onClick = {
                    onEvent(button.event, formState)
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
            ) {
                Text(button.label)
            }
        }
    }
}

@Composable
fun DynamicField(
    field: FieldData,
    value: Any?,
    onValueChange: (Any) -> Unit
) {
    when (field.type) {
        "email", "text" -> OutlinedTextField(
            value = value?.toString() ?: "",
            onValueChange = onValueChange,
            label = { Text(field.label) },
            modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(
                keyboardType = if (field.type == "email") 
                    KeyboardType.Email else KeyboardType.Text
            )
        )
        "password" -> OutlinedTextField(
            value = value?.toString() ?: "",
            onValueChange = onValueChange,
            label = { Text(field.label) },
            modifier = Modifier.fillMaxWidth(),
            visualTransformation = PasswordVisualTransformation()
        )
        "number" -> OutlinedTextField(
            value = value?.toString() ?: "",
            onValueChange = { onValueChange(it.toIntOrNull() ?: 0) },
            label = { Text(field.label) },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
        )
        "checkbox" -> Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(
                checked = value as? Boolean ?: false,
                onCheckedChange = onValueChange
            )
            Text(field.label)
        }
        // ... другие типы полей
    }
}
```

```swift
// Swift (iOS) - SwiftUI
struct DynamicScreen: View {
    let screenData: ScreenData
    let onEvent: (String, [String: Any]) -> Void
    
    @State private var formState: [String: Any] = [:]
    
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Заголовок
                if let title = screenData.title {
                    Text(title)
                        .font(.title)
                        .padding(.bottom)
                }
                
                // Поля формы
                if let fields = screenData.fields {
                    ForEach(fields, id: \.id) { field in
                        DynamicField(
                            field: field,
                            value: Binding(
                                get: { formState[field.id] },
                                set: { formState[field.id] = $0 }
                            )
                        )
                    }
                }
                
                // Компоненты
                if let components = screenData.components {
                    ForEach(components, id: \.type) { component in
                        DynamicComponent(component: component, context: formState)
                    }
                }
                
                Spacer()
                
                // Кнопки
                if let buttons = screenData.buttons {
                    ForEach(buttons, id: \.id) { button in
                        Button(action: {
                            onEvent(button.event, formState)
                        }) {
                            Text(button.label)
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.primary)
                    }
                }
            }
            .padding()
        }
    }
}

struct DynamicField: View {
    let field: FieldData
    @Binding var value: Any?
    
    var body: some View {
        switch field.type {
        case "email", "text":
            TextField(field.label, text: Binding(
                get: { (value as? String) ?? "" },
                set: { value = $0 }
            ))
            .textFieldStyle(.roundedBorder)
            .keyboardType(field.type == "email" ? .emailAddress : .default)
            
        case "password":
            SecureField(field.label, text: Binding(
                get: { (value as? String) ?? "" },
                set: { value = $0 }
            ))
            .textFieldStyle(.roundedBorder)
            
        case "number":
            TextField(field.label, text: Binding(
                get: { String(value as? Int ?? 0) },
                set: { value = Int($0) ?? 0 }
            ))
            .keyboardType(.numberPad)
            
        case "checkbox":
            Toggle(field.label, isOn: Binding(
                get: { (value as? Bool) ?? false },
                set: { value = $0 }
            ))
            
        default:
            Text("Unknown field type: \(field.type)")
        }
    }
}
```

#### 4. **SessionStorage** (Persistence)

```kotlin
// Kotlin (Android) - SharedPreferences
class SessionStorage(private val context: Context) {
    private val prefs = context.getSharedPreferences("workflow_sessions", Context.MODE_PRIVATE)
    private val gson = Gson()
    
    fun save(session: WorkflowSession) {
        val json = gson.toJson(session)
        prefs.edit().putString(session.id, json).apply()
    }
    
    fun get(sessionId: String): WorkflowSession? {
        val json = prefs.getString(sessionId, null) ?: return null
        return gson.fromJson(json, WorkflowSession::class.java)
    }
    
    fun delete(sessionId: String) {
        prefs.edit().remove(sessionId).apply()
    }
    
    fun getAllSessions(): List<WorkflowSession> {
        return prefs.all.mapNotNull { (_, value) ->
            gson.fromJson(value as? String, WorkflowSession::class.java)
        }
    }
}

data class WorkflowSession(
    val id: String,
    val workflowId: String,
    val context: MutableMap<String, Any>,
    val createdAt: Long = System.currentTimeMillis()
)
```

```swift
// Swift (iOS) - UserDefaults
class SessionStorage {
    private let userDefaults = UserDefaults.standard
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    
    func save(_ session: WorkflowSession) {
        guard let data = try? encoder.encode(session) else { return }
        userDefaults.set(data, forKey: session.id)
    }
    
    func get(_ sessionId: String) -> WorkflowSession? {
        guard let data = userDefaults.data(forKey: sessionId) else { return nil }
        return try? decoder.decode(WorkflowSession.self, from: data)
    }
    
    func delete(_ sessionId: String) {
        userDefaults.removeObject(forKey: sessionId)
    }
    
    func getAllSessions() -> [WorkflowSession] {
        // Реализация получения всех сессий
        return []
    }
}

struct WorkflowSession: Codable {
    let id: String
    let workflowId: String
    var context: [String: AnyCodable]
    let createdAt: Date
    
    init(id: String, workflowId: String, context: [String: Any]) {
        self.id = id
        self.workflowId = workflowId
        self.context = context.mapValues { AnyCodable($0) }
        self.createdAt = Date()
    }
}
```

---

## 🎯 Сценарии использования

### Сценарий 1: Простая авторизация

```kotlin
// Kotlin - ViewModel
class LoginViewModel(
    private val workflowManager: WorkflowManager
) : ViewModel() {
    
    private val _screenState = MutableStateFlow<ScreenData?>(null)
    val screenState = _screenState.asStateFlow()
    
    fun startLoginFlow() {
        viewModelScope.launch {
            try {
                val response = workflowManager.startWorkflow(
                    workflowId = "507f1f77bcf86cd799439011", // Login workflow ID
                    initialContext = mapOf(
                        "device_type" to "android",
                        "app_version" to BuildConfig.VERSION_NAME
                    )
                )
                
                _screenState.value = response.screen
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    fun onSubmitLogin(email: String, password: String) {
        viewModelScope.launch {
            try {
                val response = workflowManager.sendEvent(
                    eventName = "submit",
                    additionalContext = mapOf(
                        "email" to email,
                        "password" to password
                    )
                )
                
                when (response.stateType) {
                    "screen" -> _screenState.value = response.screen
                    "service" -> {
                        if (response.currentState == "CompletedState") {
                            // Авторизация успешна
                            navigateToDashboard()
                        }
                    }
                }
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
}
```

### Сценарий 2: Многошаговая форма заявки

```swift
// Swift - ViewModel
class LoanApplicationViewModel: ObservableObject {
    private let workflowManager: WorkflowManager
    
    @Published var currentScreen: ScreenData?
    @Published var isLoading = false
    
    init(workflowManager: WorkflowManager) {
        self.workflowManager = workflowManager
    }
    
    func startApplication() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await workflowManager.startWorkflow(
                workflowId: "loan_application_v2",
                initialContext: [
                    "user_id": getUserId(),
                    "started_at": Date().iso8601String
                ]
            )
            
            await MainActor.run {
                currentScreen = response.screen
            }
        } catch {
            // Handle error
        }
    }
    
    func submitStep(_ eventName: String, data: [String: Any]) async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await workflowManager.sendEvent(
                eventName,
                additionalContext: data
            )
            
            await MainActor.run {
                if response.stateType == "screen" {
                    currentScreen = response.screen
                } else if response.currentState == "ApplicationApproved" {
                    // Заявка одобрена
                    showSuccessScreen()
                }
            }
        } catch {
            // Handle error
        }
    }
}
```

### Сценарий 3: Восстановление после закрытия приложения

```kotlin
// Kotlin - Application
class MyApplication : Application() {
    lateinit var workflowManager: WorkflowManager
    
    override fun onCreate() {
        super.onCreate()
        
        workflowManager = WorkflowManager(
            apiClient = createApiClient(),
            sessionStorage = SessionStorage(this)
        )
        
        // Восстановление активных сессий
        lifecycleScope.launch {
            val sessions = workflowManager.sessionStorage.getAllSessions()
            sessions.forEach { session ->
                // Проверка, не истекла ли сессия (например, 24 часа)
                if (System.currentTimeMillis() - session.createdAt < 24.hours) {
                    workflowManager.restoreSession(session.id)
                }
            }
        }
    }
}
```

---

## 🚨 Обработка ошибок

### Типы ошибок

```kotlin
sealed class WorkflowError : Exception() {
    // Клиентские ошибки (4xx)
    data class BadRequest(override val message: String) : WorkflowError()
    data class NotFound(override val message: String) : WorkflowError()
    
    // Серверные ошибки (5xx)
    data class ServerError(override val message: String) : WorkflowError()
    
    // Сетевые ошибки
    object NetworkError : WorkflowError()
    object Timeout : WorkflowError()
    
    // Ошибки состояния
    object NoActiveSession : WorkflowError()
    object InvalidState : WorkflowError()
}
```

### Обработка ошибок в UI

```kotlin
class WorkflowViewModel : ViewModel() {
    private val _errorState = MutableStateFlow<String?>(null)
    val errorState = _errorState.asStateFlow()
    
    fun handleWorkflowError(error: Throwable) {
        val message = when (error) {
            is WorkflowError.BadRequest -> "Некорректные данные: ${error.message}"
            is WorkflowError.NotFound -> "Workflow не найден"
            is WorkflowError.ServerError -> "Ошибка сервера. Попробуйте позже"
            is WorkflowError.NetworkError -> "Проблема с подключением"
            is WorkflowError.Timeout -> "Превышено время ожидания"
            is WorkflowError.NoActiveSession -> "Сессия истекла. Начните заново"
            else -> "Произошла ошибка: ${error.message}"
        }
        
        _errorState.value = message
    }
}
```

---

## 🔒 Безопасность и Best Practices

### 1. Управление сессиями

```kotlin
// Установка TTL для сессий
class SessionManager(
    private val workflowManager: WorkflowManager,
    private val sessionStorage: SessionStorage
) {
    companion object {
        private const val SESSION_TTL_MS = 24 * 60 * 60 * 1000L // 24 часа
    }
    
    fun cleanupExpiredSessions() {
        val now = System.currentTimeMillis()
        sessionStorage.getAllSessions()
            .filter { now - it.createdAt > SESSION_TTL_MS }
            .forEach { sessionStorage.delete(it.id) }
    }
    
    fun isSessionValid(sessionId: String): Boolean {
        val session = sessionStorage.get(sessionId) ?: return false
        return System.currentTimeMillis() - session.createdAt < SESSION_TTL_MS
    }
}
```

### 2. Обработка конфиденциальных данных

```kotlin
// НЕ сохранять пароли и токены в context
fun submitLoginSafely(email: String, password: String) {
    workflowManager.sendEvent(
        eventName = "submit",
        additionalContext = mapOf(
            "email" to email,
            "password" to password  // Отправляется на сервер, но НЕ сохраняется в сессии
        )
    )
}

// После успешной авторизации - сохранить только токен отдельно
fun saveAuthToken(token: String) {
    secureStorage.saveToken(token)  // Используйте Keystore/Keychain
}
```

### 3. Кэширование экранов

```kotlin
// Кэш для уменьшения нагрузки
class ScreenCache {
    private val cache = LruCache<String, ScreenData>(maxSize = 20)
    
    fun get(stateId: String): ScreenData? = cache.get(stateId)
    
    fun put(stateId: String, screen: ScreenData) {
        cache.put(stateId, screen)
    }
}
```

### 4. Retry логика

```kotlin
suspend fun <T> retryWithBackoff(
    maxRetries: Int = 3,
    initialDelay: Long = 1000L,
    maxDelay: Long = 10000L,
    factor: Double = 2.0,
    block: suspend () -> T
): T {
    var currentDelay = initialDelay
    repeat(maxRetries) { attempt ->
        try {
            return block()
        } catch (e: Exception) {
            if (attempt == maxRetries - 1) throw e
            delay(currentDelay)
            currentDelay = (currentDelay * factor).toLong().coerceAtMost(maxDelay)
        }
    }
    throw IllegalStateException("Should not reach here")
}
```

---

## 📊 Мониторинг и аналитика

### События для отслеживания

```kotlin
class WorkflowAnalytics(private val analytics: AnalyticsService) {
    
    fun trackWorkflowStarted(workflowId: String) {
        analytics.logEvent("workflow_started", mapOf(
            "workflow_id" to workflowId,
            "timestamp" to System.currentTimeMillis()
        ))
    }
    
    fun trackStateTransition(
        fromState: String,
        toState: String,
        eventName: String
    ) {
        analytics.logEvent("state_transition", mapOf(
            "from_state" to fromState,
            "to_state" to toState,
            "event_name" to eventName,
            "timestamp" to System.currentTimeMillis()
        ))
    }
    
    fun trackWorkflowCompleted(
        workflowId: String,
        duration: Long,
        result: String
    ) {
        analytics.logEvent("workflow_completed", mapOf(
            "workflow_id" to workflowId,
            "duration_ms" to duration,
            "result" to result
        ))
    }
    
    fun trackError(
        error: WorkflowError,
        context: Map<String, Any>
    ) {
        analytics.logEvent("workflow_error", mapOf(
            "error_type" to error::class.simpleName,
            "error_message" to error.message,
            "context" to context
        ))
    }
}
```

---

## 🧪 Тестирование

### Unit тесты

```kotlin
class WorkflowManagerTest {
    private lateinit var mockApiClient: WorkflowApiClient
    private lateinit var mockStorage: SessionStorage
    private lateinit var workflowManager: WorkflowManager
    
    @Before
    fun setup() {
        mockApiClient = mockk()
        mockStorage = mockk()
        workflowManager = WorkflowManager(mockApiClient, mockStorage)
    }
    
    @Test
    fun `startWorkflow should create new session`() = runTest {
        // Given
        val workflowId = "test_workflow"
        val mockResponse = WorkflowResponse(
            sessionId = "session_123",
            context = mapOf("user_id" to "123"),
            currentState = "InitialScreen",
            stateType = "screen",
            screen = ScreenData(title = "Welcome")
        )
        coEvery { mockApiClient.executeWorkflow(any(), any(), any(), any()) } returns mockResponse
        
        // When
        val result = workflowManager.startWorkflow(workflowId)
        
        // Then
        assertEquals("InitialScreen", result.currentState)
        verify { mockStorage.save(any()) }
    }
    
    @Test
    fun `sendEvent should update context`() = runTest {
        // Given
        val session = WorkflowSession(
            id = "session_123",
            workflowId = "test_workflow",
            context = mutableMapOf("step" to 1)
        )
        workflowManager.currentSession = session
        
        val mockResponse = WorkflowResponse(
            sessionId = "session_123",
            context = mapOf("step" to 2, "completed" to true),
            currentState = "NextScreen",
            stateType = "screen",
            screen = null
        )
        coEvery { mockApiClient.executeWorkflow(any(), any(), any(), any()) } returns mockResponse
        
        // When
        workflowManager.sendEvent("next")
        
        // Then
        assertEquals(2, session.context["step"])
        assertEquals(true, session.context["completed"])
    }
}
```

### Integration тесты

```kotlin
@Test
fun `complete login workflow end-to-end`() = runTest {
    // 1. Start workflow
    val startResponse = workflowManager.startWorkflow("login_workflow")
    assertEquals("LoginScreen", startResponse.currentState)
    assertNotNull(startResponse.screen)
    
    // 2. Submit credentials
    val loginResponse = workflowManager.sendEvent(
        eventName = "submit",
        additionalContext = mapOf(
            "email" to "test@example.com",
            "password" to "password123"
        )
    )
    
    // 3. Verify technical state executed
    assertTrue(loginResponse.context.containsKey("is_valid"))
    
    // 4. Verify reached dashboard
    assertEquals("DashboardScreen", loginResponse.currentState)
    assertEquals("screen", loginResponse.stateType)
}
```

---

## 📦 Примеры структур экранов (Screen JSON)

### Форма с валидацией

```json
{
  "title": "Персональные данные",
  "description": "Заполните форму для продолжения",
  "fields": [
    {
      "id": "full_name",
      "type": "text",
      "label": "ФИО",
      "placeholder": "Иванов Иван Иванович",
      "required": true,
      "validation": {
        "minLength": 3,
        "maxLength": 100,
        "pattern": "^[А-Яа-яЁёA-Za-z\\s-]+$",
        "errorMessage": "Используйте только буквы, пробелы и дефисы"
      }
    },
    {
      "id": "birth_date",
      "type": "date",
      "label": "Дата рождения",
      "required": true,
      "validation": {
        "minAge": 18,
        "maxAge": 100
      }
    },
    {
      "id": "phone",
      "type": "phone",
      "label": "Телефон",
      "placeholder": "+7 (___) ___-__-__",
      "mask": "+7 (###) ###-##-##",
      "required": true
    },
    {
      "id": "agree_terms",
      "type": "checkbox",
      "label": "Согласен с условиями обработки персональных данных",
      "required": true,
      "link": {
        "text": "Прочитать условия",
        "url": "https://example.com/terms"
      }
    }
  ],
  "buttons": [
    {
      "id": "submit_btn",
      "label": "Продолжить",
      "event": "submit",
      "style": "primary",
      "enabled": "{{all_fields_valid}}"
    },
    {
      "id": "back_btn",
      "label": "Назад",
      "event": "back",
      "style": "secondary"
    }
  ]
}
```

### Информационный экран с карточками

```json
{
  "title": "Выберите тариф",
  "components": [
    {
      "type": "card_list",
      "items": [
        {
          "id": "basic",
          "title": "Базовый",
          "price": "0 ₽",
          "features": [
            "До 5 заявок в месяц",
            "Базовая поддержка",
            "Хранение 30 дней"
          ],
          "badge": "Бесплатно",
          "action": {
            "event": "select_plan",
            "params": {"plan_id": "basic"}
          }
        },
        {
          "id": "premium",
          "title": "Премиум",
          "price": "999 ₽/мес",
          "features": [
            "Неограниченные заявки",
            "Приоритетная поддержка 24/7",
            "Безлимитное хранение",
            "Персональный менеджер"
          ],
          "badge": "Популярный",
          "highlighted": true,
          "action": {
            "event": "select_plan",
            "params": {"plan_id": "premium"}
          }
        }
      ]
    }
  ],
  "buttons": [
    {
      "id": "skip",
      "label": "Пропустить",
      "event": "skip",
      "style": "text"
    }
  ]
}
```

### Экран с динамическим контентом

```json
{
  "title": "Ваша заявка",
  "components": [
    {
      "type": "text",
      "content": "Здравствуйте, {{user_name}}!",
      "style": "heading"
    },
    {
      "type": "text",
      "content": "Ваша заявка №{{application_id}} на сумму {{loan_amount}} ₽",
      "style": "body"
    },
    {
      "type": "status_badge",
      "status": "{{application_status}}",
      "statusMap": {
        "approved": {"label": "Одобрено", "color": "green"},
        "pending": {"label": "На рассмотрении", "color": "yellow"},
        "rejected": {"label": "Отклонено", "color": "red"}
      }
    },
    {
      "type": "progress_bar",
      "value": "{{completion_percent}}",
      "max": 100,
      "label": "Заполнено {{completion_percent}}%"
    },
    {
      "type": "conditional",
      "condition": "{{application_status}} == 'approved'",
      "ifTrue": {
        "type": "button",
        "label": "Получить средства",
        "event": "confirm_loan",
        "style": "primary"
      },
      "ifFalse": {
        "type": "text",
        "content": "Ожидайте решения банка",
        "style": "muted"
      }
    }
  ]
}
```

---

## ✅ Чек-лист интеграции

### Backend готовность
- [ ] Сервис развернут и доступен по HTTP/HTTPS
- [ ] Создан хотя бы один тестовый workflow через `/workflow/save`
- [ ] Получен `workflow_id` для использования в приложении
- [ ] Настроены CORS для мобильных клиентов
- [ ] Настроен мониторинг и логирование

### Mobile App - Core
- [ ] Реализован `WorkflowManager` с методами start/sendEvent/restore
- [ ] Реализован `WorkflowApiClient` для HTTP запросов
- [ ] Настроена сериализация/десериализация JSON
- [ ] Реализовано `SessionStorage` для сохранения сессий
- [ ] Добавлена обработка ошибок (сеть, сервер, состояние)

### Mobile App - UI
- [ ] Реализован `DynamicScreenRenderer` для экранов из JSON
- [ ] Поддержка базовых типов полей (text, email, password, number)
- [ ] Поддержка кнопок с событиями
- [ ] Отображение заголовков и описаний
- [ ] Поддержка интерполяции `{{variables}}` в тексте

### Testing
- [ ] Unit тесты для `WorkflowManager`
- [ ] Unit тесты для `SessionStorage`
- [ ] Integration тест полного workflow (от старта до завершения)
- [ ] UI тесты для `DynamicScreenRenderer`
- [ ] Тесты обработки ошибок

### Production Ready
- [ ] Retry логика для сетевых запросов
- [ ] Timeout для API вызовов
- [ ] Кэширование экранов
- [ ] Очистка истекших сессий
- [ ] Аналитика событий workflow
- [ ] Безопасное хранение токенов
- [ ] Логирование для отладки

---

## 🔗 Дополнительные ресурсы

### Связанные файлы в проекте

- `api/routes.py` - API endpoints
- `workflow_builder/state_parser/contract.py` - Pydantic модели
- `workflow_builder/handlers.py` - Обработчики состояний
- `workflow_builder/expressions.py` - Модели выражений
- `api/testWorkflow.py` - Примеры workflow
- `docs/TECHNICAL_STATES_IMPROVEMENT_PROMPT.md` - Документация технических состояний

### Примеры использования

См. `api/testWorkflow.py` для готовых примеров:
- `test_workflow_1_simple_login()` - Авторизация
- `test_workflow_3_complex_loan_application()` - Кредитная заявка
- `test_workflow_4_simple_survey()` - Опросник
- `test_workflow_12_simple_contact_form()` - Контактная форма

---

## 🆘 FAQ и Troubleshooting

### Q: Как обновить workflow без обновления приложения?

**A:** Просто сохраните новую версию workflow через `/workflow/save` с тем же `workflow_id`. При следующем запуске приложение получит обновленные экраны и логику.

### Q: Можно ли запустить несколько workflow одновременно?

**A:** Да, каждый workflow имеет свою сессию. Используйте разные `client_session_id` для параллельных процессов.

### Q: Как обработать случай, когда пользователь закрыл приложение на середине workflow?

**A:** Используйте `SessionStorage` и метод `restoreSession()`. При запуске приложения проверяйте наличие активных сессий и предлагайте пользователю продолжить.

```kotlin
fun onAppStarted() {
    val activeSessions = sessionStorage.getAllSessions()
    if (activeSessions.isNotEmpty()) {
        showResumeDialog(activeSessions.first())
    }
}
```

### Q: Что делать, если сервер вернул ошибку 400/500?

**A:** Обработайте через try-catch и покажите пользователю понятное сообщение. Для 400 (клиентская ошибка) - проверьте данные. Для 500 (серверная ошибка) - предложите повторить позже.

### Q: Как передать файлы (фото, документы) через workflow?

**A:** 
1. Загрузите файл на CDN/S3
2. Передайте URL файла в `context`:
```kotlin
workflowManager.sendEvent("upload_complete", mapOf(
    "document_url" to uploadedFileUrl,
    "document_type" to "passport"
))
```

### Q: Можно ли использовать этот сервис для real-time уведомлений?

**A:** Нет, сервис работает по модели request-response. Для уведомлений используйте WebSocket/SSE или Firebase Cloud Messaging отдельно.

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи сервера (MongoDB, Redis, FastAPI)
2. Проверьте формат JSON в запросах
3. Используйте инструменты отладки (Postman, curl)
4. Обратитесь к примерам в `api/testWorkflow.py`

**Контакты команды разработки:**
- Email: support@workflow-engine.example.com
- Telegram: @workflow_support
- GitHub Issues: github.com/your-repo/issues

---

_Последнее обновление: 2 октября 2025 г._
