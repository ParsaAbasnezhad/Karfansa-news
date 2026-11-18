export interface AboutFeature {
  id: number;
  kind: string;
  label: string;
  title: string;
  body: string;
  sort_order: number;
}

export interface AboutStatistic {
  id: number;
  label: string;
  value: string;
  sort_order: number;
}

export interface AboutTeamMember {
  id: number;
  name: string;
  role: string;
  bio: string;
  photo: string;
  sort_order: number;
}

export interface AboutPageContent {
  hero_kicker: string;
  title: string;
  subtitle: string;
  intro: string;
  hero_image: string;
  mission_title: string;
  mission: string;
  vision_title: string;
  vision: string;
  values_title: string;
  values: string;
  goals_title: string;
  goals: string;
  mission_image: string;
  story_eyebrow: string;
  story_title: string;
  story_body: string;
  cta_eyebrow: string;
  cta_title: string;
  closing_text: string;
  primary_cta_label: string;
  primary_cta_url: string;
  secondary_cta_label: string;
  secondary_cta_url: string;
  show_globe: boolean;
  seo_title: string;
  seo_description: string;
  features: AboutFeature[];
  statistics: AboutStatistic[];
  team_members: AboutTeamMember[];
  updated_at: string;
}

export interface ContactFAQ {
  id: number;
  question: string;
  answer: string;
  sort_order: number;
}

export interface ContactPageContent {
  title: string;
  description: string;
  support_email: string;
  business_email: string;
  phone: string;
  whatsapp: string;
  office_address: string;
  response_hours: string;
  map_url: string;
  instagram_url: string;
  linkedin_url: string;
  telegram_url: string;
  support_text: string;
  form_intro: string;
  seo_title: string;
  seo_description: string;
  faqs: ContactFAQ[];
  updated_at: string;
}
