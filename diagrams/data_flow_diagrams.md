# Диаграммы потоков данных LCT EFS

## 1. Общий поток данных в системе

```mermaid
flowchart TB
    Start([Клиент]) --> SaveWF{Сохранить<br/>workflow?}
    
    SaveWF -->|Да| SaveAPI[POST /workflow/save]
    SaveWF -->|Нет| ExecAPI[POST /client/workflow]
    
    SaveAPI --> MongoStates[(MongoDB<br/>states collection)]
    SaveAPI --> MongoWF[(MongoDB<br/>workflows collection)]
    MongoStates --> SaveResp[Response:<br/>wf_description_id]
    MongoWF --> SaveResp
    SaveResp --> End1([Клиент])
    
    ExecAPI --> CheckSession{Сессия<br/>существует?}
    
    CheckSession -->|Нет| CreateSession[Создать сессию<br/>в Redis]
    CheckSession -->|Да| LoadSession[Загрузить сессию]
    
    CreateSession --> InitAuto[Инициализация<br/>Automaton]
    LoadSession --> InitAuto
    
    InitAuto --> LoadWF[Загрузить workflow<br/>из MongoDB]
    LoadWF --> BuildGraph[Построить граф<br/>состояний]
    BuildGraph --> RunFSM[Запустить FSM]
    
    RunFSM --> EvalState{Тип<br/>состояния?}
    
    EvalState -->|Service| ServiceExec[Загрузка контекста<br/>из MongoDB→Redis]
    EvalState -->|Technical| TechExec[Вычисление<br/>выражений]
    EvalState -->|Integration| IntegExec[HTTP API<br/>вызов]
    EvalState -->|Screen| ScreenExec[Ожидание<br/>события]
    
    ServiceExec --> UpdateCtx[Обновить<br/>контекст]
    TechExec --> UpdateCtx
    IntegExec --> UpdateCtx
    ScreenExec --> CheckReturn{on_return?}
    
    CheckReturn -->|true| SaveState[Сохранить state<br/>в Redis]
    SaveState --> ReturnScreen[Вернуть экран<br/>клиенту]
    ReturnScreen --> End2([Клиент])
    
    CheckReturn -->|false| MatchEvent[Сопоставить<br/>событие]
    MatchEvent --> UpdateCtx
    
    UpdateCtx --> FindTrans[Найти подходящий<br/>переход]
    FindTrans --> CheckFinal{Финальное<br/>состояние?}
    
    CheckFinal -->|Нет| NextState[Переход к<br/>следующему состоянию]
    NextState --> EvalState
    
    CheckFinal -->|Да| SaveCtx[Сохранить контекст<br/>в Redis]
    SaveCtx --> Response[Response:<br/>session_id, context]
    Response --> End3([Клиент])
    
    style SaveAPI fill:#e3f2fd
    style ExecAPI fill:#e3f2fd
    style MongoStates fill:#f3e5f5
    style MongoWF fill:#f3e5f5
    style RunFSM fill:#e8f5e9
    style UpdateCtx fill:#fff9c4
    style SaveCtx fill:#ffe0b2
```

---

## 2. Детальный поток выполнения Automaton

