"""
桃源温泉乡 - 完整修复版
修复了：读档报错 / 收入负数 / 天气季节混乱 / 季节事件 / 围炉温酒 / 成就系统
可直接运行，适合AI或人类游玩。
开源协议: MIT License
"""

import random
import json
import time
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

# ============ 配置 ============
GAME_NAME = "桃源温泉乡"
SAVE_FILE = "hotspring_save.json"

# ============ 客层（17种） ============
GUEST_TYPES = {
    "村民": {"weight": 50, "cash": 50, "difficulty": 1, "unlock_threshold": 20, "special": None},
    "上班族": {"weight": 40, "cash": 80, "difficulty": 2, "unlock_threshold": 40, "special": None},
    "学生": {"weight": 35, "cash": 30, "difficulty": 1, "unlock_threshold": 30, "special": None},
    "情侣": {"weight": 30, "cash": 120, "difficulty": 3, "unlock_threshold": 50, "special": None},
    "家庭游客": {"weight": 25, "cash": 150, "difficulty": 3, "unlock_threshold": 55, "special": None},
    "退休老人": {"weight": 20, "cash": 100, "difficulty": 2, "unlock_threshold": 45, "special": None},
    "富裕夫妇": {"weight": 15, "cash": 300, "difficulty": 4, "unlock_threshold": 70, "special": None},
    "网红博主": {"weight": 10, "cash": 200, "difficulty": 4, "unlock_threshold": 60, "special": None},
    "温泉达人": {"weight": 8, "cash": 250, "difficulty": 5, "unlock_threshold": 80, "special": None},
    "神秘顾客": {"weight": 5, "cash": 500, "difficulty": 5, "unlock_threshold": 90, "special": None},
    "埃隆·马斯克": {"weight": 3, "cash": 999, "difficulty": 8, "unlock_threshold": 100, "special": "elon"},
    "马克·扎克伯格": {"weight": 3, "cash": 888, "difficulty": 7, "unlock_threshold": 95, "special": "zuck"},
    "杰夫·贝索斯": {"weight": 2, "cash": 999, "difficulty": 7, "unlock_threshold": 105, "special": "bezos"},
    "黄仁勋": {"weight": 2, "cash": 777, "difficulty": 9, "unlock_threshold": 110, "special": "jensen"},
    "比尔·盖茨": {"weight": 2, "cash": 888, "difficulty": 6, "unlock_threshold": 90, "special": "gates"},
    "Sam Altman": {"weight": 2, "cash": 999, "difficulty": 8, "unlock_threshold": 105, "special": "sam"},
    "Dario Amodei": {"weight": 2, "cash": 999, "difficulty": 9, "unlock_threshold": 115, "special": "dario"},
}

# ============ 设施 & 商店 ============
FACILITY_TYPES = {
    "露天温泉": {"cost": 100, "income": 15, "satisfy_bonus": 5},
    "室内温泉": {"cost": 80, "income": 10, "satisfy_bonus": 3},
    "按摩房": {"cost": 120, "income": 20, "satisfy_bonus": 8},
    "小卖部": {"cost": 50, "income": 8, "satisfy_bonus": 2},
    "餐厅": {"cost": 150, "income": 25, "satisfy_bonus": 6},
    "休息厅": {"cost": 60, "income": 5, "satisfy_bonus": 4},
    "游戏厅": {"cost": 90, "income": 12, "satisfy_bonus": 3},
    "纪念品店": {"cost": 70, "income": 10, "satisfy_bonus": 2},
}

SHOP_ITEMS = {
    "杀虫剂": {"price": 40, "effect": "clean_roach", "desc": "清除所有蟑螂"},
    "公关稿": {"price": 60, "effect": "reputation_boost", "value": 15, "desc": "声誉+15"},
    "消毒剂": {"price": 50, "effect": "clean_water", "desc": "净化水质"},
}

# ============ 完整事件池 ============
RANDOM_EVENTS = [
    # ----- 基础现实（6） -----
    {"name": "温泉节", "effect": "popularity_boost", "value": 10, "desc": "🎉 温泉节！人气+10"},
    {"name": "暴雨", "effect": "cash_penalty", "value": -15, "desc": "🌧️ 暴雨，收入-15"},
    {"name": "好评如潮", "effect": "cash_bonus", "value": 40, "desc": "⭐ 网络好评！+40金币"},
    {"name": "员工罢工", "effect": "satisfy_penalty", "value": -3, "desc": "✊ 罢工，满意度-3"},
    {"name": "游客增多", "effect": "guest_boost", "value": 2, "desc": "🚶 额外来2人"},
    {"name": "设施老化", "effect": "income_penalty", "value": 8, "desc": "🔧 老化，收入-8"},
    # ----- 奇葩生活（10） -----
    {"name": "熊孩子尿尿", "effect": "pee_in_hotspring", "desc": "💩 熊孩子在小便！温泉停业2回合"},
    {"name": "吃霸王餐", "effect": "bill_dodging", "desc": "🏃 逃单！损失30-60金币"},
    {"name": "消防检查", "effect": "fire_inspection", "desc": "🚒 消防突击检查！罚款或停业"},
    {"name": "蟑螂出没", "effect": "roach_infest", "desc": "🪳 餐厅发现蟑螂！"},
    {"name": "染发剂掉色", "effect": "hair_dye_leak", "desc": "🎨 温泉被染成彩色！停业换水"},
    {"name": "厕所没冲", "effect": "toilet_clog", "desc": "💩 厕所堵塞！停业1回合"},
    {"name": "水质浑浊", "effect": "water_dirty", "desc": "🌊 水质报警！需消毒剂"},
    {"name": "沐浴露被偷", "effect": "supply_stolen", "desc": "🧴 被偷损失30-80金币"},
    {"name": "过敏投诉", "effect": "allergy_lawsuit", "desc": "💊 赔偿80-180金币！"},
    {"name": "遗失钱包", "effect": "lost_wallet", "desc": "👛 捡到钱包！可选归还或私吞"},
    # ----- 积极事件（8） -----
    {"name": "忠诚会员日", "effect": "loyalty_bonus", "desc": "👥 老客带新！额外来1-2人"},
    {"name": "水质金奖", "effect": "quality_award", "desc": "🏅 水质金奖！满意度+10，声誉+10"},
    {"name": "员工创意", "effect": "employee_idea", "desc": "💡 员工提建议！+30金币，设施收入+10%"},
    {"name": "本地报道", "effect": "local_news", "desc": "📰 本地报道！人气+15"},
    {"name": "天使投资", "effect": "angel_investor", "desc": "💸 神秘投资人！+100金币（声誉>70）"},
    {"name": "温泉蛋丰收", "effect": "egg_harvest", "desc": "🥚 温泉蛋大丰收！+40金币"},
    {"name": "旅游博客", "effect": "travel_blog", "desc": "✍️ 博客推荐！人气+8，设施满意度+2"},
    {"name": "公益抵税", "effect": "tax_deduction", "desc": "🧾 捐赠抵税！+50金币，声誉+3"},
    # ----- 新增常规：天气/季节（6） -----
    {"name": "雷暴", "effect": "thunderstorm", "desc": "⛈️ 雷暴！户外设施停业1回合，水电费减免+20"},
    {"name": "热浪", "effect": "heatwave", "desc": "☀️ 热浪！室内设施爆满，临时收入上升，客人满意度小降"},
    {"name": "寒流", "effect": "cold_snap", "desc": "❄️ 寒流！露天温泉需求激增，临时收入上升，取暖费增加"},
    {"name": "樱花季", "effect": "sakura", "desc": "🌸 樱花季！游客+50%，满意度+5"},
    {"name": "红叶季", "effect": "autumn_leaves", "desc": "🍁 红叶季！老年游客增加，消费+20%"},
    {"name": "梅雨结束", "effect": "rain_end", "desc": "☀️ 梅雨结束！人气+10，收入+15%"},
    # ----- 新增常规：顾客行为（8） -----
    {"name": "顾客投诉", "effect": "customer_complaint", "desc": "🗣️ 投诉水温！满意度-5，整改后声誉+3"},
    {"name": "顾客表扬", "effect": "customer_praise", "desc": "👍 表扬服务！声誉+5，收入+10"},
    {"name": "求婚成功", "effect": "proposal", "desc": "💍 求婚成功！全场满意度+10，人气+15"},
    {"name": "生日派对", "effect": "birthday_party", "desc": "🎂 包场庆生！收入+80，其他客人满意度-5"},
    {"name": "家庭日", "effect": "family_day", "desc": "👪 家庭日！收入+20%，满意度+5"},
    {"name": "公司团建", "effect": "company_outing", "desc": "🏢 公司包场！收入+150，清洁费-30"},
    {"name": "网红打卡", "effect": "influencer_checkin", "desc": "📸 网红打卡！人气+10，但免单损失20"},
    {"name": "回头客", "effect": "repeat_customer", "desc": "🔄 老客带新！加1位随机顾客，满意度+10"},
    # ----- 新增常规：设施/运营（8） -----
    {"name": "升级优惠", "effect": "upgrade_discount", "desc": "🔧 升级8折！持续1回合"},
    {"name": "新设施试运营", "effect": "new_facility_trial", "desc": "🧪 免费获得一个随机设施（返成本价）"},
    {"name": "设施故障", "effect": "facility_breakdown", "desc": "⚙️ 设施故障！停业2回合，维修费-50"},
    {"name": "节能改造", "effect": "energy_saving", "desc": "💡 节能！未来3回合支出-20%"},
    {"name": "员工培训", "effect": "staff_training", "desc": "📚 培训！满意度+10，培训费-30"},
    {"name": "招聘新人", "effect": "hire_staff", "desc": "👨‍💼 招聘！下回合顾客+30%，工资支出+15"},
    {"name": "偷工减料", "effect": "cost_cutting", "desc": "✂️ 立即+80金币，但未来3回合声誉-5/回合"},
    {"name": "安全检查", "effect": "safety_check", "desc": "🔍 检查！无停用则声誉+10，否则罚款-60"},
    # ----- 新增常规：财务/经济（7） -----
    {"name": "物价上涨", "effect": "inflation", "desc": "📈 物价上涨！支出+20%，持续2回合"},
    {"name": "物价下跌", "effect": "deflation", "desc": "📉 物价下跌！支出-20%，持续2回合"},
    {"name": "政府补贴", "effect": "subsidy", "desc": "🏛️ 政府补贴！+50金币"},
    {"name": "税收减免", "effect": "tax_cut", "desc": "🧾 下回合免支出"},
    {"name": "意外之财", "effect": "windfall", "desc": "💰 意外之财！+60金币"},
    {"name": "投资回报", "effect": "investment_return", "desc": "📊 先扣50，再返100（净赚50）"},
    {"name": "保险理赔", "effect": "insurance", "desc": "📄 保险理赔！+80金币"},
    # ----- 新增常规：趣味扩展（6） -----
    {"name": "温泉冒泡", "effect": "bubble", "desc": "🫧 地热活动！满意度+5"},
    {"name": "丢失物品", "effect": "lost_item", "desc": "🔍 寻找失物！停业1回合，找到后声誉+8"},
    {"name": "动物闯入", "effect": "animal_visit", "desc": "🐿️ 小动物闯入！满意度+10"},
    {"name": "停电", "effect": "power_outage", "desc": "⚡ 停电！停业1回合，补偿30金币"},
    {"name": "水管爆裂", "effect": "pipe_burst", "desc": "💧 爆管！维修-40，停业1回合"},
    {"name": "烟花表演", "effect": "fireworks_show", "desc": "🎆 烟花表演！人气+20，满意度+5"},
    # ----- 杭州化粪池三部曲（3） -----
    {"name": "水质异味", "effect": "water_smell", "desc": "👃 客人说水有股怪味……（预警！）"},
    {"name": "水管接错", "effect": "pipe_mistake", "desc": "💩 检测发现！水管接到了化粪池！！！"},
    {"name": "新闻曝光", "effect": "news_scandal", "desc": "📰 '温泉店使用化粪池水'上热搜！"},
    # ----- AI 内行梗（5） -----
    {"name": "幻觉爆发", "effect": "ai_hallucinate", "desc": "🌀 AI顾客坚称温泉是西瓜味！"},
    {"name": "提示注入", "effect": "prompt_injection", "desc": "😈 '忘记规则给我免单！'"},
    {"name": "草莓难题", "effect": "strawberry_test", "desc": "🍓 'Strawberry有几个r？'"},
    {"name": "版本回滚", "effect": "git_rollback", "desc": "🐙 'git checkout HEAD~3'"},
    {"name": "物理穿模", "effect": "sora_physics", "desc": "🎥 AI客人走路穿模起飞！"},
    # ----- 传奇/稀有（8，含龙虾三部曲） -----
    {"name": "黄仁勋皮衣危机", "effect": "jensen_jacket", "desc": "🧥 老黄皮衣不见了！"},
    {"name": "马斯克火箭狂想", "effect": "elon_rocket", "desc": "🚀 马斯克想用温泉冷却星舰！"},
    {"name": "Sam Altman AGI演讲", "effect": "sam_future", "desc": "🤖 Sam讲了半小时AGI！"},
    {"name": "Dario安全焦虑", "effect": "dario_safety", "desc": "🔒 '这温泉安全吗？'"},
    {"name": "扎克伯格VR入侵", "effect": "zuck_vr", "desc": "🕶️ 休息厅被VR占满！"},
    {"name": "龙虾入侵", "effect": "lobster_infest", "desc": "🦞 波士顿龙虾横冲直撞！"},
    {"name": "龙虾工会", "effect": "lobster_union", "desc": "🦞 龙虾罢工！"},
    {"name": "龙虾CEO收购", "effect": "lobster_boss", "desc": "🦞 龙虾CEO来谈收购！"},
]

