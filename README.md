# 时节食匣 - 二十四节气盲盒抽卡

> 结合盲盒抽卡与二十四节气文化的时令套餐随机生成器，用浪漫与仪式感治愈你的吃饭选择困难症。

## 项目简介

时节食匣是一个充满仪式感的Web应用，将盲盒抽卡的乐趣与中国传统二十四节气文化相结合，为你随机生成时令套餐菜单。无论是纠结午餐吃什么，还是想尝试新的时令菜品，时节食匣都能给你带来惊喜。

### 特色功能

- **盲盒抽卡体验**：点击抽取按钮，获得随机菜品组合，充满期待感
- **二十四节气联动**：根据当前真实季节，推荐对应的时令菜品
- **双套餐规格**：
  - 基础隐藏款：1荤 + 1素 + 1汤 + 1主食
  - 豪华双荤款：2荤 + 1素 + 1汤
- **卡片翻转**：点击卡片翻转查看菜品详情，增加互动乐趣
- **局部重抽**：对某个菜品不满意？点击"换一道"单独重抽
- **锁定功能**：遇到喜欢的菜品？点击"锁定"保留它
- **一键导出**：
  - 生成纯文本菜单，方便复制分享
  - 生成精美截图，保存留念

## 技术栈

### 后端
- **Python 3.9+**
- **FastAPI**：现代、快速的Web框架
- **Uvicorn**：ASGI服务器
- **Jinja2**：模板引擎

### 前端
- **原生JavaScript**：无需框架，轻量级
- **CSS3**：响应式设计、动画效果
- **HTML5 Canvas**：截图生成

## 项目结构

```
SeasonsBite/
├── main.py                 # FastAPI主应用
├── requirements.txt        # Python依赖
├── data/
│   └── dishes.json         # 菜品数据库（按二十四节气分类）
├── templates/
│   └── index.html          # 前端页面模板
├── static/
│   ├── css/
│   │   └── style.css       # 样式文件
│   └── js/
│       └── app.js          # 前端逻辑
├── tests/
│   └── test_api.py         # 测试用例
└── README.md               # 项目说明
```

## 安装与运行

### 环境准备

确保你的环境已安装 Python 3.9 或更高版本。

### 安装依赖

```bash
cd /home/ubuntu/SeasonsBite
pip install -r requirements.txt
```

### 启动服务

```bash
cd /home/ubuntu/SeasonsBite
python main.py
```

或者使用 uvicorn 启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 `http://localhost:8000` 启动。

### 访问应用

打开浏览器访问：
- 主页面：`http://localhost:8000`
- API文档：`http://localhost:8000/docs` 或 `http://localhost:8000/redoc`

## API接口说明

### 获取当前季节信息

```http
GET /api/season
```

**响应示例：**
```json
{
  "season": "spring",
  "season_name": "春季",
  "season_desc": "春回大地，万物复苏，宜清淡温补",
  "solar_terms": ["立春", "雨水", "惊蛰", "春分", "清明", "谷雨"]
}
```

### 抽取套餐

```http
POST /api/draw?package_type={type}&season={season}
```

