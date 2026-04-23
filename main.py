from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import random
import json
import os
import math
from datetime import datetime, date
from enum import Enum

app = FastAPI(title="时节食匣 - 二十四节气盲盒抽卡", description="结合盲盒抽卡与二十四节气文化的时令套餐随机生成器")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

DISHES_DATA = None
SOLAR_TERMS_DATA = None
NUTRITION_DATA = None
USER_RECORDS = []
USER_PREFERENCES = None
GAME_BADGES = []
GAME_HISTORY = []

EXCLUDED_INGREDIENTS_CATEGORY = {
    "cilantro": {"name": "香菜", "keywords": ["香菜", "芫荽"]},
    "offal": {"name": "内脏", "keywords": ["肝", "肚", "肠", "肺", "心", "腰", "肾", "内脏", "下水"]},
    "spicy": {"name": "辛辣", "keywords": ["辣椒", "麻辣", "辣", "花椒"]},
    "seafood": {"name": "海鲜", "keywords": ["虾", "蟹", "鱼", "海鲜", "贝", "螺", "鱿"]},
    "mushroom": {"name": "菌类", "keywords": ["菇", "菌", "蘑菇", "香菇", "木耳"]},
    "egg": {"name": "蛋类", "keywords": ["蛋", "鸡蛋", "鸭蛋", "鹅蛋"]},
    "milk": {"name": "奶制品", "keywords": ["奶", "牛奶", "酸奶", "奶酪"]},
    "nuts": {"name": "坚果", "keywords": ["核桃", "栗子", "花生", "杏仁", "腰果"]}
}

REASON_TEMPLATES = {
    "spring": [
        "今日{term}，春回大地，宜{action}",
        "春风拂面，{term}时节，适合{action}",
        "万物复苏的{term}，正是{action}的好时机",
        "{term}到了，春意盎然，宜{action}",
        "在这{term}时节，让我们{action}"
    ],
    "summer": [
        "今日{term}，炎炎夏日，宜{action}",
        "夏日炎炎，{term}时节，适合{action}",
        "盛夏光年的{term}，正是{action}的好时机",
        "{term}到了，暑气逼人，宜{action}",
        "在这{term}时节，让我们{action}"
    ],
    "autumn": [
        "今日{term}，秋高气爽，宜{action}",
        "秋风送爽，{term}时节，适合{action}",
        "硕果累累的{term}，正是{action}的好时机",
        "{term}到了，丹桂飘香，宜{action}",
        "在这{term}时节，让我们{action}"
    ],
    "winter": [
        "今日{term}，寒风凛冽，宜{action}",
        "冬日暖阳，{term}时节，适合{action}",
        "银装素裹的{term}，正是{action}的好时机",
        "{term}到了，天寒地冻，宜{action}",
        "在这{term}时节，让我们{action}"
    ]
}

ACTION_WORDS = {
    "spring": [
        "温补阳气", "养肝护脾", "生发阳气", "调畅情志", "舒展筋骨",
        "吃春芽", "尝春鲜", "品春味", "迎春纳福", "咬春"
    ],
    "summer": [
        "清热解暑", "养心安神", "健脾祛湿", "消夏避暑", "生津止渴",
        "吃凉面", "喝绿豆汤", "尝夏鲜", "消夏解暑", "清补"
    ],
    "autumn": [
        "滋阴润燥", "养肺生津", "贴秋膘", "收敛肺气", "防燥护阴",
        "贴秋膘", "尝秋鲜", "品秋味", "养阴润肺", "润燥"
    ],
    "winter": [
        "温补御寒", "养肾藏精", "进补养生", "暖心暖胃", "驱寒暖身",
        "冬令进补", "尝冬鲜", "品冬味", "温阳散寒", "补肾"
    ]
}

DISH_REASON_PREFIXES = [
    "今天为您推荐", "今日精选", "特别推荐", "时令优选", "养生佳品",
    "舌尖上的", "温暖您的", "治愈系", "暖心推荐", "应季美食"
]

DISH_REASON_SUFFIXES = [
    "，愿您用餐愉快！", "，祝您胃口大开！", "，愿您享受美食时光！",
    "，为您的餐桌添彩！", "，温暖您的胃！", "，治愈您的选择困难症！"
]

def generate_random_reason(season: str, term_name: str = None, dish_name: str = None) -> Dict[str, str]:
    if term_name is None:
        term_name = get_current_solar_term().get("name", "")
    
    templates = REASON_TEMPLATES.get(season, REASON_TEMPLATES["spring"])
    actions = ACTION_WORDS.get(season, ACTION_WORDS["spring"])
    
    template = random.choice(templates)
    action = random.choice(actions)
    
    season_reason = template.format(term=term_name, action=action)
    
    dish_reason = ""
    if dish_name:
        prefix = random.choice(DISH_REASON_PREFIXES)
        suffix = random.choice(DISH_REASON_SUFFIXES)
        dish_reason = f"{prefix}「{dish_name}」{suffix}"
    
    return {
        "season_reason": season_reason,
        "dish_reason": dish_reason,
        "full_reason": f"{season_reason}。{dish_reason}" if dish_reason else season_reason
    }

def get_dishes_data():
    global DISHES_DATA
    if DISHES_DATA is None:
        data_path = os.path.join(DATA_DIR, "dishes.json")
        with open(data_path, "r", encoding="utf-8") as f:
            DISHES_DATA = json.load(f)
    return DISHES_DATA

def get_solar_terms_data():
    global SOLAR_TERMS_DATA
    if SOLAR_TERMS_DATA is None:
        data_path = os.path.join(DATA_DIR, "solar_terms_detail.json")
        with open(data_path, "r", encoding="utf-8") as f:
            SOLAR_TERMS_DATA = json.load(f)
    return SOLAR_TERMS_DATA

def get_nutrition_data():
    global NUTRITION_DATA
    if NUTRITION_DATA is None:
        data_path = os.path.join(DATA_DIR, "nutrition_data.json")
        with open(data_path, "r", encoding="utf-8") as f:
            NUTRITION_DATA = json.load(f)
    return NUTRITION_DATA

class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

class PackageType(str, Enum):
    BASIC = "basic"
    LUXURY = "luxury"

class DishType(str, Enum):
    MEAT = "meats"
    VEGETABLE = "vegetables"
    SOUP = "soups"
    STAPLE = "staples"

class Dish(BaseModel):
    id: str
    name: str
    desc: str
    image_hint: str
    dish_type: DishType
    is_locked: bool = False

class Package(BaseModel):
    season: Season
    season_name: str
    season_desc: str
    package_type: PackageType
    meats: List[Dish]
    vegetables: List[Dish]
    soups: List[Dish]
    staples: List[Dish]
    created_at: datetime

