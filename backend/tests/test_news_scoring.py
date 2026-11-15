from apps.news.services.news_scorer import classify_content, classify_content_with_reason
from apps.news.topic_catalog import TOPIC_CATALOG


class _Topic:
    def __init__(self, name, keywords):
        self.name = name
        self.keywords = keywords


def _topic(name):
    row = next(item for item in TOPIC_CATALOG if item["name"] == name)
    return _Topic(row["name"], row["keywords"])


TOPICS = [_topic(item["name"]) for item in TOPIC_CATALOG]


def test_economic_story_is_accepted_and_war_sport_politics_are_not():
    oil, oil_score = classify_content("تأثیر جنگ بر قیمت نفت", "نفت و انرژی", TOPICS)
    assert oil is not None
    assert oil.name == "انرژی"
    assert oil_score >= 35

    sport, sport_score = classify_content("پیروزی تیم فوتبال در لیگ", "مسابقه ورزشی", TOPICS)
    assert sport is None
    assert sport_score == 0

    cinema, _ = classify_content("بازیگر سریال جدید در کنسرت", "", TOPICS)
    assert cinema is None

    politics, _ = classify_content("استیضاح در مجلس و سیاست خارجی", "", TOPICS)
    assert politics is None


def test_environment_news_needs_a_clear_economic_link():
    weak, weak_score = classify_content("خشکسالی در شمال کشور", "باران نبارید", TOPICS)
    assert weak is None
    assert weak_score == 0

    linked, score = classify_content(
        "خشکسالی و هزینه تغییرات اقلیمی",
        "اثر اقتصادی بر صادرات و سرمایه گذاری",
        TOPICS,
    )
    assert linked is not None
    assert linked.name == "محیط‌زیست"
    assert score >= 35


def test_one_short_title_keyword_is_not_enough_to_accept_an_article():
    topic, score, reason = classify_content_with_reason("دلار", "", TOPICS)

    assert topic is None
    assert score > 0
    assert "عنوان و خلاصه" in reason


def test_budget_story_stays_in_economy():
    topic, score = classify_content("تصویب بودجه و رشد تورم", "سیاست پولی بانک مرکزی", TOPICS)
    assert topic is not None
    assert topic.name == "اقتصاد"
    assert score >= 35


def test_classification_returns_an_auditable_reason_for_acceptance_and_rejection():
    accepted_topic, accepted_score, accepted_reason = classify_content_with_reason(
        "رشد صادرات پسته و تجارت کشاورزی",
        "صادرات پسته و تجارت کشاورزی بیشتر شد",
        TOPICS,
    )
    assert accepted_topic is not None
    assert accepted_score >= 35
    assert "پذیرفته شد" in accepted_reason
    assert accepted_topic.name in accepted_reason

    rejected_topic, rejected_score, rejected_reason = classify_content_with_reason(
        "پیروزی تیم فوتبال در لیگ",
        "مسابقه ورزشی",
        TOPICS,
    )
    assert rejected_topic is None
    assert rejected_score == 0
    assert "نامرتبط" in rejected_reason
