# ⚽ 足球彩经智能采集与翻译系统

通过大语言模型（Kimi）和网络爬虫，自动搜索、翻译和整理非中国地区的足球比赛彩经，生成中文赛前分析和比分预测。

## 功能特性

- 🔍 **智能赛程发现** - 自动获取五大联赛 + 欧冠 upcoming 比赛
- 🌐 **多源文章采集** - 搜索并采集英文赛前分析文章
- 📊 **数据增强** - 补充实时积分榜、近期战绩、历史交锋
- 🤖 **AI 深度分析** - 调用 Kimi API 翻译整理并生成中文彩经
- 📝 **Markdown 输出** - 生成结构化分析报告 + 每日总览
- ⏰ **定时任务** - 支持每日自动执行

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入：

```bash
# 必需: Kimi API Key (从 https://platform.moonshot.cn/ 获取)
KIMI_API_KEY=sk-your-key-here

# 强烈建议: Football Data API Key (免费, 从 https://www.football-data.org/ 获取)
FOOTBALL_DATA_API_KEY=your-key-here
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 运行分析

```bash
# 分析未来2天的所有比赛
python main.py

# 只分析明天的比赛
python main.py --days 1

# 只分析英超
python main.py --competition 2021

# 分析指定比赛
python main.py --match "曼联 vs 利物浦"
```

### 5. 查看结果

分析报告会保存到 `output/` 目录下：
- `2024-01-15_曼联_vs_利物浦.md` - 单场比赛分析
- `2024-01-15_总览.md` - 当日赛事总览

### 6. 定时任务（可选）

```bash
# 每天早上9点自动执行
python run_scheduler.py --hour 9 --minute 0
```

## 支持的联赛

| 代码 | 联赛 |
|------|------|
| 2021 | 英超 Premier League |
| 2014 | 西甲 La Liga |
| 2019 | 意甲 Serie A |
| 2002 | 德甲 Bundesliga |
| 2015 | 法甲 Ligue 1 |
| 2001 | 欧冠 Champions League |

## 项目结构

```
match_dianping/
├── config/           # 配置和 Prompt 模板
├── core/             # 数据库模型
├── modules/          # 核心模块
│   ├── match_discovery.py   # 赛程发现
│   ├── crawler.py           # 文章采集
│   ├── data_enhancer.py     # 数据增强
│   ├── ai_processor.py      # AI 分析
│   └── output.py            # 输出管理
├── utils/            # 工具函数
├── scripts/          # 脚本
├── tests/            # 测试
├── output/           # 输出目录
├── data/             # 数据库
├── main.py           # 主入口
└── run_scheduler.py  # 定时任务
```

## 注意事项

1. **API 费用**：Kimi API 按 token 计费，每场比赛分析约消耗 5K-15K tokens
2. **免费数据 API**：football-data.org 免费版限制 10 次/分钟，已做限速处理
3. **爬虫礼貌**：已内置请求间隔，请勿调得过低以免被封
4. **文章质量**：如果某场比赛找不到足够的赛前分析，AI 会基于已有数据生成分析

## License

MIT
