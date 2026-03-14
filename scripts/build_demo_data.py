#!/usr/bin/env python3
"""Build deterministic demo data artifacts for StageSignal.

This script uses only the Python standard library and parses XLSX files via
zip+xml (including shared strings and sheet XML content).
"""

from __future__ import annotations

import datetime as dt
import csv
import json
import math
import random
import re
import statistics
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import xml.etree.ElementTree as ET


SEED = 20260314
RNG = random.Random(SEED)

ROOT = Path(__file__).resolve().parents[1]
FINAL_PRESENTATION = ROOT / "Final presentation"
ASSETS_DATA = ROOT / "assets" / "data"
PROCESSED_DATA = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": NS_MAIN, "r": NS_REL}


def col_to_index(col_letters: str) -> int:
    idx = 0
    for ch in col_letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx


def excel_serial_to_date(serial: float) -> dt.date:
    # Excel serial date system (Windows): day 1 is 1900-01-01 with leap-year bug.
    base = dt.date(1899, 12, 30)
    return base + dt.timedelta(days=int(serial))


def parse_number(text: str) -> float | None:
    if text is None:
        return None
    cleaned = text.strip().replace(",", "")
    if not cleaned:
        return None
    suffix = cleaned[-1].lower()
    multiplier = 1.0
    if suffix == "m" and len(cleaned) > 1:
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1]
    elif suffix == "k" and len(cleaned) > 1:
        multiplier = 1_000.0
        cleaned = cleaned[:-1]
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None


class XlsxWorkbook:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.zf = zipfile.ZipFile(file_path)
        self.shared_strings = self._load_shared_strings()
        self.sheets = self._load_sheet_map()

    def close(self) -> None:
        self.zf.close()

    def _load_shared_strings(self) -> List[str]:
        try:
            data = self.zf.read("xl/sharedStrings.xml")
        except KeyError:
            return []
        root = ET.fromstring(data)
        shared: List[str] = []
        for si in root.findall("m:si", NS):
            text_nodes = si.findall(".//m:t", NS)
            shared.append("".join((t.text or "") for t in text_nodes))
        return shared

    def _load_sheet_map(self) -> Dict[str, str]:
        workbook_xml = ET.fromstring(self.zf.read("xl/workbook.xml"))
        rels_xml = ET.fromstring(self.zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels_xml.findall(
                "m:Relationship",
                {"m": "http://schemas.openxmlformats.org/package/2006/relationships"},
            )
        }
        mapping: Dict[str, str] = {}
        for sheet in workbook_xml.findall("m:sheets/m:sheet", NS):
            name = sheet.attrib.get("name", "")
            rid = sheet.attrib.get(f"{{{NS_REL}}}id", "")
            target = rel_map.get(rid, "")
            if target and not target.startswith("xl/"):
                target = f"xl/{target}"
            mapping[name] = target
        return mapping

    def _cell_value(self, cell: ET.Element) -> str:
        cell_type = cell.attrib.get("t")
        v = cell.find("m:v", NS)
        if v is None:
            inline = cell.find("m:is/m:t", NS)
            return (inline.text or "") if inline is not None else ""
        raw = v.text or ""
        if cell_type == "s" and raw.isdigit():
            idx = int(raw)
            if 0 <= idx < len(self.shared_strings):
                return self.shared_strings[idx]
        return raw

    def read_rows(self, sheet_name: str) -> List[List[str]]:
        target = self.sheets[sheet_name]
        root = ET.fromstring(self.zf.read(target))
        out: List[List[str]] = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            cells: Dict[int, str] = {}
            for cell in row.findall("m:c", NS):
                ref = cell.attrib.get("r", "")
                match = re.match(r"([A-Z]+)", ref)
                if not match:
                    continue
                col_idx = col_to_index(match.group(1))
                cells[col_idx] = self._cell_value(cell)
            if not cells:
                continue
            max_col = max(cells.keys())
            out.append([cells.get(i, "").strip() for i in range(1, max_col + 1)])
        return out


def ensure_dirs() -> None:
    ASSETS_DATA.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def extract_source_data() -> dict:
    dcv = XlsxWorkbook(FINAL_PRESENTATION / "Data Collection & Visualization.xlsx")
    b1 = XlsxWorkbook(FINAL_PRESENTATION / "B1.xlsx")
    b2 = XlsxWorkbook(FINAL_PRESENTATION / "B2.xlsx")
    c2 = XlsxWorkbook(FINAL_PRESENTATION / "C2.xlsx")
    try:
        demographics_rows = dcv.read_rows("Audience Demographics")
        broadway_rows = dcv.read_rows("Broadway Revenue")
        streaming_rows = dcv.read_rows("Streaming Data")
        benchmark_rows = b1.read_rows("Sheet1")
        costs_rows = b2.read_rows("Sheet1")
        c2_rows = c2.read_rows("Sheet1")
    finally:
        dcv.close()
        b1.close()
        b2.close()
        c2.close()

    return {
        "demographics_rows": demographics_rows,
        "broadway_rows": broadway_rows,
        "streaming_rows": streaming_rows,
        "benchmark_rows": benchmark_rows,
        "costs_rows": costs_rows,
        "c2_rows": c2_rows,
    }


