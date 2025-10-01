# Диаграммы последовательности LCT EFS

## 1. Создание и сохранение Workflow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant MongoDB
    
    Client->>API: POST /workflow/save
    Note over Client,API: {states: {...}, predefined_context: {...}}
    
    API->>MongoDB: Insert states definition
    activate MongoDB
    MongoDB-->>API: workflow_id
    deactivate MongoDB
    
    API->>MongoDB: Insert predefined context
    activate MongoDB
    Note over API,MongoDB: Same ID as workflow
    MongoDB-->>API: context_id
    deactivate MongoDB
    
    API-->>Client: {wf_description_id, wf_context_id}
```

---

## 2. Запуск Workflow (новая сессия)

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Redis
    participant MongoDB
    participant Automaton
    participant SessionContext
    
    Client->>API: POST /client/workflow
    Note over Client,API: {client_session_id, client_workflow_id}
    
    API->>Redis: Check session exists
    Redis-->>API: Not found
    
    API->>Redis: Create new session
    Note over API,Redis: {__workflow_id, __created_at}
    Redis-->>API: session_id
    
    API->>Automaton: Initialize(session_id, workflow_id)
    
    activate Automaton
    Automaton->>SessionContext: Get session state
    activate SessionContext
    SessionContext->>Redis: get_state(session_id)
    Redis-->>SessionContext: StateMetadata or default
    SessionContext-->>Automaton: initial_state_name
    deactivate SessionContext
    
    Automaton->>MongoDB: Load workflow definition
    activate MongoDB
    MongoDB-->>Automaton: States JSON
    deactivate MongoDB
    
    Automaton->>Automaton: Build state graph
    Automaton->>Automaton: Create state objects
    
    Automaton->>Automaton: run()
    Note over Automaton: Start FSM iteration
    deactivate Automaton
    
    API-->>Client: {session_id, context}
```

---

## 3. Workflow Execution (Iteration Loop)

```mermaid
sequenceDiagram
    participant Automaton
    participant CurrentState as Current State
    participant Handler
    participant SessionContext
    participant Redis
    participant External as External API
    
    loop Until Final State
        alt Screen State
            Automaton->>CurrentState: Check if on_return
            alt on_return == true
                Automaton->>Redis: Save state checkpoint
                Automaton-->>Client: Return screen data
                Note over Automaton: Wait for event
            else on_return == false
                Automaton->>CurrentState: Match event
                CurrentState->>Handler: result(event_name)
                Handler-->>CurrentState: bool (matched)
                CurrentState-->>Automaton: Transition candidate
            end
        else Technical/Integration/Service State
            Automaton->>CurrentState: Get executables
            
            loop For each expression
                CurrentState->>Handler: Evaluate expression
                
                alt Technical Handler
                    Handler->>Handler: simpleeval(expression)
                    Handler-->>CurrentState: result
                else Integration Handler
                    Handler->>External: HTTP request
                    External-->>Handler: response
                    Handler-->>CurrentState: api_result
                else Service Handler
                    Handler->>MongoDB: Get workflow context
                    Handler->>Redis: Cache context
                    Handler-->>CurrentState: context loaded
                end
                
                CurrentState->>SessionContext: Update variable
            end
            
            Automaton->>CurrentState: Get transition candidates
            CurrentState->>CurrentState: Evaluate transition.case
            CurrentState-->>Automaton: next_state_id
        end
        
        Automaton->>Automaton: Set current_state = next_state
        Automaton->>Redis: Update session state
    end
    
    Automaton-->>Client: Workflow complete
```

---

## 4. Context Management Lifecycle

```mermaid
sequenceDiagram
    participant Code
    participant SessionContext
    participant Redis
    
    Code->>SessionContext: with SessionContext(session_id, wf_id) as ctx
    activate SessionContext
    
    SessionContext->>SessionContext: __enter__()
    SessionContext->>Redis: get_session(session_id)
    Redis-->>SessionContext: session_data (dict)
    SessionContext->>SessionContext: Store in self._session
    SessionContext-->>Code: context dict
    
    Code->>Code: Modify context
    Note over Code: ctx["key"] = "value"
    
    Code->>SessionContext: __exit__()
    SessionContext->>SessionContext: update_session()
    
    SessionContext->>SessionContext: Flatten nested structures
    Note over SessionContext: JSON.dumps for dict/list
    
    SessionContext->>Redis: update_session(session_id, flat_context)
    Redis-->>SessionContext: OK
    
    deactivate SessionContext
```

---

## 5. Expression Evaluation Flow

