# Диаграммы классов и структур данных LCT EFS

## 1. Class Diagram - Core Components

```mermaid
classDiagram
    class Automaton {
        -str _session_id
        -str _workflow_id
        -str zero_state
        -SessionContext session_context
        -str initial_state_name
        -GlobalStateParser global_state_parser
        -List~WorkflowState~ states
        -Dict state_mapping
        -WorkflowState _current_state
        
        +__init__(session_id, workflow_id)
        +build_state(StateModel) WorkflowState
        +_create_states() List
        +_resolve_initial_state() StateMetadata
        +_get_transition_candidates_based_on_expressions() Transition
        +_get_transition_candidates_based_on_event() Transition
        +_evaluate_executables(event_name)
        +_evaluate_service_executables()
        +_call_state_checkpoint()
        +run(event_name)
    }
    
    class SessionContext {
        -RedisCache _redis_cache
        -str _session_id
        -str _workflow_id
        -dict _session
        
        +__init__(session_id, workflow_id)
        +session() dict
        +_get_session_context() dict
        +get(key) Any
        +__enter__() dict
        +__exit__(exc_type, exc_value, traceback)
        +update_session_state(StateMetadata)
        +get_session_state() StateMetadata
        +update_session()
    }
    
    class WorkflowState {
        <<abstract>>
        +StateTypeEnum type_
        +UUID uid
        +SessionContext context
        +str name
        +bool initial_state
        +bool _final
        +dict state_local_context
        +List expressions
        +List~Transition~ transitions
        +List executables
        
        +__init__(context, name, transitions, expressions, initial_state, final)
        +_create_exec_handlers() List
        +_resolve_exec_creator() HandlerCreator
        +_bind_transitions()
    }
    
    class TechnicalState {
        +StateTypeEnum type_ = "technical"
    }
    
    class IntegrationState {
        +StateTypeEnum type_ = "integration"
    }
    
    class ScreenState {
        +StateTypeEnum type_ = "screen"
    }
    
    class ServiceState {
        +StateTypeEnum type_ = "service"
    }
    
    class BaseHandler {
        <<abstract>>
        +Any metadata
        +SessionContext context
        
        +result()* Any
    }
    
    class TechnicalHandler {
        +TechnicalStateExpression metadata
        
        +result() Any
    }
    
    class IntegrationHandler {
        +CommonAdapter adapter
        +IntegrationStateExpression metadata
        
        +_split_url() Tuple
        +_get_method(adapter) Callable
        +result() Any
    }
    
    class ScreenHandler {
        +ScreenStateExpression metadata
        
        +result(event_name) bool
    }
    
    class DependencyHandler {
        +ServiceStateExpression metadata
        +BehaviourTypeEnum behaviour_type
        
        +result() Any
        +init_result() dict
        +error_result()
    }
    
    class Expression {
        <<static>>
        +technical(dependent_variables, expression) TechnicalStateExpression
        +integration(variable, url, method, params) IntegrationStateExpression
        +screen(event_name) ScreenStateExpression
        +service(mongo_collection_name) ServiceStateExpression
    }
    
    class Transition {
        +str state_id
        +Optional~str~ case
        +Set~str~ variables
        +Set~str~ keys
        
        +matches(context) bool
    }
    
    class GlobalStateParser {
        +str current_state_name
        +str workflow_id
        +List~StateModel~ data
        
        +__init__(current_state_name, workflow_id)
        +_parse_transitions(StateModel) List~Transition~
        +_parse_expressions(StateModel, ExpressionClass) List
        +get_automaton_subgraph() List~StateModel~
    }
    
    class RedisCache {
        <<singleton>>
        +Redis r
        
        +__init__()
        +save_state(session_id, state_obj)
        +get_state(session_id) dict
        +create_session(data) str
        +get_session(session_id) dict
        +update_session(session_id, data)
        +delete_session(session_id)
        +set_workflow_context(session_id, context)
        +get_workflow_context(session_id) dict
        +get_session_key(session_id)$ str
        +get_state_key(session_id)$ str
        +get_wf_context_key(session_id)$ str
    }
    
    class MongoDBClient {
        +str mongo_url
        +str database_name
        +str collection_name
        
        +insert_description(data, overriden_id) str
        +get(id) dict
    }
    
    Automaton --> SessionContext : uses
    Automaton --> WorkflowState : manages
    Automaton --> GlobalStateParser : uses
    Automaton --> Transition : evaluates
    
    WorkflowState <|-- TechnicalState
    WorkflowState <|-- IntegrationState
    WorkflowState <|-- ScreenState
    WorkflowState <|-- ServiceState
    WorkflowState --> SessionContext : uses
    WorkflowState --> Transition : has
    WorkflowState --> BaseHandler : creates
    
    BaseHandler <|-- TechnicalHandler
    BaseHandler <|-- IntegrationHandler
    BaseHandler <|-- ScreenHandler
    BaseHandler <|-- DependencyHandler
    BaseHandler --> SessionContext : uses
    
    SessionContext --> RedisCache : uses
    
    GlobalStateParser --> MongoDBClient : uses
    
    Expression --> Transition : binds
```