```mermaid
flowchart TD
    Start([Automaton.run]) --> Init[Инициализация]
    
    Init --> LoadState[Загрузить initial_state<br/>из Redis]
    LoadState --> LoadWF[Загрузить workflow<br/>definition из MongoDB]
    LoadWF --> ParseStates[Парсинг состояний<br/>GlobalStateParser]
    
    ParseStates --> AddService[Добавить служебные<br/>состояния __init__, __error__]
    AddService --> BuildSubgraph[Построить подграф<br/>BFS до Screen states]
    BuildSubgraph --> CreateStates[Создать объекты<br/>WorkflowState]
    
    CreateStates --> SetCurrent[current_state = __init__]
    SetCurrent --> LoopStart{Цикл: while True}
    
    LoopStart --> CheckFinal{current_state<br/>._final?}
    CheckFinal -->|Да| EndFlow([Завершение<br/>workflow])
    
    CheckFinal -->|Нет| CheckType{Тип<br/>состояния?}
    
    CheckType -->|Screen| CheckOnReturn{on_return?}
    CheckOnReturn -->|true| SaveCheckpoint[Сохранить checkpoint<br/>в Redis]
    SaveCheckpoint --> ReturnToClient([Вернуть экран<br/>клиенту])
    
    CheckOnReturn -->|false| MatchEventFlow[Сопоставить событие]
    MatchEventFlow --> GetEventTrans[Получить переход<br/>по событию]
    GetEventTrans --> SetNext
    
    CheckType -->|Service| EvalService[Выполнить<br/>service handlers]
    CheckType -->|Technical| EvalTech[Вычислить<br/>expressions]
    CheckType -->|Integration| EvalInteg[HTTP запрос]
    
    EvalService --> UpdateSession[Обновить<br/>session context]
    EvalTech --> UpdateSession
    EvalInteg --> UpdateSession
    
    UpdateSession --> GetExprTrans[Получить переходы<br/>по выражениям]
    
    GetExprTrans --> CheckTrans{Переход<br/>найден?}
    CheckTrans -->|Нет| ErrorState[→ __error__]
    ErrorState --> EndFlow
    
    CheckTrans -->|Да| EvalCase{Проверить<br/>transition.case}
    EvalCase -->|None или True| SetNext[Установить<br/>next_state]
    EvalCase -->|False| GetExprTrans
    
    SetNext --> SaveState[Сохранить state<br/>metadata в Redis]
    SaveState --> LoopStart
    
    style LoopStart fill:#ffecb3
    style CheckFinal fill:#f3e5f5
    style CheckType fill:#e1f5fe
    style UpdateSession fill:#e8f5e9
    style SaveCheckpoint fill:#fce4ec
    style ReturnToClient fill:#c8e6c9
```

---

## 3. Поток управления контекстом

```mermaid
flowchart LR
    subgraph Client["Клиент"]
        Request[HTTP Request]
        Response[HTTP Response]
    end
    
    subgraph API["API Layer"]
        Route[Route Handler]
    end
    
    subgraph Automaton["Automaton Engine"]
        Auto[Automaton]
        CtxMgr[SessionContext]
    end
    
    subgraph Handlers["State Handlers"]
        TechH[TechnicalHandler]
        IntegH[IntegrationHandler]
        ScreenH[ScreenHandler]
        DepH[DependencyHandler]
    end
    
    subgraph Storage["Storage Layer"]
        RedisSession[(Redis<br/>session:{id})]
        RedisState[(Redis<br/>state:{id})]
        RedisWFCtx[(Redis<br/>workflow_context:{id})]
        MongoWF[(MongoDB<br/>workflows)]
    end
    
    Request --> Route
    Route --> Auto
    
    Auto -->|with SessionContext| CtxMgr
    CtxMgr -->|__enter__<br/>load| RedisSession
    
    Auto --> TechH
    Auto --> IntegH
    Auto --> ScreenH
    Auto --> DepH
    
    TechH -->|read/write| CtxMgr
    IntegH -->|read/write| CtxMgr
    ScreenH -->|read/write| CtxMgr
    DepH -->|read/write| CtxMgr
    
    DepH -->|lazy load| MongoWF
    MongoWF -->|cache| RedisWFCtx
    RedisWFCtx -->|merge| CtxMgr
    
    Auto -->|checkpoint| RedisState
    
    CtxMgr -->|__exit__<br/>save| RedisSession
    
    Auto --> Route
    Route --> Response
    
    style CtxMgr fill:#fff9c4
    style RedisSession fill:#e1f5fe
    style RedisState fill:#e1f5fe
    style RedisWFCtx fill:#e1f5fe
    style MongoWF fill:#f3e5f5
```

---

## 4. Поток обработки выражений

