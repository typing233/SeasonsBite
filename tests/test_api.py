import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_current_season, Season, PackageType

client = TestClient(app)


class TestSeasonInfo:
    """测试季节信息相关接口"""

    def test_get_season_info(self):
        """测试获取当前季节信息"""
        response = client.get("/api/season")
        assert response.status_code == 200
        
        data = response.json()
        assert "season" in data
        assert "season_name" in data
        assert "season_desc" in data
        assert "solar_terms" in data
        
        assert data["season"] in ["spring", "summer", "autumn", "winter"]
        assert isinstance(data["solar_terms"], list)
        assert len(data["solar_terms"]) == 6

    def test_get_season_info_response_fields(self):
        """测试季节信息响应字段完整性"""
        response = client.get("/api/season")
        data = response.json()
        
        required_fields = ["season", "season_name", "season_desc", "solar_terms"]
        for field in required_fields:
            assert field in data, f"缺少必要字段: {field}"


class TestDrawPackage:
    """测试套餐抽取接口"""

    def test_draw_basic_package(self):
        """测试抽取基础套餐"""
        response = client.post("/api/draw?package_type=basic")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        pkg = data["data"]
        assert pkg["package_type"] == "basic"
        
        assert len(pkg["meats"]) == 1
        assert len(pkg["vegetables"]) == 1
        assert len(pkg["soups"]) == 1
        assert len(pkg["staples"]) == 1

    def test_draw_luxury_package(self):
        """测试抽取豪华套餐"""
        response = client.post("/api/draw?package_type=luxury")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        pkg = data["data"]
        assert pkg["package_type"] == "luxury"
        
        assert len(pkg["meats"]) == 2
        assert len(pkg["vegetables"]) == 1
        assert len(pkg["soups"]) == 1
        assert len(pkg["staples"]) == 1

    def test_draw_package_default_type(self):
        """测试默认套餐类型（不指定package_type）"""
        response = client.post("/api/draw")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["package_type"] == "basic"

    def test_draw_package_with_season(self):
        """测试指定季节抽取套餐"""
        for season in ["spring", "summer", "autumn", "winter"]:
            response = client.post(f"/api/draw?season={season}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["season"] == season

    def test_draw_package_response_structure(self):
        """测试抽取套餐响应结构"""
        response = client.post("/api/draw")
        data = response.json()
        
        assert "success" in data
        assert "data" in data
        
        pkg = data["data"]
        required_fields = [
            "season", "season_name", "season_desc", "package_type",
            "meats", "vegetables", "soups", "staples", "created_at"
        ]
        for field in required_fields:
            assert field in pkg, f"缺少必要字段: {field}"

    def test_dish_item_structure(self):
        """测试菜品数据结构"""
        response = client.post("/api/draw")
        data = response.json()
        
        all_dishes = []
        all_dishes.extend(data["data"]["meats"])
        all_dishes.extend(data["data"]["vegetables"])
        all_dishes.extend(data["data"]["soups"])
        all_dishes.extend(data["data"]["staples"])
        
        for dish in all_dishes:
            required_fields = ["id", "name", "desc", "image_hint", "dish_type", "is_locked"]
            for field in required_fields:
                assert field in dish, f"菜品缺少必要字段: {field}"
            
            assert dish["is_locked"] is False

    def test_luxury_package_duplicate_meats(self):
        """测试豪华套餐荤菜不重复"""
        response = client.post("/api/draw?package_type=luxury")
        data = response.json()
        
        meats = data["data"]["meats"]
        assert len(meats) == 2
        
        meat_ids = [meat["id"] for meat in meats]
        assert len(set(meat_ids)) == 2, "豪华套餐荤菜不应重复"


class TestRedrawDish:
    """测试局部重抽接口"""

    def test_redraw_meat(self):
        """测试重抽荤菜"""
        response = client.post(
            "/api/redraw?dish_type=meats&season=spring"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        dish = data["data"]
        assert dish["dish_type"] == "meats"

    def test_redraw_vegetable(self):
        """测试重抽素菜"""
        response = client.post(
            "/api/redraw?dish_type=vegetables&season=summer"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["dish_type"] == "vegetables"

    def test_redraw_soup(self):
        """测试重抽汤品"""
        response = client.post(
            "/api/redraw?dish_type=soups&season=autumn"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["dish_type"] == "soups"

    def test_redraw_staple(self):
        """测试重抽主食"""
        response = client.post(
            "/api/redraw?dish_type=staples&season=winter"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["dish_type"] == "staples"

    def test_redraw_with_exclude_ids(self):
        """测试带排除ID的重抽"""
        response = client.post(
            "/api/redraw?dish_type=meats&season=spring&exclude_ids=sp_meat_1"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True

    def test_redraw_with_multiple_exclude_ids(self):
        """测试带多个排除ID的重抽"""
        response = client.post(
            "/api/redraw?dish_type=meats&season=spring&exclude_ids=sp_meat_1,sp_meat_2,sp_meat_3"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True

    def test_redraw_response_structure(self):
        """测试重抽响应结构"""
        response = client.post(
            "/api/redraw?dish_type=meats&season=spring"
        )
        data = response.json()
        
        assert "success" in data
        assert "data" in data
        
        dish = data["data"]
        required_fields = ["id", "name", "desc", "image_hint", "dish_type", "is_locked"]
        for field in required_fields:
            assert field in dish, f"重抽菜品缺少必要字段: {field}"


class TestGetAllDishes:
    """测试获取所有菜品接口"""

    def test_get_spring_meats(self):
        """测试获取春季荤菜"""
        response = client.get("/api/dishes/spring/meats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_get_summer_vegetables(self):
        """测试获取夏季素菜"""
        response = client.get("/api/dishes/summer/vegetables")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_get_autumn_soups(self):
        """测试获取秋季汤品"""
        response = client.get("/api/dishes/autumn/soups")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_get_winter_staples(self):
        """测试获取冬季主食"""
        response = client.get("/api/dishes/winter/staples")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_get_dishes_response_structure(self):
        """测试获取菜品列表响应结构"""
        response = client.get("/api/dishes/spring/meats")
        data = response.json()
        
        assert "success" in data
        assert "data" in data
        
        if data["data"]:
            dish = data["data"][0]
            required_fields = ["id", "name", "desc", "image_hint", "dish_type"]
            for field in required_fields:
                assert field in dish, f"菜品列表缺少必要字段: {field}"


class TestGenerateText:
    """测试生成菜单文本接口"""

    def test_generate_text_success(self):
        """测试成功生成菜单文本"""
        test_package = {
            "season_name": "春季",
            "meats": [{"name": "春笋炒腊肉", "desc": "鲜嫩春笋配咸香腊肉"}],
            "vegetables": [{"name": "清炒豌豆苗", "desc": "鲜嫩豌豆苗"}],
            "soups": [{"name": "春笋排骨汤", "desc": "春笋配排骨"}],
            "staples": [{"name": "阳春面", "desc": "清汤白面"}]
        }
        
        response = client.post("/api/generate-text", json={"package": test_package})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "text" in data["data"]
        assert "lines" in data["data"]

    def test_generate_text_contains_all_categories(self):
        """测试生成的文本包含所有分类"""
        test_package = {
            "season_name": "夏季",
            "meats": [{"name": "测试荤菜", "desc": "测试描述"}],
            "vegetables": [{"name": "测试素菜", "desc": "测试描述"}],
            "soups": [{"name": "测试汤品", "desc": "测试描述"}],
            "staples": [{"name": "测试主食", "desc": "测试描述"}]
        }
        
        response = client.post("/api/generate-text", json={"package": test_package})
        data = response.json()
        
        text = data["data"]["text"]
        assert "测试荤菜" in text
        assert "测试素菜" in text
        assert "测试汤品" in text
        assert "测试主食" in text
        assert "夏季" in text

    def test_generate_text_with_luxury_package(self):
        """测试豪华套餐（双荤菜）文本生成"""
        test_package = {
            "season_name": "秋季",
            "meats": [
                {"name": "荤菜1", "desc": "描述1"},
                {"name": "荤菜2", "desc": "描述2"}
            ],
            "vegetables": [{"name": "素菜", "desc": "描述"}],
            "soups": [{"name": "汤品", "desc": "描述"}],
            "staples": []
        }
        
        response = client.post("/api/generate-text", json={"package": test_package})
        data = response.json()
        
        text = data["data"]["text"]
        assert "荤菜1" in text
        assert "荤菜2" in text

    def test_generate_text_empty_staples(self):
        """测试没有主食的情况（豪华套餐）"""
        test_package = {
            "season_name": "冬季",
            "meats": [{"name": "荤菜", "desc": "描述"}],
            "vegetables": [{"name": "素菜", "desc": "描述"}],
            "soups": [{"name": "汤品", "desc": "描述"}],
            "staples": []
        }
        
        response = client.post("/api/generate-text", json={"package": test_package})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True


class TestMainPage:
    """测试主页面"""

    def test_main_page_loads(self):
        """测试主页面正常加载"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_main_page_contains_title(self):
        """测试主页面包含标题"""
        response = client.get("/")
        assert "时节食匣" in response.text

    def test_main_page_contains_draw_button(self):
        """测试主页面包含抽取按钮"""
        response = client.get("/")
        assert "抽取今日食匣" in response.text


class TestHelperFunctions:
    """测试辅助函数"""

    def test_get_current_season_returns_valid_season(self):
        """测试获取当前季节返回有效季节"""
        season = get_current_season()
        assert season in [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]


class TestEdgeCases:
    """测试边界情况"""

    def test_draw_all_seasons(self):
        """测试所有季节都能正常抽取"""
        seasons = ["spring", "summer", "autumn", "winter"]
        for season in seasons:
            response = client.post(f"/api/draw?season={season}&package_type=basic")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["season"] == season

    def test_redraw_all_dish_types(self):
        """测试所有菜品类型都能正常重抽"""
        dish_types = ["meats", "vegetables", "soups", "staples"]
        for dish_type in dish_types:
            response = client.post(f"/api/redraw?dish_type={dish_type}&season=spring")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_consistent_season_names(self):
        """测试季节名称一致性"""
        season_response = client.get("/api/season")
        season_data = season_response.json()
        
        draw_response = client.post("/api/draw")
        draw_data = draw_response.json()
        
        assert season_data["season_name"] == draw_data["data"]["season_name"]
        assert season_data["season_desc"] == draw_data["data"]["season_desc"]


class TestPackageTypeValidation:
    """测试套餐类型验证"""

    def test_invalid_package_type(self):
        """测试无效套餐类型"""
        response = client.post("/api/draw?package_type=invalid")
        assert response.status_code == 422

    def test_invalid_season(self):
        """测试无效季节"""
        response = client.post("/api/draw?season=invalid")
        assert response.status_code == 422

    def test_invalid_dish_type(self):
        """测试无效菜品类型"""
        response = client.post("/api/redraw?dish_type=invalid&season=spring")
        assert response.status_code == 422


class TestStaticFiles:
    """测试静态文件"""

    def test_css_file_exists(self):
        """测试CSS文件可访问"""
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_js_file_exists(self):
        """测试JS文件可访问"""
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"] or \
               "application/json" not in response.headers["content-type"]


@pytest.mark.asyncio
class TestAsyncTests:
    """异步测试"""

    async def test_async_draw_multiple_packages(self):
        """异步测试多次抽取套餐"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            responses = []
            for _ in range(5):
                response = await client.post("/api/draw")
                responses.append(response)
            
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    async def test_async_season_consistency(self):
        """异步测试季节信息一致性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            responses = []
            for _ in range(3):
                response = await client.get("/api/season")
                responses.append(response)
            
            first_data = responses[0].json()
            for response in responses:
                data = response.json()
                assert data["season"] == first_data["season"]
                assert data["season_name"] == first_data["season_name"]


class TestIntegrationScenarios:
    """集成测试场景"""

    def test_full_user_flow(self):
        """测试完整用户流程"""
        
        season_response = client.get("/api/season")
        assert season_response.status_code == 200
        season_data = season_response.json()
        current_season = season_data["season"]
        
        draw_response = client.post(f"/api/draw?package_type=basic&season={current_season}")
        assert draw_response.status_code == 200
        draw_data = draw_response.json()
        assert draw_data["success"] is True
        
        meats = draw_data["data"]["meats"]
        assert len(meats) == 1
        original_meat_id = meats[0]["id"]
        
        redraw_response = client.post(
            f"/api/redraw?dish_type=meats&season={current_season}&exclude_ids={original_meat_id}"
        )
        assert redraw_response.status_code == 200
        redraw_data = redraw_response.json()
        assert redraw_data["success"] is True
        
        test_package = {
            "season_name": draw_data["data"]["season_name"],
            "meats": [redraw_data["data"]],
            "vegetables": draw_data["data"]["vegetables"],
            "soups": draw_data["data"]["soups"],
            "staples": draw_data["data"]["staples"]
        }
        
        text_response = client.post("/api/generate-text", json={"package": test_package})
        assert text_response.status_code == 200
        text_data = text_response.json()
        assert text_data["success"] is True
        assert len(text_data["data"]["text"]) > 0

    def test_luxury_package_flow(self):
        """测试豪华套餐完整流程"""
        
        draw_response = client.post("/api/draw?package_type=luxury")
        assert draw_response.status_code == 200
        draw_data = draw_response.json()
        
        meats = draw_data["data"]["meats"]
        assert len(meats) == 2
        
        meat_ids = [m["id"] for m in meats]
        redraw_response = client.post(
            f"/api/redraw?dish_type=meats&season={draw_data['data']['season']}&exclude_ids={meat_ids[0]}&current_ids={','.join(meat_ids)}"
        )
        assert redraw_response.status_code == 200


def run_all_tests():
    """运行所有测试的辅助函数"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
