export interface AdvertisementSlide {
  id: number;
  title: string;
  subtitle: string;
  description: string;
  image_desktop: string;
  image_mobile: string;
  button_text: string;
  button_url: string;
  sort_order: number;
}

export interface AdvertisementSlideListResponse {
  results: AdvertisementSlide[];
  count: number;
}
