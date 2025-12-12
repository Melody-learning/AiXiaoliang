# Agent Code Action 机制深度解析

本文档旨在通过最近的实际案例（招商银行基本面查询），详细说明 **AiXiaoliang 2.0 Agent** 当前的运作机制，并解释它是如何避免常见的“幻觉”、“语法错误”和“引用错误”的。

## 1. 核心机制：Brain-Hand-Eye (大脑-手-眼)

我们的架构不同于传统的 JSON-RPC 格式，而是采用了 **Code First**（代码优先）策略。

1.  **大脑 (Brain)**: `CodeAgent` (Gemini 3 Pro) -> 负责思考并编写 Python 代码。
2.  **手 (Hand)**: `LocalPythonExecutor` -> 负责在一个受控的 Python 环境中执行这些代码。
3.  **眼 (Eye)**: `Response Capture` -> 负责捕获代码的打印结果（StdOut）并传回大脑。

---

## 2. 为什么没有幻觉？(No Hallucinations)

在早期的 LLM 应用中，模型经常编造不存在的函数名（如 `get_price_data_v2()`）或参数名（如 `stock_name="平安"`）。我们通过以下手段根除了这个问题：

### 2.1 动态签名注入 (Dynamic Signature Injection)

我们并不是简单地告诉 LLM “你有一个查股票的工具”，而是通过 Python 的 `inspect` 模块，**实时**并将工具的**准确函数签名**注入到 System Prompt 中。

**Prompt 片段示例（真实生成的）：**
```text
- search_stock(keyword: str): Search for a stock code by name. Example: 'Ping An' -> '000001.SZ'. Returns List[Dict].
- get_current_price(stock_code: str): Get the current price (or latest close) of a stock.
- get_fundamentals_data(stock_code: str): Get fundamental data (PE, PB, Market Cap, Revenue, etc.) for a stock. Returns Dict.
```

**效果**：模型看到了 `keyword: str`，就不会再去编造 `stock_name` 参数。在我们修复了 Prompt 注入逻辑后，Agent 立即修正了之前的参数错误。

---

## 3. 为什么没有语法/类型错误？(No Type Errors)

传统的 Agent 经常倒在“工具返回了字符串，Agent 却以为是字典”这类问题上。

### 3.1 强类型契约 (Strict Type Contract)

我们对工具（Tools）的返回值进行了标准化改造：

-   **旧版本**：返回便于人类阅读的 String（导致 `AttributeError: 'str' object has no attribute 'get'`）。
-   **新版本**：返回 **List** 或 **Dict** 等标准 Python 数据结构。

**案例追踪：招商银行查询**

1.  **Search 阶段**：
    -   Agent 调用：`search_stock(keyword='招商银行')`
    -   工具返回：`[{'code': '600036.SH', 'name': '招商银行', 'industry': '银行'}]` (List of Dicts)
    -   Agent 处理：`stock_code = search_results[0]['code']` -> **完美匹配 List 结构**。

2.  **Analyis 阶段**：
    -   Agent 调用：`get_fundamentals_data(stock_code='600036.SH')`
    -   工具返回：`{'pe_ratio': 7.0871, 'revenue': 251420000000.0, ...}` (Dict)
    -   Agent 处理：`pe = fundamentals.get('pe_ratio')` -> **完美匹配 Dict 结构**。

---

## 4. 完整执行流回顾 (Trace)

以下是 Tushare 迁移验证中，一次真实成功的“复杂查询”全过程：

**用户**：“帮我查一下招商银行，然后告诉我它的市盈率、市净率和营业收入”

**Step 1: 思考 (Brain)**
> "我需要先查代码，再用代码查基本面数据。我知道 `search_stock` 返回列表，`get_fundamentals_data` 返回字典。"

**Step 2: 编码 (Coding)**
```python
# 1. 搜索代码
search_results = search_stock(keyword='招商银行')
if search_results:
    code = search_results[0]['code']  # 正确索引
    name = search_results[0]['name']
    
    # 2. 获取数据
    fund = get_fundamentals_data(stock_code=code)
    
    # 3. 打印结果
    print(f"{name} PE: {fund.get('pe_ratio')}") # 正确取值
```

**Step 3: 执行 (Hand)**
-   Python 解释器加载 Pandas/Tushare 环境。
-   执行代码 -> 成功打印结果。

**结论**：
当前的稳定性并非偶然，而是源于 **Prompt 精确工程**（解决参数幻觉）与 **工具接口标准化**（解决类型错误）的双重保障。
