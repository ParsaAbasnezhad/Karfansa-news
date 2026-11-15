import { useEffect, useId, useState, type FormEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { useHeadlines } from "@/features/news/hooks/use-news";

const LOGO = "/KARFANSA%20%E2%80%94%20Logo.svg";

const NAV = [
  { to: "/", label: "صفحهٔ اصلی", end: true },
  { to: "/news", label: "اخبار", end: false },
  { to: "/about", label: "درباره", end: true },
  { to: "/contact", label: "تماس", end: true },
] as const;

export function AppLayout() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const headlines = useHeadlines();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const menuId = useId();
  const today = new Intl.DateTimeFormat("fa-IR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  const closeOverlays = () => {
    setMenuOpen(false);
    setSearchOpen(false);
  };

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const q = query.trim();
    closeOverlays();
    void navigate(q ? `/news?q=${encodeURIComponent(q)}` : "/news");
  };

  const latest = headlines.data?.latest ?? [];
  const ticker = latest.slice(0, 5);
  const topics = headlines.data?.sections.map((section) => section.topic) ?? [];

  return (
    <>
      <a className="skip-link" href="#content">
        رفتن به محتوا
      </a>
      <div className="topbar">
        <div className="wrap">
          <p className="date">
            <span>{today}</span>
          </p>
          <div className="links">
            <Link to="/about">درباره</Link>
            <Link to="/contact">تماس</Link>
            <Link to="/status">وضعیت سرویس</Link>
          </div>
        </div>
      </div>

      <header className={searchOpen ? "masthead sopen" : "masthead"}>
        <div className="wrap">
          <button
            type="button"
            className="burger iconbtn"
            aria-expanded={menuOpen}
            aria-controls={menuId}
            onClick={() => setMenuOpen(true)}
          >
            <Icon name="menu" />
            <span className="sr-only">باز کردن منو</span>
          </button>
          <Link to="/" className="logo" aria-label="کارفنسا نیوز">
            <img src={LOGO} alt="Karfansa" />
          </Link>
          <form className="search" role="search" onSubmit={submitSearch}>
            <Icon name="search" />
            <label className="sr-only" htmlFor="site-search">
              جست‌وجو در اخبار
            </label>
            <input
              id="site-search"
              type="search"
              value={query}
              placeholder="جست‌وجو در عنوان خبرها"
              onChange={(event) => setQuery(event.target.value)}
            />
            <button className="go" type="submit" aria-label="جست‌وجو">
              <Icon name="arrow" />
            </button>
          </form>
          <div className="mast-tools">
            <button
              type="button"
              className="sbtn iconbtn"
              aria-pressed={searchOpen}
              onClick={() => setSearchOpen((open) => !open)}
            >
              <Icon name="search" />
              <span className="sr-only">نمایش جست‌وجو</span>
            </button>
          </div>
        </div>
      </header>

      <nav className="navbar" aria-label="بخش‌های اصلی">
        <div className="wrap">
          <div className="mainnav">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? "on" : "")}
                onClick={closeOverlays}
              >
                {item.label}
              </NavLink>
            ))}
          </div>
          <nav className="topicnav" aria-label="موضوعات خبری">
            {topics.slice(0, 5).map((topic) => (
              <Link
                key={topic}
                to={`/news?topic=${encodeURIComponent(topic)}`}
                onClick={closeOverlays}
              >
                {topic}
              </Link>
            ))}
          </nav>
        </div>
      </nav>

      {ticker.length > 0 ? (
        <div className="ticker">
          <div className="wrap">
            <span className="label">
              <i />
              تازه‌ها
            </span>
            <div className="view">
              <div className="track">
                {ticker.map((item, index) => (
                  <Link className="item" to={`/news/${item.id}`} key={`${item.id}-${index}`}>
                    <time dateTime={item.published_at ?? item.fetched_at}>{item.source_name}</time>
                    {item.title}
                  </Link>
                ))}
              </div>
            </div>
            <Link className="all" to="/news">
              همه
            </Link>
          </div>
        </div>
      ) : null}

      <main id="content" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="wrap fcols">
          <div className="about">
            <Link to="/" className="flogo" aria-label="کارفنسا نیوز">
              <img src={LOGO} alt="" />
            </Link>
            <p>
              پایگاه خبری اقتصادی و تجاری کارفنسا. خبرهای تأییدشده، با موضوع، منبع و زمان انتشار.
            </p>
          </div>
          <div>
            <h5>بخش‌ها</h5>
            <ul>
              {NAV.map((item) => (
                <li key={item.to}>
                  <Link to={item.to}>{item.label}</Link>
                </li>
              ))}
              <li>
                <Link to="/status">وضعیت سرویس</Link>
              </li>
            </ul>
          </div>
          <div>
            <h5>موضوع‌ها</h5>
            {topics.length > 0 ? (
              <ul>
                {topics.map((topic) => (
                  <li key={topic}>
                    <Link to={`/news?topic=${encodeURIComponent(topic)}`}>{topic}</Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p>موضوع‌ها پس از رسیدن خبر تأییدشده دیده می‌شوند.</p>
            )}
          </div>
        </div>
        <div className="copy">
          <div className="wrap">
            <span>کارفنسا نیوز</span>
            <button
              type="button"
              className="totop"
              onClick={() => {
                const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
                window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
              }}
            >
              بازگشت به بالا
            </button>
          </div>
        </div>
      </footer>

      <button
        type="button"
        className={menuOpen ? "scrim open" : "scrim"}
        aria-label="بستن منو"
        tabIndex={menuOpen ? 0 : -1}
        onClick={() => setMenuOpen(false)}
      />
      <aside
        id={menuId}
        className={menuOpen ? "drawer open" : "drawer"}
        aria-hidden={!menuOpen}
        inert={!menuOpen}
      >
        <div className="dscroll">
          <div className="dh">
            <div className="row">
              <Link to="/" className="logo" aria-label="کارفنسا نیوز">
                <img src={LOGO} alt="" />
              </Link>
              <button type="button" className="dclose" onClick={() => setMenuOpen(false)}>
                <Icon name="close" />
                <span className="sr-only">بستن</span>
              </button>
            </div>
            <p className="dd">{today}</p>
          </div>
          <form className="dsearch" role="search" onSubmit={submitSearch}>
            <Icon name="search" />
            <label className="sr-only" htmlFor="drawer-search">
              جست‌وجو در اخبار
            </label>
            <input
              id="drawer-search"
              type="search"
              value={query}
              placeholder="جست‌وجو در عنوان خبرها"
              onChange={(event) => setQuery(event.target.value)}
            />
          </form>
          <p className="dt">بخش‌ها</p>
          <nav className="dnav" aria-label="منوی موبایل">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? "on" : "")}
                onClick={closeOverlays}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          {topics.length > 0 ? (
            <>
              <p className="dt">موضوعات خبری</p>
              <nav className="dchips" aria-label="موضوعات خبری">
                {topics.map((topic) => (
                  <Link
                    key={topic}
                    to={`/news?topic=${encodeURIComponent(topic)}`}
                    onClick={closeOverlays}
                  >
                    {topic}
                  </Link>
                ))}
              </nav>
            </>
          ) : null}
        </div>
      </aside>
    </>
  );
}