class Location(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    region: str
    region_name: str
    current_solar_term: str
    current_season: str
    timezone: str

class DietaryRecordItem(BaseModel):
    food_name: str
    food_category: str
    quantity: float
    unit: str
    meal_type: str

class DietaryRecord(BaseModel):
    id: Optional[str] = None
    date: str
    user_id: Optional[str] = None
    items: List[DietaryRecordItem]
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class HealthScore(BaseModel):
    overall_score: float
    score_level: str
    seasonal_health: float
    nutritional_balance: float
    tcm_harmony: float
    dietary_diversity: float
    advice: List[str]
    strengths: List[str]
    improvements: List[str]

class ShareCardRequest(BaseModel):
    package: Optional[Dict[str, Any]] = None
    record_id: Optional[str] = None
    card_type: str
    theme: Optional[str] = None

class DrawMode(str, Enum):
    RANDOM = "random"
    PERSONALIZED = "personalized"

class UserPreferences(BaseModel):
    user_id: Optional[str] = None
    excluded_categories: List[str] = []
    taste_preference: Optional[str] = None
    dietary_restrictions: List[str] = []
    constitution_type: Optional[str] = None
    updated_at: Optional[datetime] = None

class GameResult(BaseModel):
    game_type: str
    score: int
    level: Optional[int] = None
    earned_badges: List[str] = []
    completed_at: datetime
    solar_term: Optional[str] = None

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    unlocked_at: Optional[datetime] = None
    game_type: str
    requirements: str

def get_user_preferences() -> UserPreferences:
    global USER_PREFERENCES
    if USER_PREFERENCES is None:
        USER_PREFERENCES = UserPreferences(
            excluded_categories=[],
            taste_preference="balanced",
            dietary_restrictions=[],
            constitution_type="balanced"
        )
    return USER_PREFERENCES

def save_user_preferences(preferences: UserPreferences) -> UserPreferences:
    global USER_PREFERENCES
    preferences.updated_at = datetime.now()
    USER_PREFERENCES = preferences
    return USER_PREFERENCES

def is_dish_excluded(dish: Dict, preferences: UserPreferences) -> bool:
    if not preferences.excluded_categories:
        return False
    
    dish_name = dish.get("name", "")
    dish_desc = dish.get("desc", "")
    combined_text = f"{dish_name} {dish_desc}"
    
    for category_key in preferences.excluded_categories:
        category = EXCLUDED_INGREDIENTS_CATEGORY.get(category_key)
        if category:
            for keyword in category["keywords"]:
                if keyword in combined_text:
                    return True
    return False

def filter_dishes_by_preferences(dishes: List[Dict], preferences: UserPreferences) -> List[Dict]:
    filtered = [d for d in dishes if not is_dish_excluded(d, preferences)]
    return filtered if filtered else dishes

def analyze_user_preferences(records: List[DietaryRecord]) -> Dict[str, Any]:
    if not records:
        return {
            "favorite_categories": [],
            "food_frequency": {},
            "meal_patterns": {}
        }
    
    category_count = {}
    food_count = {}
    meal_type_count = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    
    for record in records:
        for item in record.items:
            category = item.food_category
            food_name = item.food_name
            meal_type = item.meal_type
            
            category_count[category] = category_count.get(category, 0) + 1
            food_count[food_name] = food_count.get(food_name, 0) + 1
            if meal_type in meal_type_count:
                meal_type_count[meal_type] += 1
    
    sorted_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)
    sorted_foods = sorted(food_count.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "favorite_categories": [cat[0] for cat in sorted_categories[:3]],
        "food_frequency": {food: count for food, count in sorted_foods[:10]},
        "meal_patterns": meal_type_count,
        "total_records": len(records)
    }

def calculate_dish_recommendation_score(
    dish: Dict,
    dish_type: DishType,
    user_analysis: Dict[str, Any],
    preferences: UserPreferences,
    health_score: Optional[HealthScore],
    season: Season
) -> float:
    score = 50.0
    
    if health_score:
        seasonal_health = health_score.seasonal_health or 60.0
        if seasonal_health < 70:
            score += 5.0
    
    favorite_categories = user_analysis.get("favorite_categories", [])
    dish_type_map = {
        DishType.MEAT: "meat",
        DishType.VEGETABLE: "vegetable",
        DishType.SOUP: "soup",
        DishType.STAPLE: "staple"
    }
    current_type = dish_type_map.get(dish_type, "")
    if current_type in favorite_categories:
        score += 10.0
    
    food_frequency = user_analysis.get("food_frequency", {})
    dish_name = dish.get("name", "")
    dish_desc = dish.get("desc", "")
    combined_text = f"{dish_name} {dish_desc}"
    
    for food, count in food_frequency.items():
        if food in combined_text and count >= 2:
            score += 8.0
            break
    
    season_keywords = {
        Season.SPRING: ["春", "韭", "笋", "香椿", "荠菜", "芦"],
        Season.SUMMER: ["夏", "苦", "瓜", "冬瓜", "绿豆", "凉"],
        Season.AUTUMN: ["秋", "栗", "藕", "梨", "银耳", "百合", "柿"],
        Season.WINTER: ["冬", "羊", "萝卜", "白菜", "饺", "腊"]
    }
    
    keywords = season_keywords.get(season, [])
    for keyword in keywords:
        if keyword in combined_text:
            score += 5.0
            break
    
    taste_preference = preferences.taste_preference
    if taste_preference == "light":
        if "清炒" in combined_text or "凉拌" in combined_text or "蒸" in combined_text:
            score += 5.0
    elif taste_preference == "rich":
        if "红烧" in combined_text or "焖" in combined_text or "烧" in combined_text:
            score += 5.0
    
    score += random.uniform(-5.0, 10.0)
    
    return max(0.0, min(100.0, score))

def select_recommended_dish(
    dishes: List[Dict],
    dish_type: DishType,
    exclude_ids: List[str] = None,
    preferences: Optional[UserPreferences] = None,
    health_score: Optional[HealthScore] = None,
    season: Optional[Season] = None
) -> Dish:
    if exclude_ids is None:
        exclude_ids = []
    
    if preferences is None:
        preferences = get_user_preferences()
    
    if season is None:
        season = get_current_season()
    
    filtered_dishes = filter_dishes_by_preferences(dishes, preferences)
    available = [d for d in filtered_dishes if d["id"] not in exclude_ids]
    
    if not available:
        available = [d for d in dishes if d["id"] not in exclude_ids]
    if not available:
        available = dishes
    
    global USER_RECORDS
    user_analysis = analyze_user_preferences(USER_RECORDS)
    
    scored_dishes = []
    for dish in available:
        score = calculate_dish_recommendation_score(
            dish, dish_type, user_analysis, preferences, health_score, season
        )
        scored_dishes.append((dish, score))
    
    scored_dishes.sort(key=lambda x: x[1], reverse=True)
    
    top_count = min(3, len(scored_dishes))
    if top_count > 0:
        selected = random.choice(scored_dishes[:top_count])[0]
    else:
        selected = random.choice(available)
    
    return Dish(
        id=selected["id"],
        name=selected["name"],
        desc=selected["desc"],
        image_hint=selected["image_hint"],
        dish_type=dish_type,
        is_locked=False
    )

def generate_recommended_package(
    season: Season,
    package_type: PackageType,
    preferences: Optional[UserPreferences] = None,
    health_score: Optional[HealthScore] = None
) -> Package:
    season_data = get_season_dishes(season)
    
    if preferences is None:
        preferences = get_user_preferences()
    
    meats_count = 2 if package_type == PackageType.LUXURY else 1
    meats = []
    meat_ids = []
    for _ in range(meats_count):
        meat = select_recommended_dish(
            season_data["meats"], DishType.MEAT, meat_ids, preferences, health_score, season
        )
        meats.append(meat)
        meat_ids.append(meat.id)
    
    vegetable = select_recommended_dish(
        season_data["vegetables"], DishType.VEGETABLE, preferences=preferences, health_score=health_score, season=season
    )
    soup = select_recommended_dish(
        season_data["soups"], DishType.SOUP, preferences=preferences, health_score=health_score, season=season
    )
    staple = select_recommended_dish(
        season_data["staples"], DishType.STAPLE, preferences=preferences, health_score=health_score, season=season
    )
    
    return Package(
        season=season,
        season_name=season_data["season_name"],
        season_desc=season_data["season_desc"],
        package_type=package_type,
        meats=meats,
        vegetables=[vegetable],
        soups=[soup],
        staples=[staple],
        created_at=datetime.now()
    )

def get_current_season() -> Season:
    month = datetime.now().month
    if month in [3, 4, 5]:
        return Season.SPRING
    elif month in [6, 7, 8]:
        return Season.SUMMER
    elif month in [9, 10, 11]:
        return Season.AUTUMN
    else:
        return Season.WINTER

def get_season_dishes(season: Season) -> Dict[str, Any]:
    data = get_dishes_data()
    return data["solar_terms"][season.value]

def select_random_dish(dishes: List[Dict], dish_type: DishType, exclude_ids: List[str] = None) -> Dish:
    if exclude_ids is None:
        exclude_ids = []
    
    available = [d for d in dishes if d["id"] not in exclude_ids]
    if not available:
        available = dishes
    
    selected = random.choice(available)
    return Dish(
        id=selected["id"],
        name=selected["name"],
        desc=selected["desc"],
        image_hint=selected["image_hint"],
        dish_type=dish_type,
        is_locked=False
    )

