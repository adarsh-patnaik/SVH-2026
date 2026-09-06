import L from "leaflet";

const busSvg = (color: string, heading: number) => `
  <div class="bus-marker" style="transform: rotate(${heading}deg)">
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="13" cy="13" r="11" fill="${color}" stroke="white" stroke-width="2"/>
      <path d="M13 6.5l3.6 6.2H9.4L13 6.5z" fill="white"/>
    </svg>
  </div>
`;

export function busIcon(color: string, heading = 0, selected = false): L.DivIcon {
  return L.divIcon({
    className: `gs-bus-icon ${selected ? "gs-bus-icon--selected" : ""}`,
    html: busSvg(color, heading),
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

export function stopIcon(selected = false): L.DivIcon {
  const size = selected ? 14 : 10;
  return L.divIcon({
    className: "gs-stop-icon",
    html: `<div style="width:${size}px;height:${size}px;border-radius:999px;background:var(--surface);border:2.5px solid var(--primary);box-shadow:0 1px 3px rgba(0,0,0,0.25)"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export function userLocationIcon(): L.DivIcon {
  return L.divIcon({
    className: "gs-user-icon",
    html: `
      <div style="position:relative;width:18px;height:18px;">
        <div style="position:absolute;inset:0;border-radius:999px;background:var(--primary);opacity:0.25;animation:live-pulse 2s ease-out infinite;"></div>
        <div style="position:absolute;inset:4px;border-radius:999px;background:var(--primary);border:2px solid white;"></div>
      </div>
    `,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}
