import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { publishedStamp } from "@/features/news/api/messages";
import { NewsImage } from "@/features/news/components/NewsImage";
import type { NewsItem } from "@/features/news/types/news";
import { formatShortDate } from "@/lib/format";

interface NewsCardProps {
  item: NewsItem;
  heading?: "h2" | "h3";
}

export function NewsCard({ item, heading = "h2" }: NewsCardProps) {
  const Title = heading;
  const stamp = publishedStamp(item.published_at, item.fetched_at);

  return (
    <article className="news-card">
      <Link className="news-card-link" to={`/news/${item.id}`}>
        <NewsImage src={item.image_url} alt="" />
        <div className="news-card-content">
          <div className="news-card-top">
            <span className="news-topic">{item.topic || "اخبار اقتصادی"}</span>
            {item.is_pinned ? <span className="news-pin">ویژه</span> : null}
          </div>
          <Title>{item.title}</Title>
          {item.summary ? <p className="news-summary">{item.summary}</p> : null}
          <footer className="news-card-meta">
            {item.source_name ? (
              <span>
                <Icon name="building" />
                {item.source_name}
              </span>
            ) : null}
            <time dateTime={stamp}>
              <Icon name="clock" />
              {formatShortDate(stamp)}
            </time>
          </footer>
        </div>
      </Link>
    </article>
  );
}
