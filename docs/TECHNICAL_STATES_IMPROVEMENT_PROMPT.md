# Промпт: Доработка логики создания технических состояний в админ-панели

## 📋 Контекст

В системе существует workflow-engine, который обрабатывает различные типы состояний, включая **технические состояния** (`technical`). Эти состояния выполняют условную логику и переключают workflow на основе вычисления выражений.

### Текущая архитектура

#### 1. **Структура технического состояния (JSON из админ-панели)**

```json
{
  "state_type": "technical",
  "name": "CheckEligibility",
  "transitions": [
    {
      "variable": "credit_score_high",
      "case": "True",
      "state_id": "ApprovedState"
    },
    {
      "variable": "credit_score_medium",
      "case": "True",
      "state_id": "AdditionalInfoState"
    },
    {
      "variable": ["credit_score_high", "credit_score_medium"],
      "case": "False",
      "state_id": "RejectedState"
    }
  ],
  "expressions": [
    {
      "variable": "credit_score_high",
      "dependent_variables": ["annual_income", "debt_ratio"],
      "expression": "annual_income > 75000 and debt_ratio < 0.3"
    },
    {
      "variable": "credit_score_medium",
      "dependent_variables": ["annual_income", "debt_ratio"],
      "expression": "annual_income > 50000 and debt_ratio < 0.4"
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

#### 2. **Обработка на бэкенде**

**Файл:** `workflow_builder/handlers.py`

```python
@define(slots=True)
class TechnicalHandler(BaseHandler):
    metadata: "TechnicalStateExpression"
    context: "SessionContext"

    @check_context_consistency
    def result(self):
        return simple_eval(
            self.metadata.expression,
            names=self.context.session,
            functions={"len": len, "sum": sum, "max": max, "min": min}
        )
```

**Файл:** `workflow_builder/expressions.py`

```python
@define(slots=True)
class TechnicalStateExpression(LogicalExpressionMixin, BaseStateExpression):
    variable: str = field(validator=validators.instance_of(str))
    dependent_variables: list[str] = field(validator=validators.instance_of(list))
    expression: str = field(validator=validators.instance_of(str))
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.technical
```

## 🎯 Проблемы текущей реализации

### 1. **Отсутствие типизации результатов выражений**

- Выражение может вернуть любой тип: `bool`, `int`, `str`, `list`, `dict`
- Нет явного указания ожидаемого типа результата
- Сложно валидировать корректность на этапе создания workflow

**Пример проблемы:**
```python
# Админ создал выражение, которое вернет строку вместо bool
"expression": "'approved'"  # Вернет 'approved', а не True/False
# При сравнении в transition: case="True" - не сработает!
```

### 2. **Ограниченный набор операторов и функций**

Текущие доступные функции: `len`, `sum`, `max`, `min`

**Недостающие возможности:**
- Математические операции: `abs()`, `round()`, `pow()`
- Строковые операции: `str.upper()`, `str.lower()`, `str.strip()`, `str.startswith()`
- Проверки типов: `isinstance()`, `type()`
- Работа со списками: `any()`, `all()`, `sorted()`, `filter()`
- Работа со словарями: `dict.get()`, `dict.keys()`, `dict.values()`
- Даты/время: `datetime.now()`, `timedelta`
- Регулярные выражения: `re.match()`, `re.search()`

**Пример проблемы:**
```python
# Нужно округлить число
"expression": "round(annual_income / 12, 2)"  # round() недоступна!

