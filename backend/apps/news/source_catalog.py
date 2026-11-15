"""RSS endpoints checked against current feed listings before seeding."""

SOURCE_CATALOG: tuple[dict[str, str], ...] = (
    {
        "name": "ایسنا - اقتصاد",
        "rss_url": "https://www.isna.ir/rss/tp/34",
        "website_url": "https://www.isna.ir/",
        "category": "economy",
    },
    {
        "name": "مهر - اقتصاد",
        "rss_url": "https://www.mehrnews.com/rss/tp/25",
        "website_url": "https://www.mehrnews.com/",
        "category": "economy",
    },
    {
        "name": "ایرنا",
        "rss_url": "https://www.irna.ir/rss",
        "website_url": "https://www.irna.ir/",
        "category": "other",
    },
)