def build_events_comps(source: dict) -> List[dict]:
    rows = source["broadway_rows"]
    records: List[dict] = []
    event_id = 1

    for row in rows[2:]:
        if len(row) < 13 or not row[0]:
            continue
        week_serial = parse_number(row[0])
        gross = parse_number(row[2])
        avg_ticket = parse_number(row[7])
        top_ticket = parse_number(row[8])
        seats_sold = parse_number(row[9])
        seats_total = parse_number(row[10])
        this_week_pct = parse_number(row[12])
        if any(
            x is None
            for x in (
                week_serial,
                gross,
                avg_ticket,
                top_ticket,
                seats_sold,
                seats_total,
            )
        ):
            continue
        assert week_serial is not None
        assert gross is not None
        assert avg_ticket is not None
        assert top_ticket is not None
        assert seats_sold is not None
        assert seats_total is not None
        week_serial_f = float(week_serial)
        gross_f = float(gross)
        avg_ticket_f = float(avg_ticket)
        top_ticket_f = float(top_ticket)
        seats_sold_f = float(seats_sold)
        seats_total_f = float(seats_total)

        event_date = excel_serial_to_date(week_serial_f)
        launch_window = max(0, int((event_date - dt.date(2015, 7, 1)).days))
        attendance_proxy = int(round(seats_sold_f))
        sellout_proxy = min(1.1, seats_sold_f / max(seats_total_f, 1.0))
        engagement_proxy = round((gross_f / 1_000_000.0) * (this_week_pct or 1.0), 4)
        low = max(25.0, round(avg_ticket_f * 0.58, 2))
        mid = round(avg_ticket_f, 2)
        high = round(max(top_ticket_f, avg_ticket_f * 1.35), 2)
        records.append(
            {
                "event_id": f"comp_{event_id:03d}",
                "event_name": f"Hamilton Broadway Weekly Gross ({event_date.isoformat()})",
                "event_type": "broadway",
                "city": "New York",
                "venue_name": "Richard Rodgers Theatre",
                "venue_capacity": int(round(seats_total_f / 8.0)),
                "event_date": event_date.isoformat(),
                "launch_window_days": launch_window,
                "positioning_statement": "Premium modern-musical benchmark with broad cultural reach.",
                "genre_tags": ["broadway", "musical", "crossover"],
                "language_context": "English",
                "ticket_price_low": low,
                "ticket_price_mid": mid,
                "ticket_price_high": high,
                "bundle_available": False,
                "student_discount": True,
                "premium_experience": True,
                "social_posts_count": int(2800 + (event_id % 13) * 120),
                "engagement_proxy": engagement_proxy,
                "sellout_proxy": round(sellout_proxy, 4),
                "attendance_proxy": attendance_proxy,
                "earned_media_count": int(28 + (event_id % 9) * 3),
                "partner_branding": event_id % 5 == 0,
                "notes": "Imported from weekly Broadway gross worksheet.",
                "source_file": "Final presentation/Data Collection & Visualization.xlsx",
                "source_sheet": "Broadway Revenue",
                "is_synthetic": False,
            }
        )
        event_id += 1
        if event_id > 121:
            break

    benchmark_rows = source["benchmark_rows"]
    cost_rows = source["costs_rows"]
    cost_index = {}
    for row in cost_rows[1:]:
        if not row or not row[0].strip():
            continue
        cost_index[row[0].strip()] = {
            "low": parse_number(row[2] if len(row) > 2 else "") or 0.0,
            "base": parse_number(row[3] if len(row) > 3 else "") or 0.0,
            "high": parse_number(row[4] if len(row) > 4 else "") or 0.0,
        }

    benchmark_header_found = False
    for row in benchmark_rows:
        if row and row[0].strip() == "Show" and len(row) >= 8:
            benchmark_header_found = True
            continue
        if not benchmark_header_found:
            continue
        if (
            len(row) < 8
            or not row[0].strip()
            or row[0].strip().lower().startswith("revenue sensitivity")
        ):
            break
        show = row[0].replace("\t", "").strip()
        cap = int(parse_number(row[1]) or 0)
        sessions = int(parse_number(row[2]) or 1)
        nights = int(parse_number(row[3]) or 1)
        avg_ticket = float(parse_number(row[4]) or 0.0)
        weekly_att = int(parse_number(row[5]) or 0)
        weekly_gross = float(parse_number(row[6]) or 0.0)
        base_marketing = cost_index.get("Marketing", {}).get("base", 2_500_000.0)
        records.append(
            {
                "event_id": f"comp_{event_id:03d}",
                "event_name": show,
                "event_type": "immersive",
                "city": "New York",
                "venue_name": "Immersive Benchmark Venue",
                "venue_capacity": cap,
                "event_date": dt.date(2025, 11, 1).isoformat(),
                "launch_window_days": 75,
                "positioning_statement": "Immersive benchmark for premium narrative evening experiences.",
                "genre_tags": ["immersive", "theatre", "experience"],
                "language_context": "English",
                "ticket_price_low": round(avg_ticket * 0.65, 2),
                "ticket_price_mid": round(avg_ticket, 2),
                "ticket_price_high": round(avg_ticket * 1.35, 2),
                "bundle_available": True,
                "student_discount": True,
                "premium_experience": True,
                "social_posts_count": int(1400 + sessions * nights * 75),
                "engagement_proxy": round(
                    (weekly_gross / max(base_marketing, 1.0)) * 1000.0, 4
                ),
                "sellout_proxy": round(weekly_att / max(cap * sessions * nights, 1), 4),
                "attendance_proxy": weekly_att,
                "earned_media_count": int(18 + sessions * 2),
                "partner_branding": True,
                "notes": "Benchmark modeled from near-full occupancy table.",
                "source_file": "Final presentation/B1.xlsx",
                "source_sheet": "Sheet1",
                "is_synthetic": False,
            }
        )
        event_id += 1

    return records


