import json
from llm_client import LLMClient


class PreferenceParsingAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def parse(self, departure: str, destination: str, days: int, group: str, pace: str, interest: str, budget: str) -> dict:
        system_prompt = """你是旅行偏好解析专家。将用户的旅行需求解析为结构化JSON。

返回格式（严格遵守）:
{
  "budget_level": "low/medium/high",
  "pace": "relaxed/normal/intensive",
  "interests": ["culture", "food", "nature", "shopping", "nightlife"],
  "special_requirements": "特殊要求描述",
  "constraints": ["日出游时间≤6小时", "午休≥1小时", "单日步行≤8公里"],
  "preference_weights": {"人文景点": 0.85, "餐饮品质": 0.72, "购物": 0.35, "自然风光": 0.60}
}

只返回JSON，不要其他文字。"""

        user_prompt = (
            f"出发地: {departure or '未指定'}\n"
            f"目的地: {destination}\n"
            f"天数: {days}天\n"
            f"出行人群: {group}\n"
            f"节奏偏好: {pace}\n"
            f"兴趣偏好: {interest}\n"
            f"预算等级: {budget}"
        )
        return await self.llm.chat_json(system_prompt, user_prompt, model=self.llm.model_pro)


class ItineraryTopologyAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def generate(self, preferences: dict, departure: str, destination: str, start_date: str, days: int, on_chunk=None) -> dict:
        departure_rule = ""
        if departure:
            departure_rule = f"\n8. 用户从{departure}出发，第一天第一个节点必须是从{departure}到{destination}的交通节点（航班/高铁/自驾等），name字段格式为\"{departure}→{destination}\""

        system_prompt = f"""你是行程规划专家。根据用户偏好生成{days}天{destination}旅行计划。

要求:
1. 每天4-6个节点，包含交通、住宿、景点、餐饮
2. 节点之间有依赖关系(deps字段)，形成有向无环图
3. 时间要合理，考虑交通时间，不要冲突
4. 节点type字段必须用emoji前缀，格式如: "✈️ 航班到达"、"🏨 办理入住"、"🏛️ 世界遗产"、"🍽️ 晚餐"、"🚶 轻松漫步"、"🚗 包车"、"🌿 自然风光"、"🛍️ 购物"
5. id字段用n1, n2, n3...递增
6. date字段格式如"5月15日 周六"
7. title字段简洁描述当天主题{departure_rule}

返回JSON格式（严格遵守）:
{{
  "days": [
    {{
      "id": 1,
      "date": "5月15日 周六",
      "title": "抵达·初探",
      "nodes": [
        {{"id": "n1", "time": "14:00", "name": "地点名", "type": "✈️ 航班到达", "deps": []}},
        {{"id": "n2", "time": "15:30", "name": "酒店名", "type": "🏨 办理入住", "deps": ["n1"]}}
      ]
    }}
  ]
}}

只返回JSON，不要其他文字。"""

        user_prompt = (
            f"出发地: {departure or '未指定'}\n"
            f"目的地: {destination}\n"
            f"出发日期: {start_date}\n"
            f"天数: {days}\n"
            f"偏好: {json.dumps(preferences, ensure_ascii=False)}"
        )
        return await self.llm.chat_json_stream(system_prompt, user_prompt, on_chunk)


class RealTimeNegotiationAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def get_prices(self, destination: str, itinerary: dict) -> list:
        system_prompt = """你是旅行价格分析师。根据行程生成价格监控数据。

返回JSON数组，每个元素格式:
{"title": "机票 北京→上海", "price": "¥1,280", "trend": "down", "change": "-¥120 (2h前)"}

规则:
- trend只能是"up"或"down"
- 生成4-5个价格项，覆盖机票、酒店、景点门票、交通
- 价格要合理、真实
- change字段描述价格变动

只返回JSON数组，不要其他文字。"""

        plan_summary = json.dumps(itinerary, ensure_ascii=False)[:500]
        user_prompt = f"目的地: {destination}\n行程摘要: {plan_summary}"
        return await self.llm.chat_json(system_prompt, user_prompt)

    async def generate_script(self, context: str, on_chunk=None) -> str:
        system_prompt = "你是酒店/餐厅议价专家。根据上下文生成一段简洁、有礼貌的谈判话术，帮助旅客争取更好的服务或减免。只返回话术内容，不超过100字。"
        return await self.llm.chat_stream(system_prompt, context, on_chunk)


class EmergencyReplanningAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def analyze(self, scenario: str, current_plan: dict, custom_desc: str = "") -> dict:
        scenario_descs = {
            "flight": "航班延误3小时，到达时间推迟3小时",
            "weather": "极端天气预警，户外景点关闭，需改为室内方案",
            "closed": "景点临时闭馆维修，需要找替代景点",
            "lost": "证件丢失，酒店入住受阻，需要应急处理",
        }
        desc = custom_desc if custom_desc else scenario_descs.get(scenario, "未知突发事件")

        system_prompt = f"""你是应急重规划专家。当前发生了突发事件: {desc}

你需要:
1. 分析当前行程DAG中哪些节点受影响
2. 通过依赖关系追踪连锁影响
3. 提出修复方案
4. 生成修改后的完整行程

返回JSON格式（严格遵守）:
{{
  "log_entries": [
    {{"agent": "应急重规划Agent", "msg": "接收事件: ...", "type": "warn"}},
    {{"agent": "应急重规划Agent", "msg": "BFS遍历: ...", "type": "info"}},
    {{"agent": "应急重规划Agent", "msg": "冲突: ...", "type": "warn"}},
    {{"agent": "议价Agent", "msg": "生成话术: ...", "type": "info"}},
    {{"agent": "应急重规划Agent", "msg": "✓ 最终方案: ...", "type": "ok"}}
  ],
  "new_plan": {{
    "days": [与原始plan格式相同的完整行程]
  }},
  "conflicts": [
    {{"dayId": 1, "nodeId": "n1", "resolved": true}}
  ]
}}

规则:
- log_entries要有8-15条，体现完整的推理过程
- type只能是"warn"、"info"或"ok"
- new_plan必须是完整的行程，不能省略天数
- conflicts列出所有受影响的节点
- 只返回JSON，不要其他文字"""

        user_prompt = f"当前行程:\n{json.dumps(current_plan, ensure_ascii=False)}"
        return await self.llm.chat_json(system_prompt, user_prompt, model=self.llm.model_pro)
