# 全能旅行管家

多Agent协作的智能旅行规划系统，用4个专职Agent协同完成行程生成、应急重规划与价格监控。

## 项目结构

```
├── main.py              # FastAPI 服务入口，REST + WebSocket 路由
├── orchestrator.py      # 编排器，调度4个Agent的执行顺序与数据流转
├── agents.py            # 4个业务Agent：偏好解析、行程拓扑、实时议价、应急重规划
├── llm_client.py        # DeepSeek API 封装，支持流式输出与token统计
├── models.py            # Pydantic 数据模型定义
├── database.py          # SQLite 行程持久化（CRUD）
├── ws_manager.py        # WebSocket 连接管理
├── travel-butler.html   # 前端单页应用
├── requirements.txt     # Python 依赖
└── .env.example         # 环境变量模板
```

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env     # 填入你的 DEEPSEEK_API_KEY
python main.py
```

浏览器打开 `http://localhost:8000`。

## Agent 架构

| Agent | 职责 |
|-------|------|
| 偏好解析 Agent | 将模糊需求（"带父母、节奏舒缓"）转为结构化约束与偏好权重 |
| 行程拓扑 Agent | 在空间距离、开放时间、体力等约束下生成多日行程 DAG |
| 实时议价 Agent | 监控机票酒店最优价格，生成议价话术 |
| 应急重规划 Agent | 处理突发事件，推演连锁反应，数秒内给出损失最小的调整方案 |

## 技术栈

- **后端**：FastAPI + WebSocket
- **LLM**：DeepSeek API（兼容 OpenAI SDK）
- **前端**：原生 HTML/CSS/JS 单页应用
- **存储**：SQLite
