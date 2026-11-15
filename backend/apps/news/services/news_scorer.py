import re

from apps.news.models import News, NewsTopic

# حداقل امتیاز برای پذیرفتن خبر
MIN_NEWS_SCORE = 35

# Generic terms do not identify a topic on their own.
GENERIC_KEYWORDS = {
    "کشور",
    "طرح",
    "تولید",
    "بازار",
}

# -------------------------------
# کلمات مسدودکننده (فقط عنوان بررسی می‌شود)
# -------------------------------
BLOCKED_TITLE_KEYWORDS = [
    # جنگ و نظامی
    "جنگ",
    "حمله موشکی",
    "حمله پهپادی",
    "بمباران",
    "درگیری نظامی",
    "عملیات نظامی",
    "رزمایش نظامی",
    # ورزش
    "فوتبال",
    "والیبال",
    "بسکتبال",
    "مسابقه ورزشی",
    "لیگ برتر فوتبال",
    "کشتی",
    "هندبال",
    "تنیس",
    "المپیک",
    "ورزش",
    # سرگرمی
    "سینما",
    "بازیگر",
    "سریال",
    "کنسرت",
    "سلبریتی",
    "سرگرمی",
    # سیاست غیرتجاری
    "انتخابات",
    "نامزد انتخابات",
    "کرسی نخست وزیری",
    "استیضاح",
    "سیاست خارجی",
    # حوادث
    "تصادف",
    "آتش سوزی",
    "زلزله",
    "سرقت",
    "قتل",
    "آدم ربایی",
    "حوادث",
]

# کلماتی که اگر در عنوان خبر باشند، حتی با وجود کلمه مسدودکننده هم خبر پذیرفته می‌شود
# (مثلاً «تأثیر جنگ بر قیمت نفت» یک خبر اقتصادی است)
BLOCKED_OVERRIDE_KEYWORDS = [
    "قیمت",
    "صادرات",
    "واردات",
    "تجارت",
    "اقتصاد",
    "سرمایه گذاری",
    "صنعت",
    "کشاورزی",
    "نفت",
    "گاز",
    "پتروشیمی",
    "بورس",
    "ارز",
    "تورم",
    "بودجه",
    "گمرک",
    "سهام",
    "دلار",
    "طلا",
    "لجستیک",
    "تسهیلات",
]

# -------------------------------
# اولویت موضوعات
# -------------------------------
_AGRICULTURE_PRIORITY = [
    "کشاورزی",
    "محصولات کشاورزی",
    "گندم",
    "جو",
    "برنج",
    "ذرت",
    "زعفران",
    "پسته",
    "باغداری",
    "دامداری",
    "طیور",
    "صنایع غذایی",
    "نهاده دامی",
    "کود کشاورزی",
]
_ENERGY_PRIORITY = [
    "نفت",
    "گاز",
    "پتروشیمی",
    "بنزین",
    "گازوئیل",
    "نیروگاه",
    "انرژی",
    "تولید برق",
    "قیمت جهانی نفت",
]
TOPIC_PRIORITY_KEYWORDS = {
    "کشاورزی": _AGRICULTURE_PRIORITY,
    "کشاورزی و صنایع غذایی": _AGRICULTURE_PRIORITY,
    "انرژی": _ENERGY_PRIORITY,
    "انرژی و نفت": _ENERGY_PRIORITY,
}

# -------------------------------
# محیط‌زیست
# -------------------------------
ENVIRONMENT_ECONOMIC_KEYWORDS = [
    "تولید",
    "صنعت",
    "کشاورزی",
    "هزینه",
    "سرمایه گذاری",
    "اقتصادی",
    "تجاری",
    "صادرات",
    "واردات",
    "بهره وری",
    "امنیت غذایی",
    "تأمین آب",
    "تامین آب",
]

# -------------------------------
# Scoring weights
# -------------------------------
TITLE_MATCH_WEIGHT = 50
SUMMARY_MATCH_WEIGHT = 15