---

## 2. Expression Type Hierarchy

```mermaid
classDiagram
    class BaseExpression {
        <<abstract>>
        +str variable
        +Optional~Transition~ transition_bind_object
        
        +bindable()* bool
        +bind_transition(name) Self
    }
    
    class TechnicalStateExpression {
        +str variable
        +List~str~ dependent_variables
        +str expression
        
        +bindable() bool
        +bind_transition(name) Self
    }
    
    class IntegrationStateExpression {
        +str variable
        +str url
        +str method
        +dict params
        +List~str~ dependent_variables
        
        +bindable() bool
        +bind_transition(name) Self
    }
    
    class ScreenStateExpression {
        +str event_name
        
        +bindable() bool
        +bind_transition(name) Self
    }
    
    class ServiceStateExpression {
        +str mongo_collection_name
        +MongoDBClient mongo_client
        +RedisCache redis_client
        
        +bindable() bool
    }
    
    class TechnicalAndExpression {
        +List~str~ expression
        +List~str~ dependent_variables
        
        +__and__(other) TechnicalAndExpression
    }
    
    class TechnicalOrExpression {
        +List~str~ expression
        +List~str~ dependent_variables
        
        +__or__(other) TechnicalOrExpression
    }
    
    BaseExpression <|-- TechnicalStateExpression
    BaseExpression <|-- IntegrationStateExpression
    BaseExpression <|-- ScreenStateExpression
    BaseExpression <|-- ServiceStateExpression
    
    TechnicalStateExpression <|-- TechnicalAndExpression
    TechnicalStateExpression <|-- TechnicalOrExpression
    
    TechnicalStateExpression --> TechnicalAndExpression : & operator
    TechnicalStateExpression --> TechnicalOrExpression : | operator
```

---

## 3. Handler Creator Pattern

```mermaid
classDiagram
    class BaseHandlersCreator~T~ {
        <<abstract>>
        +SessionContext context
        +WorkflowState workflow_state
        +List handlers
        
        +__init__(context, workflow_state, handlers)
        +__call__()* List~T~
    }
    
    class WorkflowTechnicalHandlersCreator {
        +__call__() List~TechnicalHandler~
    }
    
    class WorkflowIntegrationHandlersCreator {
        +__call__() List~IntegrationHandler~
    }
    
    class WorkflowScreenHandlersCreator {
        +__call__() List~ScreenHandler~
    }
    
    class WorkflowDependencyHandlersCreator {
        +__call__() List~DependencyHandler~
    }
    
    class StateTypeEnum {
        <<enumeration>>
        technical
        integration
        screen
        service
    }
    
    BaseHandlersCreator <|-- WorkflowTechnicalHandlersCreator
    BaseHandlersCreator <|-- WorkflowIntegrationHandlersCreator
    BaseHandlersCreator <|-- WorkflowScreenHandlersCreator
    BaseHandlersCreator <|-- WorkflowDependencyHandlersCreator
    
    note for BaseHandlersCreator "state_mapping: Dict[StateTypeEnum, Type[BaseHandlersCreator]]\n= {\n  StateTypeEnum.technical: WorkflowTechnicalHandlersCreator,\n  StateTypeEnum.integration: WorkflowIntegrationHandlersCreator,\n  StateTypeEnum.screen: WorkflowScreenHandlersCreator,\n  StateTypeEnum.service: WorkflowDependencyHandlersCreator\n}"
```