def generate_package(season: Season, package_type: PackageType) -> Package:
    season_data = get_season_dishes(season)
    
    meats_count = 2 if package_type == PackageType.LUXURY else 1
    meats = []
    meat_ids = []
    for _ in range(meats_count):
        meat = select_random_dish(season_data["meats"], DishType.MEAT, meat_ids)
        meats.append(meat)
        meat_ids.append(meat.id)
    
    vegetable = select_random_dish(season_data["vegetables"], DishType.VEGETABLE)
    soup = select_random_dish(season_data["soups"], DishType.SOUP)
    staple = select_random_dish(season_data["staples"], DishType.STAPLE)
    
    return Package(
        season=season,
        season_name=season_data["season_name"],
        season_desc=season_data["season_desc"],
        package_type=package_type,
        meats=meats,
        vegetables=[vegetable],
        soups=[soup],
        staples=[staple],
        created_at=datetime.now()
    )

SOLAR_TERMS_ORDER = [
    ("lichun", "立春", 2, 4),
    ("yushui", "雨水", 2, 19),
    ("jingzhe", "惊蛰", 3, 6),
    ("chunfen", "春分", 3, 21),
    ("qingming", "清明", 4, 5),
    ("guyu", "谷雨", 4, 20),
    ("lixia", "立夏", 5, 6),
    ("xiaoman", "小满", 5, 21),
    ("mangzhong", "芒种", 6, 6),
    ("xiazhi", "夏至", 6, 22),
    ("xiaoshu", "小暑", 7, 7),
    ("dashu", "大暑", 7, 23),
    ("liqiu", "立秋", 8, 8),
    ("chushu", "处暑", 8, 23),
    ("bailu", "白露", 9, 8),
    ("qiufen", "秋分", 9, 23),
    ("hanlu", "寒露", 10, 8),
    ("shuangjiang", "霜降", 10, 24),
    ("lidong", "立冬", 11, 8),
    ("xiaoxue", "小雪", 11, 22),
    ("daxue", "大雪", 12, 7),
    ("dongzhi", "冬至", 12, 22),
    ("xiaohan", "小寒", 1, 6),
    ("dahan", "大寒", 1, 20),
]

def get_current_solar_term() -> Dict[str, str]:
    today = datetime.now()
    current_month = today.month
    current_day = today.day
    
    for i, (term_key, term_name, month, day) in enumerate(SOLAR_TERMS_ORDER):
        prev_i = (i - 1) % len(SOLAR_TERMS_ORDER)
        prev_term = SOLAR_TERMS_ORDER[prev_i]
        
        if (month == current_month and current_day >= day) or \
           (month == current_month + 1 and current_day < day):
            return {
                "key": term_key,
                "name": term_name,
                "date": f"{month}月{day}日"
            }
        
        if month > current_month or (month == current_month and day > current_day):
            return {
                "key": prev_term[0],
                "name": prev_term[1],
                "date": f"{prev_term[2]}月{prev_term[3]}日"
            }
    
    return {
        "key": "lichun",
        "name": "立春",
        "date": "2月4日"
    }

def get_region_by_coordinates(latitude: float, longitude: float) -> Dict[str, str]:
    if longitude >= 118.0 and latitude >= 32.0:
        return {"region": "north", "name": "北方地区"}
    elif longitude >= 110.0 and latitude < 32.0:
        return {"region": "east", "name": "华东地区"}
    elif longitude < 110.0 and latitude >= 25.0:
        return {"region": "west", "name": "西南地区"}
    else:
        return {"region": "south", "name": "南方地区"}

def calculate_health_score(records: List[DietaryRecord], current_season: str) -> HealthScore:
    seasonal_health = calculate_seasonal_health(records, current_season)
    nutritional_balance = calculate_nutritional_balance(records)
    tcm_harmony = calculate_tcm_harmony(records, current_season)
    dietary_diversity = calculate_dietary_diversity(records)
    
    overall_score = (
        seasonal_health * 0.3 +
        nutritional_balance * 0.3 +
        tcm_harmony * 0.25 +
        dietary_diversity * 0.15
    )
    
    score_level = get_score_level(overall_score)
    advice = generate_advice(overall_score, seasonal_health, nutritional_balance, tcm_harmony, dietary_diversity, current_season)
    strengths = generate_strengths(seasonal_health, nutritional_balance, tcm_harmony, dietary_diversity)
    improvements = generate_improvements(seasonal_health, nutritional_balance, tcm_harmony, dietary_diversity)
    
    return HealthScore(
        overall_score=round(overall_score, 1),
        score_level=score_level,
        seasonal_health=round(seasonal_health, 1),
        nutritional_balance=round(nutritional_balance, 1),
        tcm_harmony=round(tcm_harmony, 1),
        dietary_diversity=round(dietary_diversity, 1),
        advice=advice,
        strengths=strengths,
        improvements=improvements
    )

def calculate_seasonal_health(records: List[DietaryRecord], current_season: str) -> float:
    if not records:
        return 60.0
    
    seasonal_foods = {
        "spring": ["韭菜", "春笋", "香椿", "菠菜", "荠菜", "红枣", "蜂蜜"],
        "summer": ["苦瓜", "冬瓜", "西瓜", "绿豆", "薏米", "黄瓜", "番茄"],
        "autumn": ["梨", "银耳", "百合", "蜂蜜", "杏仁", "葡萄", "石榴"],
        "winter": ["羊肉", "牛肉", "栗子", "核桃", "红枣", "桂圆", "生姜"]
    }
    
    current_foods = seasonal_foods.get(current_season, [])
    seasonal_count = 0
    total_count = 0
    
    for record in records:
        for item in record.items:
            total_count += 1
            for seasonal_food in current_foods:
                if seasonal_food in item.food_name:
                    seasonal_count += 1
                    break
    
    if total_count == 0:
        return 60.0
    
    ratio = seasonal_count / total_count
    return 50 + ratio * 50

def calculate_nutritional_balance(records: List[DietaryRecord]) -> float:
    if not records:
        return 60.0
    
    categories = {"vegetable": 0, "meat": 0, "staple": 0, "soup": 0, "fruit": 0}
    
    for record in records:
        for item in record.items:
            category = item.food_category.lower()
            if category in categories:
                categories[category] += 1
            elif "蔬菜" in category or "素菜" in category:
                categories["vegetable"] += 1
            elif "肉类" in category or "荤菜" in category:
                categories["meat"] += 1
            elif "主食" in category:
                categories["staple"] += 1
            elif "汤品" in category or "汤" in category:
                categories["soup"] += 1
            elif "水果" in category:
                categories["fruit"] += 1
    
    non_zero = sum(1 for v in categories.values() if v > 0)
    balance_score = (non_zero / 5) * 100
    
    return min(balance_score + 10, 100)

def calculate_tcm_harmony(records: List[DietaryRecord], current_season: str) -> float:
    if not records:
        return 60.0
    
    seasonal_nature = {
        "spring": "温",
        "summer": "凉",
        "autumn": "平",
        "winter": "温"
    }
    
    target_nature = seasonal_nature.get(current_season, "平")
    
    food_natures = {
        "韭菜": "温", "羊肉": "温", "牛肉": "平", "生姜": "热",
        "苦瓜": "寒", "冬瓜": "凉", "西瓜": "寒", "绿豆": "凉",
        "梨": "凉", "银耳": "平", "百合": "寒", "蜂蜜": "平",
        "栗子": "温", "核桃": "温", "红枣": "温", "桂圆": "温"
    }
    
    harmony_count = 0
    total_count = 0
    
    for record in records:
        for item in record.items:
            total_count += 1
            food_name = item.food_name
            for key_food, nature in food_natures.items():
                if key_food in food_name:
                    if nature == target_nature or nature == "平":
                        harmony_count += 1
                    break
    
    if total_count == 0:
        return 60.0
    
    return 50 + (harmony_count / total_count) * 50

def calculate_dietary_diversity(records: List[DietaryRecord]) -> float:
    if not records:
        return 50.0
    
    unique_foods = set()
    
    for record in records:
        for item in record.items:
            unique_foods.add(item.food_name)
    
    diversity_score = min(len(unique_foods) * 10, 100)
    
    return max(diversity_score, 40)