```mermaid
sequenceDiagram
    participant Automaton
    participant State
    participant Expression
    participant Handler
    participant Context
    
    Automaton->>State: Evaluate all executables
    
    loop For each expression
        State->>Expression: Get metadata
        Expression-->>State: {variable, dependent_vars, ...}
        
        State->>Handler: Check dependent_variables in context
        
        alt Variables present
            State->>Handler: result()
            
            alt Technical Expression
                Handler->>Handler: simpleeval(expression, names=context.session)
                Note over Handler: Functions: len, sum, max, min
                Handler-->>State: computed_value
            else Integration Expression
                Handler->>Handler: Parse URL
                Handler->>Handler: Get adapter method
                Handler->>External API: HTTP call
                External API-->>Handler: response
                Handler-->>State: api_response
            else Screen Expression
                Handler->>Handler: Match event_name
                Handler-->>State: bool
            else Service Expression
                Handler->>MongoDB: Load workflow context
                Handler->>Redis: Cache context
                Handler->>Context: Merge with session
                Handler-->>State: context_loaded
            end
            
            State->>Context: Update variable
            Context->>Context: context[variable] = result
        else Variables missing
            State-->>Automaton: ValueError: Missing variables
        end
    end
    
    State-->>Automaton: All expressions evaluated
```

---

## 6. Transition Selection Process

```mermaid
sequenceDiagram
    participant Automaton
    participant State
    participant Expression
    participant Transition
    participant Context
    
    Automaton->>State: Get transition candidates
    
    alt Based on Expressions (Technical/Integration)
        loop For each expression
            State->>Expression: Check if bindable
            
            alt Expression has transition_bind_object
                Expression->>Context: Get variable result
                Context-->>Expression: result_value
                
                loop For each bound transition
                    Expression->>Transition: Check case condition
                    
                    alt case == None
                        Transition-->>Expression: Match (no condition)
                    else case != None
                        Transition->>Transition: eval(case, context)
                        Note over Transition: Example: "balance > 100"
                        
                        alt Condition True
                            Transition-->>Expression: Match
                        else Condition False
                            Transition-->>Expression: No match
                        end
                    end
                end
                
                alt Transition matched
                    Expression-->>State: First matching transition
                    State-->>Automaton: transition.state_id
                end
            end
        end
        
        alt No expression transition matched
            State->>State: Find default transition (case=None)
            State-->>Automaton: default_transition.state_id
        end
        
    else Based on Event (Screen State)
        loop For each expression
            State->>Expression: result(event_name)
            
            alt Event matched
                Expression->>Expression: Get bound transitions
                Expression-->>State: First transition
                State-->>Automaton: transition.state_id
            end
        end
    end
    
    alt No transition found
        Automaton->>Automaton: Raise ValueError
        Note over Automaton: "No matching transition found"
    end
```

---

## 7. State Creation and Graph Building

```mermaid
sequenceDiagram
    participant Automaton
    participant GlobalStateParser
    participant MongoDB
    participant StateFactory
    participant State
    
    Automaton->>GlobalStateParser: Init(current_state, workflow_id)
    
    GlobalStateParser->>MongoDB: Load workflow definition
    MongoDB-->>GlobalStateParser: States JSON array
    
    GlobalStateParser->>GlobalStateParser: Add __init__ state
    GlobalStateParser->>GlobalStateParser: Add __error__ state
    
    GlobalStateParser->>GlobalStateParser: get_automaton_subgraph()
    Note over GlobalStateParser: BFS from initial state<br/>Stop at Screen states
    
    GlobalStateParser-->>Automaton: List[StateModel]
    
    loop For each StateModel
        Automaton->>StateFactory: build_state(state_model)
        
        StateFactory->>StateFactory: Get STATE_CLASSES[state_type]
        Note over StateFactory: Technical/Integration/Screen/Service
        
        StateFactory->>GlobalStateParser: Parse transitions
        GlobalStateParser-->>StateFactory: List[Transition]
        
        StateFactory->>GlobalStateParser: Parse expressions
        GlobalStateParser-->>StateFactory: List[Expression]
        
        StateFactory->>State: Create state instance
        activate State
        
        State->>State: _create_exec_handlers()
        State->>State: Resolve handler creator
        Note over State: state_mapping[state_type]
        
        State->>State: _bind_transitions()
        Note over State: Link expressions to transitions
        
        deactivate State
        StateFactory-->>Automaton: WorkflowState instance
    end
    
    Automaton->>Automaton: Create state_mapping dict
    Note over Automaton: {state.name: state}
```

---

## 8. Dependency (Service) State Initialization

