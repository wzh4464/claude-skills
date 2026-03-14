#!/usr/bin/env python3
"""
AI 行业新闻 RSS 聚合脚本
用于 start-my-day skill，从 AI 公司博客和技术媒体获取最新动态

灵感来源：
- ai-daily-digest: 多源 RSS 聚合 + 多维评分
- daily-tech-news: 多层级源策略 + 去重
- ai-daily: RSS 解析 + 分类输出
"""

import xml.etree.ElementTree as ET
import json
import re
import os
import sys
import time
import html
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from email.utils import parsedate_to_datetime
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 默认新闻源（按层级组织）
# 灵感来源: daily-tech-news 的多层级源策略
# ---------------------------------------------------------------------------
DEFAULT_NEWS_SOURCES = [
    # Tier 1: AI 公司官方博客（权威性最高）
    # 注意：Anthropic 和 Meta AI 目前没有公开 RSS，如有变动可在 config.yaml 中添加
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "tier": 1, "category": "ai-company"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "tier": 1, "category": "ai-company"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml", "tier": 1, "category": "ai-company"},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/", "tier": 1, "category": "ai-company"},
    {"name": "Meta Engineering", "url": "https://engineering.fb.com/feed/", "tier": 1, "category": "ai-company"},

    # Tier 2: AI 社区和专业媒体
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "tier": 2, "category": "ai-community"},
    {"name": "AI News (smol.ai)", "url": "https://buttondown.com/ainews/rss", "tier": 2, "category": "ai-news"},
    {"name": "The Gradient", "url": "https://thegradient.pub/rss/", "tier": 2, "category": "ai-community"},

    # Tier 3: 知名研究者博客
    {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/", "tier": 3, "category": "researcher"},
    {"name": "Lilian Weng", "url": "https://lilianweng.github.io/index.xml", "tier": 3, "category": "researcher"},
    {"name": "Sebastian Raschka", "url": "https://magazine.sebastianraschka.com/feed", "tier": 3, "category": "researcher"},
]

# ---------------------------------------------------------------------------
# 评分常量
# 灵感来源: ai-daily-digest 的三维评分 + daily-tech-news 的五维评分
# ---------------------------------------------------------------------------

# 相关性：关键词匹配加分
RELEVANCE_TITLE_KEYWORD_BOOST = 1.0
RELEVANCE_BODY_KEYWORD_BOOST = 0.5

# 层级加分（Tier 1 公司博客权威性最高）
TIER_BONUS = {1: 2.0, 2: 1.0, 3: 0.5}

# 时效性加分（越新越好）
RECENCY_BONUS_HOURS = {24: 3.0, 48: 2.0, 72: 1.5, 168: 1.0}

# 综合评分权重
WEIGHTS = {
    'relevance': 0.40,   # 与研究兴趣的相关性
    'tier': 0.25,        # 来源权威性
    'recency': 0.35,     # 时效性
}

# 评分归一化基准
SCORE_MAX_RELEVANCE = 5.0
SCORE_MAX_TIER = 2.0
SCORE_MAX_RECENCY = 3.0


def load_config(config_path: str) -> Dict:
    """加载研究配置文件"""
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed, using empty config")
        return {}
    except Exception as e:
        logger.warning("Failed to load config %s: %s", config_path, e)
        return {}


def get_news_sources(config: Dict) -> List[Dict]:
    """从配置获取新闻源，回退到默认列表"""
    sources = config.get('news_sources', [])
    if sources:
        return sources
    return DEFAULT_NEWS_SOURCES


# ---------------------------------------------------------------------------
# RSS/Atom 解析
# ---------------------------------------------------------------------------