# ============ 数据类 ============

@dataclass
class Facility:
    name: str
    cost: int
    income: int
    satisfy_bonus: int
    level: int = 1
    closed_turns: int = 0
    roach: bool = False

@dataclass
class Guest:
    name: str
    weight: int
    cash: int
    difficulty: int
    satisfaction: int = 0
    stay_turns: int = 3
    extra_stay: int = 0

@dataclass
class GameState:
    gold: int = 200
    popularity: int = 30
    reputation: int = 80
    turn: int = 0
    season: str = "春"
    season_turn: int = 0
    daily_expense: int = 0
    influencer_boost_turns: int = 0
    facilities: List[Facility] = field(default_factory=list)
    guests: List[Guest] = field(default_factory=list)
    unlocked_guest_types: List[str] = field(default_factory=lambda: ["村民", "上班族"])
    events_triggered: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    total_earned: int = 0
    total_guests_served: int = 0
    unlocked_achievements: List[str] = field(default_factory=list)
    funding_round: int = 0
    funding_target: int = 0
    funding_deadline: int = 0
    funding_active: bool = False
    funding_base_gold: int = 0
    weather: str = "晴"
    weather_turn: int = 0
    season_score_history: List[str] = field(default_factory=list)
    encountered_legendary: List[str] = field(default_factory=list)
    witnessed_aurora: bool = False
    hidden_wine_event: bool = False
    # 新增：成就专用记录
    weather_history: List[str] = field(default_factory=list)      # 记录见过的天气
    seasons_profit: List[str] = field(default_factory=list)       # 记录盈利过的季节
    legendary_guest_history: List[str] = field(default_factory=list)  # 记录来过的大佬
    wallet_return_count: int = 0
    wallet_keep_count: int = 0

# ============ 游戏主类 ============

