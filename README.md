# GEO 招投标情报站

GEO（生成式引擎优化）领域招标、投标、中标情报实时追踪。

## 这是什么？

从2025年开始，GEO（Generative Engine Optimization，生成式引擎优化）从企业营销的"可选项"变成了"必选项"。九号公司、华润集团、东鹏控股、宁波地方政府等大量企业和政府机构已启动GEO项目的公开招标。

这个工具收集整理GEO领域的所有招投标信息，帮助行业从业者：

- **了解市场格局**：哪些行业/企业在采购GEO服务
- **把握价格区间**：GEO项目的预算范围
- **发现商机**：正在招标的项目
- **分析竞争**：哪些公司中标了哪些项目

## 数据看板

在线查看：`https://<你的用户名>.github.io/geo-bidding-intel/`

（GitHub Pages 部署后生效）

## 项目结构

```
geo-bidding-intel/
├── README.md
├── data/
│   └── bidding_data.json       # 主数据文件
├── docs/
│   ├── index.html              # GitHub Pages 看板
│   └── bidding_data.json       # 同步的数据文件
└── scripts/
    └── update_bidding.py       # 更新工具
```

## 使用方式

### 查看数据概览
```bash
python scripts/update_bidding.py
```

### 添加新项目
```bash
python scripts/update_bidding.py --add
```

### 批量导入CSV
```bash
python scripts/update_bidding.py --batch projects.csv
```

CSV格式：`company,industry,title,status,budget,bid_deadline,publish_date,summary,winner,source_url`

### 同步到GitHub Pages
```bash
python scripts/update_bidding.py --sync-docs
```

## 更新频率

- 建议每周检查一次招标平台，补充新项目
- 每次更新后运行 `--sync-docs` 并推送到GitHub

## 数据来源

- 中国招标投标公共服务平台
- 华润集团守正电子招标平台
- 各政府采购网
- 企业招标平台
- 行业情报收集

## License

MIT