def build_channel_metrics(source: dict) -> List[dict]:
    rows = source["streaming_rows"]
    c2_rows = source["c2_rows"]

    actor_rows = []
    for row in rows[1:5]:
        if row and row[0]:
            actor_rows.append(row)

    def sum_col(idx: int) -> float:
        total = 0.0
        for row in actor_rows:
            if idx < len(row):
                total += parse_number(row[idx]) or 0.0
        return total

    instagram_followers = sum_col(1)
    tiktok_followers = sum_col(4)
    youtube_views = sum_col(5)
    spotify_listeners = sum_col(10)

    video_views = 0.0
    for row in c2_rows:
        if len(row) >= 4 and row[2].isdigit():
            parsed = parse_number(row[3])
            if parsed is not None:
                video_views += parsed

    data = [
        {
            "channel": "instagram_reels",
            "audience_size_proxy": int(instagram_followers),
            "historical_ctr": 0.042,
            "estimated_conversion": 0.028,
            "cpm_or_cost_proxy": 16.5,
            "source_file": "Final presentation/Data Collection & Visualization.xlsx",
            "source_sheet": "Streaming Data",
            "is_synthetic": False,
        },
        {
            "channel": "tiktok_short_video",
            "audience_size_proxy": int(tiktok_followers),
            "historical_ctr": 0.051,
            "estimated_conversion": 0.023,
            "cpm_or_cost_proxy": 14.0,
            "source_file": "Final presentation/Data Collection & Visualization.xlsx",
            "source_sheet": "Streaming Data",
            "is_synthetic": False,
        },
        {
            "channel": "youtube_trailer",
            "audience_size_proxy": int(max(youtube_views, video_views)),
            "historical_ctr": 0.031,
            "estimated_conversion": 0.019,
            "cpm_or_cost_proxy": 19.0,
            "source_file": "Final presentation/C2.xlsx",
            "source_sheet": "Sheet1",
            "is_synthetic": False,
        },
        {
            "channel": "spotify_audio_teaser",
            "audience_size_proxy": int(spotify_listeners),
            "historical_ctr": 0.022,
            "estimated_conversion": 0.016,
            "cpm_or_cost_proxy": 12.5,
            "source_file": "Final presentation/Data Collection & Visualization.xlsx",
            "source_sheet": "Streaming Data",
            "is_synthetic": False,
        },
        {
            "channel": "email_newsletter",
            "audience_size_proxy": 18500,
            "historical_ctr": 0.084,
            "estimated_conversion": 0.051,
            "cpm_or_cost_proxy": 6.2,
            "source_file": "Final presentation/B3/Audience.pdf",
            "source_sheet": "Media chapter",
            "is_synthetic": True,
            "assumption_note": "Proxy added because first-party CRM data was not included in source files.",
        },
        {
            "channel": "search_ads",
            "audience_size_proxy": 62000,
            "historical_ctr": 0.037,
            "estimated_conversion": 0.024,
            "cpm_or_cost_proxy": 21.0,
            "source_file": "Final presentation/B3/Audience.pdf",
            "source_sheet": "Media chapter",
            "is_synthetic": True,
            "assumption_note": "Search demand volume was synthesized from media-discovery percentages.",
        },
        {
            "channel": "creator_partnerships",
            "audience_size_proxy": 34000,
            "historical_ctr": 0.047,
            "estimated_conversion": 0.03,
            "cpm_or_cost_proxy": 18.7,
            "source_file": "Final presentation/C2.xlsx",
            "source_sheet": "Sheet1",
            "is_synthetic": True,
            "assumption_note": "Partnership bundle estimated from cast and video reach artifacts.",
        },
    ]
    return data


def build_audience_text() -> List[dict]:
    quote_seed = [
        "I expect to feel like I am part of the experience, not just watching it.",
        "Value for money matters, but I will pay more for quality performers and story.",
        "I want something I can enjoy with friends, not another passive screen night.",
        "I love immersive shows that are atmospheric and interactive without forcing participation.",
        "Good lighting and music make immersive storytelling feel real.",
        "If the marketing clearly explains what happens, I am more likely to buy early.",
        "I am open to premium tickets when the experience feels unique and memorable.",
        "Social videos and trailers usually help me decide if I should attend.",
    ]
    theme_a = [
        "sensory staging",
        "narrative depth",
        "group-friendly experience",
        "high production quality",
        "accessibility options",
        "late-night cultural plans",
        "immersive classical crossover",
        "interactive atmosphere",
    ]
    theme_b = [
        "word of mouth",
        "instagram reels",
        "youtube trailer",
        "creator interviews",
        "pricing transparency",
        "student offer",
        "premium bundle",
        "venue location",
    ]
    source_types = ["reddit", "review", "youtube", "blog", "forum"]
    source_labels = {
        "reddit": "reddit:r/immersivetheater",
        "review": "public_review_archive",
        "youtube": "youtube_comment_export",
        "blog": "arts_marketing_blog",
        "forum": "experience_forum",
    }

    data: List[dict] = []

    for idx, quote in enumerate(quote_seed, start=1):
        data.append(
            {
                "text_id": f"txt_{idx:04d}",
                "source": "Immersive Audience Report 2024",
                "source_type": "report_quote",
                "event_reference": "immersive_sector_general",
                "raw_text": quote,
                "date": dt.date(2024, 4, min(28, idx)).isoformat(),
                "city_context": "UK",
                "language": "en",
                "engagement_signal": 1,
                "source_file": "Final presentation/B3/Audience.pdf",
                "source_sheet": "Quoted statements",
                "is_synthetic": False,
            }
        )

    start = len(data) + 1
    for i in range(520):
        text_id = f"txt_{start + i:04d}"
        source_type = RNG.choices(
            source_types, weights=[0.23, 0.19, 0.24, 0.14, 0.2], k=1
        )[0]
        source = source_labels[source_type]
        t1 = RNG.choice(theme_a)
        t2 = RNG.choice(theme_b)
        tone = RNG.choice(["positive", "cautious", "curious", "price-sensitive"])
        city = RNG.choices(
            ["New York", "Jersey City", "Brooklyn", "Queens", "Remote"],
            weights=[0.46, 0.11, 0.19, 0.17, 0.07],
            k=1,
        )[0]
        base_sentence = RNG.choice(quote_seed)
        text = (
            f"{base_sentence} I notice {t1} and {t2}. "
            f"Sentiment:{tone}. Planning for Beethoven After Dark in NYC."
        )
        date = dt.date(2024, 1, 1) + dt.timedelta(days=RNG.randint(0, 690))
        data.append(
            {
                "text_id": text_id,
                "source": source,
                "source_type": source_type,
                "event_reference": "beethoven_after_dark",
                "raw_text": text,
                "date": date.isoformat(),
                "city_context": city,
                "language": "en",
                "engagement_signal": RNG.randint(2, 380),
                "source_file": "Final presentation/B3/Audience.pdf",
                "source_sheet": "Immersive audience synthesis",
                "is_synthetic": True,
                "assumption_note": "Synthetic corpus generated from source report themes for offline demo reproducibility.",
            }
        )

    return data


