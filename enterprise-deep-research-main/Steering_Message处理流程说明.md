# Steering Message 处理流程说明

## 📋 概述

Steering message 是用户在研究过程中发送的引导消息，用于实时调整研究方向。消息采用**队列机制**，类似于 Cursor 的 todo.md 系统。

---

## 🔄 完整处理流程

### 1. 消息发送阶段

**位置**: `routers/simple_steering_api.py:74`

```python
@router.post("/message")
async def send_steering_message(request: SteeringMessage):
    # 消息被添加到 steering_todo.pending_messages 队列
    await state.steering_todo.add_user_message(request.message)
    
    # 返回：消息已排队，但尚未处理
    return SteeringResponse(
        success=True,
        message=f"Steering message queued for processing (queue size: {len(state.steering_todo.pending_messages)})",
        todo_updated=False,  # ⚠️ 注意：此时 todo 尚未更新
    )
```

**状态**: 消息进入 `pending_messages` 队列，状态为 **"queued"**

---

### 2. 消息加载阶段

**位置**: `src/graph.py:284` - `async_multi_agents_network` 节点

**时机**: **每个研究循环开始时**

```python
async def async_multi_agents_network(state: SummaryState, callbacks=None):
    # 在每个研究循环开始时
    if hasattr(state, "steering_todo") and state.steering_todo:
        # 调用 prepare_steering_for_next_loop
        steering_result = await state.prepare_steering_for_next_loop()
```

**位置**: `src/state.py:323` - `prepare_steering_for_next_loop()`

```python
async def prepare_steering_for_next_loop(self):
    """
    SIMPLIFIED: Only fetch messages from API session store.
    The actual todo updates happen in reflect_on_report() via LLM.
    
    This function just queues messages for the reflection phase.
    """
    # 1. 从 session store 获取新消息
    await self._fetch_pending_messages_from_session_store()
    
    # 2. 消息被添加到 steering_todo.pending_messages
    # 3. 但此时消息尚未被处理，只是排队等待
```

**关键点**:
- ✅ 消息从 session store 加载到 `steering_todo.pending_messages`
- ⚠️ **消息尚未被处理**，只是排队等待
- ⚠️ Todo 列表**尚未更新**

---

### 3. 消息处理阶段

**位置**: `src/graph.py:1220` - `reflect_on_report` 节点

**时机**: **每个研究循环的反思阶段**

```python
async def reflect_on_report(state: SummaryState, config: RunnableConfig):
    # 1. 快照消息队列（防止在处理过程中有新消息到达）
    messages_snapshot = list(state.steering_todo.pending_messages)
    
    # 2. 格式化消息供 LLM 处理
    if messages_snapshot:
        steering_messages = "\n".join(
            [f'[{i}] "{msg}"' for i, msg in enumerate(messages_snapshot)]
        )
        # 例如：[0] "Focus on recent work"
        #      [1] "Exclude entertainment stuff"
    
    # 3. 将消息传递给 LLM（通过 reflection_instructions prompt）
    formatted_prompt = reflection_instructions.format(
        steering_messages=steering_messages,
        # ...
    )
    
    # 4. LLM 处理消息并返回：
    #    - mark_completed: 标记完成的任务
    #    - add_tasks: 添加新任务（基于 steering messages）
    #    - clear_messages: 指定哪些消息已被完全处理
```

---

### 4. 消息清除阶段

**位置**: `src/graph.py:1625` - `reflect_on_report` 节点

**关键逻辑**: **只有 LLM 明确指定要清除的消息才会被清除**

```python
# SMART MESSAGE CLEARING: Only clear messages LLM says are fully addressed
clear_message_indices = todo_updates.get("clear_messages", [])

if clear_message_indices:
    # 只清除 LLM 明确指定的消息索引
    remaining_snapshot_messages = [
        msg
        for i, msg in enumerate(messages_snapshot)
        if i not in clear_message_indices  # 只移除指定的索引
    ]
    
    # 更新队列
    state.steering_todo.pending_messages = (
        remaining_snapshot_messages + new_messages_during_reflection
    )
else:
    # ⚠️ 如果 LLM 返回空列表 []，消息不会被清除
    logger.info(
        "[reflect_on_report] No messages cleared (LLM didn't specify any in clear_messages)"
    )
```

---

## ⚠️ 为什么消息一直处于 Queue 状态？

### 原因分析

消息一直处于 queue 状态，通常是因为：

#### 1. **LLM 没有返回 `clear_messages` 字段**

**Prompt 要求** (`src/prompts.py:859-864`):
```
4. CLEAR MESSAGES: Which steering messages are FULLY ADDRESSED?
   - Return indices (e.g., [0, 1]) of messages that are now fully covered by tasks
   - Only clear a message if ALL its aspects have corresponding tasks (new or existing)
   - If uncertain whether a message is fully addressed, don't clear it yet
   - Return empty list [] if no messages to clear
```

**问题**: 如果 LLM 返回 `clear_messages: []`（空列表），消息不会被清除。

#### 2. **LLM 认为消息尚未被完全处理**

根据 prompt 的要求，消息只有在**所有方面都有对应任务**时才会被清除：

```python
# 只有当消息的所有方面都有对应任务时，才会被清除
# 如果 LLM 不确定，就不会清除消息
```

#### 3. **消息处理时机问题**

