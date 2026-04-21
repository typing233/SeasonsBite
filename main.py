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
    season: Optional[Season] = Query(default=None, description="指定季节，不指定则使用当前季节")
):
    if season is None:
        season = get_current_season()
    
    package = generate_package(season, package_type)
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "season": package.season.value,
            "season_name": package.season_name,
            "season_desc": package.season_desc,
            "package_type": package.package_type.value,
            "meats": [m.model_dump() for m in package.meats],
            "vegetables": [v.model_dump() for v in package.vegetables],
            "soups": [s.model_dump() for s in package.soups],
            "staples": [st.model_dump() for st in package.staples],
            "created_at": package.created_at.isoformat()
        }
    })

@app.post("/api/redraw")
async def redraw_dish(
    dish_type: DishType = Query(..., description="要重抽的菜品类型"),
    season: Season = Query(..., description="季节"),
    exclude_ids: List[str] = Query(default=[], description="要排除的菜品ID列表"),
    current_ids: List[str] = Query(default=[], description="当前已选的同类型菜品ID")
):
    season_data = get_season_dishes(season)
    
    dishes = season_data[dish_type.value]
    
    all_exclude = exclude_ids + current_ids
    
    new_dish = select_random_dish(dishes, dish_type, all_exclude)
    
    return JSONResponse(content={
        "success": True,
        "data": new_dish.model_dump()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