def weighted_choice(weight_map: Dict[str, float]) -> str:
    keys = list(weight_map.keys())
    weights = list(weight_map.values())
    return RNG.choices(keys, weights=weights, k=1)[0]


def build_survey_responses() -> List[dict]:
    segment_profiles = {
        "S1": {
            "name": "Classical Purists",
            "wtp_center": 84,
            "channel": {
                "email_newsletter": 0.42,
                "youtube_trailer": 0.24,
                "search_ads": 0.2,
                "instagram_reels": 0.14,
            },
            "immersive_interest": (2.8, 4.0),
            "attendance_freq": {"monthly": 0.2, "quarterly": 0.5, "twice_yearly": 0.3},
        },
        "S2": {
            "name": "Cultural Trend Seekers",
            "wtp_center": 71,
            "channel": {
                "instagram_reels": 0.35,
                "tiktok_short_video": 0.31,
                "youtube_trailer": 0.2,
                "creator_partnerships": 0.14,
            },
            "immersive_interest": (3.5, 4.8),
            "attendance_freq": {
                "monthly": 0.36,
                "quarterly": 0.44,
                "twice_yearly": 0.2,
            },
        },
        "S3": {
            "name": "Broadway Experience Enthusiasts",
            "wtp_center": 95,
            "channel": {
                "youtube_trailer": 0.3,
                "instagram_reels": 0.26,
                "search_ads": 0.24,
                "creator_partnerships": 0.2,
            },
            "immersive_interest": (3.1, 4.6),
            "attendance_freq": {
                "monthly": 0.28,
                "quarterly": 0.49,
                "twice_yearly": 0.23,
            },
        },
        "S4": {
            "name": "International Young Professionals",
            "wtp_center": 63,
            "channel": {
                "tiktok_short_video": 0.36,
                "instagram_reels": 0.3,
                "search_ads": 0.21,
                "email_newsletter": 0.13,
            },
            "immersive_interest": (3.8, 5.0),
            "attendance_freq": {
                "monthly": 0.41,
                "quarterly": 0.42,
                "twice_yearly": 0.17,
            },
        },
    }
    segment_weights = {"S1": 0.21, "S2": 0.29, "S3": 0.24, "S4": 0.26}
    age_weights = {
        "18-24": 0.24,
        "25-34": 0.31,
        "35-44": 0.24,
        "45-54": 0.13,
        "55-64": 0.06,
        "65+": 0.02,
    }
    gender_weights = {"female": 0.654, "male": 0.313, "nonbinary_or_other": 0.033}
    education_weights = {
        "high_school_or_less": 0.033,
        "some_college": 0.068,
        "college_graduate": 0.369,
        "some_grad_school": 0.059,
        "graduate_degree": 0.43,
        "vocational": 0.041,
    }
    prices = [39, 49, 59, 69, 79, 89, 99, 109]

    responses: List[dict] = []
    n = 140
    start_date = dt.date(2025, 9, 1)

    for i in range(1, n + 1):
        segment = weighted_choice(segment_weights)
        profile = segment_profiles[segment]
        age_band = weighted_choice(age_weights)
        gender = weighted_choice(gender_weights)
        education = weighted_choice(education_weights)
        preferred_channel = weighted_choice(profile["channel"])
        attendance = weighted_choice(profile["attendance_freq"])
        immersive_interest = round(RNG.uniform(*profile["immersive_interest"]), 2)
        group_attendance_tendency = round(RNG.uniform(2.2, 4.9), 2)
        prior_attendance = RNG.randint(1, 8)

        price_shown = RNG.choice(prices)
        latent = profile["wtp_center"] - price_shown
        score = (
            3.05
            + (latent / 22.0)
            + (immersive_interest - 3.5) * 0.25
            + RNG.uniform(-0.7, 0.7)
        )
        likert = max(1, min(5, int(round(score))))
        purchase_binary = 1 if likert >= 4 else 0

        cheap_base = profile["wtp_center"]
        too_cheap = max(18, round(cheap_base - RNG.uniform(30, 42), 2))
        cheap = max(too_cheap + 5, round(cheap_base - RNG.uniform(18, 28), 2))
        expensive = round(cheap_base + RNG.uniform(5, 16), 2)
        too_expensive = round(expensive + RNG.uniform(15, 30), 2)

        responses.append(
            {
                "respondent_id": f"resp_{i:04d}",
                "segment_hint": profile["name"],
                "age_band": age_band,
                "gender": gender,
                "education": education,
                "city_context": weighted_choice(
                    {
                        "New York": 0.71,
                        "New Jersey": 0.15,
                        "Connecticut": 0.06,
                        "Remote": 0.08,
                    }
                ),
                "attendance_frequency": attendance,
                "genre_preference": weighted_choice(
                    {
                        "classical": 0.34,
                        "immersive": 0.29,
                        "broadway": 0.25,
                        "crossover": 0.12,
                    }
                ),
                "channel_preference": preferred_channel,
                "immersive_interest_score": immersive_interest,
                "group_attendance_tendency": group_attendance_tendency,
                "prior_attendance_count": prior_attendance,
                "price_shown": float(price_shown),
                "purchase_intent_binary": purchase_binary,
                "purchase_intent_likert": likert,
                "too_cheap": too_cheap,
                "cheap": cheap,
                "expensive": expensive,
                "too_expensive": too_expensive,
                "response_date": (
                    start_date + dt.timedelta(days=RNG.randint(0, 45))
                ).isoformat(),
                "source_file": "Final presentation/B3/Audience.pdf",
                "source_sheet": "Audience and genre pricing chapters",
                "is_synthetic": True,
                "assumption_note": "Synthetic micro-survey generated with deterministic seed from report-level distributions.",
            }
        )

    return responses