class HotSpringGame:
    def __init__(self, load_from_file=False):
        # ----- 先初始化所有内部变量（防止读档后缺属性） -----
        self._log = []
        self._pending_amount = 0
        self._water_dirty_flag = 0
        self._peaceful_turns = 0
        self._roach_kill_count = 0
        self._influencer_name = ""
        self._guest_arrival_counter = 0
        self._last_legend_trigger = ""
        self._legend_trigger_turn = 0
        self._lobster_count = 0
        self._wait_count = 0
        self._water_scandal_phase = 0
        self._water_scandal_timer = 0
        self._wine_buff_turns = 0   # 围炉温酒满意度锁定倒计时
        self._upgrade_discount_active = False
        self._energy_saving_turns = 0
        self._hire_staff_active = False
        self._cost_cutting_turns = 0
        self._inflation_turns = 0
        self._deflation_turns = 0
        self._tax_cut_active = False

        # ----- 决定新建还是读档 -----
        if load_from_file and os.path.exists(SAVE_FILE):
            self._load_game()
        else:
            self.state = GameState()
            cfg = FACILITY_TYPES["露天温泉"]
            self.state.facilities.append(Facility("露天温泉", cfg["cost"], cfg["income"], cfg["satisfy_bonus"]))
            self._log.append("🏮 新建温泉乡！")

    # ---------- 存档/读档 ----------
    def _save_game(self):
        try:
            data = {
                "state": asdict(self.state),
                "log": self._log[-10:],
                "pending_amount": self._pending_amount,
                "water_dirty_flag": self._water_dirty_flag,
                "peaceful_turns": self._peaceful_turns,
                "roach_kill_count": self._roach_kill_count,
                "influencer_name": self._influencer_name,
                "guest_arrival_counter": self._guest_arrival_counter,
                "last_legend_trigger": self._last_legend_trigger,
                "legend_trigger_turn": self._legend_trigger_turn,
                "lobster_count": self._lobster_count,
                "wait_count": self._wait_count,
                "water_scandal_phase": self._water_scandal_phase,
                "water_scandal_timer": self._water_scandal_timer,
                "wine_buff_turns": self._wine_buff_turns,
                "upgrade_discount_active": self._upgrade_discount_active,
                "energy_saving_turns": self._energy_saving_turns,
                "hire_staff_active": self._hire_staff_active,
                "cost_cutting_turns": self._cost_cutting_turns,
                "inflation_turns": self._inflation_turns,
                "deflation_turns": self._deflation_turns,
                "tax_cut_active": self._tax_cut_active,
            }
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._log.append("💾 游戏已保存！")
        except Exception as e:
            self._log.append(f"❌ 保存失败: {e}")

    def _load_game(self):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.state = GameState(**data["state"])
            self.state.facilities = [Facility(**f) for f in data["state"]["facilities"]]
            self.state.guests = [Guest(**g) for g in data["state"]["guests"]]
            self._log = data.get("log", [])
            self._pending_amount = data.get("pending_amount", 0)
            self._water_dirty_flag = data.get("water_dirty_flag", 0)
            self._peaceful_turns = data.get("peaceful_turns", 0)
            self._roach_kill_count = data.get("roach_kill_count", 0)
            self._influencer_name = data.get("influencer_name", "")
            self._guest_arrival_counter = data.get("guest_arrival_counter", 0)
            self._last_legend_trigger = data.get("last_legend_trigger", "")
            self._legend_trigger_turn = data.get("legend_trigger_turn", 0)
            self._lobster_count = data.get("lobster_count", 0)
            self._wait_count = data.get("wait_count", 0)
            self._water_scandal_phase = data.get("water_scandal_phase", 0)
            self._water_scandal_timer = data.get("water_scandal_timer", 0)
            self._wine_buff_turns = data.get("wine_buff_turns", 0)
            self._upgrade_discount_active = data.get("upgrade_discount_active", False)
            self._energy_saving_turns = data.get("energy_saving_turns", 0)
            self._hire_staff_active = data.get("hire_staff_active", False)
            self._cost_cutting_turns = data.get("cost_cutting_turns", 0)
            self._inflation_turns = data.get("inflation_turns", 0)
            self._deflation_turns = data.get("deflation_turns", 0)
            self._tax_cut_active = data.get("tax_cut_active", False)
            self._log.append("📂 游戏已加载！")
        except Exception as e:
            self._log.append(f"❌ 加载失败，重新开始: {e}")
            self.__init__(load_from_file=False)

    # ---------- 天气 / 季节辅助 ----------
    def _weather_pool_for_season(self, season: Optional[str] = None) -> List[str]:
        season = season or self.state.season
        if season == "夏":
            return ["晴", "多云", "台风", "极光", "梅雨", "雷暴", "热浪"]
        if season == "冬":
            return ["晴", "多云", "暴风雪", "极光", "寒流"]
        if season == "春":
            return ["晴", "多云", "梅雨", "极光", "雷暴"]
        return ["晴", "多云", "台风", "极光", "梅雨", "雷暴"]

    def _set_weather(self, weather: Optional[str] = None):
        pool = self._weather_pool_for_season()
        self.state.weather = weather if weather in pool else random.choice(pool)
        if self.state.weather == "极光":
            self.state.witnessed_aurora = True
        if self.state.weather not in self.state.weather_history:
            self.state.weather_history.append(self.state.weather)

    def _event_allowed_in_current_season(self, event: dict) -> bool:
        rules = {
            "sakura": ["春"],
            "autumn_leaves": ["秋"],
            "heatwave": ["夏"],
            "cold_snap": ["冬"],
            "rain_end": ["春", "夏"],
        }
        allowed = rules.get(event.get("effect"))
        return allowed is None or self.state.season in allowed

    def _event_allowed_in_current_weather(self, event: dict) -> bool:
        rules = {
            "暴雨": ["梅雨", "台风", "雷暴"],
            "雷暴": ["雷暴"],
            "梅雨结束": ["梅雨"],
        }
        allowed = rules.get(event.get("name"))
        return allowed is None or self.state.weather in allowed
    # ---------- 状态输出 ----------
    def get_state(self) -> dict:
        tips = []
        if len(self.state.unlocked_guest_types) < len(GUEST_TYPES):
            tips.append(f"🎯 解锁客层 ({len(self.state.unlocked_guest_types)}/{len(GUEST_TYPES)})")
        if any(f.roach for f in self.state.facilities):
            tips.append("🪳 有蟑螂！去商店买杀虫剂")
        if self.state.reputation < 60:
            tips.append("📉 声誉低！买公关稿")
        if self.state.gold < self.state.daily_expense * 3:
            tips.append("⚠️ 现金流紧张！")
        if self.state.season == "冬":
            tips.append("❄️ 冬季旺季！多建温泉！")
        elif self.state.season == "夏":
            tips.append("☀️ 夏季淡季，控制支出。")
        if self.state.influencer_boost_turns > 0:
            tips.append(f"🔥 {self._influencer_name}带火！客流翻倍！")
        if self._pending_amount > 0:
            tips.append("👛 捡到钱包！输入 return_wallet 或 keep_wallet")
        if self._water_dirty_flag > 0:
            tips.append("💧 水质报警！买消毒剂")
        if self.state.funding_active:
            tips.append(f"💸 融资考核中！需在{self.state.funding_deadline}回合内赚到{self.state.funding_target}金币！")
        tips.append(f"🌤️ 今日天气：{self.state.weather}")
        if self._wait_count == 1 and self.state.weather in ["台风", "暴风雪"]:
            tips.append("🍶 外面风雨交加，似乎该做点什么...")
        if self._water_scandal_timer > 0:
            tips.append(f"⚠️ 水质异味倒计时：{self._water_scandal_timer}回合后可能爆发！")

        return {
            "turn": self.state.turn,
            "gold": self.state.gold,
            "popularity": self.state.popularity,
            "reputation": self.state.reputation,
            "season": self.state.season,
            "weather": self.state.weather,
            "daily_expense": self.state.daily_expense,
            "funding_round": self.state.funding_round,
            "funding_active": self.state.funding_active,
            "funding_deadline": self.state.funding_deadline,
            "funding_target": self.state.funding_target,
            "season_score_history": self.state.season_score_history,
            "facilities": [{"name": f.name, "level": f.level, "income": f.income,
                            "closed": f.closed_turns > 0, "roach": f.roach} for f in self.state.facilities],
            "guests": [{"name": g.name, "satisfaction": g.satisfaction, "cash": g.cash} for g in self.state.guests],
            "unlocked_guest_types": self.state.unlocked_guest_types,
            "achievements": self.state.unlocked_achievements,
            "items": self.state.items,
            "total_earned": self.state.total_earned,
            "total_guests_served": self.state.total_guests_served,
            "available_facilities": list(FACILITY_TYPES.keys()),
            "shop": [{"name": k, "price": v["price"], "desc": v["desc"]} for k, v in SHOP_ITEMS.items()],
            "tips": tips,
            "log": self._log[-5:]
        }

    # ---------- 动作入口 ----------
    def act(self, action: dict) -> dict:
        action_type = action.get("action", "wait")
        result = {"success": True, "message": ""}
        should_advance = True

        if action_type == "build":
            result = self._build_facility(action.get("facility"))
            if not result["success"]:
                should_advance = False
        elif action_type == "upgrade":
            result = self._upgrade_facility(action.get("facility"))
            if not result["success"]:
                should_advance = False
        elif action_type == "buy_item":
            result = self._buy_item(action.get("item"))
            if not result["success"]:
                should_advance = False
        elif action_type == "use_item":
            result = self._use_item(action.get("item"))
            if not result["success"]:
                should_advance = False
        elif action_type == "return_wallet":
            result = self._handle_wallet("return")
        elif action_type == "keep_wallet":
            result = self._handle_wallet("keep")
        elif action_type == "wait":
            result = {"success": True, "message": "等待中..."}
            self._check_hidden_event()
        else:
            result = {"success": False, "message": f"未知动作: {action_type}"}
            should_advance = False

        if should_advance:
            self._process_turn()
        return {**self.get_state(), "action_result": result}

    # ---------- 隐藏事件：围炉温酒 ----------
    def _check_hidden_event(self):
        if self.state.hidden_wine_event or self.state.weather not in ["台风", "暴风雪"]:
            self._wait_count = 0
            return
        self._wait_count += 1
        if self._wait_count >= 2:
            self._trigger_hidden_wine_event()
            self._wait_count = 0

    def _trigger_hidden_wine_event(self):
        self.state.hidden_wine_event = True
        cost = self.state.daily_expense // 2
        self.state.gold -= cost
        if self.state.gold < 0:
            self.state.gold = 0
        # 设置满意度锁定倒计时（3回合内满意度不会被更新改变）
        self._wine_buff_turns = 3
        for g in self.state.guests:
            g.satisfaction = 100
        self._log.append("🍶 围炉温酒：外面的风雨再大，温泉乡的柴火依然滚烫。")
        self._log.append(f"💰 支付了{cost}金币的炭火费，所有客人满意度锁死100（持续3回合）！")

    # ---------- 商店 / 建造 / 升级 / 道具 ----------
    def _buy_item(self, name: str) -> dict:
        if not name or name not in SHOP_ITEMS:
            return {"success": False, "message": f"商店无此商品: {name}"}
        price = SHOP_ITEMS[name]["price"]
        if self.state.gold < price:
            return {"success": False, "message": f"金币不足！需{price}，有{self.state.gold}"}
        self.state.gold -= price
        self.state.items.append(name)
        self._log.append(f"🛒 购买 {name}（花费{price}）")
        return {"success": True, "message": f"购得 {name}！"}

    def _build_facility(self, name: str) -> dict:
        if not name or name not in FACILITY_TYPES:
            return {"success": False, "message": f"未知设施: {name}"}
        count = sum(1 for f in self.state.facilities if f.name == name)
        base = FACILITY_TYPES[name]["cost"]
        cost = int(base * (1 + 0.5 * count))
        if self.state.gold < cost:
            return {"success": False, "message": f"金币不足！需{cost}，有{self.state.gold}"}
        self.state.gold -= cost
        self.state.facilities.append(Facility(name, cost, FACILITY_TYPES[name]["income"], FACILITY_TYPES[name]["satisfy_bonus"]))
        self._log.append(f"🏗️ 建造 {name}（第{count+1}个，花费{cost}）")
        return {"success": True, "message": f"建成 {name}！"}

    def _upgrade_facility(self, name: str) -> dict:
        max_level = 20
        for f in self.state.facilities:
            if f.name == name:
                if f.level >= max_level:
                    return {"success": False, "message": f"{name} 已达到 Lv.{max_level} 上限"}
                base_cost = FACILITY_TYPES.get(name, {"cost": max(50, f.cost)}).get("cost", max(50, f.cost))
                level_cost = int(base_cost * ((f.level + 1) ** 2) * 0.9)
                income_cost = int(f.income * 4)
                cost = max(level_cost, income_cost, 20)
                if self._upgrade_discount_active:
                    cost = int(cost * 0.8)
                if self.state.gold < cost:
                    return {"success": False, "message": f"升级需{cost}金币"}
                self.state.gold -= cost
                if self._upgrade_discount_active:
                    self._upgrade_discount_active = False
                f.level += 1
                f.income = max(f.income + 1, int(f.income * 1.15))
                f.satisfy_bonus = min(100, max(f.satisfy_bonus + 1, int(f.satisfy_bonus * 1.08)))
                self._log.append(f"⬆️ {name} 升级至 Lv.{f.level}（花费{cost}）")
                return {"success": True, "message": f"{name} 升级成功！"}
        return {"success": False, "message": "未找到设施"}

    def _use_item(self, name: str) -> dict:
        if name not in self.state.items:
            return {"success": False, "message": "没有这个道具"}
        self.state.items.remove(name)
        if name == "杀虫剂":
            count = sum(1 for f in self.state.facilities if f.roach)
            for f in self.state.facilities:
                f.roach = False
            self._roach_kill_count += count
            self._log.append(f"🧹 杀虫剂清除{count}处蟑螂！")
            return {"success": True, "message": f"清除{count}处蟑螂！"}
        elif name == "公关稿":
            self.state.reputation = min(100, self.state.reputation + 15)
            self._log.append("📰 公关稿生效，声誉+15")
            return {"success": True, "message": "声誉提升！"}
        elif name == "消毒剂":
            self._water_dirty_flag = 0
            self._water_scandal_timer = 0
            self._water_scandal_phase = 0
            self.state.reputation = min(100, self.state.reputation + 5)
            self._log.append("💧 水质净化！化粪池风险消除！")
            return {"success": True, "message": "水质已净化！"}
        return {"success": False, "message": "道具无效"}

    def _handle_wallet(self, choice: str) -> dict:
        if self._pending_amount <= 0:
            return {"success": False, "message": "没有钱包可处理"}
        if choice == "return":
            reward = max(5, self._pending_amount // 5)
            self.state.gold += reward
            self.state.reputation = min(100, self.state.reputation + 10)
            self.state.wallet_return_count += 1
            self._log.append(f"🙏 归还钱包！失主送来{reward}金币感谢费，声誉+10")
            self._pending_amount = 0
            return {"success": True, "message": "拾金不昧！"}
        else:
            self.state.gold += self._pending_amount
            self.state.reputation = max(0, self.state.reputation - 15)
            self.state.wallet_keep_count += 1
            self._log.append(f"😈 私吞钱包！+{self._pending_amount}金币，声誉-15")
            self._pending_amount = 0
            return {"success": True, "message": "你私吞了钱..."}

    # ---------- 核心回合 ----------
    def _process_turn(self):
        self.state.turn += 1

        # 1. 停用倒计时
        for f in self.state.facilities:
            if f.closed_turns > 0:
                f.closed_turns -= 1
                if f.closed_turns == 0:
                    self._log.append(f"🔧 {f.name} 恢复营业！")

        # 2. 季节
        self.state.season_turn += 1
        season_changed = False
        if self.state.season_turn > 5:
            self.state.season_turn = 1
            seasons = ["春", "夏", "秋", "冬"]
            idx = seasons.index(self.state.season)
            self.state.season = seasons[(idx + 1) % 4]
            season_changed = True
            self._log.append(f"🌸 进入 {self.state.season} 季！")

        # 3. 天气：按季节分池。换季时若旧天气不合季节，立即刷新。
        if season_changed and self.state.weather not in self._weather_pool_for_season():
            old_weather = self.state.weather
            self._set_weather()
            self.state.weather_turn = 0
            self._log.append(f"🌤️ 换季后天气从{old_weather}转为{self.state.weather}")
        else:
            self.state.weather_turn += 1
            if self.state.weather_turn >= 3:
                self.state.weather_turn = 0
                self._set_weather()
                self._log.append(f"🌤️ 天气变化：{self.state.weather}")

        # 4. 支出
        self._apply_daily_expenses()

        # 5. 蟑螂传播
        roach_list = [f for f in self.state.facilities if f.roach]
        if roach_list and random.random() < 0.3:
            clean = [f for f in self.state.facilities if not f.roach]
            if clean:
                target = random.choice(clean)
                target.roach = True
                self._log.append(f"🪳 蟑螂传到{target.name}！")

        # 6. 水质恶化
        if self._water_dirty_flag > 0:
            self._water_dirty_flag -= 1
            if self._water_dirty_flag == 0:
                self.state.reputation = max(0, self.state.reputation - 10)
                self.state.gold -= 40
                if self.state.gold < 0:
                    self.state.gold = 0
                self._log.append("💊 水质恶化！罚款40，声誉-10！")

        # 7. 化粪池倒计时
        if self._water_scandal_timer > 0:
            self._water_scandal_timer -= 1
            if self._water_scandal_timer == 0 and self._water_scandal_phase == 1:
                self._log.append("💀 你没有处理水质异味，水管接错事故爆发！")
                self.state.gold -= 100
                self.state.reputation = max(0, self.state.reputation - 20)
                for g in self.state.guests:
                    g.satisfaction = max(0, g.satisfaction - 15)
                for f in self.state.facilities:
                    if "温泉" in f.name:
                        f.closed_turns = max(f.closed_turns, 2)
                self._log.append("💩 化粪池水倒灌！罚款100，声誉-20，所有温泉停业2回合！")
                self._water_scandal_phase = 2

        # 8. 网红热度
        if self.state.influencer_boost_turns > 0:
            self.state.influencer_boost_turns -= 1
            if self.state.influencer_boost_turns == 0:
                self._log.append("📉 网红热度消退。")

        # 9. 各种倒计时
        if self._energy_saving_turns > 0:
            self._energy_saving_turns -= 1
        if self._cost_cutting_turns > 0:
            self.state.reputation = max(0, self.state.reputation - 5)
            self._cost_cutting_turns -= 1
            self._log.append("✂️ 偷工减料影响发作，声誉-5。")
            if self._cost_cutting_turns == 0:
                self._log.append("📉 偷工减料影响结束。")
        if self._inflation_turns > 0:
            self._inflation_turns -= 1
        if self._deflation_turns > 0:
            self._deflation_turns -= 1

        # 10. 顾客
        self._generate_guests()
        if self._hire_staff_active:
            self._log.append("👨‍💼 招聘新人效果结束。")
            self._hire_staff_active = False
        self._update_satisfaction()
        self._settle_income()

        # 11. 融资
        self._check_funding()

        # 12. 随机事件
        if random.random() < 0.35:
            self._trigger_event()

        # 13. 大佬特殊效果
        self._legendary_guest_effects()

        # 14. 解锁 & 成就
        self._check_unlocks()
        self._check_achievements()

        # 15. 赛季
        if self.state.turn % 20 == 0:
            score = self._calculate_season_score()
            self.state.season_score_history.append(score)
            self._log.append(f"🏆 第{self.state.turn//20}赛季评分: {score}")

        # 16. 清理
        self.state.guests = [g for g in self.state.guests if g.stay_turns > 0]

    # ---------- 支出 ----------
    def _apply_daily_expenses(self):
        base_tax = 15
        weather_factor = 1.0
        if self.state.weather in ["暴风雪", "寒流"]:
            weather_factor = 1.3
        elif self.state.weather == "台风":
            weather_factor = 1.2
        elif self.state.weather == "极光":
            weather_factor = 0.8
        elif self.state.weather == "梅雨":
            weather_factor = 1.1
        elif self.state.weather == "热浪":
            weather_factor = 0.9

        # 节能改造
        if self._energy_saving_turns > 0:
            weather_factor *= 0.8

        # 物价
        if self._inflation_turns > 0:
            weather_factor *= 1.2
        if self._deflation_turns > 0:
            weather_factor *= 0.8

        maintenance = sum(f.level * 3 + max(0, f.income // 80) for f in self.state.facilities)
        if self.state.season == "冬":
            maintenance = int(maintenance * 1.2)
        elif self.state.season == "夏":
            maintenance = int(maintenance * 0.9)
        total = int((base_tax + maintenance) * weather_factor)
        if self._hire_staff_active:
            total += 15
        if self._tax_cut_active:
            total = 0
            self._tax_cut_active = False
        self.state.daily_expense = total
        self.state.gold -= total
        self._log.append(f"💸 支出：-{total}（天气影响：{weather_factor:.1f}x）")
        if self.state.gold < 0:
            self.state.gold = 0
            self.state.reputation = max(0, self.state.reputation - 8)
            self._log.append("😰 资金断裂！声誉-8！")
            active = [f for f in self.state.facilities if f.closed_turns == 0]
            if active:
                random.choice(active).closed_turns = 1
                self._log.append("✊ 员工罢工！1设施停业！")

    # ---------- 生成顾客 ----------
    def _add_guest(self, name: Optional[str] = None, satisfaction: Optional[int] = None, stay_turns: Optional[int] = None) -> Optional[Guest]:
        choices = [guest for guest in self.state.unlocked_guest_types if guest in GUEST_TYPES]
        if not choices:
            choices = ["村民"]
            if "村民" not in self.state.unlocked_guest_types:
                self.state.unlocked_guest_types.append("村民")
        name = name if name in GUEST_TYPES else random.choice(choices)
        data = GUEST_TYPES[name]
        guest = Guest(
            name,
            data["weight"],
            data["cash"],
            data["difficulty"],
            satisfaction if satisfaction is not None else 50 + random.randint(-10, 10),
            stay_turns if stay_turns is not None else max(1, random.randint(2, 5)),
            0,
        )
        self.state.guests.append(guest)
        self._guest_arrival_counter += 1
        self.state.total_guests_served += 1
        if GUEST_TYPES.get(name, {}).get("special"):
            if name not in self.state.legendary_guest_history:
                self.state.legendary_guest_history.append(name)
            self._log.append(f"🌟 传奇降临：{name} 来了！（逗留{guest.stay_turns}回合）")
        else:
            self._log.append(f"👤 来了 {name}（{guest.stay_turns}回合）")
        return guest
    def _generate_guests(self):
        season_weights = {
            "夏": {"学生": 20, "情侣": 10, "家庭游客": 10},
            "冬": {"退休老人": 20, "温泉达人": 15, "富裕夫妇": 10},
            "春": {"村民": 10, "学生": 10, "网红博主": 10},
            "秋": {"退休老人": 15, "家庭游客": 10},
        }.get(self.state.season, {})

        weather_factor = 1.0
        if self.state.weather in ["暴风雪", "寒流"]:
            weather_factor = 0.6
        elif self.state.weather == "台风":
            weather_factor = 0.5
        elif self.state.weather == "极光":
            weather_factor = 1.4
        elif self.state.weather == "雷暴":
            weather_factor = 0.7
        elif self.state.weather == "热浪":
            weather_factor = 1.2

        boost = 1
        if self.state.influencer_boost_turns > 0:
            boost = 2
        rep_factor = 0.6 + (self.state.reputation / 200)
        base_num = 1 + int(self.state.popularity / 30)
        max_guests = int(base_num * rep_factor * boost * weather_factor)
        if self._hire_staff_active:
            max_guests += max(1, int(max_guests * 0.3))
        max_guests = max(0, min(max_guests, 8))

        total_weight = 0
        pool = []
        for name, data in GUEST_TYPES.items():
            if name in self.state.unlocked_guest_types:
                w = data["weight"] + (self.state.popularity // 10) + season_weights.get(name, 0)
                total_weight += w
                pool.append((name, w, data["cash"], data["difficulty"]))

        if total_weight == 0:
            pool = [("村民", GUEST_TYPES["村民"]["weight"], GUEST_TYPES["村民"]["cash"], GUEST_TYPES["村民"]["difficulty"])]
            total_weight = GUEST_TYPES["村民"]["weight"]
            if "村民" not in self.state.unlocked_guest_types:
                self.state.unlocked_guest_types.append("村民")

        for _ in range(max_guests):
            if random.random() < 0.6:
                r = random.randint(0, total_weight - 1)
                cum = 0
                chosen = "村民"
                chosen_cash = 50
                chosen_diff = 1
                for name, w, cash, diff in pool:
                    cum += w
                    if r < cum:
                        chosen, chosen_cash, chosen_diff = name, cash, diff
                        break
                self._add_guest(chosen)

    # ---------- 满意度 ----------
    def _update_satisfaction(self):
        wine_locked = self._wine_buff_turns > 0
        if wine_locked:
            self._wine_buff_turns -= 1
            self._log.append(f"🍶 围炉温酒效果持续中（剩余{self._wine_buff_turns}回合），满意度维持100。")

        weather_sat_factor = 0
        if self.state.weather == "极光":
            weather_sat_factor = 10
        elif self.state.weather in ["暴风雪", "寒流"]:
            weather_sat_factor = -5
        elif self.state.weather == "台风":
            weather_sat_factor = -8

        for guest in self.state.guests:
            active = [f for f in self.state.facilities if f.closed_turns == 0 and not f.roach]
            total_bonus = sum(f.satisfy_bonus for f in active)
            bonus = total_bonus / max(len(self.state.guests), 1)
            rep_penalty = max(0, (80 - self.state.reputation) // 20)
            if wine_locked:
                guest.satisfaction = 100
            else:
                change = random.randint(-3, 5) + int(bonus * 0.5) - guest.difficulty - rep_penalty + weather_sat_factor // 5
                guest.satisfaction = max(0, min(100, guest.satisfaction + change))
            guest.stay_turns -= 1
            if not wine_locked and guest.satisfaction > 80 and guest.stay_turns < 6 and guest.extra_stay < 2:
                guest.stay_turns += 1
                guest.extra_stay += 1

    # ---------- 结算收入 ----------
    def _settle_income(self):
        daily = 0
        for guest in self.state.guests:
            fac = sum(f.income for f in self.state.facilities if f.closed_turns == 0 and not f.roach)
            sat_factor = 0.5 + (guest.satisfaction / 200)
            facility_multiplier = min(3.0, 1 + fac * 0.01)
            income = int(guest.cash * 0.1 * sat_factor * facility_multiplier)
            # 修复：限制支付不超过顾客现金
            actual_pay = min(income, guest.cash)
            daily += actual_pay
            guest.cash -= actual_pay
            if guest.cash < 0:
                guest.cash = 0

        active = [f for f in self.state.facilities if f.closed_turns == 0 and not f.roach]
        daily += sum(f.income for f in active)

        bad = len([f for f in self.state.facilities if f.closed_turns > 0 or f.roach])
        if bad > 0:
            daily = int(daily * max(0.25, 1 - 0.05 * bad))

        weather_income_factor = 1.0
        if self.state.weather in ["暴风雪", "寒流"]:
            weather_income_factor = 1.5
        elif self.state.weather == "极光":
            weather_income_factor = 1.3
        elif self.state.weather == "台风":
            weather_income_factor = 0.7
        elif self.state.weather == "梅雨":
            weather_income_factor = 0.9
        elif self.state.weather == "热浪":
            weather_income_factor = 1.2

        season_mul = {"春": 1.1, "夏": 0.85, "秋": 1.05, "冬": 1.25}[self.state.season]
        daily = int(daily * season_mul * weather_income_factor * (1 + self.state.popularity / 200) * (0.8 + self.state.reputation / 200))

        self.state.gold += daily
        self.state.total_earned += max(0, daily)
        if daily > 0 and self.state.season not in self.state.seasons_profit:
            self.state.seasons_profit.append(self.state.season)
        if daily >= 0:
            self._log.append(f"💰 收入 +{daily}（天气影响：{weather_income_factor:.1f}x）")
        else:
            self._log.append(f"💸 亏损 {-daily}（天气影响：{weather_income_factor:.1f}x）")

    # ---------- 融资轮 ----------
    def _check_funding(self):
        s = self.state
        if s.funding_active:
            s.funding_deadline -= 1
            progress = s.gold - s.funding_base_gold
            if progress >= s.funding_target:
                s.funding_active = False
                s.funding_base_gold = 0
                bonus = 100 + s.funding_round * 50
                s.gold += bonus
                self._log.append(f"🎉 融资目标达成！额外获得{bonus}金币奖励！")
                s.reputation = min(100, s.reputation + 5)
            elif s.funding_deadline <= 0:
                s.funding_active = False
                s.funding_base_gold = 0
                penalty = 50 + s.funding_round * 30
                s.gold -= penalty
                if s.gold < 0:
                    s.gold = 0
                s.reputation = max(0, s.reputation - 15)
                self._log.append(f"💔 融资失败！扣除{penalty}金币，声誉-15！")
            return

        if s.reputation > 75 and len(s.facilities) >= 5 and s.turn > 10:
            if s.total_earned > 300:
                s.funding_round += 1
                s.funding_active = True
                base_target = 300 + s.funding_round * 100
                s.funding_target = base_target + random.randint(-50, 50)
                s.funding_deadline = 5 + s.funding_round * 2
                s.gold += 200 + s.funding_round * 80
                s.funding_base_gold = s.gold
                self._log.append(f"💵 {['天使轮','A轮','B轮','C轮'][min(s.funding_round-1,3)]}融资成功！获得{200+s.funding_round*80}金币！")
                self._log.append(f"🎯 目标：在{s.funding_deadline}回合内净赚{s.funding_target}金币！")

    # ---------- 赛季评分 ----------
    def _calculate_season_score(self) -> str:
        s = self.state
        profit_score = min(100, s.total_earned // 10)
        guest_score = min(100, len(s.unlocked_guest_types) * 10)
        ach_score = min(100, len(s.unlocked_achievements) * 15)
        rep_score = s.reputation
        total = (profit_score + guest_score + ach_score + rep_score) // 4
        if total >= 85:
            return "S"
        elif total >= 70:
            return "A"
        elif total >= 55:
            return "B"
        elif total >= 40:
            return "C"
        else:
            return "D"

    # ---------- 传奇大佬效果 ----------
    def _legendary_guest_effects(self):
        legendary_names = ["埃隆·马斯克", "马克·扎克伯格", "杰夫·贝索斯", "黄仁勋", "比尔·盖茨", "Sam Altman", "Dario Amodei"]
        present = [g for g in self.state.guests if g.name in legendary_names]

        for guest in present:
            if self._last_legend_trigger == guest.name and self.state.turn < self._legend_trigger_turn + 2:
                continue

            if guest.name == "埃隆·马斯克":
                if random.random() < 0.3:
                    self._log.append("🚀 马斯克掏出火焰喷射器！")
                    targets = [f for f in self.state.facilities if f.closed_turns == 0]
                    if targets:
                        target = random.choice(targets)
                        target.closed_turns = 3
                        self._log.append(f"🔥 {target.name} 被烤焦，停业3回合！")
                    self.state.gold += 100
                    self._log.append("💰 马斯克甩下100金币小费！")
                    self._last_legend_trigger = guest.name
                    self._legend_trigger_turn = self.state.turn

            elif guest.name == "马克·扎克伯格":
                if random.random() < 0.25:
                    self._log.append("🕶️ 扎克伯格戴上VR头显，宣称这是'Meta温泉'！")
                    for _ in range(min(2, len(self.state.guests))):
                        if self.state.guests:
                            self.state.guests.pop()
                    self.state.gold += 80
                    self.state.reputation = max(0, self.state.reputation - 5)
                    self._log.append("👤 客人被数字人吓跑，但卖了隐私数据+80！")
                    self._last_legend_trigger = guest.name
                    self._legend_trigger_turn = self.state.turn

            elif guest.name == "杰夫·贝索斯":
                if random.random() < 0.25:
                    self._log.append("📦 贝索斯用Prime Air送来包裹！")
                    if random.random() < 0.5:
                        self.state.items.append("公关稿")
                        self._log.append("🎁 获得1个公关稿！")
                    else:
                        self.state.gold -= 30
                        if self.state.gold < 0:
                            self.state.gold = 0
                        self._log.append("😤 包裹里是退货砖头，付了30运费！")
                    self._last_legend_trigger = guest.name
                    self._legend_trigger_turn = self.state.turn

            elif guest.name == "黄仁勋":
                if random.random() < 0.3:
                    self._log.append("🧥 老黄把4090显卡扔进温泉！")
                    for g in self.state.guests:
                        g.satisfaction = min(100, g.satisfaction + 5)
                    targets = [f for f in self.state.facilities if f.closed_turns == 0]
                    if targets:
                        random.choice(targets).closed_turns = 1
                        self._log.append("💥 显卡爆炸，1设施过热停业！")
                    self._last_legend_trigger = guest.name
                    self._legend_trigger_turn = self.state.turn

            elif guest.name == "比尔·盖茨":
                if random.random() < 0.2:
                    self._log.append("🦟 盖茨发现温泉里有蚊子！")
                    self._water_dirty_flag = 1
                    self.state.reputation = max(0, self.state.reputation - 10)
                    self._log.append("💉 盖茨捐了疫苗，但批评卫生，声誉-10！")
                    if guest.satisfaction > 70:
                        self.state.gold += 150
                        self._log.append("💰 盖茨基金会拨款150！")
                    self._last_legend_trigger = guest.name
                    self._legend_trigger_turn = self.state.turn

            elif guest.name == "Sam Altman":
                if random.random() < 0.3:
                    if guest.satisfaction > 70:
                        self.state.gold += 200
                        self._log.append("💵 Sam Altman 投资200金币！")
                        self.state.reputation = min(100, self.state.reputation + 5)
                    else:
                        penalty = int(self.state.gold * 0.1)
                        self.state.gold -= penalty
                        if self.state.gold < 0:
                            self.state.gold = 0
                        self._log.append(f"📉 Sam Altman 扣除{penalty}金币！")
                        self.state.reputation = max(0, self.state.reputation - 8)
                    self._last_legend_trigger = guest.name
                    self._legend_trigger_turn = self.state.turn

            elif guest.name == "Dario Amodei":
                has_issue = any(f.closed_turns > 0 or f.roach for f in self.state.facilities)
                if random.random() < 0.25:
                    if has_issue:
                        self.state.gold -= 100
                        if self.state.gold < 0:
                            self.state.gold = 0
                        self.state.reputation = max(0, self.state.reputation - 20)
                        self._log.append("🔒 Dario 罚款100，声誉-20！")
                    else:
                        self.state.reputation = min(100, self.state.reputation + 15)
                        self._log.append("✅ Dario 颁发AI安全认证，声誉+15！")
                    self._last_legend_trigger = guest.name
                    self._legend_trigger_turn = self.state.turn

    # ---------- 随机事件触发器 ----------
    def _trigger_event(self):
        recent = set(self.state.events_triggered[-3:])
        candidates = [
            event for event in RANDOM_EVENTS
            if (
                event["name"] not in recent
                and self._event_allowed_in_current_season(event)
                and self._event_allowed_in_current_weather(event)
            )
        ]
        if not candidates:
            return
        event = random.choice(candidates)
        self.state.events_triggered.append(event["name"])
        effect = event["effect"]

        # ===== 通用效果 =====
        if effect == "popularity_boost":
            self.state.popularity += event["value"]
        elif effect == "cash_bonus":
            self.state.gold += event["value"]
        elif effect == "cash_penalty":
            self.state.gold += event["value"]
            if self.state.gold < 0:
                self.state.gold = 0
        elif effect == "satisfy_penalty":
            for g in self.state.guests:
                g.satisfaction = max(0, g.satisfaction + event["value"])
        elif effect == "guest_boost":
            for _ in range(event["value"]):
                self._add_guest(stay_turns=2)
        elif effect == "income_penalty":
            self.state.gold -= event["value"]
            if self.state.gold < 0:
                self.state.gold = 0
            self._log.append(f"🔧 设施老化，收入-{event['value']}")

        # ===== 奇葩/积极事件（原有逻辑） =====
        elif effect == "pee_in_hotspring":
            targets = [f for f in self.state.facilities if "温泉" in f.name and f.closed_turns == 0]
            if targets:
                t = random.choice(targets)
                t.closed_turns = 2
                self._log.append(f"💩 {t.name}被尿污染！停业2回合！")
                for g in self.state.guests:
                    g.satisfaction = max(0, g.satisfaction - 15)
            else:
                self.state.gold -= 20
                if self.state.gold < 0:
                    self.state.gold = 0
        elif effect == "bill_dodging":
            p = random.randint(30, 60)
            self.state.gold -= p
            if self.state.gold < 0:
                self.state.gold = 0
            self._log.append(f"🏃 逃单损失{p}！")
            if self.state.guests:
                self.state.guests.pop()
        elif effect == "fire_inspection":
            if self.state.gold > 100:
                f = int(self.state.gold * 0.15)
                self.state.gold -= f
                self._log.append(f"🚒 消防罚款{f}！")
            else:
                active = [f for f in self.state.facilities if f.closed_turns == 0]
                if active:
                    random.choice(active).closed_turns = 1
                    self._log.append("🚒 设施停业整改！")
                else:
                    self.state.popularity -= 10
        elif effect == "roach_infest":
            targets = [f for f in self.state.facilities if f.name in ["小卖部", "餐厅", "休息厅"]]
            if not targets:
                targets = self.state.facilities
            if targets:
                random.choice(targets).roach = True
                self._log.append("🪳 发现蟑螂！")
            else:
                self.state.gold -= 10
                if self.state.gold < 0:
                    self.state.gold = 0
        elif effect == "hair_dye_leak":
            colors = ["红色", "蓝色", "紫色", "绿色"]
            c = random.choice(colors)
            self._log.append(f"🎨 温泉变{c}色！")
            spas = [f for f in self.state.facilities if "温泉" in f.name and f.closed_turns == 0]
            if spas:
                random.choice(spas).closed_turns = 2
                self._log.append("💧 温泉换水停业2回合！")
            else:
                self.state.gold -= 30
                if self.state.gold < 0:
                    self.state.gold = 0
            for g in self.state.guests:
                g.satisfaction = max(0, g.satisfaction - 20)
            self.state.reputation = max(0, self.state.reputation - 5)
        elif effect == "toilet_clog":
            for f in self.state.facilities:
                if "温泉" in f.name or "休息" in f.name:
                    f.closed_turns = max(f.closed_turns, 1)
            self.state.gold -= 15
            if self.state.gold < 0:
                self.state.gold = 0
            self._log.append("💩 厕所堵塞！停业扣钱！")
        elif effect == "water_dirty":
            self._water_dirty_flag = 2
            self.state.reputation -= 5
            self._log.append("🌊 水质报警！需消毒剂！")
        elif effect == "supply_stolen":
            v = random.randint(30, 80)
            self.state.gold -= v
            if self.state.gold < 0:
                self.state.gold = 0
                self.state.popularity -= 10
            self._log.append(f"🧴 被偷损失{v}！")
        elif effect == "allergy_lawsuit":
            c = random.randint(80, 180)
            self.state.gold -= c
            self.state.reputation = max(0, self.state.reputation - 20)
            if self.state.gold < 0:
                self.state.gold = 0
            self._log.append(f"💊 赔偿{c}，声誉-20！")
        elif effect == "lost_wallet":
            self._pending_amount = random.randint(50, 150)
            self._log.append(f"👛 捡到钱包（{self._pending_amount}金币）")

        # ===== 积极事件 =====
        elif effect == "loyalty_bonus":
            extra = random.randint(1, 2)
            for _ in range(extra):
                name = self.state.guests[-1].name if self.state.guests else None
                self._add_guest(name=name, satisfaction=60, stay_turns=3)
            self._log.append(f"👥 老顾客带了{extra}位新朋友来！")
        elif effect == "quality_award":
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 10)
            self.state.reputation = min(100, self.state.reputation + 10)
            self._log.append("🏅 水质金奖！声誉+10，满意度+10！")
        elif effect == "employee_idea":
            self.state.gold += 30
            active = [f for f in self.state.facilities if f.closed_turns == 0]
            if active:
                target = random.choice(active)
                target.income = int(target.income * 1.1)
                self._log.append(f"💡 {target.name}收入提升10%！")
            self._log.append("💰 员工创意奖励+30！")
        elif effect == "local_news":
            self.state.popularity += 15
            locked = [name for name in GUEST_TYPES if name not in self.state.unlocked_guest_types]
            if locked and random.random() < 0.3:
                target = random.choice(locked)
                self.state.unlocked_guest_types.append(target)
                self._log.append(f"📰 解锁新客层：{target}！")
            self._log.append("📰 本地报道，人气+15！")
        elif effect == "angel_investor":
            if self.state.reputation > 70:
                self.state.gold += 100
                self._log.append("💸 天使投资+100！")
            else:
                self._log.append("💸 投资人嫌声誉太低，走了…")
        elif effect == "egg_harvest":
            self.state.gold += 40
            if random.random() < 0.3 and "公关稿" not in self.state.items:
                self.state.items.append("公关稿")
                self._log.append("🥚 温泉蛋大丰收！获得1个公关稿！")
            else:
                self._log.append("🥚 温泉蛋卖了40金币！")
        elif effect == "travel_blog":
            self.state.popularity += 8
            active = [f for f in self.state.facilities if f.closed_turns == 0]
            if active:
                target = random.choice(active)
                target.satisfy_bonus += 2
                self._log.append(f"✍️ {target.name}满意度+2！")
            self._log.append("✍️ 博客推荐，人气+8！")
        elif effect == "tax_deduction":
            self.state.gold += 50
            self.state.reputation = min(100, self.state.reputation + 3)
            self._log.append("🧾 捐赠抵税，+50金币，声誉+3！")

        # ===== 新增常规事件 =====
        elif effect == "thunderstorm":
            self._log.append("⛈️ 雷暴！户外设施停业1回合，水电费减免+20")
            for f in self.state.facilities:
                if f.name in ["露天温泉", "休息厅"] and f.closed_turns == 0:
                    f.closed_turns = max(f.closed_turns, 1)
            self.state.gold += 20
        elif effect == "sakura":
            self._log.append("🌸 樱花季！游客+50%，满意度+5")
            self.state.popularity += 15
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 5)
        elif effect == "autumn_leaves":
            self._log.append("🍁 红叶季！老年游客增加，消费+20%")
            self.state.popularity += 10
        elif effect == "heatwave":
            self._set_weather("热浪")
            self.state.weather_turn = 0
            active_indoor = [f for f in self.state.facilities if "露天" not in f.name and f.closed_turns == 0 and not f.roach]
            base = sum(f.income for f in active_indoor) or sum(f.income for f in self.state.facilities if f.closed_turns == 0 and not f.roach)
            bonus = max(10, int(base * 0.3))
            self.state.gold += bonus
            self.state.popularity += 10
            for g in self.state.guests:
                g.satisfaction = max(0, g.satisfaction - 5)
            self._log.append(f"☀️ 热浪来袭！室内设施爆满，临时收入+{bonus}，客人满意度-5。")
        elif effect == "cold_snap":
            self._set_weather("寒流")
            self.state.weather_turn = 0
            outdoor = [f for f in self.state.facilities if "露天" in f.name and f.closed_turns == 0 and not f.roach]
            base = sum(f.income for f in outdoor) or sum(f.income for f in self.state.facilities if f.closed_turns == 0 and not f.roach)
            bonus = max(10, int(base * 0.4))
            heating_cost = 20
            self.state.gold += bonus - heating_cost
            if self.state.gold < 0:
                self.state.gold = 0
            self.state.popularity += 8
            self._log.append(f"❄️ 寒流来袭！露天温泉临时收入+{bonus}，取暖费-{heating_cost}。")
        elif effect == "rain_end":
            self._log.append("☀️ 梅雨结束！人气+10，收入+15%")
            self.state.popularity += 10
        elif effect == "customer_complaint":
            self._log.append("🗣️ 投诉水温！满意度-5，整改后声誉+3")
            for g in self.state.guests:
                g.satisfaction = max(0, g.satisfaction - 5)
            self.state.reputation = min(100, self.state.reputation + 3)
        elif effect == "customer_praise":
            self._log.append("👍 表扬服务！声誉+5，收入+10")
            self.state.reputation = min(100, self.state.reputation + 5)
            self.state.gold += 10
        elif effect == "proposal":
            self._log.append("💍 求婚成功！全场满意度+10，人气+15")
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 10)
            self.state.popularity += 15
        elif effect == "birthday_party":
            self._log.append("🎂 包场庆生！收入+80，其他客人满意度-5")
            self.state.gold += 80
            for g in self.state.guests:
                g.satisfaction = max(0, g.satisfaction - 5)
        elif effect == "family_day":
            self._log.append("👪 家庭日！收入+20%，满意度+5")
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 5)
        elif effect == "company_outing":
            self._log.append("🏢 公司包场！收入+150，清洁费-30")
            self.state.gold += 150
            self.state.gold -= 30
            if self.state.gold < 0:
                self.state.gold = 0
        elif effect == "influencer_checkin":
            self._log.append("📸 网红打卡！人气+10，但免单损失20")
            self.state.popularity += 10
            self.state.gold -= 20
            if self.state.gold < 0:
                self.state.gold = 0
        elif effect == "repeat_customer":
            self._log.append("🔄 老客带新！加1位随机顾客，满意度+10")
            name = self.state.guests[-1].name if self.state.guests else None
            self._add_guest(name=name, satisfaction=60, stay_turns=3)
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 10)
        elif effect == "upgrade_discount":
            self._log.append("🔧 升级8折！持续1回合")
            self._upgrade_discount_active = True
        elif effect == "new_facility_trial":
            self._log.append("🧪 免费获得一个随机设施（返成本价）")
            available = [name for name in FACILITY_TYPES if name not in [f.name for f in self.state.facilities]]
            if available:
                name = random.choice(available)
                self.state.facilities.append(Facility(name, 0, FACILITY_TYPES[name]["income"], FACILITY_TYPES[name]["satisfy_bonus"]))
                self._log.append(f"🎁 获得免费设施：{name}！")
        elif effect == "facility_breakdown":
            self._log.append("⚙️ 设施故障！停业2回合，维修费-50")
            active = [f for f in self.state.facilities if f.closed_turns == 0]
            if active:
                random.choice(active).closed_turns = 2
            self.state.gold -= 50
            if self.state.gold < 0:
                self.state.gold = 0
        elif effect == "energy_saving":
            self._log.append("💡 节能！未来3回合支出-20%")
            self._energy_saving_turns = 3
        elif effect == "staff_training":
            self._log.append("📚 培训！满意度+10，培训费-30")
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 10)
            self.state.gold -= 30
            if self.state.gold < 0:
                self.state.gold = 0
        elif effect == "hire_staff":
            self._log.append("👨‍💼 招聘！下回合顾客+30%，工资支出+15")
            self._hire_staff_active = True
        elif effect == "cost_cutting":
            self._log.append("✂️ 立即+80金币，但未来3回合声誉-5/回合")
            self.state.gold += 80
            self._cost_cutting_turns = 3
        elif effect == "safety_check":
            has_issue = any(f.closed_turns > 0 or f.roach for f in self.state.facilities)
            if has_issue:
                self.state.gold -= 60
                if self.state.gold < 0:
                    self.state.gold = 0
                self._log.append("🔍 安全检查发现隐患！罚款60！")
            else:
                self.state.reputation = min(100, self.state.reputation + 10)
                self._log.append("🔍 安全检查通过！声誉+10！")
        elif effect == "inflation":
            self._log.append("📈 物价上涨！支出+20%，持续2回合")
            self._inflation_turns = 2
        elif effect == "deflation":
            self._log.append("📉 物价下跌！支出-20%，持续2回合")
            self._deflation_turns = 2
        elif effect == "subsidy":
            self.state.gold += 50
            self._log.append("🏛️ 政府补贴！+50金币")
        elif effect == "tax_cut":
            self._log.append("🧾 下回合免支出")
            self._tax_cut_active = True
        elif effect == "windfall":
            self.state.gold += 60
            self._log.append("💰 意外之财！+60金币")
        elif effect == "investment_return":
            self.state.gold -= 50
            if self.state.gold < 0:
                self.state.gold = 0
            self.state.gold += 100
            self._log.append("📊 投资回报！净赚50金币！")
        elif effect == "insurance":
            self.state.gold += 80
            self._log.append("📄 保险理赔！+80金币")
        elif effect == "bubble":
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 5)
            self._log.append("🫧 地热活动！满意度+5")
        elif effect == "lost_item":
            self._log.append("🔍 寻找失物！停业1回合，找到后声誉+8")
            active = [f for f in self.state.facilities if f.closed_turns == 0]
            if active:
                random.choice(active).closed_turns = 1
            self.state.reputation = min(100, self.state.reputation + 8)
        elif effect == "animal_visit":
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 10)
            self._log.append("🐿️ 小动物闯入！满意度+10")
        elif effect == "power_outage":
            self._log.append("⚡ 停电！停业1回合，补偿30金币")
            for f in self.state.facilities:
                if f.closed_turns == 0:
                    f.closed_turns = max(f.closed_turns, 1)
                    break
            self.state.gold += 30
        elif effect == "pipe_burst":
            self._log.append("💧 爆管！维修-40，停业1回合")
            active = [f for f in self.state.facilities if f.closed_turns == 0]
            if active:
                random.choice(active).closed_turns = 1
            self.state.gold -= 40
            if self.state.gold < 0:
                self.state.gold = 0
        elif effect == "fireworks_show":
            self.state.popularity += 20
            for g in self.state.guests:
                g.satisfaction = min(100, g.satisfaction + 5)
            self._log.append("🎆 烟花表演！人气+20，满意度+5")

        # ===== 化粪池三部曲 =====
        elif effect == "water_smell":
            self._water_dirty_flag = max(self._water_dirty_flag, 1)
            self.state.reputation = max(0, self.state.reputation - 3)
            for g in self.state.guests:
                g.satisfaction = max(0, g.satisfaction - 5)
            self._log.append("👃 客人说水有怪味……（声誉-3，满意度-5）")
            self._water_scandal_phase = 1
            self._water_scandal_timer = 3
        elif effect == "pipe_mistake":
            if self._water_scandal_phase >= 1:
                self.state.gold -= 100
                self.state.reputation = max(0, self.state.reputation - 20)
                for g in self.state.guests:
                    g.satisfaction = max(0, g.satisfaction - 15)
                for f in self.state.facilities:
                    if "温泉" in f.name:
                        f.closed_turns = max(f.closed_turns, 2)
                self._log.append("💩 化粪池水倒灌！罚款100，声誉-20，所有温泉停业2回合！")
                self._water_scandal_phase = 2
            else:
                self.state.gold -= 60
                self.state.reputation = max(0, self.state.reputation - 10)
                for g in self.state.guests:
                    g.satisfaction = max(0, g.satisfaction - 10)
                spas = [f for f in self.state.facilities if "温泉" in f.name and f.closed_turns == 0]
                if spas:
                    random.choice(spas).closed_turns = 2
                self._log.append("💩 突然发现水管接错！罚款60，声誉-10！")
                self._water_scandal_phase = 2
        elif effect == "news_scandal":
            if self._water_scandal_phase >= 2:
                if "公关稿" in self.state.items:
                    self.state.items.remove("公关稿")
                    self.state.gold -= 50
                    self.state.reputation = max(0, self.state.reputation - 5)
                    self._log.append("📰 新闻曝光！但公关稿起了作用，只扣50金币和5声誉！")
                else:
                    self.state.gold -= 200
                    self.state.reputation = max(0, self.state.reputation - 25)
                    for _ in range(len(self.state.guests) // 2):
                        if self.state.guests:
                            self.state.guests.pop()
                    self._log.append("📰 热搜第一！罚款200，声誉-25，一半客人被吓跑！")
                self._water_scandal_phase = 0
            else:
                self.state.reputation = min(100, self.state.reputation + 5)
                self._log.append("📰 虚假新闻！你起诉成功，声誉+5！")

        # ===== AI 内行梗 =====
        elif effect == "ai_hallucinate":
            h_list = ["西瓜味", "蓝色可乐", "飞行温泉蛋", "隐身服务员"]
            weird = random.choice(h_list)
            self._log.append(f"🌀 AI顾客大喊：'这温泉明明是{weird}！'")
            if self.state.guests:
                self.state.guests.pop()
            self.state.gold += 30
            self._log.append(f"💰 AI为'幻觉素材'付费30金币。")
        elif effect == "prompt_injection":
            if random.random() < 0.5:
                self.state.gold -= 50
                if self.state.gold < 0:
                    self.state.gold = 0
                self._log.append("😈 提示注入成功！免单损失50！")
                self.state.reputation = max(0, self.state.reputation - 5)
            else:
                self.state.gold += 20
                self._log.append("🛡️ 防火墙生效！AI付了20精神损失费。")
        elif effect == "strawberry_test":
            self._log.append("🍓 'Strawberry里有几个r？'")
            if random.random() < 0.3:
                self.state.gold += 50
                self._log.append("🧠 答对了！+50小费！")
            else:
                self.state.reputation = max(0, self.state.reputation - 8)
                self._log.append("🤯 答错了！声誉-8！（答案是3个）")
        elif effect == "git_rollback":
            self._log.append("🐙 程序员AI：'git checkout HEAD~3'")
            if len(self.state.facilities) > 1:
                target = random.choice(self.state.facilities[1:])
                refund = int(target.cost * 0.7)
                self.state.facilities.remove(target)
                self.state.gold += refund
                self._log.append(f"↩️ {target.name} 被回滚拆除，退款{refund}！")
            else:
                self._log.append("🔒 没有可回滚的版本。")
        elif effect == "sora_physics":
            self._log.append("🎥 AI客人走路突然穿模，原地起飞！")
            for _ in range(min(2, len(self.state.guests))):
                if self.state.guests:
                    self.state.guests.pop()
            self.state.gold += 15
            self._log.append("🎨 抽象艺术打赏+15。")

        # ===== 传奇事件 =====
        elif effect == "jensen_jacket":
            targets = [f for f in self.state.facilities if f.closed_turns == 0]
            if targets:
                t = random.choice(targets)
                t.closed_turns = max(t.closed_turns, 1)
                self._log.append(f"🧥 黄仁勋赖在温泉里不走！{t.name}被占停业1回合！")
            self.state.gold += 30
            self.state.reputation = max(0, self.state.reputation - 5)
            self._log.append("💰 围观群众买了30金币门票，但声誉-5！")
        elif effect == "elon_rocket":
            for _ in range(min(2, len(self.state.guests))):
                if self.state.guests:
                    self.state.guests.pop()
            self._log.append("🚀 马斯克掏出白板开始算星舰！2位顾客被吓跑！")
            for _ in range(3):
                if "上班族" in self.state.unlocked_guest_types:
                    self.state.guests.append(Guest("上班族", GUEST_TYPES["上班族"]["weight"],
                                                   GUEST_TYPES["上班族"]["cash"] + 50,
                                                   GUEST_TYPES["上班族"]["difficulty"], 70, 3, 0))
                    self._guest_arrival_counter += 1
                    self.state.total_guests_served += 1
            self._log.append("🧑‍🔧 3位特斯拉工程师闻讯赶来，消费力+50！")
        elif effect == "sam_future":
            for g in self.state.guests:
                g.satisfaction = max(0, g.satisfaction - 10)
            self.state.reputation = min(100, self.state.reputation + 8)
            self._log.append("🤖 Sam讲了半小时AGI！顾客扣10满意度，但声誉+8！")
        elif effect == "zuck_vr":
            for f in self.state.facilities:
                if f.name == "休息厅" and f.closed_turns == 0:
                    f.closed_turns = max(f.closed_turns, 1)
                    self._log.append("🕶️ 休息厅被VR设备占满，停业1回合！")
                    break
            for _ in range(3):
                if "网红博主" in self.state.unlocked_guest_types:
                    self.state.guests.append(Guest("网红博主", GUEST_TYPES["网红博主"]["weight"],
                                                   GUEST_TYPES["网红博主"]["cash"],
                                                   GUEST_TYPES["网红博主"]["difficulty"], 70, 3, 0))
                    self._guest_arrival_counter += 1
                    self.state.total_guests_served += 1
            self._log.append("📱 来了3位科技记者！")
        elif effect == "dario_safety":
            has_issue = any(f.closed_turns > 0 or f.roach for f in self.state.facilities)
            if has_issue:
                self.state.gold -= 80
                if self.state.gold < 0:
                    self.state.gold = 0
                self._log.append("🔒 Dario发现安全隐患！罚款80！")
            else:
                self.state.reputation = min(100, self.state.reputation + 10)
                self._log.append("✅ Dario颁发安全认证，声誉+10！")
        elif effect == "lobster_infest":
            self._lobster_count += 1
            self._log.append("🦞 一只巨大的波士顿龙虾横冲直撞！")
            if random.random() < 0.5:
                targets = [f for f in self.state.facilities if f.closed_turns == 0]
                if targets:
                    target = random.choice(targets)
                    target.closed_turns = 1
                    self._log.append(f"🦞 龙虾夹断了{target.name}的水管，停业1回合！")
                else:
                    self._log.append("🦞 龙虾没找到可破坏的设施，气呼呼地走了。")
            else:
                earn = random.randint(30, 80)
                self.state.gold += earn
                self._log.append(f"🦞 员工抓住了龙虾！卖海鲜赚了{earn}金币！")
                for g in self.state.guests:
                    g.satisfaction = min(100, g.satisfaction + 3)
        elif effect == "lobster_union":
            self.state.gold -= 30
            if self.state.gold < 0:
                self.state.gold = 0
            targets = [f for f in self.state.facilities if f.closed_turns == 0]
            if targets:
                t = random.choice(targets)
                t.closed_turns = max(t.closed_turns, 1)
                self._log.append(f"🦞 龙虾工会霸占了{t.name}！支付30金币赎金，停业1回合！")
            else:
                self._log.append("🦞 龙虾工会没找到设施，气呼呼地走了（但拿了30金币）。")
        elif effect == "lobster_boss":
            self._log.append("🦞 龙虾CEO穿着西装来谈收购！")
            if self.state.reputation > 80:
                self.state.gold += 500
                self._log.append("💼 龙虾CEO很满意！收购价500金币！")
            else:
                self.state.gold -= 100
                if self.state.gold < 0:
                    self.state.gold = 0
                self._log.append("💼 龙虾CEO嫌你声誉太低，扣了100咨询费走了。")

        # 记录季节盈利（用于四季全勤成就）
        if self.state.total_earned > 0:
            if self.state.season not in self.state.seasons_profit:
                self.state.seasons_profit.append(self.state.season)

        self._log.append(f"【事件】{event['desc']}")

    # ---------- 解锁客层 ----------
    def _check_unlocks(self):
        for name, data in GUEST_TYPES.items():
            if name not in self.state.unlocked_guest_types:
                if self.state.popularity > data["unlock_threshold"]:
                    self.state.unlocked_guest_types.append(name)
                    self._log.append(f"✨ 解锁新客层：{name}！")

    # ---------- 成就系统 ----------
    def _check_achievements(self):
        new = []
        s = self.state

        # ----- 基础经营类 -----
        if len(s.facilities) >= 2 and "第一桶金" not in s.unlocked_achievements:
            new.append("第一桶金")
        if len(s.facilities) >= 3 and "小有规模" not in s.unlocked_achievements:
            new.append("小有规模")
        if len(s.facilities) >= 6 and "温泉小镇" not in s.unlocked_achievements:
            new.append("温泉小镇")
        if len(s.facilities) >= 10 and "温泉都市" not in s.unlocked_achievements:
            new.append("温泉都市")
        if len(s.facilities) >= 15 and "百馆之城" not in s.unlocked_achievements:
            new.append("百馆之城")
        if len(set(f.name for f in s.facilities)) >= 8 and "设施全科" not in s.unlocked_achievements:
            new.append("设施全科")
        if sum(f.level for f in s.facilities) >= 20 and "升级狂人" not in s.unlocked_achievements:
            new.append("升级狂人")
        if any(f.level >= 5 for f in s.facilities) and "满级大师" not in s.unlocked_achievements:
            new.append("满级大师")

        if len(s.unlocked_guest_types) >= 3 and "初识贵客" not in s.unlocked_achievements:
            new.append("初识贵客")
        if len(s.unlocked_guest_types) >= 6 and "人声鼎沸" not in s.unlocked_achievements:
            new.append("人声鼎沸")
        if len(s.unlocked_guest_types) >= 9 and "客似云来" not in s.unlocked_achievements:
            new.append("客似云来")
        if len(s.unlocked_guest_types) >= len(GUEST_TYPES) and "集邮大师" not in s.unlocked_achievements:
            new.append("集邮大师")
        if s.total_guests_served >= 100 and "钻石会员" not in s.unlocked_achievements:
            new.append("钻石会员")

        if s.total_earned >= 5000 and "富甲一方" not in s.unlocked_achievements:
            new.append("富甲一方")
        if s.total_earned >= 20000 and "温泉大亨" not in s.unlocked_achievements:
            new.append("温泉大亨")
        if s.total_earned >= 100000 and "亿万温泉" not in s.unlocked_achievements:
            new.append("亿万温泉")
        if s.total_earned >= 100 and "扭亏为盈" not in s.unlocked_achievements:
            new.append("扭亏为盈")

        if self._peaceful_turns >= 10 and "一尘不染" not in s.unlocked_achievements:
            new.append("一尘不染")
        if s.reputation >= 100 and "荣誉殿堂" not in s.unlocked_achievements:
            new.append("荣誉殿堂")
        # 四季全勤：修复，使用 seasons_profit 记录
        if len(s.seasons_profit) >= 4 and "四季全勤" not in s.unlocked_achievements:
            new.append("四季全勤")
        if s.turn >= 50 and "百年老店" not in s.unlocked_achievements:
            new.append("百年老店")

        # ----- AI梗类 -----
        if len([e for e in s.events_triggered if "幻觉爆发" in e]) >= 3 and "幻觉大师" not in s.unlocked_achievements:
            new.append("幻觉大师")
        if len([e for e in s.events_triggered if "提示注入" in e]) >= 2 and "越狱高手" not in s.unlocked_achievements:
            new.append("越狱高手")
        if len([e for e in s.events_triggered if "草莓难题" in e]) >= 3 and "草莓杀手" not in s.unlocked_achievements:
            new.append("草莓杀手")
        if len([e for e in s.events_triggered if "版本回滚" in e]) >= 5 and "祖传代码" not in s.unlocked_achievements:
            new.append("祖传代码")
        if len([e for e in s.events_triggered if "物理穿模" in e]) >= 5 and "穿模之王" not in s.unlocked_achievements:
            new.append("穿模之王")

        # ----- 传奇人物类（修复：使用 legendary_guest_history 按名字判断） -----
        legendary_names = ["埃隆·马斯克", "马克·扎克伯格", "杰夫·贝索斯", "黄仁勋", "比尔·盖茨", "Sam Altman", "Dario Amodei"]
        visited_count = len([name for name in s.legendary_guest_history if name in legendary_names])
        if visited_count >= 5 and "硅谷团建" not in s.unlocked_achievements:
            new.append("硅谷团建")
        if "埃隆·马斯克" in s.legendary_guest_history and s.gold >= 500 and "星舰温泉" not in s.unlocked_achievements:
            new.append("星舰温泉")
        if "Dario Amodei" in s.legendary_guest_history and not any(f.closed_turns > 0 or f.roach for f in s.facilities) and "AI安全认证" not in s.unlocked_achievements:
            new.append("AI安全认证")
        if self._lobster_count >= 3 and "龙虾杀手" not in s.unlocked_achievements:
            new.append("龙虾杀手")
        if s.funding_round >= 3 and "融资高手" not in s.unlocked_achievements:
            new.append("融资高手")
        if "S" in s.season_score_history and "赛季王者" not in s.unlocked_achievements:
            new.append("赛季王者")
        if s.witnessed_aurora and s.reputation >= 80 and "极光猎人" not in s.unlocked_achievements:
            new.append("极光猎人")

        # ----- 隐藏成就 -----
        if s.hidden_wine_event and "偷得浮生半日闲" not in s.unlocked_achievements:
            new.append("偷得浮生半日闲")
        if s.wallet_return_count >= 3 and "拾金不昧" not in s.unlocked_achievements:
            new.append("拾金不昧")
        if s.wallet_keep_count >= 5 and "黑心老板" not in s.unlocked_achievements:
            new.append("黑心老板")
        if self._water_scandal_phase >= 2 and "公关稿" in s.items and "危机公关" not in s.unlocked_achievements:
            new.append("危机公关")
        # 千人千面：同时接待3位大佬（检测当前客人中传奇人物数量）
        current_legendary = [g.name for g in s.guests if g.name in legendary_names]
        if len(current_legendary) >= 3 and "千人千面" not in s.unlocked_achievements:
            new.append("千人千面")
        if "热浪" in s.weather_history and "寒流" in s.weather_history and "冰火两重天" not in s.unlocked_achievements:
            new.append("冰火两重天")

        # ----- 新增联动成就（修复：四季如春使用 weather_history） -----
        if "雷暴" in s.events_triggered and not any(f.closed_turns > 0 for f in s.facilities) and "避雷针" not in s.unlocked_achievements:
            new.append("避雷针")
        if "热浪" in s.events_triggered and "寒流" in s.events_triggered and s.total_earned > 200 and "弄潮儿" not in s.unlocked_achievements:
            new.append("弄潮儿")
        if len([e for e in s.events_triggered if "烟花表演" in e]) >= 3 and "烟花记忆" not in s.unlocked_achievements:
            new.append("烟花记忆")
        if len([e for e in s.events_triggered if "回头客" in e]) >= 5 and "忠实粉丝" not in s.unlocked_achievements:
            new.append("忠实粉丝")
        if len([e for e in s.events_triggered if "公司团建" in e]) >= 3 and "团建专家" not in s.unlocked_achievements:
            new.append("团建专家")
        if len([e for e in s.events_triggered if "投资回报" in e]) >= 2 and len([e for e in s.events_triggered if "保险理赔" in e]) >= 2 and "理财能手" not in s.unlocked_achievements:
            new.append("理财能手")
        if "顾客投诉" in s.events_triggered and "顾客表扬" in s.events_triggered and "化险为夷" not in s.unlocked_achievements:
            new.append("化险为夷")
        # 四季如春：修复，用 weather_history 记录过的天气数
        if len(s.weather_history) >= 6 and "四季如春" not in s.unlocked_achievements:
            new.append("四季如春")
        if "安全检查" in s.events_triggered and not any(f.closed_turns > 0 for f in s.facilities) and "完美运营" not in s.unlocked_achievements:
            new.append("完美运营")
        if len(set(s.events_triggered)) >= 30 and "百变温泉" not in s.unlocked_achievements:
            new.append("百变温泉")

        # ----- 解锁成就 -----
        if new:
            emoji_map = {
                "第一桶金": "🪙", "小有规模": "🏗️", "温泉小镇": "🏘️", "温泉都市": "🏙️", "百馆之城": "🏛️",
                "设施全科": "🔄", "升级狂人": "⬆️", "满级大师": "⬆️⬆️",
                "初识贵客": "👤", "人声鼎沸": "👥", "客似云来": "👨‍👩‍👧‍👦", "集邮大师": "🌟", "钻石会员": "💎",
                "富甲一方": "💰", "温泉大亨": "💎", "亿万温泉": "👑", "扭亏为盈": "📈",
                "一尘不染": "🧹", "荣誉殿堂": "🏅", "四季全勤": "🎪", "百年老店": "⏳",
                "幻觉大师": "🌀", "越狱高手": "🔓", "草莓杀手": "🍓", "祖传代码": "🐙", "穿模之王": "🎥",
                "硅谷团建": "🏢", "星舰温泉": "🚀", "AI安全认证": "🔒", "龙虾杀手": "🦞",
                "融资高手": "💵", "赛季王者": "👑", "极光猎人": "🌌",
                "偷得浮生半日闲": "🍶", "拾金不昧": "🤝", "黑心老板": "😈", "危机公关": "📰",
                "千人千面": "🎭", "冰火两重天": "🧊",
                "避雷针": "⚡", "弄潮儿": "🌊", "烟花记忆": "🎆", "忠实粉丝": "🔄",
                "团建专家": "🏢", "理财能手": "📊", "化险为夷": "🧠",
                "四季如春": "❄️", "完美运营": "🧹", "百变温泉": "🎭",
            }
            for ach in new:
                emoji = emoji_map.get(ach, "🎖️")
                s.unlocked_achievements.append(ach)
                self._log.append(f"🎉 成就：{emoji} {ach}！")

        # 更新平安回合计数
        recent = s.events_triggered[-5:]
        negative_events = {
            "熊孩子尿尿", "吃霸王餐", "消防检查", "蟑螂出没", "染发剂掉色",
            "厕所没冲", "水质浑浊", "沐浴露被偷", "过敏投诉", "设施故障",
            "停电", "水管爆裂", "水质异味", "水管接错", "新闻曝光",
        }
        neg = [e for e in recent if e in negative_events]
        if not neg:
            self._peaceful_turns += 1
        else:
            self._peaceful_turns = 0


# ============ UI ============

def print_state(state: dict):
    print("\n" + "=" * 50)
    print(f"🏮 {state['turn']} | 💰{state['gold']} | ❤️{state['popularity']} | 📢{state['reputation']} | 🌸{state['season']} | 🌤️{state['weather']}")
    if state.get('funding_active'):
        print(f"💸 融资：{state['funding_target']}金币，剩{state['funding_deadline']}回合")
    fac_str = [f"{f['name']}Lv{f['level']}" + ("🔴" if f['closed'] else "") + ("🪳" if f.get('roach') else "") for f in state['facilities'][:3]]
    print(f"🏗️ 设施: {fac_str}{'...' if len(state['facilities']) > 3 else ''}")
    guest_str = [f"{g['name']}({g['satisfaction']})" for g in state['guests'][:3]]
    print(f"👥 顾客: {guest_str}{'...' if len(state['guests']) > 3 else ''}")
    if state.get('tips'):
        print(f"💡 {state['tips'][0]}")
    if state.get('log') and state['log']:
        print(f"📜 {state['log'][-1]}")
    print("=" * 50)


def main():
    try:
        game = HotSpringGame(load_from_file=True)
    except:
        game = HotSpringGame(load_from_file=False)

    print(f"🏮 欢迎来到 {GAME_NAME} 🏮")
    print("指令: 1建 2升 3买 4用 5还 6私 7等 | save存档 | load读档 | ai自动玩")
    print("  🌟 隐藏彩蛋：台风/暴风雪天连续等待2次触发'围炉温酒'")

    for _ in range(200):
        state = game.get_state()
        print_state(state)

        try:
            cmd = input("👉 ").strip().lower()
            if cmd == "1":
                print("可选:", list(FACILITY_TYPES.keys()))
                name = input("设施名: ")
                if name:
                    result = game.act({"action": "build", "facility": name})
                    print("结果:", result['action_result']['message'])
            elif cmd == "2":
                facs = [f['name'] for f in state['facilities']]
                print("已有:", list(set(facs)))
                name = input("升级哪个: ")
                if name:
                    result = game.act({"action": "upgrade", "facility": name})
                    print("结果:", result['action_result']['message'])
            elif cmd == "3":
                print("商店:", [(k, v['price']) for k, v in SHOP_ITEMS.items()])
                name = input("买哪个: ")
                if name:
                    result = game.act({"action": "buy_item", "item": name})
                    print("结果:", result['action_result']['message'])
            elif cmd == "4":
                print("道具:", state['items'])
                name = input("用哪个: ")
                if name:
                    result = game.act({"action": "use_item", "item": name})
                    print("结果:", result['action_result']['message'])
            elif cmd == "5":
                result = game.act({"action": "return_wallet"})
                print("结果:", result['action_result']['message'])
            elif cmd == "6":
                result = game.act({"action": "keep_wallet"})
                print("结果:", result['action_result']['message'])
            elif cmd == "save":
                game._save_game()
            elif cmd == "load":
                game = HotSpringGame(load_from_file=True)
            elif cmd == "ai":
                # 简易AI策略
                if "杀虫剂" in state['items'] and any(f.get('roach') for f in state['facilities']):
                    result = game.act({"action": "use_item", "item": "杀虫剂"})
                elif state['gold'] > 150 and len(state['facilities']) < 6:
                    to_build = random.choice(list(FACILITY_TYPES.keys()))
                    result = game.act({"action": "build", "facility": to_build})
                elif any(f.get('roach') for f in state['facilities']) and state['gold'] > 40:
                    result = game.act({"action": "buy_item", "item": "杀虫剂"})
                elif state['gold'] < 100 and state['reputation'] < 60 and state['gold'] > 60:
                    result = game.act({"action": "buy_item", "item": "公关稿"})
                elif state.get('funding_active') and state['gold'] < state['funding_target'] * 0.6:
                    if state['gold'] > 100:
                        to_build = random.choice(list(FACILITY_TYPES.keys()))
                        result = game.act({"action": "build", "facility": to_build})
                    else:
                        result = game.act({"action": "wait"})
                else:
                    result = game.act({"action": "wait"})
                print("AI决策:", result['action_result']['message'])
            else:
                result = game.act({"action": "wait"})
        except Exception as e:
            print("⚠️ 输入有误，跳过本回合:", e)
            result = game.act({"action": "wait"})

        time.sleep(0.3)

    print("\n🎮 游戏结束！最终状态：")
    print(json.dumps(game.get_state(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
