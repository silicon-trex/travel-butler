import copy
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# ------------------- 基础数据结构 -------------------
class EventType(Enum):
    FLIGHT = 1
    HOTEL_CHECKIN = 2
    TRAIN = 3
    RESTAURANT = 4
    MUSEUM = 5
    FREE_TIME = 6

@dataclass
class TimeWindow:
    start: datetime
    end: datetime

@dataclass
class TripEvent:
    id: str
    type: EventType
    time_window: TimeWindow
    location: str
    is_flexible: bool = False          # 是否可以调整时间或取消
    prerequisite_events: List[str] = field(default_factory=list)  # 前置事件ID列表
    dependent_events: List[str] = field(default_factory=list)     # 依赖此事件的事件ID列表
    reservation_id: Optional[str] = None
    notes: str = ""

@dataclass
class UserPreferences:
    budget_level: str          # "low", "medium", "high"
    pace: str                  # "relaxed", "normal", "intensive"
    interests: List[str]       # 如 ["culture", "food", "nature"]
    special_requirements: str = ""

# ------------------- 1. 偏好解析Agent -------------------
class PreferenceParsingAgent:
    def parse(self, user_description: str) -> UserPreferences:
        # 简化版：基于关键词模拟解析
        prefs = UserPreferences(
            budget_level="medium",
            pace="relaxed",
            interests=["culture", "food"],
            special_requirements=""
        )
        if "父母" in user_description or "老人" in user_description:
            prefs.pace = "relaxed"
        if "历史" in user_description:
            prefs.interests.append("history")
        if "穷游" in user_description:
            prefs.budget_level = "low"
        return prefs

# ------------------- 2. 行程拓扑生成Agent -------------------
class ItineraryTopologyAgent:
    def generate(self, prefs: UserPreferences, start_date: datetime, end_date: datetime) -> List[TripEvent]:
        """
        根据偏好生成一个包含飞机、酒店、火车、餐厅、景点的有向无环图事件列表。
        实际中这会是一个复杂的约束求解过程，这里用固定示例模拟。
        """
        # 模拟一个简单的3天行程
        events = [
            TripEvent("flight1", EventType.FLIGHT,
                      TimeWindow(start_date.replace(hour=8), start_date.replace(hour=11)),
                      "北京-上海", is_flexible=False),
            TripEvent("hotel1_checkin", EventType.HOTEL_CHECKIN,
                      TimeWindow(start_date.replace(hour=12), start_date.replace(hour=14)),
                      "上海酒店A", is_flexible=False,
                      prerequisite_events=["flight1"]),
            TripEvent("museum1", EventType.MUSEUM,
                      TimeWindow(start_date.replace(hour=14, minute=30), start_date.replace(hour=17)),
                      "上海博物馆", is_flexible=True,
                      prerequisite_events=["hotel1_checkin"]),
            TripEvent("restaurant1", EventType.RESTAURANT,
                      TimeWindow(start_date.replace(hour=18), start_date.replace(hour=20)),
                      "外滩某餐厅", is_flexible=True,
                      prerequisite_events=["museum1"]),
            # 第二天
            TripEvent("train1", EventType.TRAIN,
                      TimeWindow(start_date.replace(hour=9) + timedelta(days=1),
                                 start_date.replace(hour=10, minute=30) + timedelta(days=1)),
                      "上海-苏州", is_flexible=False,
                      prerequisite_events=["restaurant1"]),
            TripEvent("garden1", EventType.MUSEUM,
                      TimeWindow(start_date.replace(hour=11) + timedelta(days=1),
                                 start_date.replace(hour=16) + timedelta(days=1)),
                      "拙政园", is_flexible=True,
                      prerequisite_events=["train1"]),
        ]
        # 构建依赖关系
        self._build_dependencies(events)
        return events

    def _build_dependencies(self, events: List[TripEvent]):
        """根据prerequisite_events更新dependent_events字段，形成拓扑图"""
        for evt in events:
            for pre_id in evt.prerequisite_events:
                pre_evt = next(e for e in events if e.id == pre_id)
                pre_evt.dependent_events.append(evt.id)

# ------------------- 3. 实时保障与议价Agent -------------------
class RealTimeNegotiationAgent:
    def generate_negotiation_script(self, event_type: EventType, target: str) -> str:
        """模拟生成议价话术（实际会调用LLM），这里返回固定模板"""
        if event_type == EventType.HOTEL_CHECKIN:
            return f"您好，我们因为航班延迟可能晚到，能否保留房间并尽可能升级？"
        elif event_type == EventType.RESTAURANT:
            return f"您好，由于行程变动，我们可能无法按时到达，能否免除迟到取消的定金？"
        else:
            return f"请求灵活处理相关预订。"

