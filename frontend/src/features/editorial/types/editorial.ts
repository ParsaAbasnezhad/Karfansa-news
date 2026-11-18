export interface EditorialCategory {
  id: number;
  slug: string;
  name: string;
}

export interface EditorialArticle {
  id: number;
  slug: string;
  title: string;
  summary: string;
  source_url: string;
  featured_image_url: string;
  featured_image_srcset: string;
  featured_image_width: number | null;
  featured_image_height: number | null;
  category: EditorialCategory | null;
  tags: string[];
  author_name: string;
  published_at: string;
  updated_at: string;
  reading_time: number;
  is_featured: boolean;
  is_breaking: boolean;
  is_pinned: boolean;
  priority: number;
}

export interface EditorialGalleryImage {
  id: number;
  image_url: string;
  image_srcset: string;
  width: number | null;
  height: number | null;
  alt_text: string;
  caption: string;
}

export interface EditorialDetail extends EditorialArticle {
  content: string;
  gallery: EditorialGalleryImage[];
  editor_name: string;
  source_name: string;
  seo_title: string;
  seo_description: string;
  view_count: number;
}

export type EditorialOrdering = "-published_at" | "published_at" | "priority";

export interface EditorialListParams {
  category?: string;
  q?: string;
  ordering?: EditorialOrdering;
  page?: number;
  pageSize?: number;
}

export interface EditorialListResponse {
  results: EditorialArticle[];
  categories: EditorialCategory[];
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface EditorialFeaturedResponse {
  featured: EditorialArticle | null;
  secondary: EditorialArticle[];
}

export interface EditorialLatestResponse {
  results: EditorialArticle[];
}

export interface EditorialCategoriesResponse {
  results: EditorialCategory[];
}

export interface EditorialDetailResponse {
  item: EditorialDetail;
  related: EditorialArticle[];
}