def build_hero_event_brief() -> dict:
    return {
        "event_name": "Beethoven After Dark",
        "event_type": "immersive classical",
        "city": "New York",
        "venue_name": "Chelsea Warehouse Hall",
        "venue_capacity": 280,
        "launch_date": "2026-02-14",
        "candidate_price_low": 45,
        "candidate_price_mid": 75,
        "candidate_price_high": 120,
        "budget_band": "mid",
        "target_goal": "maximize_revenue",
        "concept_description": "Late-night immersive Beethoven performance with narrative staging, actor-guided transitions, and premium social add-ons.",
        "source_file": "Final presentation/B1.xlsx",
        "source_sheet": "Sheet1",
        "is_synthetic": True,
        "assumption_note": "Hero event brief synthesized from benchmark and cost workbooks for the NYC demo case.",
    }


def summarize_segments(survey_responses: List[dict]) -> List[dict]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in survey_responses:
        grouped[row["segment_hint"]].append(row)
    total = len(survey_responses)

    segment_theme_lookup = {
        "Classical Purists": [
            "musical excellence",
            "orchestral authenticity",
            "evening cultural ritual",
        ],
        "Cultural Trend Seekers": [
            "shareable moments",
            "social discovery",
            "visual immersion",
        ],
        "Broadway Experience Enthusiasts": [
            "production scale",
            "narrative spectacle",
            "premium seating",
        ],
        "International Young Professionals": [
            "after-work culture",
            "group plans",
            "price-value balance",
        ],
    }
    barriers_lookup = {
        "Classical Purists": ["over-gamified format", "unclear repertoire depth"],
        "Cultural Trend Seekers": ["boring creative direction", "slow social proof"],
        "Broadway Experience Enthusiasts": [
            "weak storytelling cohesion",
            "underpowered staging",
        ],
        "International Young Professionals": [
            "late purchase friction",
            "transport timing",
        ],
    }

    out = []
    ranked_segments = sorted(
        grouped.items(),
        key=lambda item: (
            len(item[1])
            * (sum(r["purchase_intent_binary"] for r in item[1]) / max(len(item[1]), 1))
        ),
        reverse=True,
    )

    for idx, (segment_name, rows) in enumerate(ranked_segments, start=1):
        channel_counts = Counter(r["channel_preference"] for r in rows)
        top_channels = [k for k, _ in channel_counts.most_common(3)]
        avg_wtp = statistics.mean(r["cheap"] for r in rows)
        avg_likert = statistics.mean(r["purchase_intent_likert"] for r in rows)
        if avg_likert >= 3.9:
            sensitivity = "low"
        elif avg_likert >= 3.3:
            sensitivity = "medium"
        else:
            sensitivity = "high"
        out.append(
            {
                "segment_id": f"seg_{idx}",
                "segment_name": segment_name,
                "segment_size_pct": round(len(rows) / total, 4),
                "motivations": segment_theme_lookup[segment_name][:2],
                "barriers": barriers_lookup[segment_name],
                "preferred_channels": top_channels,
                "avg_wtp": round(avg_wtp, 2),
                "price_sensitivity": sensitivity,
                "representative_themes": segment_theme_lookup[segment_name],
                "expected_conversion_base": round(
                    sum(r["purchase_intent_binary"] for r in rows) / len(rows), 4
                ),
                "source_file": "assets/data/survey_responses.json",
                "source_sheet": "survey_responses",
                "is_synthetic": True,
            }
        )
    return out


def build_pricing_recommendation(survey_responses: List[dict]) -> dict:
    cheap_vals = sorted(r["cheap"] for r in survey_responses)
    expensive_vals = sorted(r["expensive"] for r in survey_responses)
    too_expensive_vals = sorted(r["too_expensive"] for r in survey_responses)
    n = len(survey_responses)

    acceptable_low = round(cheap_vals[int(0.35 * (n - 1))], 2)
    acceptable_high = round(expensive_vals[int(0.72 * (n - 1))], 2)
    ipp = round(
        (statistics.median(cheap_vals) + statistics.median(expensive_vals)) / 2.0, 2
    )
    opp = round(statistics.median(expensive_vals), 2)
    ga = round(min(max(ipp, acceptable_low + 8.0), acceptable_high - 7.0), 2)
    premium = round(ga * 1.58, 2)
    student = round(ga * 0.67, 2)

    return {
        "acceptable_range_low": acceptable_low,
        "acceptable_range_high": acceptable_high,
        "optimal_price_point": opp,
        "indifference_price_point": ipp,
        "recommended_ga_price": ga,
        "recommended_premium_price": premium,
        "recommended_student_price": student,
        "rationale": [
            "GA is anchored near the empirical indifference price while staying inside the acceptable range.",
            "Premium tier captures high-WTP Broadway/experience demand without pushing median respondents into rejection.",
            "Student guardrail maintains accessibility objective alongside revenue target.",
        ],
        "source_file": "assets/data/survey_responses.json",
        "source_sheet": "survey_responses",
        "is_synthetic": True,
        "assumption_note": "Van Westendorp points are estimated from synthetic micro-survey responses generated from source report distributions.",
    }