# Нужно проверить, начинается ли строка с определенного символа
"expression": "email.startswith('admin@')"  # str.startswith() недоступен!
```

### 3. **Отсутствие валидации на этапе создания**

- Выражение проверяется только во время выполнения
- Синтаксические ошибки в expression обнаруживаются поздно
- Нет проверки существования dependent_variables в контексте

**Пример проблемы:**
```json
{
  "variable": "is_adult",
  "dependent_variables": ["age", "country"],
  "expression": "age >= 18 and country == 'US'"
  // Если в контексте нет "country" - ошибка возникнет во время выполнения!
}
```

### 4. **Сложность отладки**

- При ошибке в expression непонятно, на каком этапе и где именно произошла ошибка
- Нет логирования промежуточных результатов
- Трудно диагностировать, почему transition не сработал

**Пример проблемы:**
```python
# Сложное выражение с ошибкой
"expression": "annual_income > 75000 and debt_ratio < 0.3 and credit_history == 'good'"
# Если credit_history is None - получим TypeError, но не будет понятно, что именно None
```

### 5. **Отсутствие метаданных для админ-панели**

- Нет описания (description) для понимания логики состояния
- Нет тегов/категорий для группировки
- Нет примеров входных/выходных данных
- Нет версионирования выражений

### 6. **Проблемы с множественными переходами**

```json
{
  "variable": ["credit_score_high", "credit_score_medium"],
  "case": "False",
  "state_id": "RejectedState"
}
```

- Непонятно, как интерпретировать массив переменных: AND или OR?
- Нет явного указания логики (всех False или хотя бы одного False?)

### 7. **Безопасность выполнения кода**

- `simple_eval` имеет ограничения, но они могут быть недостаточными
- Нет ограничения по времени выполнения (timeout)
- Нет ограничения по глубине вложенности выражений
- Возможна инъекция кода через контекст

## 🚀 Предлагаемые улучшения

### 1. **Добавить типизацию результатов**

#### Расширить модель выражения:

```json
{
  "variable": "credit_score_high",
  "dependent_variables": ["annual_income", "debt_ratio"],
  "expression": "annual_income > 75000 and debt_ratio < 0.3",
  "return_type": "boolean",  // NEW: Ожидаемый тип результата
  "default_value": false      // NEW: Значение по умолчанию при ошибке
}
```

**Поддерживаемые типы:**
- `boolean` - True/False
- `integer` - целые числа
- `float` - числа с плавающей точкой
- `string` - строки
- `list` - массивы
- `dict` - словари
- `any` - любой тип (не рекомендуется)

#### Изменения в коде:

```python
@define(slots=True)
class TechnicalStateExpression(LogicalExpressionMixin, BaseStateExpression):
    variable: str = field(validator=validators.instance_of(str))
    dependent_variables: list[str] = field(validator=validators.instance_of(list))
    expression: str = field(validator=validators.instance_of(str))
    return_type: str = field(default="boolean")  # NEW
    default_value: Any = field(default=None)     # NEW
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.technical
    
    @return_type.validator
    def _validate_return_type(self, attribute, value):
        allowed_types = ["boolean", "integer", "float", "string", "list", "dict", "any"]
        if value not in allowed_types:
            raise ValueError(f"return_type must be one of {allowed_types}")
```

```python
class TechnicalHandler(BaseHandler):
    @check_context_consistency
    def result(self):
        try:
            result = simple_eval(
                self.metadata.expression,
                names=self.context.session,
                functions=self._get_safe_functions()
            )
            
            # Валидация типа результата
            if not self._validate_result_type(result):
                logger.warning(
                    f"Result type mismatch for {self.metadata.variable}: "
                    f"expected {self.metadata.return_type}, got {type(result).__name__}"
                )
                return self.metadata.default_value
            
            return result
        except Exception as e:
            logger.error(
                f"Error evaluating expression for {self.metadata.variable}: {e}",
                exc_info=True
            )
            return self.metadata.default_value
    
    def _validate_result_type(self, result) -> bool:
        type_map = {
            "boolean": bool,
            "integer": int,
            "float": (int, float),
            "string": str,
            "list": list,
            "dict": dict,
            "any": object
        }
        expected_type = type_map.get(self.metadata.return_type)
        return isinstance(result, expected_type)