# ------------------- 4. 应急重规划Agent（核心） -------------------
class EmergencyReplanningAgent:
    def __init__(self):
        self.negotiation_agent = RealTimeNegotiationAgent()

    def handle_disruption(self, disrupted_event_id: str, delay_minutes: int,
                          original_events: List[TripEvent]) -> List[TripEvent]:
        """
        核心长链推理：处理某个事件延迟，推演所有受影响的下游事件，并尝试修复。
        返回修正后的新事件列表。
        """
        # 深拷贝原始事件，避免修改原数据
        new_events = copy.deepcopy(original_events)
        # 获取事件对象
        disrupted_event = next(e for e in new_events if e.id == disrupted_event_id)
        # 模拟延迟：将事件时间窗口后移
        disrupted_event.time_window.start += timedelta(minutes=delay_minutes)
        disrupted_event.time_window.end += timedelta(minutes=delay_minutes)

        print(f"[应急Agent] 检测到事件 {disrupted_event_id} 延迟 {delay_minutes} 分钟，开始全局影响推演...")
        # 广度优先遍历所有受牵连的后置事件
        affected_queue = [disrupted_event_id]
        processed = set()
        conflict_log = []

        while affected_queue:
            current_id = affected_queue.pop(0)
            if current_id in processed:
                continue
            processed.add(current_id)
            current_evt = next(e for e in new_events if e.id == current_id)
            # 检查该事件与其直接依赖项之间是否有时间窗口冲突
            for dep_id in current_evt.dependent_events:
                dep_evt = next(e for e in new_events if e.id == dep_id)
                # 简单规则：如果依赖事件开始时间晚于当前事件结束时间，则无冲突；否则有冲突
                if dep_evt.time_window.start < current_evt.time_window.end:
                    conflict_desc = f"冲突：{current_evt.id} 结束于 {current_evt.time_window.end}，但 {dep_evt.id} 开始于 {dep_evt.time_window.start}"
                    conflict_log.append(conflict_desc)
                    print(f"  [冲突] {conflict_desc}")
                    # 尝试修复冲突：如果依赖事件是可调整的，顺延它
                    if dep_evt.is_flexible:
                        shift = current_evt.time_window.end - dep_evt.time_window.start
                        dep_evt.time_window.start += shift
                        dep_evt.time_window.end += shift
                        print(f"  [修复] 灵活事件 {dep_evt.id} 已顺延 {shift}")
                        # 将修复后的事件加入队列，因为顺延可能影响它的后续事件
                        if dep_id not in processed:
                            affected_queue.append(dep_id)
                    else:
                        # 不可灵活调整，尝试取消并生成谈判话术
                        print(f"  [严重] 非灵活事件 {dep_evt.id} 受影响，尝试谈判或取消。")
                        script = self.negotiation_agent.generate_negotiation_script(dep_evt.type, dep_evt.location)
                        dep_evt.notes = f"需要执行谈判：{script}"
                        # 取消该事件（标记为灵活并置为极晚时间，或从计划中移除方案）
                        # 此处简单处理：将其时间窗设置为一天后，表示已取消原有安排
                        dep_evt.time_window.start += timedelta(days=1)
                        dep_evt.time_window.end += timedelta(days=1)
                    # 不管是否修复，都要检查此依赖事件的后置事件
                    if dep_id not in processed:
                        affected_queue.append(dep_id)

        print(f"[应急Agent] 推演完成，共检测到 {len(conflict_log)} 个冲突。")
        return new_events

# ------------------- 5. 主协调器 -------------------
class TravelPlannerSystem:
    def __init__(self):
        self.preference_agent = PreferenceParsingAgent()
        self.topology_agent = ItineraryTopologyAgent()
        self.emergency_agent = EmergencyReplanningAgent()

    def plan(self, user_desc: str, start_date: datetime, end_date: datetime):
        prefs = self.preference_agent.parse(user_desc)
        print(f"偏好解析结果: {prefs}")
        itinerary = self.topology_agent.generate(prefs, start_date, end_date)
        print("原始行程已生成：")
        for e in itinerary:
            print(f"  {e.id} [{e.type.name}] {e.time_window.start} - {e.time_window.end} at {e.location}")
        return itinerary

    def inject_disruption(self, itinerary: List[TripEvent], event_id: str, delay_min: int):
        print(f"\n===== 注入突发事件：{event_id} 延误 {delay_min} 分钟 =====")
        new_plan = self.emergency_agent.handle_disruption(event_id, delay_min, itinerary)
        print("\n调整后的行程：")
        for e in new_plan:
            print(f"  {e.id} [{e.type.name}] {e.time_window.start} - {e.time_window.end} at {e.location}, 备注: {e.notes}")
        return new_plan

# ------------------- 演示运行 -------------------
if __name__ == "__main__":
    system = TravelPlannerSystem()
    start = datetime(2026, 5, 15)
    end = datetime(2026, 5, 17)
    # 用户输入模糊需求
    user_input = "带父母去上海苏州，喜欢人文，节奏舒缓"
    events = system.plan(user_input, start, end)

    # 模拟航班延误2小时（120分钟）
    system.inject_disruption(events, "flight1", 120)