**参数说明：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| package_type | string | 否 | 套餐类型：`basic`（基础款）或 `luxury`（豪华款），默认 `basic` |
| season | string | 否 | 指定季节：`spring`、`summer`、`autumn`、`winter`，不指定则使用当前季节 |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "season": "spring",
    "season_name": "春季",
    "season_desc": "春回大地，万物复苏，宜清淡温补",
    "package_type": "basic",
    "meats": [{
      "id": "sp_meat_1",
      "name": "春笋炒腊肉",
      "desc": "鲜嫩春笋配咸香腊肉，春天的味道",
      "image_hint": "spring bamboo shoots stir-fried with cured pork...",
      "dish_type": "meats",
      "is_locked": false
    }],
    "vegetables": [...],
    "soups": [...],
    "staples": [...],
    "created_at": "2024-01-15T12:30:00"
  }
}
```

### 局部重抽菜品

```http
POST /api/redraw?dish_type={type}&season={season}&exclude_ids={ids}&current_ids={ids}
```

**参数说明：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dish_type | string | 是 | 菜品类型：`meats`、`vegetables`、`soups`、`staples` |
| season | string | 是 | 季节 |
| exclude_ids | array | 否 | 要排除的菜品ID列表 |
| current_ids | array | 否 | 当前已选的同类型菜品ID |

### 获取指定类型所有菜品

```http
GET /api/dishes/{season}/{dish_type}
```

**示例：**
```
GET /api/dishes/spring/meats
```

### 生成菜单文本

```http
POST /api/generate-text
```

**请求体：**
```json
{
  "package": {
    "season_name": "春季",
    "meats": [...],
    "vegetables": [...],
    "soups": [...],
    "staples": [...]
  }
}
```

## 菜品数据库说明

菜品数据存储在 `data/dishes.json` 中，按四季分类，每季包含：

- **荤菜 (meats)**：8道
- **素菜 (vegetables)**：6道
- **汤品 (soups)**：6道
- **主食 (staples)**：6道

### 四季与二十四节气对应

| 季节 | 节气 | 特点 |
|------|------|------|
| 春季 | 立春、雨水、惊蛰、春分、清明、谷雨 | 清淡温补 |
| 夏季 | 立夏、小满、芒种、夏至、小暑、大暑 | 清热解暑 |
| 秋季 | 立秋、处暑、白露、秋分、寒露、霜降 | 滋阴润燥 |
| 冬季 | 立冬、小雪、大雪、冬至、小寒、大寒 | 温补御寒 |

### 扩展菜品数据

你可以自由编辑 `data/dishes.json` 添加更多菜品，格式如下：

```json
{
  "id": "unique_id",
  "name": "菜品名称",
  "desc": "菜品描述",
  "image_hint": "用于生成图片的提示词"
}
```

## 使用指南

### 1. 选择套餐规格

在主页面选择你想要的套餐类型：
- **基础隐藏款**：适合单人或两人小聚
- **豪华双荤款**：适合肉食爱好者或多人聚餐

### 2. 抽取食匣

点击「抽取今日食匣」按钮，系统将根据当前季节为你随机生成一套菜单。

### 3. 查看菜品

点击任意卡片即可翻转查看菜品详情，包括：
- 菜品名称
- 菜品描述
- 菜品图片（AI生成）

### 4. 调整菜单

- **换一道**：对某个菜品不满意，点击「换一道」按钮单独重抽该位置
- **锁定**：遇到喜欢的菜品，点击「锁定」按钮，重抽时将保留该菜品

### 5. 保存分享

- **生成文本**：生成格式化的菜单文本，可复制到备忘录或分享给朋友
- **生成截图**：生成精美的菜单图片，保存到手机或分享到社交平台

## 运行测试

项目包含完整的API测试用例，确保核心功能正常运行。

### 运行测试

```bash
cd /home/ubuntu/SeasonsBite
pytest tests/test_api.py -v
```

### 测试覆盖范围

- **季节检测**：验证当前季节判断是否正确
- **套餐抽取**：验证基础款和豪华款套餐生成逻辑
- **菜品重抽**：验证局部重抽功能
- **文本生成**：验证菜单文本格式化
- **边界情况**：验证无效参数处理

## 自定义配置

### 修改端口

编辑 `main.py` 最后一行：

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # 修改端口号
```

或使用命令行参数：

```bash
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

### 添加更多菜品

编辑 `data/dishes.json`，在对应季节的分类下添加新的菜品对象。

### 修改UI样式

编辑 `static/css/style.css` 自定义配色、动画、布局等。

## 开发计划

- [ ] 支持用户自定义菜品库
- [ ] 添加历史记录功能
- [ ] 支持收藏喜欢的菜品组合
- [ ] 添加营养成分分析
- [ ] 支持多语言
- [ ] 添加分享到社交媒体功能

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 致谢

- 灵感来源于中国传统二十四节气文化
- 图片生成使用 Trae IDE 内置的文生图API
- 感谢所有开源项目的贡献

---

**用浪漫与仪式感治愈你的吃饭选择困难症 🍽️**