```

### 2. **Расширить набор безопасных функций**

```python
def _get_safe_functions(self) -> dict:
    """Возвращает безопасный набор функций для simple_eval"""
    return {
        # Математические
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        
        # Строковые (через безопасные обертки)
        "upper": lambda s: str(s).upper() if s is not None else "",
        "lower": lambda s: str(s).lower() if s is not None else "",
        "strip": lambda s: str(s).strip() if s is not None else "",
        "startswith": lambda s, prefix: str(s).startswith(prefix) if s is not None else False,
        "endswith": lambda s, suffix: str(s).endswith(suffix) if s is not None else False,
        "contains": lambda s, substr: substr in str(s) if s is not None else False,
        
        # Коллекции
        "len": len,
        "any": any,
        "all": all,
        "sorted": sorted,
        "reversed": lambda x: list(reversed(x)),
        
        # Проверки
        "is_none": lambda x: x is None,
        "is_not_none": lambda x: x is not None,
        "is_empty": lambda x: len(x) == 0 if hasattr(x, '__len__') else False,
        
        # Словари
        "get": lambda d, k, default=None: d.get(k, default) if isinstance(d, dict) else default,
        "keys": lambda d: list(d.keys()) if isinstance(d, dict) else [],
        "values": lambda d: list(d.values()) if isinstance(d, dict) else [],
        
        # Преобразования типов
        "int": lambda x, default=0: int(x) if x is not None else default,
        "float": lambda x, default=0.0: float(x) if x is not None else default,
        "str": lambda x: str(x) if x is not None else "",
        "bool": lambda x: bool(x),
    }
```

### 3. **Добавить валидацию на этапе сохранения**

```python
class TechnicalExpressionValidator:
    """Валидатор технических выражений"""
    
    def validate(self, expression: TechnicalExpressionModel, context_schema: dict) -> list[str]:
        """
        Валидирует выражение и возвращает список ошибок
        
        Args:
            expression: Модель технического выражения
            context_schema: Схема доступных переменных контекста
            
        Returns:
            Список ошибок (пустой список если валидация прошла успешно)
        """
        errors = []
        
        # 1. Проверка синтаксиса выражения
        try:
            compile(expression.expression, '<string>', 'eval')
        except SyntaxError as e:
            errors.append(f"Syntax error in expression: {e}")
        
        # 2. Проверка существования dependent_variables в контексте
        for var in expression.dependent_variables:
            if var not in context_schema:
                errors.append(f"Variable '{var}' not found in context schema")
        
        # 3. Проверка используемых переменных в выражении
        used_vars = self._extract_variables(expression.expression)
        for var in used_vars:
            if var not in expression.dependent_variables:
                errors.append(
                    f"Variable '{var}' used in expression but not listed in dependent_variables"
                )
        
        # 4. Проверка безопасности (запрещенные конструкции)
        forbidden = ['__', 'import', 'eval', 'exec', 'compile', 'open', 'file']
        for word in forbidden:
            if word in expression.expression:
                errors.append(f"Forbidden keyword '{word}' in expression")
        
        # 5. Проверка типа результата с dependent_variables
        if expression.return_type and context_schema:
            # Проверяем, что типы dependent_variables совместимы с выражением
            pass  # Реализация зависит от схемы контекста
        
        return errors
    
    def _extract_variables(self, expression: str) -> set[str]:
        """Извлекает имена переменных из выражения"""
        import ast
        try:
            tree = ast.parse(expression, mode='eval')
            return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        except:
            return set()
```

**Интеграция в API:**

```python
@router.post("/workflow/save")
async def save_workflow(body: SaveWorkflowRequest):
    # ... existing code ...
    
    # Валидация технических состояний
    validator = TechnicalExpressionValidator()
    context_schema = body.predefined_context or {}
    
    for state in body.states:
        if state.state_type == "technical":
            for expr in state.expressions:
                errors = validator.validate(expr, context_schema)
                if errors:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Validation errors in state '{state.name}': {errors}"
                    )
    
    # ... continue with saving ...