```mermaid
flowchart TD
    Start([State Execution]) --> GetExprs[Получить список<br/>expressions]
    
    GetExprs --> LoopExprs{Для каждого<br/>expression}
    
    LoopExprs --> CheckDeps{Проверить<br/>dependent_variables}
    
    CheckDeps -->|Отсутствуют| RaiseError[Raise ValueError:<br/>Missing variables]
    CheckDeps -->|Присутствуют| CheckType{Тип<br/>expression?}
    
    CheckType -->|Technical| EvalPython[simpleeval<br/>Python expression]
    CheckType -->|Integration| CallAPI[HTTP request<br/>via CommonAdapter]
    CheckType -->|Screen| MatchEvent[Сопоставить<br/>event_name]
    CheckType -->|Service| LoadCtx[Загрузить context<br/>MongoDB→Redis]
    
    EvalPython --> StoreResult[Сохранить результат<br/>в context variable]
    CallAPI --> StoreResult
    MatchEvent --> ReturnBool[Вернуть<br/>bool]
    LoadCtx --> MergeCtx[Merge с<br/>session context]
    
    StoreResult --> CheckBindable{Expression<br/>bindable?}
    ReturnBool --> CheckBindable
    MergeCtx --> LoopExprs
    
    CheckBindable -->|Нет| LoopExprs
    CheckBindable -->|Да| GetBoundTrans[Получить<br/>transition_bind_object]
    
    GetBoundTrans --> LoopExprs
    
    LoopExprs -->|Все обработаны| AllDone[Все expressions<br/>вычислены]
    AllDone --> End([Переход к<br/>transition logic])
    
    style CheckDeps fill:#fff9c4
    style StoreResult fill:#e8f5e9
    style MergeCtx fill:#c8e6c9
    style GetBoundTrans fill:#e1bee7
```

---

## 5. Поток выбора перехода

```mermaid
flowchart TD
    Start([После выполнения<br/>expressions]) --> CheckStateType{Тип<br/>состояния?}
    
    CheckStateType -->|Screen| ScreenFlow[Поток по событиям]
    CheckStateType -->|Other| ExprFlow[Поток по выражениям]
    
    ScreenFlow --> LoopScreenExpr{Для каждого<br/>screen expression}
    LoopScreenExpr --> CallHandler[Handler.result<br/>event_name]
    
    CallHandler --> CheckMatch{Event<br/>совпал?}
    CheckMatch -->|Нет| LoopScreenExpr
    CheckMatch -->|Да| GetScreenTrans[Получить<br/>bound transitions]
    GetScreenTrans --> ReturnFirst1[Вернуть первый<br/>переход]
    ReturnFirst1 --> End
    
    LoopScreenExpr -->|Не найдено| NoMatch1[Нет совпадения]
    NoMatch1 --> RaiseError1[Raise ValueError]
    
    ExprFlow --> LoopExpr{Для каждого<br/>expression}
    
    LoopExpr --> CheckBindable{Expression<br/>bindable?}
    CheckBindable -->|Нет| LoopExpr
    CheckBindable -->|Да| GetResult[Получить result<br/>из context variable]
    
    GetResult --> GetBoundTrans[Получить<br/>transition_bind_object]
    GetBoundTrans --> LoopTrans{Для каждого<br/>bound transition}
    
    LoopTrans --> CheckCase{transition.case<br/>существует?}
    CheckCase -->|Нет| ReturnTrans[Вернуть переход]
    CheckCase -->|Да| EvalCase[eval case<br/>с context]
    
    EvalCase --> CaseResult{Результат?}
    CaseResult -->|True| ReturnTrans
    CaseResult -->|False| LoopTrans
    
    LoopTrans -->|Не найдено| LoopExpr
    LoopExpr -->|Не найдено| CheckDefault{Есть default<br/>transition?}
    
    CheckDefault -->|Да| GetDefault[Получить transition<br/>без case]
    CheckDefault -->|Нет| NoMatch2[Нет совпадения]
    
    GetDefault --> ReturnFirst2[Вернуть<br/>default transition]
    NoMatch2 --> RaiseError2[Raise ValueError]
    
    ReturnTrans --> End([Установить<br/>next_state])
    ReturnFirst2 --> End
    
    style CheckCase fill:#fff9c4
    style EvalCase fill:#ffe0b2
    style ReturnTrans fill:#c8e6c9
    style End fill:#a5d6a7
```

---

## 6. Поток сохранения и загрузки workflow

