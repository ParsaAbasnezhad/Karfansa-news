const ICONS = {
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6L6 18",
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16M21 21l-4.3-4.3",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M12 7v5l3 2",
  arrow: "M19 12H5M11 18l-6-6 6-6",
  "chevron-left": "M14 6l-6 6 6 6",
  "chevron-right": "M10 6l6 6-6 6",
  building: "M4 20h16M6 20V6h8v14M10 9h2M10 13h2M14 20V12h4v8",
  mail: "M4 7h16v10H4zM4 7l8 6 8-6",
  phone: "M8 4h3l1 4-2 1a12 12 0 0 0 5 5l1-2 4 1v3a2 2 0 0 1-2 2A14 14 0 0 1 6 6a2 2 0 0 1 2-2",
  user: "M12 12a4 4 0 1 0-8 0 4 4 0 0 0 8 0M5 20a7 7 0 0 1 14 0",
  send: "M4 12 16-8-6 16-2-6z",
  file: "M7 3h7l5 5v13H7zM14 3v5h5",
  news: "M5 5h11a1 1 0 0 1 1 1v12H6a1 1 0 0 1-1-1zM8 9h6M8 13h6M16 8h3v10H9",
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="i" viewBox="0 0 24 24" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}
