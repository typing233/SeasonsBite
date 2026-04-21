from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import random
import json
import os
from datetime import datetime
from enum import Enum

app = FastAPI(title="时节食匣 - 二十四节气盲盒抽卡", description="结合盲盒抽卡与二十四节气文化的时令套餐随机生成器")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

DISHES_DATA = None

def get_dishes_data():
    global DISHES_DATA
    if DISHES_DATA is None:
        data_path = os.path.join(DATA_DIR, "dishes.json")
        with open(data_path, "r", encoding="utf-8") as f:
            DISHES_DATA = json.load(f)
    return DISHES_DATA

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