```

### 4. **Улучшить отладку и логирование**

```python
class TechnicalHandler(BaseHandler):
    @check_context_consistency
    def result(self):
        logger.info(
            f"Evaluating technical state: {self.metadata.variable}",
            extra={
                "state_name": self.metadata.variable,
                "dependent_vars": self.metadata.dependent_variables,
                "expression": self.metadata.expression,
                "context_values": {
                    var: self.context.session.get(var)
                    for var in self.metadata.dependent_variables
                }
            }
        )
        
        try:
            result = simple_eval(
                self.metadata.expression,
                names=self.context.session,
                functions=self._get_safe_functions()
            )
            
            logger.info(
                f"Technical state evaluation successful: {self.metadata.variable} = {result}",
                extra={
                    "state_name": self.metadata.variable,
                    "result": result,
                    "result_type": type(result).__name__
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Technical state evaluation failed: {self.metadata.variable}",
                extra={
                    "state_name": self.metadata.variable,
                    "expression": self.metadata.expression,
                    "error": str(e),
                    "context_values": {
                        var: self.context.session.get(var)
                        for var in self.metadata.dependent_variables
                    }
                },
                exc_info=True
            )
            return self.metadata.default_value
```

### 5. **Добавить метаданные**

```json
{
  "variable": "credit_score_high",
  "dependent_variables": ["annual_income", "debt_ratio"],
  "expression": "annual_income > 75000 and debt_ratio < 0.3",
  "return_type": "boolean",
  "default_value": false,
  
  // NEW: Метаданные для админ-панели
  "metadata": {
    "description": "Проверяет, соответствует ли заявитель критериям высокого кредитного рейтинга",
    "category": "credit_check",
    "tags": ["credit", "eligibility", "high_score"],
    "examples": [
      {
        "input": {"annual_income": 80000, "debt_ratio": 0.25},
        "output": true,
        "description": "Высокий доход и низкий долг"
      },
      {
        "input": {"annual_income": 70000, "debt_ratio": 0.25},
        "output": false,
        "description": "Доход ниже порога"
      }
    ],
    "author": "admin",
    "created_at": "2025-10-01T10:00:00Z",
    "version": "1.0"
  }
}
```

**Модель:**

```python
@define(slots=True)
class ExpressionMetadata:
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = field(factory=list)
    examples: list[dict] = field(factory=list)
    author: Optional[str] = None
    created_at: Optional[str] = None
    version: Optional[str] = None

@define(slots=True)
class TechnicalStateExpression(LogicalExpressionMixin, BaseStateExpression):
    variable: str = field(validator=validators.instance_of(str))
    dependent_variables: list[str] = field(validator=validators.instance_of(list))
    expression: str = field(validator=validators.instance_of(str))
    return_type: str = field(default="boolean")
    default_value: Any = field(default=None)
    metadata: Optional[ExpressionMetadata] = field(default=None)  # NEW
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.technical
```

### 6. **Улучшить обработку множественных переходов**

```json
{
  "transitions": [
    {
      "variables": ["credit_score_high", "credit_score_medium"],
      "logic": "none_true",  // NEW: Явная логика для множественных переменных
      "state_id": "RejectedState"
    }
  ]
}
```

**Поддерживаемые логики:**
- `all_true` - все переменные должны быть True
- `any_true` - хотя бы одна переменная True
- `none_true` - все переменные должны быть False
- `all_false` - все переменные должны быть False (синоним `none_true`)
- `exactly_one_true` - ровно одна переменная True

**Модель:**

```python
class TransitionModel(BaseModel):
    case: Optional[str] = None
    state_id: str
    variable: Optional[Union[str, list[str]]] = None
    logic: Optional[str] = "any_true"  # NEW: Для множественных переменных
    
    @model_validator(mode="after")
    def validate_logic(self):
        if isinstance(self.variable, list) and len(self.variable) > 1:
            allowed_logics = ["all_true", "any_true", "none_true", "all_false", "exactly_one_true"]
            if self.logic not in allowed_logics:
                raise ValueError(f"logic must be one of {allowed_logics} for multiple variables")
        return self
```

### 7. **Добавить безопасность выполнения**

```python
import signal
from contextlib import contextmanager

@contextmanager
def time_limit(seconds):
    """Context manager для ограничения времени выполнения"""
    def signal_handler(signum, frame):
        raise TimeoutError("Expression evaluation timed out")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

class TechnicalHandler(BaseHandler):
    EXECUTION_TIMEOUT = 5  # секунд
    MAX_EXPRESSION_LENGTH = 1000  # символов
    
    @check_context_consistency
    def result(self):
        # Проверка длины выражения
        if len(self.metadata.expression) > self.MAX_EXPRESSION_LENGTH:
            logger.error(f"Expression too long: {len(self.metadata.expression)} characters")
            return self.metadata.default_value
        
        try:
            # Выполнение с timeout
            with time_limit(self.EXECUTION_TIMEOUT):
                result = simple_eval(
                    self.metadata.expression,
                    names=self.context.session,
                    functions=self._get_safe_functions()
                )
            
            if not self._validate_result_type(result):
                logger.warning(f"Result type mismatch for {self.metadata.variable}")
                return self.metadata.default_value
            
            return result
            
        except TimeoutError:
            logger.error(f"Expression evaluation timeout for {self.metadata.variable}")
            return self.metadata.default_value
        except Exception as e:
            logger.error(f"Expression evaluation error: {e}", exc_info=True)
            return self.metadata.default_value
```

### 8. **Добавить тестирование выражений через API**

```python
@router.post("/workflow/test-expression")
async def test_expression(
    expression: str,
    context: dict,
    return_type: str = "boolean"
) -> dict:
    """
    Тестирует техническое выражение с заданным контекстом
    
    Полезно для отладки и проверки выражений перед сохранением workflow
    """
    try:
        handler = TechnicalHandler(
            metadata=TechnicalStateExpression(
                variable="test_var",
                dependent_variables=list(context.keys()),
                expression=expression,
                return_type=return_type
            ),
            context=SessionContext(session=context, workflow_id="test")
        )
        
        result = handler.result()
        
        return {
            "success": True,
            "result": result,
            "result_type": type(result).__name__,
            "matches_expected_type": handler._validate_result_type(result)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

## 📝 План реализации

### Этап 1: Базовые улучшения (Высокий приоритет)
1. ✅ Добавить `return_type` и `default_value` в модель
2. ✅ Расширить набор безопасных функций
3. ✅ Добавить валидацию типа результата
4. ✅ Улучшить обработку ошибок и логирование

### Этап 2: Валидация (Средний приоритет)
5. ✅ Реализовать `TechnicalExpressionValidator`
6. ✅ Интегрировать валидацию в API `/workflow/save`
7. ✅ Добавить API для тестирования выражений

### Этап 3: Метаданные и UX (Средний приоритет)
8. ✅ Добавить метаданные (description, tags, examples)
9. ✅ Улучшить обработку множественных переходов с явной логикой
10. ✅ Добавить версионирование выражений

### Этап 4: Безопасность (Высокий приоритет)
11. ✅ Добавить timeout для выполнения
12. ✅ Ограничить длину выражений
13. ✅ Усилить проверки безопасности

### Этап 5: Документация (Низкий приоритет)
14. ✅ Документировать все доступные функции
15. ✅ Создать примеры для админ-панели
16. ✅ Написать руководство по созданию технических состояний

## 📊 Примеры использования улучшенной модели

### Пример 1: Проверка кредитного рейтинга (улучшенная версия)

```json
{
  "state_type": "technical",
  "name": "CreditScoreEvaluation",
  "transitions": [
    {
      "variable": "credit_approved",
      "case": "True",
      "state_id": "ApprovedState"
    },
    {
      "variable": "credit_approved",
      "case": "False",
      "state_id": "RejectedState"
    }
  ],
  "expressions": [
    {
      "variable": "credit_approved",
      "dependent_variables": ["annual_income", "debt_ratio", "credit_history", "employment_years"],
      "expression": "(annual_income > 75000 and debt_ratio < 0.3) or (annual_income > 50000 and debt_ratio < 0.4 and credit_history == 'excellent' and employment_years >= 2)",
      "return_type": "boolean",
      "default_value": false,
      "metadata": {
        "description": "Комплексная оценка кредитоспособности заявителя",
        "category": "credit_evaluation",
        "tags": ["credit", "approval", "risk_assessment"],
        "examples": [
          {
            "input": {
              "annual_income": 80000,
              "debt_ratio": 0.25,
              "credit_history": "good",
              "employment_years": 5
            },
            "output": true,
            "description": "Высокий доход и низкий уровень долга - одобрено"
          },
          {
            "input": {
              "annual_income": 55000,
              "debt_ratio": 0.35,
              "credit_history": "excellent",
              "employment_years": 3
            },
            "output": true,
            "description": "Средний доход, но отличная кредитная история - одобрено"
          },
          {
            "input": {
              "annual_income": 40000,
              "debt_ratio": 0.5,
              "credit_history": "fair",
              "employment_years": 1
            },
            "output": false,
            "description": "Низкий доход и высокий долг - отклонено"
          }
        ],
        "author": "risk_team",
        "created_at": "2025-10-01T12:00:00Z",
        "version": "2.1"
      }
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

### Пример 2: Проверка email с использованием новых функций

```json
{
  "variable": "email_valid",
  "dependent_variables": ["user_email"],
  "expression": "is_not_none(user_email) and contains(user_email, '@') and contains(user_email, '.') and len(strip(user_email)) > 5",
  "return_type": "boolean",
  "default_value": false,
  "metadata": {
    "description": "Базовая валидация email адреса",
    "category": "validation",
    "tags": ["email", "validation", "user_input"]
  }
}
```

### Пример 3: Расчет скидки с использованием математических функций

```json
{
  "variable": "final_price",
  "dependent_variables": ["base_price", "discount_percent", "is_premium_member"],
  "expression": "round(base_price * (1 - discount_percent / 100) * (0.9 if is_premium_member else 1), 2)",
  "return_type": "float",
  "default_value": 0.0,
  "metadata": {
    "description": "Расчет финальной цены с учетом скидки и премиум-статуса",
    "category": "pricing",
    "tags": ["price", "discount", "premium"],
    "examples": [
      {
        "input": {"base_price": 100, "discount_percent": 20, "is_premium_member": true},
        "output": 72.0,
        "description": "100 - 20% скидка - 10% премиум = 72"
      }
    ]
  }
}
```

### Пример 4: Множественные переходы с явной логикой

```json
{
  "state_type": "technical",
  "name": "MultiFactorCheck",
  "transitions": [
    {
      "variables": ["id_verified", "email_verified", "phone_verified"],
      "logic": "all_true",
      "state_id": "FullyVerifiedState"
    },
    {
      "variables": ["id_verified", "email_verified", "phone_verified"],
      "logic": "any_true",
      "state_id": "PartiallyVerifiedState"
    },
    {
      "variables": ["id_verified", "email_verified", "phone_verified"],
      "logic": "none_true",
      "state_id": "NotVerifiedState"
    }
  ],
  "expressions": [
    {
      "variable": "id_verified",
      "dependent_variables": ["id_document"],
      "expression": "is_not_none(id_document) and len(id_document) > 0",
      "return_type": "boolean",
      "default_value": false
    },
    {
      "variable": "email_verified",
      "dependent_variables": ["email_confirmed_at"],
      "expression": "is_not_none(email_confirmed_at)",
      "return_type": "boolean",
      "default_value": false
    },
    {
      "variable": "phone_verified",
      "dependent_variables": ["phone_confirmed_at"],
      "expression": "is_not_none(phone_confirmed_at)",
      "return_type": "boolean",
      "default_value": false
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

## 🎨 Рекомендации для админ-панели

### UI для создания технического состояния

1. **Expression Builder** - визуальный конструктор выражений:
   - Dropdown для выбора переменных из контекста
   - Автодополнение для функций
   - Подсветка синтаксиса
   - Валидация в реальном времени

2. **Тестирование выражений:**
   - Кнопка "Test Expression"
   - Поля для ввода тестовых значений
   - Отображение результата и типа
   - История тестов

3. **Документация встроенная:**
   - Список доступных функций с примерами
   - Подсказки при наведении
   - Примеры из metadata

4. **Валидация:**
   - Проверка синтаксиса при вводе
   - Предупреждения о несуществующих переменных
   - Проверка типов

## 🔗 Связанные файлы для изменения

1. `workflow_builder/expressions.py` - Модели выражений
2. `workflow_builder/handlers.py` - Обработчики состояний
3. `workflow_builder/state_parser/contract.py` - Pydantic модели для API
4. `api/routes.py` - API endpoints
5. `docs/` - Документация

## ✅ Критерии приемки

- [ ] Добавлен `return_type` и `default_value` в модель
- [ ] Расширен набор безопасных функций (минимум +15 функций)
- [ ] Реализована валидация выражений на этапе сохранения
- [ ] Добавлено логирование с контекстом выполнения
- [ ] Реализованы метаданные для админ-панели
- [ ] Улучшена обработка множественных переходов
- [ ] Добавлен timeout и ограничения безопасности
- [ ] Создан API для тестирования выражений
- [ ] Написана документация с примерами
- [ ] Покрыто тестами (unit + integration)