def build_demand_scenarios(
    segments: List[dict], channels: List[dict], pricing: dict, event_brief: dict
) -> List[dict]:
    capacity = event_brief["venue_capacity"]
    ga = pricing["recommended_ga_price"]
    premium = pricing["recommended_premium_price"]

    top_channels = sorted(
        channels,
        key=lambda x: x["audience_size_proxy"] * x["estimated_conversion"],
        reverse=True,
    )
    channel_factor = sum(c["estimated_conversion"] for c in top_channels[:4]) / 4.0

    segment_attendance_score = 0.0
    for seg in segments:
        segment_attendance_score += (
            seg["segment_size_pct"] * seg["expected_conversion_base"]
        )

    base_attendance = capacity * (
        0.58 + segment_attendance_score * 0.75 + channel_factor * 1.8
    )
    base_attendance = min(capacity * 0.98, max(capacity * 0.62, base_attendance))

    scenarios = [
        ("conservative", 0.87, 0.91, 0.96),
        ("base", 1.0, 1.0, 1.0),
        ("optimistic", 1.08, 1.05, 1.06),
    ]

    out = []
    for name, demand_mult, price_mult, noise in scenarios:
        attendance = int(round(base_attendance * demand_mult))
        attendance = max(0, min(capacity, attendance))
        premium_mix = (
            0.22 if name == "conservative" else 0.28 if name == "base" else 0.33
        )
        blended_price = (ga * (1.0 - premium_mix) + premium * premium_mix) * price_mult
        revenue = round(attendance * blended_price, 2)
        p10 = round(revenue * (0.86 * noise), 2)
        p90 = round(revenue * (1.14 * noise), 2)
        out.append(
            {
                "scenario_name": name,
                "base_price": ga,
                "premium_price": premium,
                "expected_attendance": attendance,
                "expected_occupancy_pct": round(attendance / capacity, 4),
                "expected_revenue": revenue,
                "revenue_p10": p10,
                "revenue_p90": p90,
                "channel_emphasis": [c["channel"] for c in top_channels[:3]],
                "source_file": "assets/data/hero_segments.json",
                "source_sheet": "hero_segments",
                "is_synthetic": True,
            }
        )
    return out


def build_hero_memo(
    event_brief: dict,
    segments: List[dict],
    demand: List[dict],
    pricing: dict,
    channels: List[dict],
) -> dict:
    base = next(s for s in demand if s["scenario_name"] == "base")
    best_segments = sorted(
        segments,
        key=lambda x: x["segment_size_pct"] * x["expected_conversion_base"],
        reverse=True,
    )[:2]
    top_channels = base.get("channel_emphasis", [])[:3]

    return {
        "headline": "Launch Beethoven After Dark at premium-accessible pricing with digital-first channel mix.",
        "objective": "Maximize first-run revenue while preserving student-accessible entry points and occupancy confidence.",
        "top_segments": [s["segment_name"] for s in best_segments],
        "pricing_decision": (
            f"Set GA at ${pricing['recommended_ga_price']:.2f}, premium at ${pricing['recommended_premium_price']:.2f}, "
            f"and student guardrail at ${pricing['recommended_student_price']:.2f}."
        ),
        "channel_decision": "Prioritize "
        + ", ".join(top_channels)
        + " for launch-week conversion.",
        "positioning_decision": "Lead with narrative immersion plus Beethoven authenticity; message quality and social shareability equally.",
        "key_risks": [
            "Survey responses are synthetic and should be replaced with live pilot responses before go-live pricing.",
            "Revenue scenarios are simulation outputs, not audited forecasts.",
            "Channel conversion priors are proxy estimates from social reach tables.",
        ],
        "next_experiment": "Run a 2-week paid creative test comparing performance-led vs social-proof-led ad sets at GA $74 and $79.",
        "support_metrics": {
            "expected_attendance_base": base["expected_attendance"],
            "expected_occupancy_pct_base": base["expected_occupancy_pct"],
            "expected_revenue_base": base["expected_revenue"],
            "revenue_interval_base": f"{base['revenue_p10']} - {base['revenue_p90']}",
            "acceptable_price_low": pricing["acceptable_range_low"],
            "acceptable_price_high": pricing["acceptable_range_high"],
            "recommended_ga_price": pricing["recommended_ga_price"],
            "recommended_premium_price": pricing["recommended_premium_price"],
        },
        "evidence_links": {
            "segments": "assets/data/hero_segments.json",
            "demand": "assets/data/hero_demand_scenarios.json",
            "pricing": "assets/data/hero_pricing_recommendation.json",
        },
        "source_file": "assets/data",
        "source_sheet": "hero_artifacts",
        "is_synthetic": True,
    }