def normalize_text(value: str) -> str:
    """یکسان‌سازی متن فارسی برای مقایسه کلمات کلیدی."""
    value = value or ""
    value = value.replace("ي", "ی").replace("ك", "ک")
    value = value.replace("‌", " ")  # نیم‌فاصله → فاصله
    # حذف علائم نگارشی که تطبیق را می‌شکنند (نقطه، ویرگول، پرانتز، ...)
    value = re.sub(r"[.,،؛:!?؟«»\"'()\[\]{}]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def _keyword_in(keyword_norm: str, text_norm: str) -> bool:
    """
    تطبیق کلمه کلیدی به صورت مرز کلمه (word-boundary) با پشتیبانی از فارسی.
    از substring ساده استفاده نمی‌کنیم تا «جنگ» در «جنگل» تطبیق نخورد.
    """
    if not keyword_norm:
        return False
    # \b در فارسی درست کار نمی‌کند؛ از lookaround با فاصله/ابتدای/انتهای رشته استفاده می‌کنیم
    pattern = r"(?<![\w\u0600-\u06FF])" + re.escape(keyword_norm) + r"(?![\w\u0600-\u06FF])"
    return re.search(pattern, text_norm) is not None


def _normalize_keywords(keywords) -> list[str]:
    seen = set()
    result = []
    for kw in keywords or []:
        n = normalize_text(kw)
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result


def _score_matches(title_norm, summary_norm, keyword_norms, tags=None, topic_name=""):
    specific_keywords = [kw for kw in keyword_norms if kw not in GENERIC_KEYWORDS]
    title_matches = _independent_matches(specific_keywords, title_norm)
    summary_matches = _independent_matches(
        [kw for kw in specific_keywords if kw not in title_matches],
        summary_norm,
    )
    tag_matches = _independent_matches(
        specific_keywords,
        "\0".join(tags or []),
    )
    direct_topic_tag = normalize_text(topic_name) in (tags or [])
    multiword_title_matches = sum(" " in kw for kw in title_matches)

    text_score = (
        len(title_matches) * TITLE_MATCH_WEIGHT
        + len(summary_matches) * SUMMARY_MATCH_WEIGHT
        + min(multiword_title_matches * 10, 20)
    )
    tag_score = 60 if direct_topic_tag else min(45 * len(tag_matches), 90)
    score = max(text_score, tag_score)
    if tag_matches and (title_matches or summary_matches):
        score = min(100, score + 10)

    strong_evidence = (len(title_matches) >= 3 and bool(summary_matches)) or (
        len(tag_matches) >= 2 and bool(title_matches or summary_matches)
    )
    if score >= 100 and not strong_evidence:
        score = 95

    return {
        "score": min(100, score),
        "title_matches": title_matches,
        "summary_matches": summary_matches,
        "weighted_matches": len(title_matches) * 2 + len(summary_matches),
        "multiword_title_matches": multiword_title_matches,
        "tag_matches": tag_matches,
        "direct_topic_tag": direct_topic_tag,
    }


def _independent_matches(keyword_norms, text_norm):
    candidates = []
    for keyword in keyword_norms:
        pattern = r"(?<![\w\u0600-\u06FF])" + re.escape(keyword) + r"(?![\w\u0600-\u06FF])"
        match = re.search(pattern, text_norm)
        if match:
            candidates.append((match.start(), match.end(), keyword))

    selected = []
    matches = []
    for start, end, keyword in sorted(
        candidates,
        key=lambda item: (item[1] - item[0], item[2]),
        reverse=True,
    ):
        if not any(
            start < selected_end and end > selected_start
            for selected_start, selected_end in selected
        ):
            selected.append((start, end))
            matches.append(keyword)
    return matches


def classify_content_with_reason(title, summary, topics=None, tags=None):
    """Return a topic decision and a short, auditable explanation."""
    normalized_title = normalize_text(title)
    normalized_summary = normalize_text(summary)
    full_text = f"{normalized_title} {normalized_summary}"
    normalized_tags = _normalize_keywords(tags)

    # ---- فیلتر مسدودکننده با امکان override ----
    blocked_terms = [
        normalize_text(kw)
        for kw in BLOCKED_TITLE_KEYWORDS
        if _keyword_in(normalize_text(kw), normalized_title)
    ]
    if blocked_terms:
        has_override = any(
            _keyword_in(normalize_text(kw), normalized_title) for kw in BLOCKED_OVERRIDE_KEYWORDS
        )
        if not has_override:
            return (
                None,
                0,
                f"عنوان دارای عبارت نامرتبط «{blocked_terms[0]}» است و نشانهٔ اقتصادی ندارد.",
            )

    if topics is None:
        topics = NewsTopic.objects.filter(is_active=True)

    best_topic = None
    best_rank = None
    best_score = 0
    best_evidence = None
    best_rejected_score = 0
    best_rejection_reason = ""

    for topic in topics:
        keyword_norms = _normalize_keywords(topic.keywords)
        if not keyword_norms:
            continue

        evidence = _score_matches(
            normalized_title,
            normalized_summary,
            keyword_norms,
            tags=normalized_tags,
            topic_name=topic.name,
        )
        text_match_count = len(evidence["title_matches"]) + len(evidence["summary_matches"])
        has_specific_title_phrase = (
            len(evidence["title_matches"]) == 1 and " " in evidence["title_matches"][0]
        )
        if text_match_count < 2 and not has_specific_title_phrase:
            if evidence["score"] > best_rejected_score:
                best_rejected_score = evidence["score"]
                best_rejection_reason = "تطبیق عنوان و خلاصه برای تعیین موضوع کافی نیست."
            continue

        score = evidence["score"]
        if score < MIN_NEWS_SCORE:
            if score > best_rejected_score:
                best_rejected_score = score
                best_rejection_reason = (
                    f"امتیاز ارتباط {score} از حداقل امتیاز {MIN_NEWS_SCORE} کمتر است."
                )
            continue

        priority_keywords = TOPIC_PRIORITY_KEYWORDS.get(topic.name, [])
        priority_hits = sum(
            1 for kw in priority_keywords if _keyword_in(normalize_text(kw), full_text)
        )

        # محیط‌زیست فقط با اثر اقتصادی/تجاری پذیرفته شود
        if "محیط" in topic.name:
            economic_hits = sum(
                1
                for kw in ENVIRONMENT_ECONOMIC_KEYWORDS
                if _keyword_in(normalize_text(kw), full_text)
            )
            if economic_hits < 2:
                if score > best_rejected_score:
                    best_rejected_score = score
                    best_rejection_reason = (
                        "خبر محیط‌زیستی اثر اقتصادی یا تجاری مشخصی در عنوان و خلاصه ندارد."
                    )
                continue

        rank = (
            score,
            evidence["direct_topic_tag"],
            len(evidence["tag_matches"]),
            evidence["weighted_matches"],
            len(evidence["title_matches"]),
            evidence["multiword_title_matches"],
            priority_hits,
            topic.name,
        )
        if best_rank is None or rank > best_rank:
            best_rank = rank
            best_score = score
            best_topic = topic
            best_evidence = evidence

    if best_topic is None:
        return (
            None,
            round(best_rejected_score),
            (best_rejection_reason or "برای دسته‌های اقتصادی تطبیق معتبری پیدا نشد."),
        )

    matches = []
    if best_evidence:
        matches.extend(best_evidence["title_matches"])
        matches.extend(best_evidence["summary_matches"])
        matches.extend(best_evidence["tag_matches"])
    evidence_text = "، ".join(dict.fromkeys(matches[:8]))
    reason = f"پذیرفته شد در موضوع «{best_topic.name}» با امتیاز {round(best_score)} از 100"
    if evidence_text:
        reason += f"؛ شواهد: {evidence_text}"
    return best_topic, round(best_score), reason


def classify_content(title, summary, topics=None, tags=None):
    """Compatibility wrapper returning the original (topic, score) pair."""
    topic, score, _ = classify_content_with_reason(title, summary, topics, tags)
    return topic, score if topic is not None else 0


# -------------------------------
# سازگاری: تابع قدیمی حفظ شود اما از منطق مشترک استفاده کند
# -------------------------------
def calculate_topic_score(title, summary, keywords, tags=None, topic_name=""):
    """محاسبه امتیاز ارتباط خبر با یک موضوع (هم‌راستا با classify_content)."""
    keyword_norms = _normalize_keywords(keywords)
    if not keyword_norms:
        return 0

    normalized_title = normalize_text(title)
    normalized_summary = normalize_text(summary)
    return round(
        _score_matches(
            normalized_title,
            normalized_summary,
            keyword_norms,
            tags=_normalize_keywords(tags),
            topic_name=topic_name,
        )["score"]
    )


def classify_news(news):
    """دسته‌بندی خبر با استفاده از الگوریتم مشترک."""
    topic, score = classify_content(title=news.title, summary=news.summary)
    news.topic = topic
    news.score = score
    news.save(update_fields=["topic", "score"])
    return {"title": news.title, "topic": topic.name if topic else None, "score": score}


def classify_unclassified_news():
    """دسته‌بندی خبرهایی که هنوز موضوع ندارند."""
    news_items = News.objects.filter(topic__isnull=True)
    return [classify_news(news) for news in news_items]