def get_score_level(score: float) -> str:
    if score >= 85:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"

def generate_advice(overall: float, seasonal: float, nutritional: float, tcm: float, diversity: float, season: str) -> List[str]:
    advice = []
    
    season_names = {
        "spring": "春季",
        "summer": "夏季",
        "autumn": "秋季",
        "winter": "冬季"
    }
    
    if seasonal < 70:
        advice.append(f"建议多食用{season_names.get(season, '当季')}时令食材，如：")
        if season == "spring":
            advice.append("  韭菜、春笋、香椿、菠菜等")
        elif season == "summer":
            advice.append("  苦瓜、冬瓜、西瓜、绿豆等")
        elif season == "autumn":
            advice.append("  梨、银耳、百合、蜂蜜等")
        else:
            advice.append("  羊肉、牛肉、栗子、红枣等")
    
    if nutritional < 70:
        advice.append("建议保持饮食均衡，确保摄入各类营养素")
        advice.append("  每餐应包含主食、蔬菜、蛋白质类食物")
    
    if tcm < 70:
        advice.append("建议根据中医养生原则调整饮食")
        advice.append(f"  {season_names.get(season, '当前')}宜选择性味平和或温补的食物")
    
    if diversity < 70:
        advice.append("建议增加食物种类，丰富饮食多样性")
        advice.append("  尝试不同种类的蔬菜、水果和主食")
    
    if not advice:
        advice.append("您的饮食习惯很好！继续保持均衡的季节性饮食")
        advice.append("  定期检查身体状况，根据需要调整饮食")
    
    return advice

def generate_strengths(seasonal: float, nutritional: float, tcm: float, diversity: float) -> List[str]:
    strengths = []
    
    if seasonal >= 70:
        strengths.append("时令饮食意识强，能根据季节选择合适的食材")
    
    if nutritional >= 70:
        strengths.append("营养搭配均衡，能确保各类营养素的摄入")
    
    if tcm >= 70:
        strengths.append("中医调和度高，饮食符合阴阳平衡原则")
    
    if diversity >= 70:
        strengths.append("食物种类丰富，饮食多样性良好")
    
    if not strengths:
        strengths.append("继续努力，逐步改善饮食习惯")
    
    return strengths

def generate_improvements(seasonal: float, nutritional: float, tcm: float, diversity: float) -> List[str]:
    improvements = []
    
    if seasonal < 70:
        improvements.append("增加时令食材的摄入")
    
    if nutritional < 70:
        improvements.append("改善营养搭配均衡度")
    
    if tcm < 70:
        improvements.append("调整饮食以符合中医养生原则")
    
    if diversity < 70:
        improvements.append("丰富食物种类多样性")
    
    if not improvements:
        improvements.append("保持当前良好的饮食习惯")
    
    return improvements

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/season")
async def get_season_info():
    season = get_current_season()
    season_data = get_season_dishes(season)
    
    return JSONResponse(content={
        "season": season.value,
        "season_name": season_data["season_name"],
        "season_desc": season_data["season_desc"],
        "solar_terms": season_data["terms"]
    })

@app.post("/api/draw")
async def draw_package(
    package_type: PackageType = Query(default=PackageType.BASIC, description="套餐类型: basic(1荤1素1汤1主食) 或 luxury(2荤1素1汤)"),
    season: Optional[Season] = Query(default=None, description="指定季节，不指定则使用当前季节"),
    draw_mode: DrawMode = Query(default=DrawMode.PERSONALIZED, description="抽取模式: random(纯随机) 或 personalized(个性化推荐)")
):
    if season is None:
        season = get_current_season()
    
    preferences = get_user_preferences()
    
    if draw_mode == DrawMode.PERSONALIZED:
        package = generate_recommended_package(season, package_type, preferences)
    else:
        package = generate_package(season, package_type)
    
    current_term = get_current_solar_term()
    
    all_dishes = []
    all_dishes.extend(package.meats)
    all_dishes.extend(package.vegetables)
    all_dishes.extend(package.soups)
    all_dishes.extend(package.staples)
    
    main_dish = random.choice(all_dishes) if all_dishes else None
    main_dish_name = main_dish.name if main_dish else None
    
    reason = generate_random_reason(
        season.value,
        current_term.get("name", ""),
        main_dish_name
    )
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "season": package.season.value,
            "season_name": package.season_name,
            "season_desc": package.season_desc,
            "package_type": package.package_type.value,
            "draw_mode": draw_mode.value,
            "meats": [m.model_dump() for m in package.meats],
            "vegetables": [v.model_dump() for v in package.vegetables],
            "soups": [s.model_dump() for s in package.soups],
            "staples": [st.model_dump() for st in package.staples],
            "created_at": package.created_at.isoformat(),
            "reason": reason,
            "current_solar_term": current_term.get("name", "")
        }
    })

@app.post("/api/redraw")
async def redraw_dish(
    dish_type: DishType = Query(..., description="要重抽的菜品类型"),
    season: Season = Query(..., description="季节"),
    exclude_ids: List[str] = Query(default=[], description="要排除的菜品ID列表"),
    current_ids: List[str] = Query(default=[], description="当前已选的同类型菜品ID"),
    draw_mode: DrawMode = Query(default=DrawMode.PERSONALIZED, description="抽取模式: random(纯随机) 或 personalized(个性化推荐)")
):
    season_data = get_season_dishes(season)
    
    dishes = season_data[dish_type.value]
    
    all_exclude = exclude_ids + current_ids
    
    preferences = get_user_preferences()
    
    if draw_mode == DrawMode.PERSONALIZED:
        new_dish = select_recommended_dish(dishes, dish_type, all_exclude, preferences, season=season)
    else:
        new_dish = select_random_dish(dishes, dish_type, all_exclude)
    
    current_term = get_current_solar_term()
    reason = generate_random_reason(
        season.value,
        current_term.get("name", ""),
        new_dish.name
    )
    
    return JSONResponse(content={
        "success": True,
        "data": {
            **new_dish.model_dump(),
            "reason": reason
        }
    })

@app.get("/api/dishes/{season}/{dish_type}")
async def get_all_dishes(season: Season, dish_type: DishType):
    season_data = get_season_dishes(season)
    dishes = season_data[dish_type.value]
    
    result = []
    for d in dishes:
        result.append({
            "id": d["id"],
            "name": d["name"],
            "desc": d["desc"],
            "image_hint": d["image_hint"],
            "dish_type": dish_type.value
        })
    
    return JSONResponse(content={
        "success": True,
        "data": result
    })

@app.post("/api/generate-text")
async def generate_text_menu(request: Request):
    body = await request.json()
    package = body.get("package", {})
    
    lines = []
    lines.append("═" * 30)
    lines.append(f"  时节食匣 - {package.get('season_name', '')}特供")
    lines.append("═" * 30)
    lines.append("")
    
    if package.get("meats"):
        lines.append("【荤菜】")
        for meat in package["meats"]:
            lines.append(f"  • {meat['name']}")
            lines.append(f"    {meat['desc']}")
        lines.append("")
    
    if package.get("vegetables"):
        lines.append("【素菜】")
        for veg in package["vegetables"]:
            lines.append(f"  • {veg['name']}")
            lines.append(f"    {veg['desc']}")
        lines.append("")
    
    if package.get("soups"):
        lines.append("【汤品】")
        for soup in package["soups"]:
            lines.append(f"  • {soup['name']}")
            lines.append(f"    {soup['desc']}")
        lines.append("")
    
    if package.get("staples"):
        lines.append("【主食】")
        for staple in package["staples"]:
            lines.append(f"  • {staple['name']}")
            lines.append(f"    {staple['desc']}")
    
    lines.append("")
    lines.append("═" * 30)
    lines.append("  用浪漫与仪式感治愈你的吃饭选择困难症")
    lines.append("═" * 30)
    
    text = "\n".join(lines)
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "text": text,
            "lines": lines
        }
    })

