import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { useAdvertisementSlides } from "@/features/advertising/hooks";
import type { AdvertisementSlide } from "@/features/advertising/types";
import { formatNumber } from "@/lib/format";
import { isSafeHref } from "@/lib/safe-text-utils";

import "../advertising.css";

const AUTOPLAY_MS = 6000;
const SWIPE_THRESHOLD = 48;

function isExternal(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

function CtaLink({ slide }: { slide: AdvertisementSlide }) {
  if (!slide.button_text || !slide.button_url || !isSafeHref(slide.button_url)) return null;
  const className = "ad-slide-cta";
  if (isExternal(slide.button_url)) {
    return (
      <a className={className} href={slide.button_url} target="_blank" rel="noopener noreferrer">
        {slide.button_text}
        <Icon name="arrow" />
      </a>
    );
  }
  return (
    <Link className={className} to={slide.button_url}>
      {slide.button_text}
      <Icon name="arrow" />
    </Link>
  );
}

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() =>
    typeof window !== "undefined"
      ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
      : false,
  );

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(media.matches);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  return reduced;
}

export function AdSlider({ autoPlay = true }: { autoPlay?: boolean }) {
  const slidesQuery = useAdvertisementSlides();
  const slides = slidesQuery.data?.results ?? [];
  const reducedMotion = usePrefersReducedMotion();
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [progressKey, setProgressKey] = useState(0);
  const pointerStart = useRef<number | null>(null);
  const labelId = useId();

  const count = slides.length;
  const safeIndex = count === 0 ? 0 : ((index % count) + count) % count;
  const canAutoplay = autoPlay && !reducedMotion && !paused && count > 1;

  const goTo = useCallback(
    (next: number) => {
      if (count === 0) return;
      setIndex(((next % count) + count) % count);
      setProgressKey((value) => value + 1);
    },
    [count],
  );

  const next = useCallback(() => goTo(safeIndex + 1), [goTo, safeIndex]);
  const prev = useCallback(() => goTo(safeIndex - 1), [goTo, safeIndex]);

  useEffect(() => {
    if (!canAutoplay) return;
    const timer = window.setTimeout(next, AUTOPLAY_MS);
    return () => window.clearTimeout(timer);
  }, [canAutoplay, next, progressKey]);

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      next();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      prev();
    } else if (event.key === "Home") {
      event.preventDefault();
      goTo(0);
    } else if (event.key === "End") {
      event.preventDefault();
      goTo(count - 1);
    }
  };

  const onPointerDown = (event: ReactPointerEvent<HTMLElement>) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    pointerStart.current = event.clientX;
  };

  const onPointerUp = (event: ReactPointerEvent<HTMLElement>) => {
    if (pointerStart.current == null) return;
    const delta = event.clientX - pointerStart.current;
    pointerStart.current = null;
    if (Math.abs(delta) < SWIPE_THRESHOLD) return;
    // Finger moves left (negative delta) → next slide
    if (delta < 0) next();
    else prev();
  };

  if (slidesQuery.isPending) {
    return <div className="ad-slider-skel" aria-hidden="true" />;
  }

  if (slidesQuery.isError) {
    return null;
  }

  if (count === 0) {
    return null;
  }

  return (
    <section
      className={canAutoplay ? "ad-slider is-playing" : "ad-slider"}
      style={{ ["--ad-interval" as string]: `${AUTOPLAY_MS}ms` }}
      aria-roledescription="carousel"
      aria-labelledby={labelId}
      tabIndex={0}
      onKeyDown={onKeyDown}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setPaused(false);
        }
      }}
      onPointerDown={onPointerDown}
      onPointerUp={onPointerUp}
      onPointerCancel={() => {
        pointerStart.current = null;
      }}
    >
      <h2 id={labelId} className="sr-only">
        تبلیغات کارفنسا
      </h2>
      <div className="ad-slider-track">
        {slides.map((slide, slideIndex) => {
          const active = slideIndex === safeIndex;
          const image = slide.image_mobile || slide.image_desktop;
          return (
            <article
              key={slide.id}
              className={active ? "ad-slide is-active" : "ad-slide"}
              aria-hidden={!active}
              aria-roledescription="slide"
              aria-label={`${formatNumber(slideIndex + 1)} از ${formatNumber(count)}`}
            >
              <div className="ad-slide-media">
                <picture>
                  {slide.image_desktop ? (
                    <source media="(min-width: 768px)" srcSet={slide.image_desktop} />
                  ) : null}
                  <img
                    src={image}
                    alt=""
                    width={1280}
                    height={548}
                    loading={slideIndex === 0 ? "eager" : "lazy"}
                    decoding="async"
                    fetchPriority={slideIndex === 0 ? "high" : "auto"}
                    draggable={false}
                  />
                </picture>
                <div className="ad-slide-overlay" aria-hidden="true" />
              </div>
              <div className="ad-slide-copy">
                {slide.subtitle ? <span className="ad-slide-kicker">{slide.subtitle}</span> : null}
                <h3>{slide.title}</h3>
                {slide.description ? <p>{slide.description}</p> : null}
                <CtaLink slide={slide} />
              </div>
            </article>
          );
        })}
      </div>

      {count > 1 ? (
        <>
          <div className="ad-slider-nav">
            <button
              type="button"
              className="ad-slider-arrow"
              aria-label="اسلاید بعدی"
              onClick={next}
            >
              <Icon name="chevron-right" />
            </button>
            <button
              type="button"
              className="ad-slider-arrow"
              aria-label="اسلاید قبلی"
              onClick={prev}
            >
              <Icon name="chevron-left" />
            </button>
          </div>
          <div className="ad-slider-footer">
            <div className="ad-slider-dots" role="tablist" aria-label="انتخاب اسلاید">
              {slides.map((slide, slideIndex) => (
                <button
                  key={slide.id}
                  type="button"
                  role="tab"
                  className={slideIndex === safeIndex ? "ad-slider-dot is-active" : "ad-slider-dot"}
                  aria-label={`اسلاید ${formatNumber(slideIndex + 1)}`}
                  aria-selected={slideIndex === safeIndex}
                  onClick={() => goTo(slideIndex)}
                />
              ))}
            </div>
            <span className="ad-slider-count" aria-live="polite">
              {formatNumber(safeIndex + 1)} / {formatNumber(count)}
            </span>
          </div>
        </>
      ) : null}

      <div className="ad-slider-progress" aria-hidden="true">
        <span key={progressKey} />
      </div>
    </section>
  );
}