---

## 4. Data Models

```mermaid
classDiagram
    class StateModel {
        +str state_type
        +str name
        +List~TransitionModel~ transitions
        +List~ExpressionModel~ expressions
        +bool initial_state
        +bool final_state
        
        +zero_state(next_state_name)$ StateModel
        +error_state()$ StateModel
    }
    
    class TransitionModel {
        +str state_id
        +Optional~str~ case
        +Set~str~ variables
        +Set~str~ keys
    }
    
    class ExpressionModel {
        <<union>>
        TechnicalExpressionModel | IntegrationExpressionModel | ScreenExpressionModel
    }
    
    class TechnicalExpressionModel {
        +str variable
        +List~str~ dependent_variables
        +str expression
    }
    
    class IntegrationExpressionModel {
        +str variable
        +str url
        +str method
        +dict params
    }
    
    class ScreenExpressionModel {
        +str event_name
    }
    
    class StateMetadata {
        +str name
        +StateTypeEnum type_
    }
    
    class StateSet {
        +List~StateModel~ states
    }
    
    StateModel --> TransitionModel : has many
    StateModel --> ExpressionModel : has many
    
    ExpressionModel <|-- TechnicalExpressionModel
    ExpressionModel <|-- IntegrationExpressionModel
    ExpressionModel <|-- ScreenExpressionModel
```

---

## 5. API Request/Response Models

```mermaid
classDiagram
    class WorkflowRequest {
        +str client_session_id
        +Optional~str~ client_workflow_id
        +Optional~str~ event_name
    }
    
    class SaveWorkflowRequest {
        +StateSet states
        +dict predefined_context
    }
    
    class SaveWorkflowResponse {
        +str status
        +str wf_description_id
        +str wf_context_id
    }
    
    class WorkflowExecutionResponse {
        +str session_id
        +dict context
    }
```

---

## 6. Storage Layer Structure

```mermaid
classDiagram
    class RedisCache {
        <<singleton>>
        +Redis r
        
        +create_session(data: dict) str
        +get_session(session_id: str) dict
        +update_session(session_id: str, data: dict)
        +delete_session(session_id: str)
        +save_state(session_id: str, state_obj: dict)
        +get_state(session_id: str) dict
        +set_workflow_context(session_id: str, context: dict)
        +get_workflow_context(session_id: str) dict
        +cache_screen(screen_id: str, screen: dict)
    }
    
    class MongoDBClient {
        +MongoClient client
        +Database db
        +Collection collection
        
        +__init__(mongo_url, database_name, collection_name)
        +insert_description(data: dict, overriden_id: str) str
        +get(id: str) dict
        +find(query: dict) List~dict~
    }
    
    note for RedisCache "Keys:\n• session:{id}\n• state:{id}\n• workflow_context:{id}\n• screen:{id}"
    
    note for MongoDBClient "Collections:\n• states (STATES_MONGO_COLLECTION)\n• workflows (WORKFLOW_MONGO_COLLECTION)"
```

---

## 7. State Lifecycle Diagram