```mermaid
flowchart TB
    subgraph Save["Сохранение Workflow"]
        S1[Клиент отправляет<br/>POST /workflow/save]
        S2[API получает<br/>StateSet + context]
        S3[Сериализация states<br/>в JSON]
        S4[Сохранение в MongoDB<br/>states collection]
        S5[Генерация workflow_id]
        S6[Сохранение context<br/>с тем же ID]
        S7[Возврат IDs клиенту]
        
        S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7
    end
    
    subgraph Load["Загрузка Workflow"]
        L1[Automaton.__init__]
        L2[GlobalStateParser<br/>инициализация]
        L3[MongoDB.get<br/>workflow_id]
        L4[Десериализация<br/>JSON → StateModel]
        L5[Добавление<br/>__init__, __error__]
        L6[get_automaton_subgraph<br/>BFS обход]
        L7[Создание<br/>WorkflowState объектов]
        
        L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7
    end
    
    subgraph Context["Загрузка Context"]
        C1[DependencyHandler.init_result]
        C2[Проверка Redis<br/>workflow_context:{id}]
        C3{В кэше?}
        C4[MongoDB.get<br/>workflow_id]
        C5[Redis.set_workflow_context]
        C6[Redis.get_workflow_context]
        C7[Merge с session context]
        
        C1 --> C2 --> C3
        C3 -->|Нет| C4 --> C5 --> C7
        C3 -->|Да| C6 --> C7
    end
    
    S7 -.->|workflow_id| L1
    L7 -.->|Service state| C1
    
    style S4 fill:#f3e5f5
    style S6 fill:#f3e5f5
    style L3 fill:#f3e5f5
    style C4 fill:#f3e5f5
    style C5 fill:#e1f5fe
    style C6 fill:#e1f5fe
    style C7 fill:#c8e6c9
```

---

## 7. Поток обработки Screen State

```mermaid
sequenceDiagram
    participant C as Клиент
    participant A as Automaton
    participant S as ScreenState
    participant H as ScreenHandler
    participant R as Redis
    
    Note over C,R: Первый визит (on_return=true)
    
    C->>A: POST /client/workflow<br/>{session_id, workflow_id}
    A->>A: current_state = ScreenState
    A->>A: Check on_return = true
    A->>R: Save state checkpoint
    A->>C: Return {session_id, screen_data}
    
    Note over C: Пользователь взаимодействует с UI
    
    Note over C,R: Второй визит (on_return=false)
    
    C->>A: POST /client/workflow<br/>{session_id, event_name: "confirm"}
    A->>A: on_return = false
    A->>S: Get transition by event
    
    loop Для каждого expression
        S->>H: result("confirm")
        H->>H: Check event_name == "confirm"
        alt Event matched
            H->>S: return True
            S->>S: Get transition_bind_object
            S->>A: Return matching transition
        else Event not matched
            H->>S: return False
        end
    end
    
    A->>A: Set next_state
    A->>A: Continue FSM iteration
    A->>C: Eventually return response
```

---

## 8. Поток интеграции с внешним API

```mermaid
flowchart TD
    Start([Integration State]) --> GetExprs[Получить integration<br/>expressions]
    
    GetExprs --> CheckDeps{Проверить<br/>dependent_variables}
    CheckDeps -->|Отсутствуют| Error1[Raise ValueError]
    CheckDeps -->|Присутствуют| CreateHandler[Создать<br/>IntegrationHandler]
    
    CreateHandler --> ParseURL[Парсинг URL<br/>на base_url + endpoint]
    ParseURL --> CreateAdapter[Создать<br/>CommonAdapter base_url]
    
    CreateAdapter --> GetMethod[Получить метод<br/>adapter.get/post/etc]
    GetMethod --> PrepareParams[Подготовить params<br/>из metadata]
    
    PrepareParams --> CheckDepVars{Все variables<br/>в контексте?}
    CheckDepVars -->|Нет| Error2[Raise ValueError]
    CheckDepVars -->|Да| MakeRequest[HTTP Request<br/>method endpoint, params]
    
    MakeRequest --> CheckResponse{Успешный<br/>ответ?}
    CheckResponse -->|Нет| Error3[HTTP Error]
    CheckResponse -->|Да| ParseResponse[Парсинг response]
    
    ParseResponse --> StoreInContext[Сохранить в context<br/>variable = response]
    StoreInContext --> GetTransition[Получить единственный<br/>bound transition]
    
    GetTransition --> CheckCase{transition.case<br/>exists?}
    CheckCase -->|Да| Error4[ValueError:<br/>Integration can't have case]
    CheckCase -->|Нет| ReturnTrans[Вернуть переход]
    
    ReturnTrans --> End([Переход к<br/>next_state])
    
    style MakeRequest fill:#fff9c4
    style StoreInContext fill:#e8f5e9
    style ReturnTrans fill:#c8e6c9
```