@app.post("/api/location")
async def process_location(location: Location):
    try:
        region_info = get_region_by_coordinates(location.latitude, location.longitude)
        current_term = get_current_solar_term()
        current_season = get_current_season()
        
        season_name_map = {
            "spring": "春季",
            "summer": "夏季",
            "autumn": "秋季",
            "winter": "冬季"
        }
        
        solar_terms_data = get_solar_terms_data()
        term_detail = solar_terms_data["solar_terms"].get(current_term["key"], {})
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "region": region_info["region"],
                "region_name": region_info["name"],
                "current_solar_term": current_term["name"],
                "current_solar_term_key": current_term["key"],
                "current_solar_term_date": current_term["date"],
                "current_season": current_season.value,
                "current_season_name": season_name_map.get(current_season.value, ""),
                "timezone": "Asia/Shanghai",
                "term_detail": {
                    "description": term_detail.get("description", ""),
                    "customs": term_detail.get("customs", []),
                    "dietary_advice": term_detail.get("dietary_advice", {}),
                    "health_tips": term_detail.get("health_tips", []),
                    "cultural_story": term_detail.get("cultural_story", ""),
                    "icon": term_detail.get("icon", "🌱")
                }
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理位置信息失败: {str(e)}")

@app.get("/api/solar-term/{term_key}")
async def get_solar_term_detail(term_key: str):
    try:
        solar_terms_data = get_solar_terms_data()
        term_detail = solar_terms_data["solar_terms"].get(term_key)
        
        if not term_detail:
            raise HTTPException(status_code=404, detail="节气不存在")
        
        return JSONResponse(content={
            "success": True,
            "data": term_detail
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取节气详情失败: {str(e)}")

@app.get("/api/solar-terms")
async def get_all_solar_terms():
    try:
        solar_terms_data = get_solar_terms_data()
        current_term = get_current_solar_term()
        
        terms_list = []
        for term_key, term_data in solar_terms_data["solar_terms"].items():
            terms_list.append({
                "key": term_key,
                "name": term_data.get("name", ""),
                "season": term_data.get("season", ""),
                "date_range": term_data.get("date_range", []),
                "description": term_data.get("description", ""),
                "icon": term_data.get("icon", "🌱"),
                "is_current": term_key == current_term["key"]
            })
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "current_term": current_term,
                "all_terms": terms_list,
                "seasonal_guidelines": solar_terms_data.get("seasonal_dietary_guidelines", {}),
                "location_adjustment": solar_terms_data.get("location_based_adjustment", {})
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取节气列表失败: {str(e)}")

@app.post("/api/records")
async def create_dietary_record(record: DietaryRecord):
    try:
        global USER_RECORDS
        
        record_id = f"record_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        record.id = record_id
        record.created_at = datetime.now()
        
        USER_RECORDS.append(record)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "id": record.id,
                "date": record.date,
                "items": [item.model_dump() for item in record.items],
                "notes": record.notes,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建饮食记录失败: {str(e)}")

@app.get("/api/records")
async def get_dietary_records(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    limit: Optional[int] = Query(30, description="返回记录数量限制")
):
    try:
        global USER_RECORDS
        
        filtered_records = USER_RECORDS
        
        if start_date:
            filtered_records = [r for r in filtered_records if r.date >= start_date]
        
        if end_date:
            filtered_records = [r for r in filtered_records if r.date <= end_date]
        
        filtered_records = sorted(filtered_records, key=lambda r: r.created_at or r.date, reverse=True)
        filtered_records = filtered_records[:limit]
        
        result = []
        for record in filtered_records:
            result.append({
                "id": record.id,
                "date": record.date,
                "items": [item.model_dump() for item in record.items],
                "notes": record.notes,
                "created_at": record.created_at.isoformat() if record.created_at else None
            })
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "records": result,
                "total": len(USER_RECORDS),
                "filtered": len(filtered_records)
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取饮食记录失败: {str(e)}")

@app.get("/api/health-score")
async def get_health_score(
    date: Optional[str] = Query(None, description="指定日期，格式：YYYY-MM-DD"),
    days: Optional[int] = Query(7, description="计算最近多少天的评分")
):
    try:
        global USER_RECORDS
        
        current_season = get_current_season()
        
        if date:
            target_records = [r for r in USER_RECORDS if r.date == date]
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            target_records = [r for r in USER_RECORDS if r.date >= today]
        
        if not target_records:
            sample_records = []
            health_score = calculate_health_score(sample_records, current_season.value)
        else:
            health_score = calculate_health_score(target_records, current_season.value)
        
        solar_terms_data = get_solar_terms_data()
        seasonal_guidelines = solar_terms_data.get("seasonal_dietary_guidelines", {}).get(current_season.value, {})
        
        score_level_info = {
            "excellent": {"name": "优秀", "color": "#4CAF50", "emoji": "🌟"},
            "good": {"name": "良好", "color": "#8BC34A", "emoji": "👍"},
            "fair": {"name": "一般", "color": "#FFC107", "emoji": "⚠️"},
            "poor": {"name": "需改善", "color": "#F44336", "emoji": "❌"}
        }
        
        level_info = score_level_info.get(health_score.score_level, score_level_info["fair"])
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "overall_score": health_score.overall_score,
                "score_level": health_score.score_level,
                "score_level_name": level_info["name"],
                "score_color": level_info["color"],
                "score_emoji": level_info["emoji"],
                "dimensions": {
                    "seasonal_health": {
                        "score": health_score.seasonal_health,
                        "name": "时令健康度",
                        "weight": 0.3
                    },
                    "nutritional_balance": {
                        "score": health_score.nutritional_balance,
                        "name": "营养均衡度",
                        "weight": 0.3
                    },
                    "tcm_harmony": {
                        "score": health_score.tcm_harmony,
                        "name": "中医调和度",
                        "weight": 0.25
                    },
                    "dietary_diversity": {
                        "score": health_score.dietary_diversity,
                        "name": "饮食多样性",
                        "weight": 0.15
                    }
                },
                "advice": health_score.advice,
                "strengths": health_score.strengths,
                "improvements": health_score.improvements,
                "current_season": current_season.value,
                "seasonal_guidelines": seasonal_guidelines
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算健康评分失败: {str(e)}")

@app.post("/api/share-card")
async def generate_share_card(request: Request, share_request: ShareCardRequest):
    try:
        card_id = f"card_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        current_term = get_current_solar_term()
        current_season = get_current_season()
        
        season_name_map = {
            "spring": "春季",
            "summer": "夏季",
            "autumn": "秋季",
            "winter": "冬季"
        }
        
        card_data = {
            "id": card_id,
            "card_type": share_request.card_type,
            "theme": share_request.theme or "default",
            "created_at": datetime.now().isoformat(),
            "current_solar_term": current_term["name"],
            "current_solar_term_icon": "🌱",
            "current_season": season_name_map.get(current_season.value, ""),
            "package": None,
            "record": None
        }
        
        if share_request.package:
            card_data["package"] = share_request.package
        
        if share_request.record_id:
            global USER_RECORDS
            record = next((r for r in USER_RECORDS if r.id == share_request.record_id), None)
            if record:
                card_data["record"] = {
                    "id": record.id,
                    "date": record.date,
                    "items": [item.model_dump() for item in record.items]
                }
        
        return JSONResponse(content={
            "success": True,
            "data": card_data,
            "share_url": f"/share/{card_id}",
            "download_url": f"/api/share-card/{card_id}/download"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成分享卡片失败: {str(e)}")

@app.get("/api/seasonal-recommendations")
async def get_seasonal_recommendations(
    season: Optional[str] = Query(None, description="指定季节：spring, summer, autumn, winter"),
    region: Optional[str] = Query(None, description="指定地区：north, south, east, west")
):
    try:
        if not season:
            current_season = get_current_season()
            season = current_season.value
        
        solar_terms_data = get_solar_terms_data()
        dishes_data = get_dishes_data()
        
        seasonal_guidelines = solar_terms_data.get("seasonal_dietary_guidelines", {}).get(season, {})
        location_adjustment = solar_terms_data.get("location_based_adjustment", {})
        
        season_dishes = dishes_data["solar_terms"].get(season, {})
        
        region_adjustment = None
        if region and region in location_adjustment.get("regions", {}):
            region_adjustment = location_adjustment["regions"][region]
        
        current_term = get_current_solar_term()
        term_detail = solar_terms_data["solar_terms"].get(current_term["key"], {})
        
        season_name_map = {
            "spring": "春季",
            "summer": "夏季",
            "autumn": "秋季",
            "winter": "冬季"
        }
        
        recommendations = {
            "season": season,
            "season_name": season_name_map.get(season, ""),
            "current_solar_term": current_term["name"],
            "current_solar_term_icon": term_detail.get("icon", "🌱"),
            "description": seasonal_guidelines.get("description", ""),
            "dietary_principle": seasonal_guidelines.get("dietary_principle", ""),
            "recommended_foods": seasonal_guidelines.get("recommended_foods", []),
            "avoid_foods": seasonal_guidelines.get("avoid_foods", []),
            "dishes": {
                "meats": season_dishes.get("meats", []),
                "vegetables": season_dishes.get("vegetables", []),
                "soups": season_dishes.get("soups", []),
                "staples": season_dishes.get("staples", [])
            },
            "region_adjustment": region_adjustment,
            "term_dietary_advice": term_detail.get("dietary_advice", {}),
            "term_health_tips": term_detail.get("health_tips", [])
        }
        
        return JSONResponse(content={
            "success": True,
            "data": recommendations
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时令推荐失败: {str(e)}")

@app.get("/api/preferences")
async def get_preferences():
    try:
        preferences = get_user_preferences()
        return JSONResponse(content={
            "success": True,
            "data": {
                "excluded_categories": preferences.excluded_categories,
                "taste_preference": preferences.taste_preference,
                "dietary_restrictions": preferences.dietary_restrictions,
                "constitution_type": preferences.constitution_type,
                "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户偏好失败: {str(e)}")

@app.post("/api/preferences")
async def update_preferences(preferences: UserPreferences):
    try:
        saved = save_user_preferences(preferences)
        return JSONResponse(content={
            "success": True,
            "data": {
                "excluded_categories": saved.excluded_categories,
                "taste_preference": saved.taste_preference,
                "dietary_restrictions": saved.dietary_restrictions,
                "constitution_type": saved.constitution_type,
                "updated_at": saved.updated_at.isoformat() if saved.updated_at else None
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户偏好失败: {str(e)}")

@app.get("/api/excluded-categories")
async def get_excluded_categories():
    try:
        categories = []
        for key, value in EXCLUDED_INGREDIENTS_CATEGORY.items():
            categories.append({
                "key": key,
                "name": value["name"],
                "keywords": value["keywords"]
            })
        return JSONResponse(content={
            "success": True,
            "data": categories
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排除类别失败: {str(e)}")

@app.get("/api/generate-reason")
async def generate_reason(
    season: Optional[str] = Query(None, description="指定季节：spring, summer, autumn, winter"),
    term_name: Optional[str] = Query(None, description="节气名称"),
    dish_name: Optional[str] = Query(None, description="菜品名称")
):
    try:
        if not season:
            current_season = get_current_season()
            season = current_season.value
        
        reason = generate_random_reason(season, term_name, dish_name)
        
        return JSONResponse(content={
            "success": True,
            "data": reason
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成理由失败: {str(e)}")

SOLAR_TERM_INGREDIENTS = {
    "lichun": {
        "name": "立春",
        "ingredients": ["韭菜", "春笋", "香椿", "菠菜", "荠菜", "红枣", "蜂蜜"],
        "dishes": ["春饼", "春卷", "萝卜", "五辛盘"],
        "theme": "春回大地，宜温补阳气"
    },
    "yushui": {
        "name": "雨水",
        "ingredients": ["蜂蜜", "山药", "百合", "银耳", "莲子"],
        "dishes": ["蜂蜜水", "山药粥", "百合汤"],
        "theme": "降水增多，宜养脾胃"
    },
    "jingzhe": {
        "name": "惊蛰",
        "ingredients": ["梨", "菠菜", "芹菜", "鸡蛋", "春笋"],
        "dishes": ["梨汤", "炒菠菜", "芹菜炒肉"],
        "theme": "春雷惊醒，宜平肝清热"
    },
    "chunfen": {
        "name": "春分",
        "ingredients": ["香椿", "豆芽", "蒜苗", "荠菜", "枸杞芽"],
        "dishes": ["香椿炒鸡蛋", "豆芽汤", "蒜苗炒肉"],
        "theme": "昼夜平分，宜阴阳平衡"
    },
    "qingming": {
        "name": "清明",
        "ingredients": ["艾草", "青团", "螺蛳", "韭菜", "春笋"],
        "dishes": ["青团", "螺蛳", "清明粿"],
        "theme": "踏青扫墓，宜清淡养生"
    },
    "guyu": {
        "name": "谷雨",
        "ingredients": ["香椿", "菠菜", "芹菜", "黄豆芽", "荞麦"],
        "dishes": ["香椿拌豆腐", "菠菜汤", "荞麦面"],
        "theme": "雨生百谷，宜养肝健脾"
    },
    "lixia": {
        "name": "立夏",
        "ingredients": ["苦瓜", "冬瓜", "西瓜", "绿豆", "薏米"],
        "dishes": ["立夏蛋", "立夏饭", "尝三鲜"],
        "theme": "夏日初临，宜清热养心"
    },
    "xiaoman": {
        "name": "小满",
        "ingredients": ["苦瓜", "冬瓜", "黄瓜", "绿豆", "薏米"],
        "dishes": ["苦菜", "绿豆汤", "冬瓜汤"],
        "theme": "作物饱满，宜清热祛湿"
    },
    "mangzhong": {
        "name": "芒种",
        "ingredients": ["青梅", "桑葚", "西瓜", "绿豆", "苦瓜"],
        "dishes": ["煮梅", "桑葚", "凉面"],
        "theme": "播种时节，宜清补"
    },
    "xiazhi": {
        "name": "夏至",
        "ingredients": ["面条", "饺子", "西瓜", "绿豆", "苦瓜"],
        "dishes": ["夏至面", "馄饨", "凉面"],
        "theme": "昼长夜短，宜清暑益气"
    },
    "xiaoshu": {
        "name": "小暑",
        "ingredients": ["黄鳝", "莲藕", "绿豆芽", "西瓜", "冬瓜"],
        "dishes": ["黄鳝", "莲藕汤", "绿豆汤"],
        "theme": "初伏开始，宜温补"
    },
    "dashu": {
        "name": "大暑",
        "ingredients": ["生姜", "羊肉", "冬瓜", "绿豆", "西瓜"],
        "dishes": ["伏羊", "姜茶", "冬瓜汤"],
        "theme": "最热时节，宜冬病夏治"
    },
    "liqiu": {
        "name": "立秋",
        "ingredients": ["猪肉", "鸭肉", "西瓜", "桃子", "葡萄"],
        "dishes": ["贴秋膘", "啃秋", "秋桃"],
        "theme": "秋高气爽，宜贴秋膘"
    },
    "chushu": {
        "name": "处暑",
        "ingredients": ["鸭子", "莲藕", "梨", "百合", "银耳"],
        "dishes": ["鸭子", "莲藕汤", "梨汤"],
        "theme": "暑气渐消，宜滋阴润燥"
    },
    "bailu": {
        "name": "白露",
        "ingredients": ["龙眼", "白露茶", "红薯", "梨", "百合"],
        "dishes": ["龙眼", "白露米酒", "红薯"],
        "theme": "白露凝珠，宜补养肾气"
    },
    "qiufen": {
        "name": "秋分",
        "ingredients": ["螃蟹", "桂花", "梨", "银耳", "百合"],
        "dishes": ["螃蟹", "桂花糕", "秋菜"],
        "theme": "昼夜平分，宜阴阳平衡"
    },
    "hanlu": {
        "name": "寒露",
        "ingredients": ["螃蟹", "芝麻", "菊花", "梨", "银耳"],
        "dishes": ["螃蟹", "芝麻糕", "菊花茶"],
        "theme": "露凝而寒，宜养阴防燥"
    },
    "shuangjiang": {
        "name": "霜降",
        "ingredients": ["柿子", "萝卜", "栗子", "鸭肉", "牛肉"],
        "dishes": ["柿子", "萝卜汤", "栗子焖鸡"],
        "theme": "霜降始霜，宜平补"
    },
    "lidong": {
        "name": "立冬",
        "ingredients": ["羊肉", "牛肉", "饺子", "萝卜", "白菜"],
        "dishes": ["饺子", "羊肉汤", "火锅"],
        "theme": "冬日伊始，宜温补"
    },
    "xiaoxue": {
        "name": "小雪",
        "ingredients": ["腊肉", "香肠", "萝卜", "白菜", "羊肉"],
        "dishes": ["腊肉", "香肠", "腌菜"],
        "theme": "小雪初降，宜温补御寒"
    },
    "daxue": {
        "name": "大雪",
        "ingredients": ["羊肉", "牛肉", "萝卜", "白菜", "红枣"],
        "dishes": ["羊肉汤", "萝卜炖牛肉", "红枣粥"],
        "theme": "大雪纷飞，宜温补"
    },
    "dongzhi": {
        "name": "冬至",
        "ingredients": ["饺子", "汤圆", "羊肉", "牛肉", "萝卜"],
        "dishes": ["饺子", "汤圆", "羊肉汤"],
        "theme": "冬至大如年，宜进补"
    },
    "xiaohan": {
        "name": "小寒",
        "ingredients": ["羊肉", "牛肉", "栗子", "核桃", "红枣"],
        "dishes": ["羊肉汤", "栗子焖鸡", "腊八粥"],
        "theme": "小寒料峭，宜温补"
    },
    "dahan": {
        "name": "大寒",
        "ingredients": ["羊肉", "牛肉", "红枣", "桂圆", "生姜"],
        "dishes": ["腊八粥", "年糕", "鸡汤"],
        "theme": "大寒岁末，宜温补助阳"
    }
}

BADGE_DEFINITIONS = {
    "spring_master": {
        "name": "春之使者",
        "description": "完成所有春季节气挑战",
        "icon": "🌸",
        "game_type": "chef_challenge",
        "requirements": "完成立春、雨水、惊蛰、春分、清明、谷雨六个节气的主厨挑战"
    },
    "summer_master": {
        "name": "夏之守护者",
        "description": "完成所有夏季节气挑战",
        "icon": "☀️",
        "game_type": "chef_challenge",
        "requirements": "完成立夏、小满、芒种、夏至、小暑、大暑六个节气的主厨挑战"
    },
    "autumn_master": {
        "name": "秋之收获者",
        "description": "完成所有秋季节气挑战",
        "icon": "🍂",
        "game_type": "chef_challenge",
        "requirements": "完成立秋、处暑、白露、秋分、寒露、霜降六个节气的主厨挑战"
    },
    "winter_master": {
        "name": "冬之守护者",
        "description": "完成所有冬季节气挑战",
        "icon": "❄️",
        "game_type": "chef_challenge",
        "requirements": "完成立冬、小雪、大雪、冬至、小寒、大寒六个节气的主厨挑战"
    },
    "match_master": {
        "name": "连连看大师",
        "description": "完成所有食材连连看挑战",
        "icon": "🎯",
        "game_type": "match_game",
        "requirements": "完成所有24个节气的食材连连看挑战"
    },
    "speed_demon": {
        "name": "速度之王",
        "description": "在30秒内完成一次连连看挑战",
        "icon": "⚡",
        "game_type": "match_game",
        "requirements": "在30秒内完成任意一次食材连连看挑战"
    },
    "perfect_chef": {
        "name": "完美主厨",
        "description": "在主厨挑战中获得满分",
        "icon": "👨‍🍳",
        "game_type": "chef_challenge",
        "requirements": "在任意一次节气主厨挑战中获得满分"
    },
    "daily_player": {
        "name": "每日玩家",
        "description": "连续7天完成每日挑战",
        "icon": "📅",
        "game_type": "both",
        "requirements": "连续7天完成每日节气挑战"
    },
    "collector": {
        "name": "徽章收藏家",
        "description": "收集5个以上徽章",
        "icon": "🏆",
        "game_type": "both",
        "requirements": "收集5个或更多徽章"
    }
}

def get_game_badges() -> List[Dict[str, Any]]:
    global GAME_BADGES
    if not GAME_BADGES:
        for badge_id, badge_data in BADGE_DEFINITIONS.items():
            GAME_BADGES.append({
                "id": badge_id,
                **badge_data,
                "unlocked": False,
                "unlocked_at": None
            })
    return GAME_BADGES

def unlock_badge(badge_id: str) -> Optional[Dict[str, Any]]:
    badges = get_game_badges()
    for badge in badges:
        if badge["id"] == badge_id and not badge["unlocked"]:
            badge["unlocked"] = True
            badge["unlocked_at"] = datetime.now()
            return badge
    return None

def generate_chef_challenge(term_key: Optional[str] = None) -> Dict[str, Any]:
    if term_key is None:
        current_term = get_current_solar_term()
        term_key = current_term.get("key", "lichun")
    
    term_data = SOLAR_TERM_INGREDIENTS.get(term_key, SOLAR_TERM_INGREDIENTS["lichun"])
    
    all_ingredients = []
    for key, data in SOLAR_TERM_INGREDIENTS.items():
        all_ingredients.extend(data["ingredients"])
    all_ingredients = list(set(all_ingredients))
    
    correct_ingredients = term_data["ingredients"]
    distractors = [i for i in all_ingredients if i not in correct_ingredients]
    
    selected_distractors = random.sample(distractors, min(6, len(distractors)))
    selected_correct = random.sample(correct_ingredients, min(4, len(correct_ingredients)))
    
    options = selected_correct + selected_distractors
    random.shuffle(options)
    
    return {
        "term_key": term_key,
        "term_name": term_data["name"],
        "theme": term_data["theme"],
        "challenge": f"为{term_data['name']}节气搭配合适的养生食材",
        "correct_ingredients": correct_ingredients,
        "options": options,
        "required_count": min(3, len(correct_ingredients)),
        "dishes": term_data["dishes"]
    }

def evaluate_chef_challenge(
    term_key: str,
    selected_ingredients: List[str]
) -> Dict[str, Any]:
    term_data = SOLAR_TERM_INGREDIENTS.get(term_key, SOLAR_TERM_INGREDIENTS["lichun"])
    correct_ingredients = term_data["ingredients"]
    
    correct_count = 0
    incorrect_count = 0
    correct_selected = []
    incorrect_selected = []
    
    for ing in selected_ingredients:
        if ing in correct_ingredients:
            correct_count += 1
            correct_selected.append(ing)
        else:
            incorrect_count += 1
            incorrect_selected.append(ing)
    
    missed = [ing for ing in correct_ingredients if ing not in selected_ingredients]
    
    total_possible = len(correct_ingredients)
    score = int((correct_count / total_possible) * 100) if total_possible > 0 else 0
    score = max(0, min(100, score - incorrect_count * 10))
    
    if score >= 80:
        level = "excellent"
        message = "太棒了！你是真正的节气主厨！"
    elif score >= 60:
        level = "good"
        message = "不错！继续努力，你会成为更好的主厨！"
    else:
        level = "need_improvement"
        message = "还需要多了解一下节气养生知识哦！"
    
    return {
        "score": score,
        "level": level,
        "message": message,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "correct_selected": correct_selected,
        "incorrect_selected": incorrect_selected,
        "missed_ingredients": missed,
        "all_correct": correct_ingredients
    }

def generate_match_game(term_key: Optional[str] = None) -> Dict[str, Any]:
    if term_key is None:
        current_term = get_current_solar_term()
        term_key = current_term.get("key", "lichun")
    
    term_data = SOLAR_TERM_INGREDIENTS.get(term_key, SOLAR_TERM_INGREDIENTS["lichun"])
    
    pairs = []
    for ing in term_data["ingredients"]:
        pairs.append({
            "type": "ingredient",
            "value": ing,
            "term_key": term_key
        })
        pairs.append({
            "type": "term",
            "value": term_data["name"],
            "term_key": term_key
        })
    
    other_terms = [k for k in SOLAR_TERM_INGREDIENTS.keys() if k != term_key]
    selected_other_terms = random.sample(other_terms, min(3, len(other_terms)))
    
    for other_term in selected_other_terms:
        other_data = SOLAR_TERM_INGREDIENTS[other_term]
        if other_data["ingredients"]:
            ing = random.choice(other_data["ingredients"])
            pairs.append({
                "type": "ingredient",
                "value": ing,
                "term_key": other_term
            })
            pairs.append({
                "type": "term",
                "value": other_data["name"],
                "term_key": other_term
            })
    
    random.shuffle(pairs)
    
    cards = []
    for i, pair in enumerate(pairs):
        cards.append({
            "id": f"card_{i}",
            "type": pair["type"],
            "value": pair["value"],
            "term_key": pair["term_key"],
            "matched": False
        })
    
    return {
        "term_key": term_key,
        "term_name": term_data["name"],
        "theme": term_data["theme"],
        "cards": cards,
        "total_pairs": len(cards) // 2,
        "challenge": f"将食材与对应的节气进行配对"
    }

def evaluate_match_game(
    card_pairs: List[Dict[str, str]],
    time_spent: int
) -> Dict[str, Any]:
    correct_pairs = 0
    incorrect_pairs = 0
    
    for pair in card_pairs:
        card1_term = pair.get("card1_term", "")
        card2_term = pair.get("card2_term", "")
        if card1_term == card2_term and card1_term != "":
            correct_pairs += 1
        else:
            incorrect_pairs += 1
    
    total_pairs = len(card_pairs)
    score = int((correct_pairs / total_pairs) * 100) if total_pairs > 0 else 0
    
    time_bonus = 0
    if time_spent < 30:
        time_bonus = 20
    elif time_spent < 60:
        time_bonus = 10
    
    final_score = min(100, score + time_bonus)
    
    if final_score >= 80:
        level = "excellent"
        message = "完美配对！你是节气连连看大师！"
    elif final_score >= 60:
        level = "good"
        message = "不错！继续练习会更好！"
    else:
        level = "need_improvement"
        message = "多了解一下节气与食材的对应关系吧！"
    
    earned_badges = []
    if time_spent < 30 and score == 100:
        badge = unlock_badge("speed_demon")
        if badge:
            earned_badges.append(badge)
    
    return {
        "score": final_score,
        "level": level,
        "message": message,
        "correct_pairs": correct_pairs,
        "incorrect_pairs": incorrect_pairs,
        "time_spent": time_spent,
        "time_bonus": time_bonus,
        "earned_badges": earned_badges
    }

@app.get("/api/games/badges")
async def get_all_badges():
    try:
        badges = get_game_badges()
        return JSONResponse(content={
            "success": True,
            "data": {
                "badges": [
                    {
                        "id": b["id"],
                        "name": b["name"],
                        "description": b["description"],
                        "icon": b["icon"],
                        "game_type": b["game_type"],
                        "requirements": b["requirements"],
                        "unlocked": b["unlocked"],
                        "unlocked_at": b["unlocked_at"].isoformat() if b["unlocked_at"] else None
                    }
                    for b in badges
                ],
                "unlocked_count": sum(1 for b in badges if b["unlocked"]),
                "total_count": len(badges)
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取徽章列表失败: {str(e)}")

@app.get("/api/games/chef-challenge")
async def get_chef_challenge(
    term_key: Optional[str] = Query(None, description="指定节气key，不指定则使用当前节气")
):
    try:
        challenge = generate_chef_challenge(term_key)
        return JSONResponse(content={
            "success": True,
            "data": challenge
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成主厨挑战失败: {str(e)}")

@app.post("/api/games/chef-challenge/submit")
async def submit_chef_challenge(request: Request):
    try:
        body = await request.json()
        term_key = body.get("term_key")
        selected_ingredients = body.get("selected_ingredients", [])
        
        if not term_key or not selected_ingredients:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        result = evaluate_chef_challenge(term_key, selected_ingredients)
        
        earned_badges = []
        if result["score"] == 100:
            badge = unlock_badge("perfect_chef")
            if badge:
                earned_badges.append(badge)
        
        game_result = GameResult(
            game_type="chef_challenge",
            score=result["score"],
            level=1,
            earned_badges=[b["id"] for b in earned_badges],
            completed_at=datetime.now(),
            solar_term=term_key
        )
        global GAME_HISTORY
        GAME_HISTORY.append(game_result)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                **result,
                "earned_badges": earned_badges
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交主厨挑战失败: {str(e)}")

@app.get("/api/games/match-game")
async def get_match_game(
    term_key: Optional[str] = Query(None, description="指定节气key，不指定则使用当前节气")
):
    try:
        game = generate_match_game(term_key)
        return JSONResponse(content={
            "success": True,
            "data": game
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成连连看游戏失败: {str(e)}")

@app.post("/api/games/match-game/submit")
async def submit_match_game(request: Request):
    try:
        body = await request.json()
        card_pairs = body.get("card_pairs", [])
        time_spent = body.get("time_spent", 0)
        term_key = body.get("term_key")
        
        if not card_pairs:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        result = evaluate_match_game(card_pairs, time_spent)
        
        game_result = GameResult(
            game_type="match_game",
            score=result["score"],
            level=1,
            earned_badges=[b["id"] for b in result.get("earned_badges", [])],
            completed_at=datetime.now(),
            solar_term=term_key
        )
        global GAME_HISTORY
        GAME_HISTORY.append(game_result)
        
        return JSONResponse(content={
            "success": True,
            "data": result
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交连连看游戏失败: {str(e)}")

@app.get("/api/games/history")
async def get_game_history(
    limit: Optional[int] = Query(20, description="返回记录数量限制")
):
    try:
        global GAME_HISTORY
        history = sorted(GAME_HISTORY, key=lambda x: x.completed_at, reverse=True)[:limit]
        
        result = []
        for record in history:
            result.append({
                "game_type": record.game_type,
                "score": record.score,
                "level": record.level,
                "earned_badges": record.earned_badges,
                "completed_at": record.completed_at.isoformat(),
                "solar_term": record.solar_term
            })
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "history": result,
                "total_games": len(GAME_HISTORY)
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取游戏历史失败: {str(e)}")

@app.post("/api/games/share-card")
async def generate_game_share_card(request: Request):
    try:
        body = await request.json()
        game_type = body.get("game_type")
        score = body.get("score", 0)
        level = body.get("level")
        term_name = body.get("term_name", "")
        earned_badges = body.get("earned_badges", [])
        
        card_id = f"game_card_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        current_term = get_current_solar_term()
        
        game_type_names = {
            "chef_challenge": "节气主厨挑战",
            "match_game": "食材连连看"
        }
        
        level_info = {
            "excellent": {"name": "优秀", "color": "#4CAF50", "emoji": "🌟"},
            "good": {"name": "良好", "color": "#8BC34A", "emoji": "👍"},
            "need_improvement": {"name": "需努力", "color": "#FF9800", "emoji": "💪"}
        }
        
        level_data = level_info.get(level, level_info["good"])
        
        card_data = {
            "id": card_id,
            "game_type": game_type,
            "game_type_name": game_type_names.get(game_type, game_type),
            "score": score,
            "level": level,
            "level_name": level_data["name"],
            "level_color": level_data["color"],
            "level_emoji": level_data["emoji"],
            "term_name": term_name or current_term.get("name", ""),
            "earned_badges": earned_badges,
            "created_at": datetime.now().isoformat(),
            "message": f"我在{game_type_names.get(game_type, '小游戏')}中获得了{score}分！快来挑战我吧！"
        }
        
        return JSONResponse(content={
            "success": True,
            "data": card_data,
            "share_url": f"/share/game/{card_id}",
            "download_url": f"/api/games/share-card/{card_id}/download"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成游戏分享卡片失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9424)
