from datetime import datetime

from ninja import Schema


class AboutFeatureOut(Schema):
    id: int
    kind: str
    label: str
    title: str
    body: str
    sort_order: int


class AboutStatisticOut(Schema):
    id: int
    label: str
    value: str
    sort_order: int


class AboutTeamMemberOut(Schema):
    id: int
    name: str
    role: str
    bio: str
    photo: str
    sort_order: int


class AboutPageOut(Schema):
    hero_kicker: str
    title: str
    subtitle: str
    intro: str
    hero_image: str
    mission_title: str
    mission: str
    vision_title: str
    vision: str
    values_title: str
    values: str
    goals_title: str
    goals: str
    mission_image: str
    story_eyebrow: str
    story_title: str
    story_body: str
    cta_eyebrow: str
    cta_title: str
    closing_text: str
    primary_cta_label: str
    primary_cta_url: str
    secondary_cta_label: str
    secondary_cta_url: str
    show_globe: bool
    seo_title: str
    seo_description: str
    features: list[AboutFeatureOut]
    statistics: list[AboutStatisticOut]
    team_members: list[AboutTeamMemberOut]
    updated_at: datetime


class ContactFAQOut(Schema):
    id: int
    question: str
    answer: str
    sort_order: int


class ContactPageOut(Schema):
    title: str
    description: str
    support_email: str
    business_email: str
    phone: str
    whatsapp: str
    office_address: str
    response_hours: str
    map_url: str
    instagram_url: str
    linkedin_url: str
    telegram_url: str
    support_text: str
    form_intro: str
    seo_title: str
    seo_description: str
    faqs: list[ContactFAQOut]
    updated_at: datetime
