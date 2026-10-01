from __future__ import annotations

import csv
import hashlib
import io
import json
import mimetypes
import os
import re
import secrets
import socket
import sqlite3
import sys
import time
import uuid
import warnings
from http.cookies import SimpleCookie
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from PIL import Image, ImageOps, UnidentifiedImageError


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "frontend" / "dist"
DATA_DIR = Path(os.environ.get("COFFEE_ATLAS_DATA_DIR", str(ROOT / "data"))).expanduser()
DB_PATH = DATA_DIR / "coffee_atlas.db"
UPLOAD_DIR = DATA_DIR / "uploads" / "samples"
MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "4183"))
SESSION_COOKIE = "coffee_atlas_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
PASSWORD_ITERATIONS = 240_000
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
SESSIONS: dict[str, dict] = {}


def session_cookie(token: str, max_age: int) -> str:
    secure = "; Secure" if COOKIE_SECURE else ""
    return f"{SESSION_COOKIE}={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={max_age}{secure}"


CATEGORIES = [
    ("fruit", "水果", "#d95f43", 1),
    ("floral", "花与草本", "#796aa8", 2),
    ("nut", "坚果可可", "#8a5138", 3),
    ("spice", "香料", "#b24f63", 4),
    ("sweet", "甜感", "#d9aa3e", 5),
    ("ferment", "发酵", "#35705a", 6),
]

TAGS = [
    ("citrus", "柑橘", "fruit", "明亮酸质与清爽香气"),
    ("berry", "莓果", "fruit", "草莓、蓝莓、黑莓等浆果调性"),
    ("stone", "核果", "fruit", "桃、杏、李子等甜熟果香"),
    ("jasmine", "茉莉", "floral", "白花香与高海拔水洗常见特征"),
    ("herbal", "草本", "floral", "茶感、香草与植物气息"),
    ("cocoa", "可可", "nut", "黑巧、可可粉、烘焙尾韵"),
    ("almond", "杏仁", "nut", "坚果甜香与油脂感"),
    ("cinnamon", "肉桂", "spice", "温暖辛香调"),
    ("brownSugar", "红糖", "sweet", "焦糖化甜感与圆润口感"),
    ("wine", "酒香", "ferment", "日晒、厌氧处理中的发酵香气"),
]