- 消息在 `reflect_on_report` 节点处理
- 如果研究循环还没到达反思阶段，消息会一直排队
- 如果研究已经完成（`research_complete=True`），可能不会进入反思阶段

---

## 🔍 消息处理的关键时机

### 消息加载时机

```
用户发送消息
    ↓
消息进入 pending_messages 队列（queued 状态）
    ↓
下一个研究循环开始
    ↓
multi_agents_network 节点
    ↓
prepare_steering_for_next_loop()
    ↓
_fetch_pending_messages_from_session_store()
    ↓
消息从 session store 加载到 steering_todo.pending_messages
    ↓
消息仍然处于 queued 状态（等待处理）
```

### 消息处理时机

```
研究循环执行完成
    ↓
generate_report 节点生成报告
    ↓
reflect_on_report 节点（关键处理点）
    ↓
LLM 分析消息并创建任务
    ↓
LLM 返回 clear_messages 字段
    ↓
根据 clear_messages 清除已处理的消息
    ↓
消息状态更新（如果被清除）
```

---

## 🛠️ 调试建议

### 1. 检查消息是否被加载

查看日志中的以下信息：
```
[STEERING] Found {N} pending messages in session {session_id}
[STEERING] Fetched message for processing: {message_content}
[STEERING] Queued {N} messages for reflection phase
```

### 2. 检查消息是否被处理

查看 `reflect_on_report` 节点的日志：
```
[reflect_on_report] Snapshotted {N} steering messages for LLM processing
[reflect_on_report] Steering messages: {N}
```

### 3. 检查 LLM 的 clear_messages 响应

查看反思结果的日志：
```
[reflect_on_report] Cleared {N}/{total} steering messages: indices {indices}
或
[reflect_on_report] No messages cleared (LLM didn't specify any in clear_messages)
```

### 4. 检查研究循环状态

确认研究是否还在进行中：
- 如果 `research_complete=True` 且研究已结束，消息可能不会被处理
- 如果研究循环数已达到最大值，可能不会进入新的反思阶段

---

## 📊 消息状态流转图

```
用户发送消息
    ↓
[QUEUED] pending_messages.append(message)
    ↓
下一个研究循环开始
    ↓
[LOADED] _fetch_pending_messages_from_session_store()
    ↓
消息仍在 pending_messages（状态：QUEUED）
    ↓
reflect_on_report 节点
    ↓
[PROCESSING] LLM 分析消息并创建任务
    ↓
LLM 返回 clear_messages
    ↓
    ├─→ clear_messages = [0, 1] → [CLEARED] 消息被清除
    │
    └─→ clear_messages = [] → [QUEUED] 消息继续排队
```

---

## 🔧 常见问题排查

### Q1: 消息发送后一直显示 "queued" 状态

**可能原因**:
1. 研究循环还没到达 `reflect_on_report` 节点
2. LLM 返回了 `clear_messages: []`（认为消息尚未完全处理）
3. 研究已经完成，不会再进入反思阶段

**解决方法**:
- 等待下一个研究循环完成
- 检查日志中是否有 `[reflect_on_report]` 相关的输出
- 确认研究是否还在进行中

### Q2: 消息被处理但没有被清除

**可能原因**:
- LLM 创建了任务，但认为消息的所有方面还没有完全覆盖
- LLM 返回了 `clear_messages: []`

**解决方法**:
- 等待任务完成后，LLM 可能会在下一轮清除消息
- 检查创建的任务是否完全覆盖了消息的所有方面

### Q3: 消息没有被加载

**可能原因**:
- Session ID 不匹配
- `steering_enabled=False`
- `steering_todo` 未初始化

**解决方法**:
- 检查 session store 中是否有消息
- 确认 steering 是否启用
- 查看日志中的错误信息

---

## 📝 关键代码位置

### 消息发送
- **文件**: `routers/simple_steering_api.py:74`
- **函数**: `send_steering_message()`
- **操作**: `await state.steering_todo.add_user_message(request.message)`

### 消息加载
- **文件**: `src/state.py:323`
- **函数**: `prepare_steering_for_next_loop()`
- **调用**: `await self._fetch_pending_messages_from_session_store()`
- **时机**: 每个研究循环开始时（`multi_agents_network` 节点）

### 消息处理
- **文件**: `src/graph.py:1220`
- **函数**: `reflect_on_report()`
- **时机**: 每个研究循环的反思阶段

### 消息清除
- **文件**: `src/graph.py:1625`
- **逻辑**: 根据 LLM 返回的 `clear_messages` 字段清除消息
- **条件**: 只有 LLM 明确指定的消息索引才会被清除

---

## 🎯 总结

1. **消息加载时机**: 每个研究循环开始时（`multi_agents_network` 节点）
2. **消息处理时机**: 每个研究循环的反思阶段（`reflect_on_report` 节点）
3. **消息清除条件**: LLM 必须在 `clear_messages` 字段中明确指定要清除的消息索引
4. **Queue 状态原因**: 
   - 消息已加载但尚未处理
   - 或 LLM 认为消息尚未完全处理（返回 `clear_messages: []`）

**关键点**: 消息采用**延迟处理**机制，只有在 `reflect_on_report` 节点才会被 LLM 处理并转换为任务。如果消息一直处于 queue 状态，说明要么还没到达反思阶段，要么 LLM 认为消息的所有方面还没有完全覆盖。