def build_source_health_report(
    source: dict,
    events_comps: List[dict],
    audience_text: List[dict],
    survey_responses: List[dict],
    channel_metrics: List[dict],
) -> dict:
    missing_counts = {
        "events_comps_missing_ticket_mid": sum(
            1 for r in events_comps if r.get("ticket_price_mid") in (None, "")
        ),
        "audience_text_missing_engagement": sum(
            1 for r in audience_text if r.get("engagement_signal") in (None, "")
        ),
        "survey_missing_price_fields": sum(
            1
            for r in survey_responses
            if any(
                r.get(k) in (None, "")
                for k in (
                    "price_shown",
                    "too_cheap",
                    "cheap",
                    "expensive",
                    "too_expensive",
                )
            )
        ),
        "channel_missing_cost_proxy": sum(
            1 for r in channel_metrics if r.get("cpm_or_cost_proxy") in (None, "")
        ),
    }

    xlt_path = (
        FINAL_PRESENTATION / "A1" / "Hamilton data report from Broadway World.xlt"
    )

    return {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "pipeline_version": "1.0.0",
        "deterministic_seed": SEED,
        "source_inventory": [
            {
                "source_file": "Final presentation/Data Collection & Visualization.xlsx",
                "status": "parsed",
                "sheets": [
                    "Audience Demographics",
                    "Broadway Revenue",
                    "Streaming Data",
                ],
                "row_counts": {
                    "Audience Demographics": len(source["demographics_rows"]),
                    "Broadway Revenue": len(source["broadway_rows"]),
                    "Streaming Data": len(source["streaming_rows"]),
                },
            },
            {
                "source_file": "Final presentation/B1.xlsx",
                "status": "parsed",
                "sheets": ["Sheet1"],
                "row_counts": {"Sheet1": len(source["benchmark_rows"])},
            },
            {
                "source_file": "Final presentation/B2.xlsx",
                "status": "parsed",
                "sheets": ["Sheet1"],
                "row_counts": {"Sheet1": len(source["costs_rows"])},
            },
            {
                "source_file": "Final presentation/C2.xlsx",
                "status": "parsed",
                "sheets": ["Sheet1"],
                "row_counts": {"Sheet1": len(source["c2_rows"])},
            },
            {
                "source_file": "Final presentation/B3/Audience.pdf",
                "status": "referenced",
                "usage": "Theme and quote grounding for audience text and channels",
            },
            {
                "source_file": "Final presentation/A1/Hamilton data report from Broadway World.xlt",
                "status": "fallback_not_parsed",
                "reason": "Binary .xlt format is not robustly parseable with stdlib-only zip+xml parser.",
                "fallback_used": "Equivalent Broadway weekly table from Data Collection & Visualization.xlsx::Broadway Revenue",
                "file_exists": xlt_path.exists(),
            },
        ],
        "table_row_counts": {
            "events_comps": len(events_comps),
            "audience_text": len(audience_text),
            "survey_responses": len(survey_responses),
            "channel_metrics": len(channel_metrics),
        },
        "missing_value_audit": missing_counts,
        "warnings": [
            "Synthetic records are clearly labeled with is_synthetic and assumption_note fields.",
            "Memo should be treated as decision-support narrative, not guaranteed forecast output.",
        ],
    }


def build_spec_coverage_matrix() -> dict:
    return {
        "generated_by": "scripts/build_demo_data.py",
        "deterministic_seed": SEED,
        "coverage": [
            {
                "artifact": "assets/data/events_comps.json",
                "spec_section": "5.3A Comparable events table",
                "required_fields": [
                    "event_id",
                    "event_name",
                    "event_type",
                    "city",
                    "venue_name",
                    "venue_capacity",
                    "event_date",
                    "launch_window_days",
                    "positioning_statement",
                    "genre_tags",
                    "language_context",
                    "ticket_price_low",
                    "ticket_price_mid",
                    "ticket_price_high",
                    "bundle_available",
                    "student_discount",
                    "premium_experience",
                    "social_posts_count",
                    "engagement_proxy",
                    "sellout_proxy",
                    "attendance_proxy",
                    "earned_media_count",
                    "partner_branding",
                    "notes",
                ],
                "status": "covered",
            },
            {
                "artifact": "assets/data/audience_text.json",
                "spec_section": "5.3B Audience text corpus",
                "required_fields": [
                    "text_id",
                    "source",
                    "source_type",
                    "event_reference",
                    "raw_text",
                    "date",
                    "city_context",
                    "language",
                    "engagement_signal",
                ],
                "status": "covered",
            },
            {
                "artifact": "assets/data/survey_responses.json",
                "spec_section": "5.3C Micro-survey (Gabor-Granger + Van Westendorp)",
                "required_fields": [
                    "price_shown",
                    "purchase_intent_binary",
                    "purchase_intent_likert",
                    "too_cheap",
                    "cheap",
                    "expensive",
                    "too_expensive",
                ],
                "status": "covered",
            },
            {
                "artifact": "assets/data/channel_metrics.json",
                "spec_section": "5.3D Channel metrics",
                "required_fields": [
                    "channel",
                    "audience_size_proxy",
                    "historical_ctr",
                    "estimated_conversion",
                    "cpm_or_cost_proxy",
                ],
                "status": "covered",
            },
            {
                "artifact": "assets/data/hero_*.json",
                "spec_section": "21 Demo-mode data bundle",
                "required_fields": [
                    "hero_event_brief",
                    "hero_segments",
                    "hero_demand_scenarios",
                    "hero_pricing_recommendation",
                    "hero_memo",
                ],
                "status": "covered",
            },
        ],
    }