SAMPLES = [
    {
        "name": "埃塞俄比亚 耶加雪菲 水洗",
        "country": "Ethiopia",
        "region": "Yirgacheffe",
        "latitude": 6.16,
        "longitude": 38.21,
        "species": "Arabica",
        "variety": "Heirloom",
        "process": "水洗",
        "roast": "浅烘",
        "altitude": "1900m",
        "year": "2025",
        "description": "高海拔水洗样本，酸质清晰，带茉莉、柑橘和茶感尾韵。",
        "flavors": {"citrus": 5, "jasmine": 5, "herbal": 3, "stone": 3, "brownSugar": 2},
    },
    {
        "name": "巴拿马 波奎特 瑰夏",
        "country": "Panama",
        "region": "Boquete",
        "latitude": 8.78,
        "longitude": -82.43,
        "species": "Arabica",
        "variety": "Geisha",
        "process": "蜜处理",
        "roast": "浅烘",
        "altitude": "1700m",
        "year": "2024",
        "description": "花香与核果甜感突出，适合作为高端竞赛豆对比样本。",
        "flavors": {"jasmine": 5, "stone": 5, "citrus": 4, "brownSugar": 3, "herbal": 2},
    },
    {
        "name": "哥伦比亚 薇拉 卡杜拉",
        "country": "Colombia",
        "region": "Huila",
        "latitude": 2.54,
        "longitude": -75.53,
        "species": "Arabica",
        "variety": "Caturra",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1800m",
        "year": "2025",
        "description": "甜橙、红糖和可可均衡，适合展示风味强度模型。",
        "flavors": {"citrus": 4, "brownSugar": 4, "cocoa": 3, "stone": 3, "almond": 2},
    },
    {
        "name": "巴西 米纳斯 黄波旁",
        "country": "Brazil",
        "region": "Minas Gerais",
        "latitude": -18.51,
        "longitude": -44.56,
        "species": "Arabica",
        "variety": "Yellow Bourbon",
        "process": "日晒",
        "roast": "中烘",
        "altitude": "1200m",
        "year": "2024",
        "description": "坚果、可可和红糖感突出，酸度较低，适合意式拼配分析。",
        "flavors": {"almond": 5, "cocoa": 5, "brownSugar": 4, "cinnamon": 2, "berry": 1},
    },
    {
        "name": "肯尼亚 涅里 SL28",
        "country": "Kenya",
        "region": "Nyeri",
        "latitude": -0.42,
        "longitude": 36.95,
        "species": "Arabica",
        "variety": "SL28",
        "process": "水洗",
        "roast": "浅烘",
        "altitude": "1750m",
        "year": "2025",
        "description": "黑加仑、柑橘和明亮酸质清楚，适合做高酸样本参照。",
        "flavors": {"berry": 5, "citrus": 5, "brownSugar": 3, "herbal": 2, "jasmine": 2},
    },
    {
        "name": "印度尼西亚 曼特宁 湿刨",
        "country": "Indonesia",
        "region": "Sumatra",
        "latitude": 0.59,
        "longitude": 101.34,
        "species": "Arabica",
        "variety": "Typica",
        "process": "湿刨",
        "roast": "中深烘",
        "altitude": "1400m",
        "year": "2024",
        "description": "草本、香料和厚重可可尾韵，展示非洲豆以外的风味路径。",
        "flavors": {"herbal": 5, "cinnamon": 4, "cocoa": 4, "almond": 3, "brownSugar": 2},
    },
    {
        "name": "哥斯达黎加 塔拉珠 蜜处理",
        "country": "Costa Rica",
        "region": "Tarrazu",
        "latitude": 9.66,
        "longitude": -84.02,
        "species": "Arabica",
        "variety": "Villa Sarchi",
        "process": "蜜处理",
        "roast": "中浅烘",
        "altitude": "1650m",
        "year": "2025",
        "description": "蜂蜜甜、柑橘和杏仁结构清晰，适合处理法对比。",
        "flavors": {"brownSugar": 5, "citrus": 4, "almond": 4, "stone": 3, "jasmine": 2},
    },
    {
        "name": "卢旺达 西部省 波旁",
        "country": "Rwanda",
        "region": "Western Province",
        "latitude": -2.08,
        "longitude": 29.33,
        "species": "Arabica",
        "variety": "Bourbon",
        "process": "厌氧发酵",
        "roast": "浅烘",
        "altitude": "1850m",
        "year": "2025",
        "description": "莓果、酒香和红糖感明显，用于展示发酵处理的流向特征。",
        "flavors": {"berry": 5, "wine": 5, "brownSugar": 4, "citrus": 3, "cocoa": 2},
    },
    {
        "name": "中国 云南保山 小粒咖啡 水洗",
        "country": "China",
        "region": "Baoshan, Yunnan",
        "latitude": 24.95,
        "longitude": 99.16,
        "species": "Arabica",
        "variety": "Catimor / Typica",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1200-1600m",
        "year": "2025",
        "description": "云南保山小粒咖啡样本，坚果甜感、温和果酸与可可尾韵较清晰，适合补充中国咖啡产地分析。",
        "dataSource": "保山公开产区资料整理",
        "flavors": {"almond": 4, "brownSugar": 4, "citrus": 3, "cocoa": 3, "herbal": 2},
    },
    {
        "name": "中国 云南普洱 卡蒂姆 日晒",
        "country": "China",
        "region": "Pu'er, Yunnan",
        "latitude": 22.79,
        "longitude": 100.97,
        "species": "Arabica",
        "variety": "Catimor",
        "process": "日晒",
        "roast": "中烘",
        "altitude": "1100-1500m",
        "year": "2025",
        "description": "云南普洱日晒样本，红糖、核果和柔和莓果感明显，可用于展示中国云南不同产区和处理法差异。",
        "dataSource": "云南公开产区资料整理",
        "flavors": {"brownSugar": 4, "stone": 4, "berry": 3, "cocoa": 3, "wine": 2},
    },
    {
        "name": "危地马拉 安提瓜 波旁",
        "country": "Guatemala",
        "region": "Antigua",
        "latitude": 14.56,
        "longitude": -90.73,
        "species": "Arabica",
        "variety": "Bourbon",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1500-1700m",
        "year": "2025",
        "description": "火山土壤与高海拔环境带来可可、柑橘和焦糖感，酸质明亮但整体平衡。",
        "dataSource": "经典产区资料整理",
        "flavors": {"cocoa": 4, "citrus": 4, "brownSugar": 4, "almond": 3, "stone": 2},
    },
    {
        "name": "洪都拉斯 科潘 卡杜艾",
        "country": "Honduras",
        "region": "Copan",
        "latitude": 14.84,
        "longitude": -88.78,
        "species": "Arabica",
        "variety": "Catuai",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1300-1700m",
        "year": "2025",
        "description": "中美洲常见的均衡型表达，红糖、核果和可可感柔和，适合观察产区与处理法差异。",
        "dataSource": "经典产区资料整理",
        "flavors": {"brownSugar": 5, "stone": 4, "cocoa": 3, "citrus": 3, "almond": 2},
    },
    {
        "name": "萨尔瓦多 阿帕内卡 蜜处理",
        "country": "El Salvador",
        "region": "Apaneca",
        "latitude": 13.86,
        "longitude": -89.85,
        "species": "Arabica",
        "variety": "Bourbon",
        "process": "蜜处理",
        "roast": "中浅烘",
        "altitude": "1300-1600m",
        "year": "2024",
        "description": "蜜处理让红糖、杏仁与成熟核果更集中，口感圆润，甜感收束清晰。",
        "dataSource": "经典产区资料整理",
        "flavors": {"brownSugar": 5, "almond": 4, "stone": 4, "cocoa": 2, "citrus": 2},
    },
    {
        "name": "尼加拉瓜 希诺特加 日晒",
        "country": "Nicaragua",
        "region": "Jinotega",
        "latitude": 13.09,
        "longitude": -86.00,
        "species": "Arabica",
        "variety": "Caturra",
        "process": "日晒",
        "roast": "中浅烘",
        "altitude": "1200-1500m",
        "year": "2025",
        "description": "日晒样本常见熟果、红糖和可可调性，酸质柔和，体现中美洲更甜熟的一面。",
        "dataSource": "经典产区资料整理",
        "flavors": {"stone": 5, "brownSugar": 4, "cocoa": 3, "berry": 3, "citrus": 2},
    },
    {
        "name": "墨西哥 恰帕斯 水洗",
        "country": "Mexico",
        "region": "Chiapas",
        "latitude": 15.10,
        "longitude": -92.30,
        "species": "Arabica",
        "variety": "Bourbon",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1200-1700m",
        "year": "2024",
        "description": "恰帕斯高地样本常有坚果、可可和温和柑橘感，结构干净，甜感稳定。",
        "dataSource": "经典产区资料整理",
        "flavors": {"almond": 4, "cocoa": 4, "citrus": 3, "brownSugar": 3, "herbal": 2},
    },
    {
        "name": "秘鲁 卡哈马卡 水洗",
        "country": "Peru",
        "region": "Cajamarca",
        "latitude": -6.63,
        "longitude": -78.78,
        "species": "Arabica",
        "variety": "Caturra",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1600-2000m",
        "year": "2025",
        "description": "安第斯高地水洗豆通常具有红糖、柑橘和可可感，酸质清晰而不过分尖锐。",
        "dataSource": "经典产区资料整理",
        "flavors": {"citrus": 4, "brownSugar": 4, "cocoa": 3, "stone": 3, "herbal": 2},
    },
    {
        "name": "玻利维亚 卡拉纳维 水洗",
        "country": "Bolivia",
        "region": "Caranavi",
        "latitude": -15.84,
        "longitude": -67.57,
        "species": "Arabica",
        "variety": "Typica",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1400-1700m",
        "year": "2024",
        "description": "高海拔安第斯产区常见核果、柑橘与红糖感，兼具清晰度和柔和甜感。",
        "dataSource": "经典产区资料整理",
        "flavors": {"stone": 4, "citrus": 4, "brownSugar": 4, "jasmine": 2, "almond": 2},
    },
    {
        "name": "厄瓜多尔 洛哈 水洗",
        "country": "Ecuador",
        "region": "Loja",
        "latitude": -4.00,
        "longitude": -79.20,
        "species": "Arabica",
        "variety": "Typica",
        "process": "水洗",
        "roast": "浅烘",
        "altitude": "1700-2100m",
        "year": "2025",
        "description": "洛哈高海拔样本常有花香、柑橘和核果，酸质细致，余韵带轻盈茶感。",
        "dataSource": "经典产区资料整理",
        "flavors": {"jasmine": 4, "citrus": 4, "stone": 3, "herbal": 3, "brownSugar": 2},
    },
    {
        "name": "坦桑尼亚 姆贝亚 波旁",
        "country": "Tanzania",
        "region": "Mbeya",
        "latitude": -8.91,
        "longitude": 33.46,
        "species": "Arabica",
        "variety": "Bourbon",
        "process": "水洗",
        "roast": "浅烘",
        "altitude": "1500-1900m",
        "year": "2025",
        "description": "东非高地样本常见莓果、柑橘和红茶感，酸质明亮并带有干净甜感。",
        "dataSource": "经典产区资料整理",
        "flavors": {"berry": 4, "citrus": 4, "brownSugar": 3, "herbal": 3, "jasmine": 2},
    },
    {
        "name": "乌干达 鲁文佐里 日晒",
        "country": "Uganda",
        "region": "Rwenzori",
        "latitude": 0.35,
        "longitude": 30.10,
        "species": "Arabica",
        "variety": "SL14",
        "process": "日晒",
        "roast": "中浅烘",
        "altitude": "1400-1900m",
        "year": "2024",
        "description": "鲁文佐里山麓日晒豆具有莓果、红糖与可可调性，果感饱满，口感较厚。",
        "dataSource": "经典产区资料整理",
        "flavors": {"berry": 5, "brownSugar": 4, "cocoa": 3, "stone": 3, "wine": 2},
    },
    {
        "name": "布隆迪 卡扬扎 水洗",
        "country": "Burundi",
        "region": "Kayanza",
        "latitude": -2.93,
        "longitude": 29.63,
        "species": "Arabica",
        "variety": "Bourbon",
        "process": "水洗",
        "roast": "浅烘",
        "altitude": "1700-2000m",
        "year": "2025",
        "description": "高海拔小农样本常见红色莓果、柑橘和红茶感，酸质活泼且收尾清爽。",
        "dataSource": "经典产区资料整理",
        "flavors": {"berry": 5, "citrus": 4, "herbal": 3, "brownSugar": 3, "jasmine": 2},
    },
    {
        "name": "印度 奇克马格鲁 水洗",
        "country": "India",
        "region": "Chikmagalur",
        "latitude": 13.32,
        "longitude": 75.78,
        "species": "Arabica",
        "variety": "Sln.274",
        "process": "水洗",
        "roast": "中烘",
        "altitude": "1000-1400m",
        "year": "2024",
        "description": "南印度高地咖啡常有坚果、可可和温和香料感，质地圆润，适合中烘表现。",
        "dataSource": "经典产区资料整理",
        "flavors": {"almond": 4, "cocoa": 4, "cinnamon": 3, "brownSugar": 3, "herbal": 2},
    },
    {
        "name": "越南 大叻 卡蒂姆",
        "country": "Vietnam",
        "region": "Da Lat",
        "latitude": 11.95,
        "longitude": 108.45,
        "species": "Arabica",
        "variety": "Catimor",
        "process": "日晒",
        "roast": "中烘",
        "altitude": "1400-1650m",
        "year": "2024",
        "description": "大叻高原阿拉比卡样本带有可可、红糖和熟果感，展示越南精品阿拉比卡的发展。",
        "dataSource": "经典产区资料整理",
        "flavors": {"cocoa": 4, "brownSugar": 4, "stone": 3, "almond": 3, "wine": 2},
    },
    {
        "name": "巴布亚新几内亚 东部高地 水洗",
        "country": "Papua New Guinea",
        "region": "Eastern Highlands",
        "latitude": -6.20,
        "longitude": 145.40,
        "species": "Arabica",
        "variety": "Typica",
        "process": "水洗",
        "roast": "中浅烘",
        "altitude": "1500-1800m",
        "year": "2024",
        "description": "山地小农体系下常见热带水果、柑橘和可可感，风味兼具明亮度与厚度。",
        "dataSource": "经典产区资料整理",
        "flavors": {"stone": 4, "citrus": 4, "cocoa": 3, "herbal": 3, "brownSugar": 3},
    },
    {
        "name": "也门 哈拉兹 日晒",
        "country": "Yemen",
        "region": "Haraz",
        "latitude": 15.20,
        "longitude": 43.80,
        "species": "Arabica",
        "variety": "Typica",
        "process": "日晒",
        "roast": "中烘",
        "altitude": "1900-2400m",
        "year": "2024",
        "description": "传统高山日晒样本常见酒香、干果和香料感，风味集中且具有鲜明历史辨识度。",
        "dataSource": "经典产区资料整理",
        "flavors": {"wine": 5, "cinnamon": 4, "stone": 4, "brownSugar": 3, "cocoa": 3},
    },
]


class DatabaseConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, factory=DatabaseConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS flavor_category (
                category_id TEXT PRIMARY KEY,
                parent_id TEXT REFERENCES flavor_category(category_id),
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS flavor_tag (
                tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_code TEXT NOT NULL UNIQUE,
                category_id TEXT NOT NULL REFERENCES flavor_category(category_id),
                tag_name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS origin (
                origin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_code TEXT NOT NULL DEFAULT '',
                country_name TEXT NOT NULL,
                region TEXT NOT NULL,
                latitude REAL NOT NULL DEFAULT 0,
                longitude REAL NOT NULL DEFAULT 0,
                UNIQUE(country_name, region)
            );

            CREATE TABLE IF NOT EXISTS coffee_sample (
                sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_id INTEGER NOT NULL REFERENCES origin(origin_id),
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                variety TEXT NOT NULL DEFAULT '',
                process_method TEXT NOT NULL,
                roast_level TEXT NOT NULL,
                altitude TEXT NOT NULL DEFAULT '',
                harvest_year TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                data_source TEXT NOT NULL DEFAULT '系统录入',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS coffee_flavor (
                sample_id INTEGER NOT NULL REFERENCES coffee_sample(sample_id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES flavor_tag(tag_id) ON DELETE CASCADE,
                intensity INTEGER NOT NULL CHECK(intensity BETWEEN 1 AND 5),
                PRIMARY KEY(sample_id, tag_id)
            );

            CREATE TABLE IF NOT EXISTS app_user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS brew_recipe (
                recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                method TEXT NOT NULL,
                dose REAL NOT NULL CHECK(dose > 0),
                water REAL NOT NULL CHECK(water > 0),
                temperature REAL NOT NULL CHECK(temperature BETWEEN 0 AND 100),
                brew_time INTEGER NOT NULL CHECK(brew_time > 0),
                grind TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasting_record (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
                sample_id INTEGER REFERENCES coffee_sample(sample_id) ON DELETE SET NULL,
                sample_name TEXT NOT NULL,
                aroma INTEGER NOT NULL CHECK(aroma BETWEEN 1 AND 5),
                acidity INTEGER NOT NULL CHECK(acidity BETWEEN 1 AND 5),
                sweetness INTEGER NOT NULL CHECK(sweetness BETWEEN 1 AND 5),
                body INTEGER NOT NULL CHECK(body BETWEEN 1 AND 5),
                aftertaste INTEGER NOT NULL CHECK(aftertaste BETWEEN 1 AND 5),
                flavor_notes TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS coffee_review (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id INTEGER NOT NULL REFERENCES coffee_sample(sample_id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_brew_user ON brew_recipe(user_id);
            CREATE INDEX IF NOT EXISTS idx_tasting_user ON tasting_record(user_id);
            CREATE INDEX IF NOT EXISTS idx_review_sample ON coffee_review(sample_id);
            CREATE INDEX IF NOT EXISTS idx_review_user ON coffee_review(user_id);

            CREATE INDEX IF NOT EXISTS idx_sample_origin ON coffee_sample(origin_id);
            CREATE INDEX IF NOT EXISTS idx_tag_category ON flavor_tag(category_id);
            """
        )

        columns = {row["name"] for row in connection.execute("PRAGMA table_info(coffee_sample)")}
        if "image_url" not in columns:
            connection.execute("ALTER TABLE coffee_sample ADD COLUMN image_url TEXT NOT NULL DEFAULT ''")

        if connection.execute("SELECT COUNT(*) FROM flavor_category").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO flavor_category(category_id, name, color, sort_order) VALUES (?, ?, ?, ?)",
                CATEGORIES,
            )

        if connection.execute("SELECT COUNT(*) FROM flavor_tag").fetchone()[0] == 0:
            connection.executemany(
                """
                INSERT INTO flavor_tag(tag_code, tag_name, category_id, description)
                VALUES (?, ?, ?, ?)
                """,
                TAGS,
            )

        ensure_seed_samples(connection)
        ensure_seed_users(connection)


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    actual = hash_password(password, salt).split("$", 1)[1]
    return secrets.compare_digest(actual, expected)


def ensure_seed_users(connection: sqlite3.Connection) -> None:
    admin_password = ADMIN_PASSWORD or "admin123"
    users = [
        ("admin", hash_password(admin_password), "admin"),
        ("user", hash_password("user123"), "user"),
    ]
    connection.executemany(
        "INSERT OR IGNORE INTO app_user(username, password_hash, role) VALUES (?, ?, ?)",
        users,
    )
    if ADMIN_PASSWORD:
        connection.execute(
            "UPDATE app_user SET password_hash = ? WHERE username = 'admin'",
            (hash_password(ADMIN_PASSWORD),),
        )


def ensure_seed_samples(connection: sqlite3.Connection) -> None:
    for sample in SAMPLES:
        exists = connection.execute(
            "SELECT sample_id FROM coffee_sample WHERE name = ?",
            (sample["name"],),
        ).fetchone()
        if exists:
            continue
        sample_id = insert_sample(connection, sample)
        insert_flavors(connection, sample_id, sample["flavors"])


def get_or_create_origin(connection: sqlite3.Connection, payload: dict) -> int:
    country = str(payload.get("country", "")).strip()
    region = str(payload.get("region", "")).strip()
    latitude = float(payload.get("latitude") or 0)
    longitude = float(payload.get("longitude") or 0)
    row = connection.execute(
        "SELECT origin_id FROM origin WHERE country_name = ? AND region = ?",
        (country, region),
    ).fetchone()
    if row:
        connection.execute(
            "UPDATE origin SET latitude = ?, longitude = ? WHERE origin_id = ?",
            (latitude, longitude, row["origin_id"]),
        )
        return int(row["origin_id"])
    cursor = connection.execute(
        """
        INSERT INTO origin(country_code, country_name, region, latitude, longitude)
        VALUES (?, ?, ?, ?, ?)
        """,
        (country[:2].upper(), country, region, latitude, longitude),
    )
    return int(cursor.lastrowid)


def insert_sample(connection: sqlite3.Connection, payload: dict) -> int:
    origin_id = get_or_create_origin(connection, payload)
    cursor = connection.execute(
        """
        INSERT INTO coffee_sample(
            origin_id, name, species, variety, process_method, roast_level,
            altitude, harvest_year, description, data_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            origin_id,
            str(payload.get("name", "")).strip(),
            str(payload.get("species", "Arabica")).strip(),
            str(payload.get("variety", "")).strip() or "Unknown",
            str(payload.get("process", "")).strip(),
            str(payload.get("roast", "")).strip(),
            str(payload.get("altitude", "")).strip() or "-",
            str(payload.get("year", "")).strip() or "-",
            str(payload.get("description", "")).strip() or "等待补充杯测描述。",
            str(payload.get("dataSource", "系统录入")).strip() or "系统录入",
        ),
    )
    return int(cursor.lastrowid)


def insert_flavors(connection: sqlite3.Connection, sample_id: int, flavors: dict) -> None:
    for tag_code, raw_intensity in flavors.items():
        tag = connection.execute(
            "SELECT tag_id FROM flavor_tag WHERE tag_code = ?", (tag_code,)
        ).fetchone()
        if not tag:
            continue
        intensity = int(raw_intensity)
        if intensity < 1 or intensity > 5:
            raise ValueError("风味强度必须在 1 到 5 之间")
        connection.execute(
            "INSERT INTO coffee_flavor(sample_id, tag_id, intensity) VALUES (?, ?, ?)",
            (sample_id, tag["tag_id"], intensity),
        )


def serialize_bootstrap(connection: sqlite3.Connection) -> dict:
    categories = [
        dict(row)
        for row in connection.execute(
            """
            SELECT category_id AS id, name, color
            FROM flavor_category
            ORDER BY sort_order, name
            """
        )
    ]
    tags = [
        dict(row)
        for row in connection.execute(
            """
            SELECT t.tag_code AS id, t.tag_name AS name, c.name AS category, t.description
            FROM flavor_tag t
            JOIN flavor_category c ON c.category_id = t.category_id
            ORDER BY c.sort_order, t.tag_id
            """
        )
    ]
    samples = []
    rows = connection.execute(
        """
        SELECT
            s.sample_id AS id, s.name, o.country_name AS country, o.region,
            o.latitude, o.longitude, s.species, s.variety,
            s.process_method AS process, s.roast_level AS roast,
            s.altitude, s.harvest_year AS year, s.description, s.data_source AS dataSource,
            s.image_url AS imageUrl
        FROM coffee_sample s
        JOIN origin o ON o.origin_id = s.origin_id
        ORDER BY s.sample_id
        """
    )
    for row in rows:
        sample = dict(row)
        sample["flavors"] = {
            flavor["tag_code"]: flavor["intensity"]
            for flavor in connection.execute(
                """
                SELECT t.tag_code, cf.intensity
                FROM coffee_flavor cf
                JOIN flavor_tag t ON t.tag_id = cf.tag_id
                WHERE cf.sample_id = ?
                ORDER BY cf.intensity DESC, t.tag_id
                """,
                (sample["id"],),
            )
        }
        samples.append(sample)
    return {"categories": categories, "tags": tags, "coffees": samples}


def validate_sample(payload: dict) -> None:
    for field in ("name", "country", "region", "process", "roast"):
        if not str(payload.get(field, "")).strip():
            raise ValueError(f"字段 {field} 不能为空")
    flavors = payload.get("flavors")
    if not isinstance(flavors, dict) or not flavors:
        raise ValueError("请至少选择一个风味标签")
    latitude = float(payload.get("latitude") or 0)
    longitude = float(payload.get("longitude") or 0)
    if not -90 <= latitude <= 90:
        raise ValueError("纬度必须在 -90 到 90 之间")
    if not -180 <= longitude <= 180:
        raise ValueError("经度必须在 -180 到 180 之间")


def normalized_sample_image(raw: bytes, content_type: str) -> bytes:
    formats = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
    expected = formats.get(content_type)
    if not expected:
        raise ValueError("只支持 JPG、PNG 或 WebP 图片")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format != expected:
                    raise ValueError("图片内容与文件类型不符")
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise ValueError("图片像素过大，请缩小后上传")
                source.verify()
            with Image.open(io.BytesIO(raw)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((1600, 1600))
                output = io.BytesIO()
                # Re-encoding removes embedded metadata and never serves the original upload.
                image.save(output, format="WEBP", quality=88)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise ValueError("无法读取这张图片，请更换有效的 JPG、PNG 或 WebP 文件") from error


def remove_sample_image(url: str) -> None:
    if re.fullmatch(r"/media/samples/[a-f0-9]{32}\.webp", url or ""):
        (UPLOAD_DIR / url.rsplit("/", 1)[1]).unlink(missing_ok=True)


class CoffeeAtlasHandler(SimpleHTTPRequestHandler):
    server_version = "CoffeeAtlas/1.0"
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".webp": "image/webp"}

    def current_user(self) -> dict | None:
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        morsel = cookie.get(SESSION_COOKIE)
        if not morsel:
            return None
        token = morsel.value
        session = SESSIONS.get(token)
        if not session:
            return None
        if session["expires_at"] <= time.time():
            SESSIONS.pop(token, None)
            return None
        with connect() as connection:
            row = connection.execute(
                "SELECT user_id, username, role FROM app_user WHERE user_id = ?",
                (session["user_id"],),
            ).fetchone()
        return dict(row) if row else None

    def require_admin(self) -> bool:
        user = self.current_user()
        if not user:
            self.send_json({"error": "请先登录管理员账户"}, status=HTTPStatus.UNAUTHORIZED)
            return False
        if user["role"] != "admin":
            self.send_json({"error": "只有管理员账户可以访问研究者后台"}, status=HTTPStatus.FORBIDDEN)
            return False
        return True

    def require_user(self) -> dict | None:
        user = self.current_user()
        if not user:
            self.send_json({"error": "请先登录后保存个人记录"}, status=HTTPStatus.UNAUTHORIZED)
            return None
        return user

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        if re.fullmatch(r"/media/samples/[a-f0-9]{32}\.webp", parsed.path):
            candidate = (UPLOAD_DIR / parsed.path.rsplit("/", 1)[1]).resolve()
            if candidate.parent == UPLOAD_DIR.resolve():
                return str(candidate)
            return str(WEB_ROOT / "__forbidden__")
        relative = unquote(parsed.path).lstrip("/") or "index.html"
        candidate = (WEB_ROOT / relative).resolve()
        if WEB_ROOT not in candidate.parents:
            return str(WEB_ROOT / "__forbidden__")
        return str(candidate)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        sys.stdout.write("%s - %s\n" % (self.log_date_time_string(), format % args))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/session":
            user = self.current_user()
            self.send_json({
                "authenticated": bool(user),
                "user": {"username": user["username"], "role": user["role"]} if user else None,
            })
            return
        if path == "/api/bootstrap":
            with connect() as connection:
                self.send_json(serialize_bootstrap(connection))
            return
        if path == "/api/health":
            with connect() as connection:
                count = connection.execute("SELECT COUNT(*) FROM coffee_sample").fetchone()[0]
            self.send_json({"status": "ok", "database": str(DB_PATH), "samples": count})
            return
        if path == "/api/export.csv":
            if not self.require_admin():
                return
            self.send_csv()
            return
        if path == "/api/tools":
            user = self.require_user()
            if not user:
                return
            with connect() as connection:
                recipes = [dict(row) for row in connection.execute(
                    """
                    SELECT recipe_id AS id, name, method, dose, water, temperature,
                           brew_time AS brewTime, grind, notes, created_at AS createdAt
                    FROM brew_recipe WHERE user_id = ? ORDER BY recipe_id DESC
                    """,
                    (user["user_id"],),
                )]
                tastings = [dict(row) for row in connection.execute(
                    """
                    SELECT record_id AS id, sample_id AS sampleId, sample_name AS sampleName,
                           aroma, acidity, sweetness, body, aftertaste,
                           flavor_notes AS flavorNotes, notes, created_at AS createdAt
                    FROM tasting_record WHERE user_id = ? ORDER BY record_id DESC
                    """,
                    (user["user_id"],),
                )]
            self.send_json({"recipes": recipes, "tastings": tastings})
            return
        review_match = re.fullmatch(r"/api/reviews/(\d+)", path)
        if review_match:
            sample_id = int(review_match.group(1))
            with connect() as connection:
                sample = connection.execute(
                    "SELECT sample_id FROM coffee_sample WHERE sample_id = ?", (sample_id,)
                ).fetchone()
                if not sample:
                    self.send_json({"error": "咖啡样本不存在"}, status=HTTPStatus.NOT_FOUND)
                    return
                reviews = [dict(row) for row in connection.execute(
                    """
                    SELECT r.review_id AS id, r.rating, r.content, r.created_at AS createdAt,
                           u.username AS username
                    FROM coffee_review r
                    JOIN app_user u ON u.user_id = r.user_id
                    WHERE r.sample_id = ? ORDER BY r.review_id DESC
                    """,
                    (sample_id,),
                )]
                summary = connection.execute(
                    "SELECT COUNT(*) AS count, COALESCE(AVG(rating), 0) AS average FROM coffee_review WHERE sample_id = ?",
                    (sample_id,),
                ).fetchone()
            self.send_json({"reviews": reviews, "count": summary["count"], "average": round(summary["average"], 1)})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/login":
                username = str(payload.get("username", "")).strip()
                password = str(payload.get("password", ""))
                if not username or not password:
                    raise ValueError("请输入用户名和密码")
                with connect() as connection:
                    user = connection.execute(
                        "SELECT user_id, username, password_hash, role FROM app_user WHERE username = ?",
                        (username,),
                    ).fetchone()
                if not user or not verify_password(password, user["password_hash"]):
                    self.send_json({"error": "用户名或密码不正确"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                token = secrets.token_urlsafe(32)
                SESSIONS[token] = {
                    "user_id": user["user_id"],
                    "expires_at": time.time() + SESSION_TTL_SECONDS,
                }
                self.send_json(
                    {
                        "authenticated": True,
                        "user": {"username": user["username"], "role": user["role"]},
                    },
                    headers={
                        "Set-Cookie": session_cookie(token, SESSION_TTL_SECONDS)
                    },
                )
                return
            if path == "/api/register":
                username = str(payload.get("username", "")).strip()
                password = str(payload.get("password", ""))
                if len(username) < 2 or len(username) > 24:
                    raise ValueError("用户名长度需要在 2 到 24 个字符之间")
                if len(password) < 6 or len(password) > 128:
                    raise ValueError("密码长度需要在 6 到 128 个字符之间")
                with connect() as connection:
                    exists = connection.execute(
                        "SELECT 1 FROM app_user WHERE username = ?", (username,)
                    ).fetchone()
                    if exists:
                        self.send_json({"error": "用户名已存在，请换一个用户名"}, status=HTTPStatus.CONFLICT)
                        return
                    cursor = connection.execute(
                        "INSERT INTO app_user(username, password_hash, role) VALUES (?, ?, 'user')",
                        (username, hash_password(password)),
                    )
                token = secrets.token_urlsafe(32)
                SESSIONS[token] = {
                    "user_id": cursor.lastrowid,
                    "expires_at": time.time() + SESSION_TTL_SECONDS,
                }
                self.send_json(
                    {
                        "authenticated": True,
                        "user": {"username": username, "role": "user"},
                    },
                    status=HTTPStatus.CREATED,
                    headers={
                        "Set-Cookie": session_cookie(token, SESSION_TTL_SECONDS)
                    },
                )
                return
            if path == "/api/logout":
                self.clear_session()
                return
            if path == "/api/brew-recipes":
                user = self.require_user()
                if not user:
                    return
                name = str(payload.get("name", "")).strip() or "我的冲煮方案"
                method = str(payload.get("method", "手冲")).strip() or "手冲"
                grind = str(payload.get("grind", "")).strip()
                notes = str(payload.get("notes", "")).strip()
                dose = float(payload.get("dose") or 0)
                water = float(payload.get("water") or 0)
                temperature = float(payload.get("temperature") or 0)
                brew_time = int(payload.get("brewTime") or 0)
                if dose <= 0 or water <= 0 or temperature <= 0 or brew_time <= 0:
                    raise ValueError("请填写有效的冲煮参数")
                if temperature > 100:
                    raise ValueError("水温不能超过 100°C")
                with connect() as connection:
                    cursor = connection.execute(
                        """
                        INSERT INTO brew_recipe(user_id, name, method, dose, water, temperature, brew_time, grind, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (user["user_id"], name, method, dose, water, temperature, brew_time, grind, notes),
                    )
                self.send_json({"id": cursor.lastrowid}, status=HTTPStatus.CREATED)
                return
            if path == "/api/tastings":
                user = self.require_user()
                if not user:
                    return
                sample_id = payload.get("sampleId")
                sample_id = int(sample_id) if sample_id not in (None, "", "all") else None
                sample_name = str(payload.get("sampleName", "")).strip() or "未指定样本"
                scores = {key: int(payload.get(key) or 0) for key in ("aroma", "acidity", "sweetness", "body", "aftertaste")}
                if any(value < 1 or value > 5 for value in scores.values()):
                    raise ValueError("各项杯测评分必须在 1 到 5 之间")
                with connect() as connection:
                    cursor = connection.execute(
                        """
                        INSERT INTO tasting_record(
                            user_id, sample_id, sample_name, aroma, acidity, sweetness, body, aftertaste,
                            flavor_notes, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user["user_id"], sample_id, sample_name, scores["aroma"], scores["acidity"],
                            scores["sweetness"], scores["body"], scores["aftertaste"],
                            str(payload.get("flavorNotes", "")).strip(), str(payload.get("notes", "")).strip(),
                        ),
                    )
                self.send_json({"id": cursor.lastrowid}, status=HTTPStatus.CREATED)
                return
            review_match = re.fullmatch(r"/api/reviews/(\d+)", path)
            if review_match:
                user = self.require_user()
                if not user:
                    return
                sample_id = int(review_match.group(1))
                rating = int(payload.get("rating") or 0)
                content = str(payload.get("content", "")).strip()
                if rating < 1 or rating > 5:
                    raise ValueError("评分必须在 1 到 5 之间")
                if len(content) < 2 or len(content) > 500:
                    raise ValueError("评价内容需要在 2 到 500 个字符之间")
                with connect() as connection:
                    sample = connection.execute(
                        "SELECT sample_id FROM coffee_sample WHERE sample_id = ?", (sample_id,)
                    ).fetchone()
                    if not sample:
                        self.send_json({"error": "咖啡样本不存在"}, status=HTTPStatus.NOT_FOUND)
                        return
                    cursor = connection.execute(
                        "INSERT INTO coffee_review(sample_id, user_id, rating, content) VALUES (?, ?, ?, ?)",
                        (sample_id, user["user_id"], rating, content),
                    )
                self.send_json({"id": cursor.lastrowid}, status=HTTPStatus.CREATED)
                return
            if path == "/api/samples":
                if not self.require_admin():
                    return
                validate_sample(payload)
                with connect() as connection:
                    sample_id = insert_sample(connection, payload)
                    insert_flavors(connection, sample_id, payload["flavors"])
                self.send_json({"id": sample_id}, status=HTTPStatus.CREATED)
                return
            if path == "/api/tags":
                if not self.require_admin():
                    return
                name = str(payload.get("name", "")).strip()
                category_name = str(payload.get("category", "")).strip()
                if not name or not category_name:
                    raise ValueError("标签名和所属大类不能为空")
                tag_code = f"tag-{uuid.uuid4().hex[:10]}"
                with connect() as connection:
                    category = connection.execute(
                        "SELECT category_id FROM flavor_category WHERE name = ?",
                        (category_name,),
                    ).fetchone()
                    if not category:
                        raise ValueError("风味大类不存在")
                    connection.execute(
                        """
                        INSERT INTO flavor_tag(tag_code, category_id, tag_name, description)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            tag_code,
                            category["category_id"],
                            name,
                            str(payload.get("description", "")).strip(),
                        ),
                    )
                self.send_json({"id": tag_code}, status=HTTPStatus.CREATED)
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, sqlite3.IntegrityError) as error:
            self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def do_PUT(self) -> None:
        match = re.fullmatch(r"/api/samples/(\d+)/image", urlparse(self.path).path)
        if not match:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.require_admin():
            return
        sample_id = int(match.group(1))
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                raise ValueError("请选择一张图片")
            if length > MAX_IMAGE_BYTES:
                self.send_json({"error": "图片不能超过 6 MB"}, status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                return
            with connect() as connection:
                if not connection.execute("SELECT 1 FROM coffee_sample WHERE sample_id = ?", (sample_id,)).fetchone():
                    self.send_json({"error": "咖啡样本不存在"}, status=HTTPStatus.NOT_FOUND)
                    return
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            image = normalized_sample_image(self.rfile.read(length), content_type)
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            name = f"{uuid.uuid4().hex}.webp"
            image_url = f"/media/samples/{name}"
            file_path = UPLOAD_DIR / name
            file_path.write_bytes(image)
            try:
                with connect() as connection:
                    row = connection.execute("SELECT image_url FROM coffee_sample WHERE sample_id = ?", (sample_id,)).fetchone()
                    if not row:
                        raise ValueError("咖啡样本已被删除")
                    connection.execute("UPDATE coffee_sample SET image_url = ?, updated_at = CURRENT_TIMESTAMP WHERE sample_id = ?", (image_url, sample_id))
            except Exception:
                file_path.unlink(missing_ok=True)
                raise
            remove_sample_image(row["image_url"])
            self.send_json({"id": sample_id, "imageUrl": image_url})
        except ValueError as error:
            self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except OSError:
            self.send_json({"error": "图片保存失败，请检查磁盘空间或目录权限"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        image_match = re.fullmatch(r"/api/samples/(\d+)/image", path)
        if image_match:
            if not self.require_admin():
                return
            sample_id = int(image_match.group(1))
            with connect() as connection:
                row = connection.execute("SELECT image_url FROM coffee_sample WHERE sample_id = ?", (sample_id,)).fetchone()
                if not row:
                    self.send_json({"error": "样本不存在"}, status=HTTPStatus.NOT_FOUND)
                    return
                connection.execute("UPDATE coffee_sample SET image_url = '', updated_at = CURRENT_TIMESTAMP WHERE sample_id = ?", (sample_id,))
            remove_sample_image(row["image_url"])
            self.send_json({"id": sample_id, "imageUrl": ""})
            return
        sample_match = re.fullmatch(r"/api/samples/(\d+)", path)
        tag_match = re.fullmatch(r"/api/tags/([^/]+)", path)
        if sample_match:
            if not self.require_admin():
                return
            sample_id = int(sample_match.group(1))
            with connect() as connection:
                image = connection.execute("SELECT image_url FROM coffee_sample WHERE sample_id = ?", (sample_id,)).fetchone()
                cursor = connection.execute(
                    "DELETE FROM coffee_sample WHERE sample_id = ?", (sample_id,)
                )
            if cursor.rowcount == 0:
                self.send_json({"error": "样本不存在"}, status=HTTPStatus.NOT_FOUND)
            else:
                remove_sample_image(image["image_url"])
                self.send_json({"deleted": sample_id})
            return
        if tag_match:
            if not self.require_admin():
                return
            tag_code = unquote(tag_match.group(1))
            with connect() as connection:
                cursor = connection.execute(
                    "DELETE FROM flavor_tag WHERE tag_code = ?", (tag_code,)
                )
            if cursor.rowcount == 0:
                self.send_json({"error": "标签不存在"}, status=HTTPStatus.NOT_FOUND)
            else:
                self.send_json({"deleted": tag_code})
            return
        recipe_match = re.fullmatch(r"/api/brew-recipes/(\d+)", path)
        tasting_match = re.fullmatch(r"/api/tastings/(\d+)", path)
        review_match = re.fullmatch(r"/api/reviews/(\d+)", path)
        if recipe_match or tasting_match or review_match:
            user = self.require_user()
            if not user:
                return
            table = "brew_recipe" if recipe_match else ("tasting_record" if tasting_match else "coffee_review")
            id_column = "recipe_id" if recipe_match else ("record_id" if tasting_match else "review_id")
            record_id = int((recipe_match or tasting_match or review_match).group(1))
            with connect() as connection:
                cursor = connection.execute(
                    f"DELETE FROM {table} WHERE {id_column} = ? AND user_id = ?",
                    (record_id, user["user_id"]),
                )
            if cursor.rowcount == 0:
                self.send_json({"error": "记录不存在"}, status=HTTPStatus.NOT_FOUND)
            else:
                self.send_json({"deleted": record_id})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def clear_session(self) -> None:
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        morsel = cookie.get(SESSION_COOKIE)
        if morsel:
            SESSIONS.pop(morsel.value, None)
        self.send_json(
            {"authenticated": False},
            headers={"Set-Cookie": session_cookie("", 0)},
        )

    def send_json(
        self,
        payload: dict,
        status: HTTPStatus = HTTPStatus.OK,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_csv(self) -> None:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "sample_id",
                "name",
                "country",
                "region",
                "species",
                "variety",
                "process",
                "roast_level",
                "altitude",
                "harvest_year",
                "flavors",
            ]
        )
        with connect() as connection:
            data = serialize_bootstrap(connection)
        tag_names = {tag["id"]: tag["name"] for tag in data["tags"]}
        for sample in data["coffees"]:
            writer.writerow(
                [
                    sample["id"],
                    sample["name"],
                    sample["country"],
                    sample["region"],
                    sample["species"],
                    sample["variety"],
                    sample["process"],
                    sample["roast"],
                    sample["altitude"],
                    sample["year"],
                    "|".join(
                        f"{tag_names.get(tag_id, tag_id)}:{value}"
                        for tag_id, value in sample["flavors"].items()
                    ),
                ]
            )
        body = ("\ufeff" + buffer.getvalue()).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="coffee-samples.csv"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class AtlasHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def run() -> None:
    if not (WEB_ROOT / "index.html").is_file():
        raise SystemExit("Vue build missing. Run npm run build in frontend first, or use start.ps1.")
    initialize_database()
    mimetypes.add_type("text/javascript", ".js")
    for port in range(PORT, PORT + 20):
        try:
            server = AtlasHTTPServer((HOST, port), CoffeeAtlasHandler)
            break
        except OSError as error:
            if error.errno not in (48, 98, 10048) and getattr(error, "winerror", None) != 10048:
                raise
    else:
        raise SystemExit("No free local port found. Stop an existing server and try again.")
    if port != PORT:
        print(f"Port {PORT} is occupied; using {port} for this instance.")
    print(f"Coffee Flavor Atlas: http://{HOST}:{port}/", flush=True)
    print(f"SQLite database: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
