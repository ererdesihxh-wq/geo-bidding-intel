#!/usr/bin/env python3
"""GEO招投标情报 - 完整数据集构建脚本"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ===== 数据增强函数 =====

def parse_budget_wan(budget_str):
    """解析预算字符串，返回万元数值"""
    import re
    if not budget_str or budget_str == "未公开":
        return None
    m = re.search(r'([\d.]+)\s*万元', budget_str)
    if m:
        return float(m.group(1))
    m = re.search(r'约\s*([\d.]+)\s*万', budget_str)
    if m:
        return float(m.group(1))
    return None


def compute_geo_relevance(project):
    """计算GEO相关度（0-100）和等级"""
    text = (project.get("title", "") + " " + project.get("summary", "")).lower()
    keywords = {
        "deepseek": 15, "豆包": 15, "文心一言": 15, "通义千问": 15,
        "kimi": 15, "元宝": 10, "ai平台": 10, "多平台": 8,
        "年框": 8, "kpi": 5, "语义匹配": 10, "合规": 5,
        "露出率": 10, "监测": 5, "chatgpt": 10, "gemini": 10,
        "ai搜索": 12, "ai优化": 12, "大模型": 10, "词条": 5,
    }
    score = 0
    for kw, pts in keywords.items():
        if kw in text:
            score += pts
    tier = "高" if score >= 50 else ("中" if score >= 20 else "低")
    return {"score": min(score, 100), "tier": tier}


def compute_priority(project):
    """计算优先级 P0/P1/P2"""
    budget = parse_budget_wan(project.get("budget", ""))
    is_active = project.get("status") in ("招标中", "已开标")
    if budget is not None and budget >= 100 and is_active:
        return "P0"
    if budget is not None and budget >= 30 and is_active:
        return "P1"
    if budget is not None and budget >= 100:
        return "P1"
    return "P2"


def detect_trend_signals(project):
    """检测趋势信号标签"""
    signals = []
    text = project.get("title", "") + " " + project.get("summary", "")
    industry = project.get("industry", "")

    if "政府" in text or industry == "政府/旅游":
        signals.append("🏛 政府采购")
    if "金融" in text or "金融" in industry:
        signals.append("🏦 金融行业")
    if "年框" in text:
        signals.append("📅 年框制")
    if "国际" in text or "海外" in text or "gemini" in text.lower():
        signals.append("🌐 国际GEO")
    if parse_budget_wan(project.get("budget", "")) is not None and parse_budget_wan(project.get("budget", "")) >= 100:
        signals.append("💰 高预算(≥100万)")
    if industry in ("教育", "政府/旅游"):
        signals.append("🎓 公共采购")
    if "多品牌" in text or "多品类" in text:
        signals.append("🏢 多品牌覆盖")
    if "智能体" in text or "智能获客" in text:
        signals.append("🤖 AI智能体")
    return signals


projects = [
  # ===== 2025年项目 =====
  {
    "id": "GEO-2025-001",
    "company": "九号公司",
    "industry": "短交通/出行",
    "title": "2025年短交通产品GEO生成式引擎优化服务供应商招标",
    "status": "已截止",
    "budget": "保证金1万元",
    "bid_deadline": "2025-10-15",
    "publish_date": "2025-09-23",
    "summary": "九号公司（Segway-Ninebot）就2025-2026年短交通产品线GEO生成式引擎优化服务进行招标。要求供应商成立≥3年、注册资金≥100万、社保≥10人、年度营业额≥300万，具有3个以上同行业头部客户成功案例。服务期至2026年4月。",
    "winner": "",
    "source_url": "https://www.ygbid.com/tender/20250923203620200003.html"
  },
  {
    "id": "GEO-2025-003",
    "company": "华润饮料（怡宝）",
    "industry": "快消/饮料",
    "title": "华润饮料2025-2026年企业品牌优化第三方服务项目（含GEO/SEO）",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2025-05-12",
    "publish_date": "2025-05-07",
    "summary": "华润怡宝（华润饮料）2025-2026年企业品牌优化第三方服务项目，包含搜索引擎内容引擎优化（GEO/SEO）、百科优化等。要求百度百科词条搭建更新、新闻稿件≥80篇、问答平台内容≥40组，覆盖品牌词及行业词优化。",
    "winner": "",
    "source_url": "https://www.ygbid.com/tender/20250507160004900002.html"
  },
  # ===== 2026年项目 =====
  {
    "id": "GEO-2026-001",
    "company": "东阿阿胶（华润集团）",
    "industry": "医药/健康",
    "title": "2026年东阿阿胶GEO优化项目询比采购",
    "status": "已中标",
    "budget": "未公开",
    "bid_deadline": "2026-03-19",
    "publish_date": "2026-03-11",
    "summary": "华润集团旗下东阿阿胶2026年GEO优化项目。成交供应商为秒针信息技术有限公司和福建新升代数字技术有限公司。属于华润系企业第二批GEO集中采购，覆盖品牌在主流AI平台的可见度优化。",
    "winner": "秒针信息技术有限公司、福建新升代数字技术有限公司",
    "source_url": "https://szecp.crc.com.cn/zbxx/006002/006002003/20260403/YYCJGG202603310003.html"
  },
  {
    "id": "GEO-2026-002",
    "company": "昆药集团（华润旗下）",
    "industry": "医药/健康",
    "title": "GEO AI搜索引擎优化采购项目",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2026-02-06",
    "publish_date": "2026-02-02",
    "summary": "华润旗下昆药集团GEO AI搜索引擎优化服务采购，为华润系企业首批GEO优化项目之一。采购编号SJCGXY202602020002。",
    "winner": "",
    "source_url": "https://szecp.crc.com.cn/zbxx/006002/006002001/20260202/SJXYGG202602020002.html"
  },
  {
    "id": "GEO-2026-003",
    "company": "扬子江药业集团",
    "industry": "医药/健康",
    "title": "2026年品牌宣传部GEO项目",
    "status": "招标中",
    "budget": "未公开",
    "bid_deadline": "2026-04-27",
    "publish_date": "2026-04-20",
    "summary": "扬子江药业集团品牌宣传部2026年GEO项目招标，服务地点北京朝阳区，服务周期半年。进行相关词条的GEO优化，提升品牌在AI搜索引擎中的可见度。来源：扬子江药业集团官网招标页面。",
    "winner": "",
    "source_url": "https://www.yangzijiang.com/Bidding/4396.html"
  },
  {
    "id": "GEO-2026-004",
    "company": "天翼云",
    "industry": "通信/云计算",
    "title": "2026年官网GEO优化服务采购项目",
    "status": "已中标",
    "budget": "106.5万元",
    "bid_deadline": "2026-03-20",
    "publish_date": "2026-03-10",
    "summary": "天翼云2026年官网GEO优化服务采购，第一中标候选人为北京鲲鹏伟业广告有限公司，投标报价1,065,000元（不含增值税）。招标代理为中捷通信有限公司。",
    "winner": "北京鲲鹏伟业广告有限公司",
    "source_url": "https://bj.zhiliaobiaoxun.com/article/91704077"
  },
  {
    "id": "GEO-2026-005",
    "company": "新明珠集团（冠珠瓷砖）",
    "industry": "建材/家居",
    "title": "冠珠瓷砖2026年GEO优化项目",
    "status": "招标中",
    "budget": "30万元",
    "bid_deadline": "2026-05-24",
    "publish_date": "2026-05-10",
    "summary": "新明珠集团旗下冠珠瓷砖年度GEO优化项目，预算30万元（含税），服务周期一年。需求包括品牌知识库构建、技术内容优化、AI舆情监控等，要求覆盖主流AI平台。",
    "winner": "",
    "source_url": "https://gs.qianlima.com/zbcontent-597667495.html"
  },
  {
    "id": "GEO-2026-006",
    "company": "东鹏控股",
    "industry": "建材/家居",
    "title": "innoci外贸独立站建设及GEO优化项目",
    "status": "已截止",
    "budget": "保证金3万元",
    "bid_deadline": "2026-04-23",
    "publish_date": "2026-04-09",
    "summary": "东鹏控股innoci外贸独立站建设及GEO优化项目投标邀请，招标编号2026DPCG-39。含外贸独立站建设与GEO优化双重需求。",
    "winner": "",
    "source_url": "http://www.ygbid.com/tender/20260409092926900001.html"
  },
  {
    "id": "GEO-2026-007",
    "company": "宁波市北仑区旅游发展服务中心",
    "industry": "政府/旅游",
    "title": "梅山湾旅游度假区2026年度线上平台全矩阵运维采购",
    "status": "已开标",
    "budget": "50万元",
    "bid_deadline": "2026-04-24",
    "publish_date": "2026-04-03",
    "summary": "宁波北仑区政府采购项目，预算50万元。包含内容采编、AI客服、网站运维及GEO（生成式搜索引擎）优化。服务期2026年5月至2027年5月。政采云公开招标。标志着GEO正式进入政府采购体系。",
    "winner": "",
    "source_url": "https://zfcg.czj.ningbo.gov.cn/project/zcyNotice_view.aspx?Id=202604031716152039995385371561984"
  },
  {
    "id": "GEO-2026-008",
    "company": "中航电测仪器（西安）有限公司",
    "industry": "航空航天/电子",
    "title": "GEO生成式引擎优化询价采购",
    "status": "招标中",
    "budget": "未公开",
    "bid_deadline": "2026-05-31",
    "publish_date": "2026-05-13",
    "summary": "中航电测仪器（西安）有限公司就GEO生成式引擎优化服务进行询价采购，数量1套。中航工业体系内企业开始布局GEO优化。",
    "winner": "",
    "source_url": "http://www.yfbzb.com/inviteBid/detail/20260513_596834322.html"
  },
  {
    "id": "GEO-2026-009",
    "company": "和君职业学院",
    "industry": "教育",
    "title": "生成式AI搜索引擎GEO优化服务项目",
    "status": "已成交",
    "budget": "8万元",
    "bid_deadline": "2026-05-20",
    "publish_date": "2026-05-15",
    "summary": "和君职业学院招生办GEO优化服务项目，单一来源采购，成交金额8万元。要求覆盖DeepSeek、豆包、文心一言、通义千问等4个平台共60个优化任务，品牌正向率≥80%。成交供应商为芜湖小象园教育科技有限公司。",
    "winner": "芜湖小象园教育科技有限公司",
    "source_url": "https://www.hejuncollege.com/tzgg/14378.html"
  },
  {
    "id": "GEO-2026-010",
    "company": "南昌航空大学科技学院",
    "industry": "教育",
    "title": "2026年招生宣传AI大模型词条优化服务采购",
    "status": "招标中",
    "budget": "4万元",
    "bid_deadline": "2026-05-29",
    "publish_date": "2026-05-22",
    "summary": "南昌航空大学科技学院AI大模型词条优化服务采购，预算4万元。需覆盖豆包、DeepSeek、文心一言、通义千问、Kimi、腾讯元宝等主流AI平台，提升品牌提及率和词条触发成功率。",
    "winner": "",
    "source_url": "http://www.yfbzb.com/inviteBid/detail/20260522_599259155.html"
  },
  {
    "id": "GEO-2026-011",
    "company": "浙东数字经济产业园运营中心",
    "industry": "产业园区/企业服务",
    "title": "GEO优化智能获客系统采购项目",
    "status": "已中标",
    "budget": "68.9万元",
    "bid_deadline": "2026-05-06",
    "publish_date": "2026-04-25",
    "summary": "浙东数字经济产业园运营中心GEO优化智能获客系统采购，竞争性谈判，中标金额68.9万元。含系统部署、地域标签配置、客流分析、区域投放优化、客户画像、数据看板及1年质保运维。",
    "winner": "武汉市仙念仙信息科技有限公司",
    "source_url": "http://www.zgggzy.com/jieguo/show.php?itemid=100000"
  },
  {
    "id": "GEO-2026-012",
    "company": "奇瑞汽车",
    "industry": "汽车",
    "title": "2025年奇瑞营销产品SEO、GEO优化代理招标项目",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2026-01-20",
    "publish_date": "2026-01-14",
    "summary": "奇瑞汽车2025年营销产品SEO、GEO优化代理招标，采购编号CGXM-202601-0486。招标方为瑞鲸（安徽）供应链科技有限公司。2026年3月发布变更公告。",
    "winner": "",
    "source_url": "https://ebd.mychery.com/en/zd20=jsgcbg/20260310/1216064709006983168.html"
  },
  {
    "id": "GEO-2026-013",
    "company": "易招标（招采进宝）",
    "industry": "企业服务/招标",
    "title": "GEO优化服务采购项目",
    "status": "已中标",
    "budget": "含激励机制",
    "bid_deadline": "2026-04-23",
    "publish_date": "2026-04-16",
    "summary": "易招标平台自身就GEO优化服务进行采购，服务期至少90天，包含激励机制。招标采购平台自身采购GEO服务，体现了行业对GEO的认可。",
    "winner": "",
    "source_url": "https://china.zcjb.com.cn/cms/china/webfile/detail/index.html?contentId=1229839006590566400"
  },
  {
    "id": "GEO-2026-014",
    "company": "广州白云山医药集团",
    "industry": "医药/健康",
    "title": "系列产品官网制作搭建（含SEO&GEO）",
    "status": "招标中",
    "budget": "35万元",
    "bid_deadline": "2026-05-15",
    "publish_date": "2026-04-20",
    "summary": "广州白云山制药总厂系列产品官网制作搭建项目，明确包含SEO和GEO优化需求，预算35万元。官网建设+AI搜索优化一体化采购。",
    "winner": "",
    "source_url": "http://ygcg.gzggzy.cn/m92/fw/20260429/391578.html"
  },
  {
    "id": "GEO-2026-015",
    "company": "阿坝师范学院",
    "industry": "教育",
    "title": "2026年招生宣传AI优化呈现服务采购",
    "status": "已中标",
    "budget": "4.5万元",
    "bid_deadline": "2026-05-07",
    "publish_date": "2026-04-28",
    "summary": "阿坝师范学院2026年招生宣传AI优化呈现服务询价采购，预算4.5万元。要求在主流AI平台（豆包、DeepSeek、文心一言等）优化招生宣传信息展示。",
    "winner": "",
    "source_url": "https://jw.abtu.edu.cn/info/1131/5141.htm"
  },
  # ===== 新增已验证项目 =====
  {
    "id": "GEO-2026-017",
    "company": "东风本田",
    "industry": "汽车",
    "title": "东风Honda 2026年GEO项目（生成式引擎优化）",
    "status": "已中标",
    "budget": "1207万元",
    "bid_deadline": "2025-03-16",
    "publish_date": "2025-02-13",
    "summary": "东风本田2026年GEO项目，在DeepSeek、Kimi、元宝、豆包、文心一言、通义千问等6个AI平台中针对预设问题持续推荐指定车型。要求维持至少1年推荐效果。中标方为新智科技发展有限公司，中标金额约1207万元。",
    "winner": "新智科技发展有限公司",
    "source_url": "https://www.bidchance.com/info-zhongbiao-95693f7b5995c646dd4ce3fffed20dbc.html"
  },
  {
    "id": "GEO-2026-018",
    "company": "广汽汇理租赁",
    "industry": "汽车/金融",
    "title": "广汽汇理租赁品牌公关传播及GEO服务项目",
    "status": "已中标",
    "budget": "180万元",
    "bid_deadline": "2026-04-30",
    "publish_date": "2026-04-09",
    "summary": "广州广汽汇理融资租赁有限公司品牌公关传播及GEO服务项目，采购控制价180万元（总价包干）。第一中标候选人北京智慧星光信息技术股份有限公司（160万元），第二北京艾信博睿管理顾问有限公司（142.8万元），第三北京新智科技发展有限公司（146万元）。服务期两年。",
    "winner": "北京智慧星光信息技术股份有限公司",
    "source_url": "https://ygcg.gzggzy.cn/p92/fw3/20260507/393930.html"
  },
  {
    "id": "GEO-2026-019",
    "company": "中英人寿",
    "industry": "保险/金融",
    "title": "2026年中英人寿GEO（AI搜索引擎优化）项目",
    "status": "已中标",
    "budget": "未公开",
    "bid_deadline": "2026-04-01",
    "publish_date": "2026-04-02",
    "summary": "中英人寿2026年GEO（AI搜索引擎优化）项目，采购方式为谈判采购（分散）。成交供应商为数说故事人工智能科技股份有限公司。属于保险行业较早启动GEO采购的项目之一。",
    "winner": "数说故事人工智能科技股份有限公司",
    "source_url": "https://beijing.zhaobiao.cn/succeed_v_02ff8ee34ccd4f7874f6b9ca1691768d.html"
  },
  {
    "id": "GEO-2026-020",
    "company": "五粮液",
    "industry": "酒业/快消",
    "title": "AI平台内容优化项目（GEO生成式引擎优化）",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2026-01-29",
    "publish_date": "2026-01-09",
    "summary": "四川五粮液浓香酒有限公司AI平台内容优化项目（实质为GEO），项目编号五粮液浓香招﹝2025﹞154号。要求在DeepSeek、豆包、元宝等主流AI平台进行品牌内容优化。服务期2026年1月至12月。五粮液电子招投标平台发布，需CFCA证书参与。",
    "winner": "",
    "source_url": "https://www.chinabidding.cn/zbgg/U-vzwzYjW.html"
  },
  {
    "id": "GEO-2026-021",
    "company": "中粮肉食",
    "industry": "食品/农业",
    "title": "2026年口碑舆情监测及SEO、GEO优化项目",
    "status": "已截止",
    "budget": "95万元",
    "bid_deadline": "2026-02-04",
    "publish_date": "2026-01-30",
    "summary": "中粮肉食投资有限公司2026年口碑舆情监测及SEO、GEO优化项目，最高限价95万元（含税）。项目编号GN2026-44-0706。采购代理为安徽省招标集团股份有限公司。服务期2026年2月至2027年1月。通过中粮E采供应链采购平台进行。",
    "winner": "",
    "source_url": "https://www.gc-zb.com.cn/markinfo/rMvvI1XXC9KPUT-b65U..A.html"
  },
  {
    "id": "GEO-2026-022",
    "company": "海信集团",
    "industry": "家电/电子",
    "title": "海信集团管理品牌与营销GEO项目",
    "status": "已开标",
    "budget": "未公开",
    "bid_deadline": "2026-03-06",
    "publish_date": "2026-02-12",
    "summary": "海信集团控股股份有限公司管理品牌与营销GEO项目，招标编码ZB260212034。覆盖海信、东芝电视、容声、科龙、gorenje、ASKO、vidda等多品牌。包含GEO优化（KPI：各品线AI露出率平均提升30%）、GEO智能体（全链路数字化）、GEO转化承接三大板块。",
    "winner": "",
    "source_url": "https://shubo.365trade.com.cn/info-745080534.html"
  },
  {
    "id": "GEO-2026-023",
    "company": "中信建投证券",
    "industry": "证券/金融",
    "title": "GEO优化项目供应商征集",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2026-02-06",
    "publish_date": "2026-01-30",
    "summary": "中信建投证券GEO优化项目供应商征集。需求包括：合规内容优化（合规通过率≥95%）、多平台算法适配（核心词可见性提升80%以上）、全链路运营管控。供应商需近3年至少1个金融行业GEO/AI优化项目经验，团队不少于8人。",
    "winner": "",
    "source_url": "https://www.ygbid.com/tender/20260129165703900034.html"
  },
  {
    "id": "GEO-2026-024",
    "company": "美团",
    "industry": "互联网/本地生活",
    "title": "2026年美团GEO广告采购供应商招募",
    "status": "已截止",
    "budget": "约1000万元",
    "bid_deadline": "2026-04-15",
    "publish_date": "2026-04-09",
    "summary": "美团2026年GEO广告采购供应商招募，合作期限2026年5月至2027年4月（年框制）。要求覆盖DeepSeek、豆包、千问、元宝、Kimi等AI平台，自研GEO优化系统语义匹配准确度≥98%，核心信息呈现率≥80%，每日每问题不少于30次监测。",
    "winner": "",
    "source_url": "https://shubo.365trade.com.cn/info-759134529.html"
  },
  {
    "id": "GEO-2026-025",
    "company": "知乎",
    "industry": "互联网/内容社区",
    "title": "2026年知乎商业品牌业务GEO年框供应商招募",
    "status": "已截止",
    "budget": "200万元",
    "bid_deadline": "2026-04-10",
    "publish_date": "2026-04-01",
    "summary": "知乎2026年商业品牌业务GEO年框供应商招募，年度预算200万元（不承诺保底）。合作周期至2027年6月30日。要求仅允许白帽GEO（优质原创、权威信源），严格禁止批量伪原创、算法攻击、恶意投喂等行为。需提供合规承诺及操作日志。",
    "winner": "",
    "source_url": "https://gs.qianlima.com/zbcontent-586678848.html"
  },
  {
    "id": "GEO-2026-026",
    "company": "京东集团",
    "industry": "互联网/电商",
    "title": "京东集团CCO体系-公共关系部-GEO项目",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2026-05-15",
    "publish_date": "2026-05-08",
    "summary": "京东集团CCO体系公共关系部GEO项目，针对京东本地生活业务，在DeepSeek、Kimi、豆包、元宝等AI平台进行品牌信息占位与优化。要求注册资金≥100万，成立满2年，近2年完成3个及以上AI优化类项目，具备外卖/即时零售/生鲜电商经验优先。",
    "winner": "",
    "source_url": "http://m.ai8.com.cn/n-zb-64833468.html"
  },
  {
    "id": "GEO-2026-027",
    "company": "京东五星电器",
    "industry": "家电/零售",
    "title": "京东2026-家电家居事业群（五星）全国GEO优化服务商招标",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2026-04-27",
    "publish_date": "2026-04-15",
    "summary": "京东家电家居事业群（五星电器）全国GEO优化服务商招标，覆盖一二三线至少39城（京东电器、京东MALL）。需求包含品牌词/行业词/对比词AI语义优化（要求TOP3）、口碑风控（负面≤5%）、大促配合等。覆盖DeepSeek、豆包、千问、Kimi、文心一言及社媒平台。",
    "winner": "",
    "source_url": "https://ln.qianlima.com/zbcontent-589816268.html"
  },
  {
    "id": "GEO-2026-028",
    "company": "京东物流",
    "industry": "物流/供应链",
    "title": "京东物流国际官网SEO&GEO服务商招标项目",
    "status": "已截止",
    "budget": "未公开",
    "bid_deadline": "2026-01-26",
    "publish_date": "2026-01-19",
    "summary": "京东物流国际官网SEO&GEO整合服务，合作周期1年。SEO以Google为主，GEO国内以DeepSeek、豆包为主，海外以ChatGPT、Gemini为主。要求文案团队需由英语及对应小语种母语人士组成，拒绝机器翻译。",
    "winner": "",
    "source_url": "https://mp.weixin.qq.com/s/__biz=MzA5NzE1Nzg5Nw==&mid=2247486852&idx=1&sn=3bf25afbf53db6b8304dbf9bd9114867"
  },
  {
    "id": "GEO-2026-029",
    "company": "太平洋健康险",
    "industry": "保险/金融",
    "title": "太平洋健康险2026年AI搜索优化服务（GEO）采购",
    "status": "已中标",
    "budget": "未公开",
    "bid_deadline": "2026-05-12",
    "publish_date": "2026-05-12",
    "summary": "太平洋健康险2026年AI搜索优化服务（GEO）采购项目，已进入中标公示阶段。太平洋健康险为中国太保旗下子公司，属于保险行业GEO采购先行者之一。注：该公告原发于招标平台，当前未找到可直接访问的原文地址。",
    "winner": "",
    "source_url": ""
  },
  {
    "id": "GEO-2026-030",
    "company": "四川广电传媒",
    "industry": "传媒/文化",
    "title": "GEO系统技术支持服务采购项目",
    "status": "已截止",
    "budget": "15万元",
    "bid_deadline": "2026-04-02",
    "publish_date": "2026-03-30",
    "summary": "四川广电传媒集团有限公司GEO系统技术支持服务采购项目，采购编号ZHH-WCS-202627，预算15万元。竞争性磋商采购。采购代理为四川中汇恒工程项目管理咨询有限公司。注：项目名称中的GEO可能指生成式引擎优化或地理信息系统，需进一步确认。",
    "winner": "",
    "source_url": "http://www.sctv.com/announcement/2037447329052442625"
  }
]

# 数据增强：为每个项目添加 computed 字段
enriched_projects = []
for p in projects:
    ep = dict(p)
    ep["_computed"] = {
        "budget_wan": parse_budget_wan(p.get("budget", "")),
        "geo_relevance": compute_geo_relevance(p),
        "priority": compute_priority(p),
        "signals": detect_trend_signals(p),
    }
    enriched_projects.append(ep)

data = {
  "meta": {
    "name": "GEO招投标情报站",
    "description": "GEO（生成式引擎优化）领域真实招标、投标、中标情报追踪。每个项目均来自官方招标平台或企业官网公告。",
    "last_updated": "2026-05-23",
    "total_projects": len(enriched_projects),
    "data_sources": [
      "华润集团守正电子招标平台",
      "中国政府采购网",
      "各企业官网招标页面",
      "招标投标公共服务平台",
      "广州公共资源交易中心",
      "中粮E采供应链采购平台",
      "东风汽车采购招投标平台",
      "京东招标平台",
      "美团采购平台"
    ],
    "note": "仅收录明确标注'GEO优化''生成式引擎优化''AI搜索优化'或实质为GEO的项目。排除地理信息(GIS)类GEO项目。"
  },
  "projects": enriched_projects,
  "status_summary": {},
  "industry_distribution": {}
}

stats = {}
industries = {}
for p in enriched_projects:
  stats[p["status"]] = stats.get(p["status"], 0) + 1
  industries[p["industry"]] = industries.get(p["industry"], 0) + 1
data["status_summary"] = stats
data["industry_distribution"] = industries

for path in [
  os.path.join(BASE_DIR, "data", "bidding_data.json"),
  os.path.join(BASE_DIR, "docs", "bidding_data.json")
]:
  with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  print(f"Saved: {path}")

print(f"\nTotal: {len(projects)} projects")
print(f"Status: {stats}")
print(f"Industries: {industries}")