---

## 9. Поток обработки Technical State

```mermaid
flowchart TD
    Start([Technical State]) --> GetExprs[Получить technical<br/>expressions]
    
    GetExprs --> LoopExpr{Для каждого<br/>expression}
    
    LoopExpr --> CheckDeps{Проверить<br/>dependent_variables<br/>в context}
    
    CheckDeps -->|Отсутствуют| Error1[Raise ValueError:<br/>Missing variables]
    CheckDeps -->|Присутствуют| CreateHandler[Создать<br/>TechnicalHandler]
    
    CreateHandler --> CallResult[Handler.result]
    CallResult --> CheckComposite{Тип<br/>expression?}
    
    CheckComposite -->|TechnicalAndExpression| EvalAnd[Вычислить все<br/>выражения через AND]
    CheckComposite -->|TechnicalOrExpression| EvalOr[Вычислить все<br/>выражения через OR]
    CheckComposite -->|Simple| EvalSimple[simpleeval<br/>одно выражение]
    
    EvalAnd --> AllowedFunc{Использует только<br/>разрешенные функции?}
    EvalOr --> AllowedFunc
    EvalSimple --> AllowedFunc
    
    AllowedFunc -->|Нет| Error2[SecurityError:<br/>Forbidden function]
    AllowedFunc -->|Да| ExecuteEval[simpleeval<br/>names=context.session]
    
    ExecuteEval --> GetResult[Получить результат]
    GetResult --> StoreVar[context variable<br/>= result]
    
    StoreVar --> LoopExpr
    
    LoopExpr -->|Все обработаны| GetTransitions[Получить transitions<br/>по переменным]
    
    GetTransitions --> LoopTrans{Для каждого<br/>bound transition}
    
    LoopTrans --> CheckCase{transition.case<br/>exists?}
    CheckCase -->|Нет| ReturnTrans[Вернуть переход]
    CheckCase -->|Да| EvalCase[eval case<br/>с context]
    
    EvalCase --> CaseResult{Результат?}
    CaseResult -->|True| ReturnTrans
    CaseResult -->|False| LoopTrans
    
    LoopTrans -->|Не найдено| DefaultTrans{Есть default?}
    DefaultTrans -->|Да| ReturnDefault[Вернуть default<br/>без case]
    DefaultTrans -->|Нет| Error3[ValueError:<br/>No transition]
    
    ReturnTrans --> End([Переход к<br/>next_state])
    ReturnDefault --> End
    
    style ExecuteEval fill:#fff9c4
    style AllowedFunc fill:#ffecb3
    style StoreVar fill:#e8f5e9
    style ReturnTrans fill:#c8e6c9
```

---

## 10. Полный цикл: от запроса до ответа