def parse_rss_date(date_str: str) -> Optional[datetime]:
    """
    解析 RSS/Atom 日期格式
    支持 RFC 2822 (RSS) 和 ISO 8601 (Atom) 两种格式
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # RFC 2822 格式 (RSS pubDate)
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass

    # ISO 8601 格式 (Atom published/updated)
    for fmt in [
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    logger.debug("Could not parse date: %s", date_str)
    return None


def strip_html(text: str) -> str:
    """移除 HTML 标签，保留纯文本"""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_feed(source: Dict, timeout: int = 15) -> List[Dict]:
    """
    获取并解析单个 RSS/Atom 源

    灵感来源: ai-daily-digest 的优雅降级策略 - 失败的源直接跳过

    Args:
        source: 源配置 {name, url, tier, category}
        timeout: 超时秒数

    Returns:
        文章列表
    """
    url = source['url']
    name = source.get('name', url)

    logger.info("[RSS] Fetching: %s", name)

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'StartMyDay-NewsFetcher/1.0 (Research Paper Recommender)',
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode('utf-8', errors='replace')
    except Exception as e:
        logger.warning("[RSS] Failed to fetch %s: %s", name, e)
        return []

    # 解析 XML
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.warning("[RSS] Failed to parse XML from %s: %s", name, e)
        return []

    # 检测 Feed 类型并解析
    tag = root.tag.lower()
    if '}feed' in tag or tag == 'feed':
        articles = parse_atom_feed(root, source)
    elif tag == 'rss' or root.find('channel') is not None:
        articles = parse_rss_feed(root, source)
    else:
        # 尝试两种格式
        articles = parse_rss_feed(root, source)
        if not articles:
            articles = parse_atom_feed(root, source)

    logger.info("[RSS] Got %d articles from %s", len(articles), name)
    return articles


def parse_rss_feed(root: ET.Element, source: Dict) -> List[Dict]:
    """解析 RSS 2.0 格式"""
    articles = []

    channel = root.find('channel')
    if channel is None:
        channel = root

    for item in channel.findall('item'):
        article = _make_article_base(source)

        title_el = item.find('title')
        if title_el is not None and title_el.text:
            article['title'] = strip_html(title_el.text.strip())

        link_el = item.find('link')
        if link_el is not None and link_el.text:
            article['link'] = link_el.text.strip()

        desc_el = item.find('description')
        if desc_el is not None and desc_el.text:
            article['description'] = strip_html(desc_el.text)

        # content:encoded (完整内容)
        content_el = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        if content_el is not None and content_el.text:
            article['content'] = strip_html(content_el.text)

        # 发布日期
        pub_el = item.find('pubDate')
        if pub_el is not None and pub_el.text:
            article['published_date'] = parse_rss_date(pub_el.text)
            article['published_str'] = pub_el.text.strip()

        # dc:date 回退
        if 'published_date' not in article:
            dc_date = item.find('{http://purl.org/dc/elements/1.1/}date')
            if dc_date is not None and dc_date.text:
                article['published_date'] = parse_rss_date(dc_date.text)
                article['published_str'] = dc_date.text.strip()

        # 作者
        author_el = item.find('{http://purl.org/dc/elements/1.1/}creator')
        if author_el is None:
            author_el = item.find('author')
        if author_el is not None and author_el.text:
            article['author'] = author_el.text.strip()

        if article.get('title'):
            articles.append(article)

    return articles


def parse_atom_feed(root: ET.Element, source: Dict) -> List[Dict]:
    """解析 Atom 格式"""
    articles = []

    # 处理命名空间
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'

    for entry in root.findall(f'{ns}entry'):
        article = _make_article_base(source)

        title_el = entry.find(f'{ns}title')
        if title_el is not None and title_el.text:
            article['title'] = strip_html(title_el.text.strip())

        # Atom link
        for link_el in entry.findall(f'{ns}link'):
            rel = link_el.get('rel', 'alternate')
            if rel in ('alternate', ''):
                href = link_el.get('href', '')
                if href:
                    article['link'] = href
                    break

        summary_el = entry.find(f'{ns}summary')
        if summary_el is not None and summary_el.text:
            article['description'] = strip_html(summary_el.text)

        content_el = entry.find(f'{ns}content')
        if content_el is not None and content_el.text:
            article['content'] = strip_html(content_el.text)

        # 发布日期 (优先 published，回退 updated)
        for date_tag in ['published', 'updated']:
            date_el = entry.find(f'{ns}{date_tag}')
            if date_el is not None and date_el.text:
                article['published_date'] = parse_rss_date(date_el.text)
                article['published_str'] = date_el.text.strip()
                break

        # 作者
        author_el = entry.find(f'{ns}author')
        if author_el is not None:
            name_el = author_el.find(f'{ns}name')
            if name_el is not None and name_el.text:
                article['author'] = name_el.text.strip()

        if article.get('title'):
            articles.append(article)

    return articles


def _make_article_base(source: Dict) -> Dict:
    """创建文章基础字典"""
    return {
        'source_name': source.get('name', ''),
        'source_url': source.get('url', ''),
        'source_tier': source.get('tier', 3),
        'source_category': source.get('category', 'other'),
    }


# ---------------------------------------------------------------------------
# 评分系统
# 灵感来源:
# - ai-daily-digest: relevance + quality + timeliness 三维评分
# - daily-tech-news: impact + practicality + novelty + depth + authority 五维评分
# 这里简化为: relevance + tier(authority) + recency 三维评分
# ---------------------------------------------------------------------------

def calculate_article_relevance(article: Dict, config: Dict) -> Tuple[float, List[str]]:
    """
    计算文章与研究兴趣的相关性

    Returns:
        (相关性评分, 匹配的关键词列表)
    """
    title = article.get('title', '').lower()
    desc = article.get('description', '').lower()
    content = article.get('content', '').lower()
    text = f"{title} {desc} {content}"

    domains = config.get('research_domains', {})
    excluded = [kw.lower() for kw in config.get('excluded_keywords', [])]

    # 排除关键词检查
    for kw in excluded:
        if kw in title:
            return 0, []

    score = 0.0
    matched_keywords = set()

    for domain_name, domain_config in domains.items():
        for keyword in domain_config.get('keywords', []):
            kw_lower = keyword.lower()
            if kw_lower in title:
                score += RELEVANCE_TITLE_KEYWORD_BOOST
                matched_keywords.add(keyword)
            elif kw_lower in text:
                score += RELEVANCE_BODY_KEYWORD_BOOST
                matched_keywords.add(keyword)

    return score, list(matched_keywords)


def calculate_recency_bonus(published_date: Optional[datetime]) -> float:
    """计算时效性加分"""
    if not published_date:
        return 0

    now = datetime.now(timezone.utc)
    if published_date.tzinfo is None:
        published_date = published_date.replace(tzinfo=timezone.utc)

    hours_ago = (now - published_date).total_seconds() / 3600

    for max_hours, bonus in sorted(RECENCY_BONUS_HOURS.items()):
        if hours_ago <= max_hours:
            return bonus
    return 0


def score_article(article: Dict, config: Dict) -> Dict:
    """
    为文章计算综合评分

    综合评分 = relevance(40%) + tier(25%) + recency(35%)
    归一化到 0-10 分
    """
    # 相关性
    relevance, matched_keywords = calculate_article_relevance(article, config)

    # 层级加分
    tier = article.get('source_tier', 3)
    tier_bonus = TIER_BONUS.get(tier, 0)

    # 时效性
    recency = calculate_recency_bonus(article.get('published_date'))

    # 归一化到 0-10
    norm_relevance = min(relevance / SCORE_MAX_RELEVANCE, 1.0) * 10
    norm_tier = min(tier_bonus / SCORE_MAX_TIER, 1.0) * 10
    norm_recency = min(recency / SCORE_MAX_RECENCY, 1.0) * 10

    final_score = (
        norm_relevance * WEIGHTS['relevance'] +
        norm_tier * WEIGHTS['tier'] +
        norm_recency * WEIGHTS['recency']
    )

    article['scores'] = {
        'relevance': round(relevance, 2),
        'tier_bonus': round(tier_bonus, 2),
        'recency': round(recency, 2),
        'final': round(final_score, 2),
    }
    article['matched_keywords'] = matched_keywords

    return article


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def fetch_and_filter_news(
    config: Dict,
    hours: int = 72,
    top_n: int = 15,
) -> Dict:
    """
    主流程：获取、过滤、评分新闻

    灵感来源:
    - ai-daily-digest: 并发获取 + 优雅降级（失败跳过）
    - daily-tech-news: 去重 + 按重要性排序

    Args:
        config: 研究配置
        hours: 时间窗口（小时）
        top_n: 返回前 N 篇

    Returns:
        结果字典
    """
    sources = get_news_sources(config)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    logger.info("=" * 70)
    logger.info("Fetching news from %d sources (last %d hours)", len(sources), hours)
    logger.info("=" * 70)

    all_articles = []
    failed_sources = []
    successful_sources = []

    for source in sources:
        articles = fetch_feed(source)
        if not articles:
            failed_sources.append(source.get('name', source['url']))
            continue

        successful_sources.append(source.get('name', source['url']))

        # 按时间过滤
        for article in articles:
            pub_date = article.get('published_date')
            if pub_date:
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                if pub_date >= cutoff:
                    all_articles.append(article)
            else:
                # 没有日期信息的也保留（时效性评分为0）
                all_articles.append(article)

        # 友好速率限制
        time.sleep(0.5)

    logger.info("Total articles within time window: %d", len(all_articles))
    if failed_sources:
        logger.warning("Failed sources (%d): %s", len(failed_sources), ", ".join(failed_sources))

    # 评分
    scored = [score_article(a, config) for a in all_articles]

    # 按综合评分排序
    scored.sort(key=lambda x: x['scores']['final'], reverse=True)

    # 去重（基于 URL）
    seen_urls = set()
    unique = []
    for article in scored:
        url = article.get('link', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)
        elif not url:
            unique.append(article)

    top = unique[:top_n]

    # 按来源分类统计
    source_stats = {}
    for article in unique:
        sname = article.get('source_name', 'Unknown')
        source_stats[sname] = source_stats.get(sname, 0) + 1

    # 按 category 分类统计
    category_stats = {}
    for article in unique:
        cat = article.get('source_category', 'other')
        category_stats[cat] = category_stats.get(cat, 0) + 1

    output = {
        'fetch_time': datetime.now(timezone.utc).isoformat(),
        'time_window_hours': hours,
        'total_sources': len(sources),
        'successful_sources': successful_sources,
        'failed_sources': failed_sources,
        'total_articles': len(all_articles),
        'total_unique': len(unique),
        'source_stats': source_stats,
        'category_stats': category_stats,
        'top_articles': top,
    }

    return output


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fetch AI industry news from curated RSS feeds'
    )
    parser.add_argument('--config', type=str,
                        help='Research config file path (config.yaml)')
    parser.add_argument('--output', type=str, default='news_filtered.json',
                        help='Output JSON file path')
    parser.add_argument('--hours', type=int, default=72,
                        help='Time window in hours (default: 72)')
    parser.add_argument('--top-n', type=int, default=15,
                        help='Number of top articles to return (default: 15)')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    config = {}
    if args.config:
        config = load_config(args.config)

    result = fetch_and_filter_news(config, args.hours, args.top_n)

    # 序列化 datetime 对象
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=json_serializer)

    logger.info("Results saved to: %s", args.output)
    logger.info("Top %d articles:", len(result['top_articles']))
    for i, a in enumerate(result['top_articles'], 1):
        logger.info("  %d. [%s] %s (Score: %.1f)",
                     i, a.get('source_name', '?'), a.get('title', '')[:60],
                     a['scores']['final'])

    # 同时输出到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2, default=json_serializer))

    return 0


if __name__ == '__main__':
    sys.exit(main())
