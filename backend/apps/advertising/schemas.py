from ninja import Schema


class AdvertisementSlideOut(Schema):
    id: int
    title: str
    subtitle: str
    description: str
    image_desktop: str
    image_mobile: str
    button_text: str
    button_url: str
    sort_order: int


class AdvertisementSlideListOut(Schema):
    results: list[AdvertisementSlideOut]
    count: int