```mermaid
sequenceDiagram
    participant Automaton
    participant ServiceState
    participant DependencyHandler
    participant MongoDB
    participant Redis
    participant SessionContext
    
    Automaton->>ServiceState: Execute (type=service)
    
    ServiceState->>DependencyHandler: result()
    
    DependencyHandler->>Redis: Check workflow_context:{workflow_id} exists
    
    alt Context not in Redis
        DependencyHandler->>MongoDB: get(workflow_id)
        activate MongoDB
        MongoDB-->>DependencyHandler: workflow_context (dict)
        deactivate MongoDB
        
        alt Context found
            DependencyHandler->>DependencyHandler: dump_context(wf_context)
            Note over DependencyHandler: Serialize to JSON
            
            DependencyHandler->>Redis: set_workflow_context(wf_id, context)
            Redis-->>DependencyHandler: OK
        else Context not found
            DependencyHandler-->>ServiceState: Raise ValueError
        end
    else Context in Redis
        DependencyHandler->>Redis: get_workflow_context(workflow_id)
        Redis-->>DependencyHandler: workflow_context
    end
    
    DependencyHandler->>SessionContext: Check for key conflicts
    Note over DependencyHandler: wf_context.keys() & session.keys()
    
    alt No conflicts
        DependencyHandler->>SessionContext: Update session with wf_context
        SessionContext->>SessionContext: context.update(wf_context)
    end
    
    DependencyHandler-->>ServiceState: workflow_context
    ServiceState-->>Automaton: Context initialized
```

---

## 9. Handler Creation Pattern

```mermaid
sequenceDiagram
    participant State
    participant HandlerCreator
    participant Handler
    
    State->>State: _create_exec_handlers()
    
    State->>State: _resolve_exec_creator()
    State->>State: Get from state_mapping[state_type]
    Note over State: state_mapping = {<br/>  technical: WorkflowTechnicalHandlersCreator,<br/>  integration: WorkflowIntegrationHandlersCreator,<br/>  screen: WorkflowScreenHandlersCreator,<br/>  service: WorkflowDependencyHandlersCreator<br/>}
    
    State->>HandlerCreator: __init__(context, workflow_state, handlers)
    
    HandlerCreator->>HandlerCreator: __call__()
    
    loop For each expression
        alt Technical
            HandlerCreator->>Handler: TechnicalHandler(metadata, context)
        else Integration
            HandlerCreator->>Handler: IntegrationHandler(adapter, metadata, context)
        else Screen
            HandlerCreator->>Handler: ScreenHandler(metadata, context)
        else Service
            HandlerCreator->>Handler: DependencyHandler(metadata, context, behaviour)
        end
        
        Handler-->>HandlerCreator: Handler instance
    end
    
    HandlerCreator-->>State: List[Handler]
```

---

## 10. Screen State Event Handling

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Automaton
    participant ScreenState
    participant Handler
    participant Redis
    
    Client->>API: POST /client/workflow
    Note over Client,API: {session_id, event_name: "button_click"}
    
    API->>Automaton: run(event_name="button_click")
    
    Automaton->>Automaton: Check current_state.type_ == screen
    
    alt First visit (on_return=true)
        Automaton->>Redis: update_session_state(ScreenState metadata)
        Automaton-->>API: Return screen data
        API-->>Client: {session_id, screen_state}
        Note over Client: User interacts with UI
        
        Client->>API: POST /client/workflow
        Note over Client,API: {session_id, event_name: "button_click"}
        
        API->>Automaton: run(event_name="button_click")
        Automaton->>Automaton: on_return=false (continue)
    end
    
    Automaton->>ScreenState: Get transition based on event
    
    loop For each expression
        ScreenState->>Handler: result(event_name)
        
        Handler->>Handler: Check metadata.event_name == event_name
        
        alt Event matches
            Handler-->>ScreenState: True
            
            ScreenState->>ScreenState: Get transition_bind_object
            ScreenState-->>Automaton: First matching transition
            
            Automaton->>Automaton: Set next state
            Automaton->>Automaton: Continue iteration
        else Event doesn't match
            Handler-->>ScreenState: False
        end
    end
    
    alt No matching event
        Automaton-->>API: ValueError: No transition found
    end
```

---

## Ключевые моменты

### 🔄 Циклическая природа FSM
- Автомат итерируется в бесконечном цикле `while True`
- Выход происходит при достижении `final_state` или `Screen` состояния (на первом посещении)

### 🎯 Два режима работы Screen State
1. **on_return=True**: Возврат экрана клиенту, сохранение состояния
2. **on_return=False**: Обработка события, переход к следующему состоянию

### 🔗 Связывание Transitions и Expressions
- Происходит в методе `_bind_transitions()` каждого состояния
- Для Technical/Integration: по `variable`
- Для Screen: по `event_name`

### 📦 Context Manager Pattern
- `SessionContext` автоматически сохраняет изменения при выходе из блока `with`
- Thread-safe операции с контекстом

### 🛡️ Безопасность выполнения
- `simpleeval` для изолированного выполнения Python кода
- Ограниченный набор функций: `len`, `sum`, `max`, `min`
- Валидация наличия всех `dependent_variables` перед выполнением
