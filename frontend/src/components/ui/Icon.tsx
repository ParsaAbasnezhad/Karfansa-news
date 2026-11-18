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
  send: "M22 2L11 13M22 2l-7 20-4-9-9-4z",
  file: "M7 3h7l5 5v13H7zM14 3v5h5",
  news: "M5 5h11a1 1 0 0 1 1 1v12H6a1 1 0 0 1-1-1zM8 9h6M8 13h6M16 8h3v10H9",
  eye: "M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6",
  "eye-off":
    "M3 3l18 18M10.7 10.7A3 3 0 0 0 12 15a3 3 0 0 0 2.3-1.3M9.9 5.2A10.4 10.4 0 0 1 12 5c6.5 0 10 7 10 7a17.6 17.6 0 0 1-4.1 4.6M6.1 6.1A17.4 17.4 0 0 0 2 12s3.5 6 10 6a10.4 10.4 0 0 0 3.2-.5",
  check: "M5 12l4 4L19 6",
  calendar: "M5 5h14v15H5zM8 3v4M16 3v4M5 9h14",
  edit: "M4 20l4.5-1 10-10-3.5-3.5-10 10zM13.5 6.5l3.5 3.5",
  shield: "M12 3l7 3v5c0 4.5-2.8 8-7 10-4.2-2-7-5.5-7-10V6zM9 12l2 2 4-4",
  ticket: "M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4zM9 7v10",
  briefcase: "M4 8h16v11H4zM9 8V5h6v3M4 12h16M10 12v2h4v-2",
  logout: "M10 5H5v14h5M14 8l4 4-4 4M18 12H9",
  box: "M4 7l8-4 8 4-8 4zM4 7v10l8 4 8-4V7M12 11v10",
  compass: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M15 9l-2 4-4 2 2-4z",
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="i" viewBox="0 0 24 24" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}
