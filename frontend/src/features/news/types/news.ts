export interface NewsItem {
  id: number;
  title: string;
  summary: string;
  source_name: string;
  source_website: string;
  topic: string;
  original_url: string;
  image_url: string;
  published_at: string | null;
  fetched_at: string;
  score: number;
  is_pinned: boolean;
}

export interface TopicSection {
  topic: string;
  items: NewsItem[];
}

export interface NewsListResponse {
  results: NewsItem[];
  topics: string[];
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  updated_at: string | null;
}

export interface HeadlinesResponse {
  featured: NewsItem | null;
  minis: NewsItem[];
  latest: NewsItem[];
  pinned: NewsItem[];
  highlights: NewsItem[];
  sections: TopicSection[];
  source_count: number;
  updated_at: string | null;
}

export interface NewsDetailResponse {
  item: NewsItem;
  related: NewsItem[];
}

export type NewsOrdering = "-published_at" | "published_at";

export interface NewsListParams {
  topic?: string;
  q?: string;
  page?: number;
  pageSize?: number;
  ordering?: NewsOrdering;
}