```mermaid
stateDiagram-v2
    [*] --> __init__ : Automaton.run()
    
    __init__ --> TechnicalState : Load context
    __init__ --> IntegrationState : Load context
    __init__ --> ScreenState : Load context
    
    TechnicalState --> TechnicalState : Evaluate expression
    TechnicalState --> IntegrationState : Transition
    TechnicalState --> ScreenState : Transition
    TechnicalState --> __error__ : Error
    
    IntegrationState --> IntegrationState : HTTP call
    IntegrationState --> TechnicalState : Transition
    IntegrationState --> ScreenState : Transition
    IntegrationState --> __error__ : Error
    
    ScreenState --> ScreenState : on_return=true (wait event)
    ScreenState --> TechnicalState : on_return=false (event matched)
    ScreenState --> IntegrationState : Transition
    ScreenState --> FinalState : Transition
    
    TechnicalState --> FinalState : final=true
    IntegrationState --> FinalState : final=true
    
    FinalState --> [*]
    __error__ --> [*]
    
    note right of __init__
        Service State
        - Load workflow context from MongoDB
        - Cache to Redis
        - Merge with session
    end note
    
    note right of TechnicalState
        - Evaluate Python expressions
        - simpleeval for safety
        - Update context variables
    end note
    
    note right of IntegrationState
        - Make HTTP API calls
        - CommonAdapter
        - Store response in context
    end note
    
    note right of ScreenState
        - Event-driven transitions
        - First visit: return screen
        - Second visit: process event
    end note
```

---

## 8. Context Data Flow

```mermaid
graph TB
    subgraph "MongoDB"
        WF_DEF[Workflow Definition<br/>states collection]
        WF_CTX[Predefined Context<br/>workflows collection]
    end
    
    subgraph "Redis Cache"
        SESSION[session:{id}<br/>Current session data]
        STATE[state:{id}<br/>State metadata]
        WF_CACHE[workflow_context:{id}<br/>Cached workflow context]
        SCREEN[screen:{id}<br/>Screen cache]
    end
    
    subgraph "Automaton Runtime"
        CTX[SessionContext<br/>Active context]
        HANDLERS[Handlers<br/>Execute logic]
    end
    
    WF_DEF -->|Load on init| Automaton
    WF_CTX -->|Lazy load| WF_CACHE
    WF_CACHE -->|Merge| CTX
    
    SESSION <-->|Read/Write| CTX
    STATE <-->|Checkpoint| CTX
    
    CTX <-->|Variables| HANDLERS
    HANDLERS -->|Update| CTX
    
    CTX -->|Auto-save on exit| SESSION
    
    style SESSION fill:#e1f5fe
    style STATE fill:#e1f5fe
    style WF_CACHE fill:#e1f5fe
    style SCREEN fill:#e1f5fe
    
    style WF_DEF fill:#f3e5f5
    style WF_CTX fill:#f3e5f5
    
    style CTX fill:#e8f5e9
    style HANDLERS fill:#e8f5e9
```

---

## 9. Expression Binding Mechanism

```mermaid
graph TD
    subgraph "State Initialization"
        STATE[WorkflowState]
        EXPR[Expressions List]
        TRANS[Transitions List]
    end
    
    subgraph "Binding Process (_bind_transitions)"
        CHECK{State Type?}
        
        TECH_BIND[Technical/Integration:<br/>Match by variable]
        SCREEN_BIND[Screen:<br/>Match by event_name]
        
        FILTER_TECH[Filter transitions where<br/>variable in transition.variables]
        FILTER_SCREEN[Filter transitions where<br/>event_name in transition.keys]
    end
    
    subgraph "Result"
        BOUND_EXPR[Expression with<br/>transition_bind_object]
    end
    
    STATE --> EXPR
    STATE --> TRANS
    
    EXPR --> CHECK
    TRANS --> CHECK
    
    CHECK -->|technical/integration| TECH_BIND
    CHECK -->|screen| SCREEN_BIND
    
    TECH_BIND --> FILTER_TECH
    SCREEN_BIND --> FILTER_SCREEN
    
    FILTER_TECH --> BOUND_EXPR
    FILTER_SCREEN --> BOUND_EXPR
    
    BOUND_EXPR -->|Used in| TRANSITION_EVAL[Transition Evaluation]
    
    style BOUND_EXPR fill:#c8e6c9
    style TRANSITION_EVAL fill:#fff9c4
```

---