```mermaid
flowchart TB
    Start([🔵 START]) --> ClientReq[📱 Клиент:<br/>POST /client/workflow]
    
    ClientReq --> APIRoute[🌐 API Route Handler]
    APIRoute --> CheckSess{🔍 Сессия<br/>существует?}
    
    CheckSess -->|❌ Нет| CreateSess[➕ Redis:<br/>create_session]
    CheckSess -->|✅ Да| LoadSess[📥 Redis:<br/>get_session]
    
    CreateSess --> InitAuto[⚙️ Automaton:<br/>__init__]
    LoadSess --> InitAuto
    
    InitAuto --> LoadDef[📚 MongoDB:<br/>Load workflow definition]
    LoadDef --> ParseDef[🔧 GlobalStateParser:<br/>Parse states]
    ParseDef --> BuildGraph[🔗 Build state graph<br/>BFS]
    BuildGraph --> CreateStates[🏗️ Create WorkflowState<br/>objects]
    
    CreateStates --> StartRun[▶️ Automaton.run]
    StartRun --> FSMLoop{🔄 FSM Loop<br/>while not final}
    
    FSMLoop --> StateType{❓ State Type?}
    
    StateType -->|🔧 Service| ExecService[🛠️ Load context<br/>MongoDB→Redis]
    StateType -->|📐 Technical| ExecTech[🧮 Evaluate<br/>expressions]
    StateType -->|🌐 Integration| ExecInteg[📡 HTTP API<br/>call]
    StateType -->|🖥️ Screen| ExecScreen[👁️ Check<br/>on_return]
    
    ExecService --> UpdateCtx1[💾 Update<br/>context]
    ExecTech --> UpdateCtx1
    ExecInteg --> UpdateCtx1
    ExecScreen --> CheckReturn{🔀 on_return?}
    
    CheckReturn -->|✅ true| SaveCheckpoint[📌 Save checkpoint<br/>to Redis]
    SaveCheckpoint --> ReturnScreen[⏸️ Return screen<br/>to client]
    ReturnScreen --> ClientResp1[📤 Response to Client]
    ClientResp1 --> End1([🟢 END - Screen Returned])
    
    CheckReturn -->|❌ false| MatchEvt[🎯 Match event]
    MatchEvt --> UpdateCtx2[💾 Update<br/>context]
    
    UpdateCtx1 --> FindTrans[🔍 Find matching<br/>transition]
    UpdateCtx2 --> FindTrans
    
    FindTrans --> CheckTransFound{✅ Transition<br/>found?}
    CheckTransFound -->|❌ No| ErrorState[❌ → __error__]
    ErrorState --> SaveErr[💾 Save error state]
    SaveErr --> ClientResp2[📤 Error Response]
    ClientResp2 --> End2([🔴 END - Error])
    
    CheckTransFound -->|✅ Yes| EvalCase{📋 Evaluate<br/>transition.case}
    EvalCase -->|✅ Match| SetNext[⏭️ Set next_state]
    EvalCase -->|❌ No match| FindTrans
    
    SetNext --> SaveStateMeta[💾 Save state<br/>metadata to Redis]
    SaveStateMeta --> CheckFinal{🏁 Final<br/>state?}
    
    CheckFinal -->|❌ No| FSMLoop
    CheckFinal -->|✅ Yes| SaveFinal[💾 Save final<br/>context to Redis]
    SaveFinal --> ClientResp3[📤 Final Response]
    ClientResp3 --> End3([🟢 END - Workflow Complete])
    
    style Start fill:#4CAF50,color:#fff
    style End1 fill:#4CAF50,color:#fff
    style End2 fill:#f44336,color:#fff
    style End3 fill:#4CAF50,color:#fff
    style FSMLoop fill:#FFC107
    style UpdateCtx1 fill:#2196F3,color:#fff
    style UpdateCtx2 fill:#2196F3,color:#fff
    style SaveCheckpoint fill:#9C27B0,color:#fff
    style ReturnScreen fill:#00BCD4,color:#fff
```

---

## Легенда символов

| Символ | Значение |
|--------|----------|
| 🔵 | Точка входа |
| 🟢 | Успешное завершение |
| 🔴 | Завершение с ошибкой |
| 📱 | Клиентский запрос |
| 🌐 | API endpoint |
| 📚 | MongoDB операция |
| 💾 | Redis операция |
| ⚙️ | Инициализация компонента |
| 🔄 | Цикл |
| ❓ | Условие/проверка |
| ⏭️ | Переход к следующему |
| 🔧 | Service state |
| 📐 | Technical state |
| 🌐 | Integration state |
| 🖥️ | Screen state |
| 🧮 | Вычисление |
| 📡 | Внешний API вызов |
| 👁️ | Проверка |
| 🎯 | Сопоставление |
| 📌 | Checkpoint |
| ⏸️ | Приостановка |
| 🏁 | Финальное состояние |

---

## Ключевые точки потока

### 1. **Точки принятия решений**
- Существование сессии → создание или загрузка
- Тип состояния → выбор обработчика
- on_return флаг → возврат экрана или продолжение
- Финальное состояние → завершение или итерация

### 2. **Точки персистентности**
- Создание сессии → Redis `session:{id}`
- Checkpoint состояния → Redis `state:{id}`
- Контекст workflow → Redis `workflow_context:{id}`
- Финальный контекст → Redis `session:{id}` update

### 3. **Точки взаимодействия с внешними системами**
- Загрузка workflow → MongoDB `states`
- Загрузка контекста → MongoDB `workflows`
- Integration state → Внешние HTTP API
- DependencyHandler → MongoDB → Redis (lazy loading)

### 4. **Точки возврата клиенту**
- Screen state (on_return=true) → частичный результат
- Final state → полный результат
- Error state → ошибка выполнения