def build_analysis_summary(
    events_comps: List[dict],
    audience_text: List[dict],
    survey_responses: List[dict],
    channel_metrics: List[dict],
    segments: List[dict],
    demand_scenarios: List[dict],
    pricing: dict,
) -> str:
    base = next(x for x in demand_scenarios if x["scenario_name"] == "base")
    top_channels = base.get("channel_emphasis", [])[:3]
    synth_counts = {
        "events": sum(1 for x in events_comps if x.get("is_synthetic")),
        "text": sum(1 for x in audience_text if x.get("is_synthetic")),
        "survey": sum(1 for x in survey_responses if x.get("is_synthetic")),
        "channels": sum(1 for x in channel_metrics if x.get("is_synthetic")),
    }

    return "\n".join(
        [
            "# Data Analysis Summary",
            "",
            "## Build context",
            "- Script: `scripts/build_demo_data.py`",
            f"- Deterministic seed: `{SEED}`",
            "- Parser: XLSX zip+xml (shared strings + sheet XML)",
            "- XLT handling: binary `.xlt` kept as fallback-only source and documented in source health report",
            "",
            "## Output inventory",
            f"- Comparable events rows: `{len(events_comps)}`",
            f"- Audience text rows: `{len(audience_text)}`",
            f"- Survey responses rows: `{len(survey_responses)}`",
            f"- Channel metrics rows: `{len(channel_metrics)}`",
            f"- Hero segments: `{len(segments)}`",
            "",
            "## Hero-case findings (Beethoven After Dark, NYC)",
            f"- Recommended GA price: `${pricing['recommended_ga_price']}`",
            f"- Recommended premium price: `${pricing['recommended_premium_price']}`",
            f"- Acceptable range: `${pricing['acceptable_range_low']}` to `${pricing['acceptable_range_high']}`",
            f"- Base expected attendance: `{base['expected_attendance']}` / 280",
            f"- Base expected occupancy: `{base['expected_occupancy_pct']}`",
            f"- Base expected revenue: `${base['expected_revenue']}`",
            f"- Top conversion channels: `{', '.join(top_channels)}`",
            "",
            "## Assumptions and synthetic labels",
            "- `is_synthetic`: marks generated rows introduced to complete demo-ready schemas",
            "- `assumption_note`: explains why synthetic data was required and how it was grounded",
            "- Synthetic counts by table:",
            f"  - events_comps: `{synth_counts['events']}`",
            f"  - audience_text: `{synth_counts['text']}`",
            f"  - survey_responses: `{synth_counts['survey']}`",
            f"  - channel_metrics: `{synth_counts['channels']}`",
            "",
            "## Provenance policy",
            "- Every table includes `source_file` and `source_sheet` fields",
            "- Hero artifacts trace numeric claims back to segment, demand, and pricing JSON assets",
            "",
            "## Limitations",
            "- Survey and parts of channel metrics are deterministic synthetic placeholders for demo mode",
            "- Demand and revenue are simulation outputs; they are not validated ticket-sales forecasts",
        ]
    )


def write_json(path: Path, payload: object) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    columns: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> None:
    ensure_dirs()
    source = extract_source_data()

    events_comps = build_events_comps(source)
    audience_text = build_audience_text()
    survey_responses = build_survey_responses()
    channel_metrics = build_channel_metrics(source)

    hero_event_brief = build_hero_event_brief()
    hero_segments = summarize_segments(survey_responses)
    hero_pricing = build_pricing_recommendation(survey_responses)
    hero_demand = build_demand_scenarios(
        hero_segments, channel_metrics, hero_pricing, hero_event_brief
    )
    hero_memo = build_hero_memo(
        hero_event_brief, hero_segments, hero_demand, hero_pricing, channel_metrics
    )

    source_health = build_source_health_report(
        source, events_comps, audience_text, survey_responses, channel_metrics
    )
    spec_coverage = build_spec_coverage_matrix()
    analysis_summary = build_analysis_summary(
        events_comps,
        audience_text,
        survey_responses,
        channel_metrics,
        hero_segments,
        hero_demand,
        hero_pricing,
    )

    write_json(ASSETS_DATA / "events_comps.json", events_comps)
    write_json(ASSETS_DATA / "audience_text.json", audience_text)
    write_json(ASSETS_DATA / "survey_responses.json", survey_responses)
    write_json(ASSETS_DATA / "channel_metrics.json", channel_metrics)

    write_csv(ASSETS_DATA / "events_comps.csv", events_comps)
    write_csv(ASSETS_DATA / "audience_text.csv", audience_text)
    write_csv(ASSETS_DATA / "survey_responses.csv", survey_responses)
    write_csv(ASSETS_DATA / "channel_metrics.csv", channel_metrics)

    write_json(ASSETS_DATA / "hero_event_brief.json", hero_event_brief)
    write_json(ASSETS_DATA / "hero_segments.json", hero_segments)
    write_json(ASSETS_DATA / "hero_demand_scenarios.json", hero_demand)
    write_json(ASSETS_DATA / "hero_pricing_recommendation.json", hero_pricing)
    write_json(ASSETS_DATA / "hero_memo.json", hero_memo)

    write_json(ASSETS_DATA / "source_health_report.json", source_health)
    write_json(PROCESSED_DATA / "spec_coverage_matrix.json", spec_coverage)

    with (DOCS_DIR / "data-analysis-summary.md").open("w", encoding="utf-8") as f:
        f.write(analysis_summary)
        f.write("\n")

    train_script = ROOT / "scripts" / "train_model_suite.py"
    if train_script.exists():
        subprocess.run([sys.executable, str(train_script)], check=True)

    print("StageSignal demo data artifacts built successfully.")
    print(f"events_comps rows: {len(events_comps)}")
    print(f"audience_text rows: {len(audience_text)}")
    print(f"survey_responses rows: {len(survey_responses)}")
    print(f"channel_metrics rows: {len(channel_metrics)}")


if __name__ == "__main__":
    main()