## 10. Complete System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLIENT[Client Application]
    end
    
    subgraph "API Layer (FastAPI)"
        SAVE[POST /workflow/save]
        EXEC[POST /client/workflow]
    end
    
    subgraph "Core FSM Engine"
        AUTO[Automaton]
        PARSER[GlobalStateParser]
        
        subgraph "States"
            TECH[TechnicalState]
            INTEG[IntegrationState]
            SCR[ScreenState]
            SERV[ServiceState]
        end
        
        subgraph "Handlers"
            H_TECH[TechnicalHandler]
            H_INTEG[IntegrationHandler]
            H_SCR[ScreenHandler]
            H_DEP[DependencyHandler]
        end
    end
    
    subgraph "Context Management"
        SCTX[SessionContext]
    end
    
    subgraph "Storage"
        MONGO[(MongoDB)]
        REDIS[(Redis)]
    end
    
    subgraph "External Services"
        API_EXT[External APIs]
    end
    
    CLIENT -->|Save workflow| SAVE
    CLIENT -->|Execute workflow| EXEC
    
    SAVE --> MONGO
    
    EXEC --> AUTO
    AUTO --> PARSER
    PARSER --> MONGO
    
    AUTO --> TECH
    AUTO --> INTEG
    AUTO --> SCR
    AUTO --> SERV
    
    TECH --> H_TECH
    INTEG --> H_INTEG
    SCR --> H_SCR
    SERV --> H_DEP
    
    H_TECH --> SCTX
    H_INTEG --> SCTX
    H_INTEG --> API_EXT
    H_SCR --> SCTX
    H_DEP --> SCTX
    H_DEP --> MONGO
    
    SCTX <--> REDIS
    
    AUTO --> SCTX
    
    style CLIENT fill:#e3f2fd
    style MONGO fill:#f3e5f5
    style REDIS fill:#fce4ec
    style AUTO fill:#e8f5e9
    style SCTX fill:#fff9c4
```

---

## Key Design Patterns

### 1. **Registry Pattern**
```python
state_mapping: dict[StateTypeEnum, Type[BaseHandlersCreator]] = {
    StateTypeEnum.technical: WorkflowTechnicalHandlersCreator,
    StateTypeEnum.integration: WorkflowIntegrationHandlersCreator,
    StateTypeEnum.screen: WorkflowScreenHandlersCreator,
    StateTypeEnum.service: WorkflowDependencyHandlersCreator,
}
```

### 2. **Factory Pattern**
- `BaseHandlersCreator` создает handlers на основе типа состояния
- `Automaton.build_state()` создает состояния из моделей

### 3. **Singleton Pattern**
- `RedisCache` использует `GeneralPurposeSingletonMeta`

### 4. **Context Manager Pattern**
- `SessionContext` с автоматическим сохранением при `__exit__`

### 5. **Strategy Pattern**
- Различные `Handler` классы для разных типов выражений

### 6. **Decorator Pattern**
- `@check_context_consistency` для валидации переменных
- `@execute_safe` для безопасных внешних вызовов

---

## Type Relationships

```python
# State → Handler mapping
TechnicalState      → TechnicalHandler      → TechnicalStateExpression
IntegrationState    → IntegrationHandler    → IntegrationStateExpression  
ScreenState         → ScreenHandler         → ScreenStateExpression
ServiceState        → DependencyHandler     → ServiceStateExpression

# Expression → Transition binding
Technical/Integration: expression.variable ∈ transition.variables
Screen:               expression.event_name ∈ transition.keys
```

---

## Data Persistence Strategy

| Data Type | Storage | Key Pattern | Lifetime |
|-----------|---------|-------------|----------|
| Workflow Definition | MongoDB | `states` collection | Permanent |
| Predefined Context | MongoDB | `workflows` collection | Permanent |
| Session Data | Redis | `session:{id}` | Session (TTL) |
| State Metadata | Redis | `state:{id}` | Session |
| Workflow Context Cache | Redis | `workflow_context:{id}` | Cached |
| Screen Data | Redis | `screen:{id}` | Short (1s) |
