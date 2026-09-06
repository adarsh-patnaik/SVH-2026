import type { Metadata, Viewport } from "next";
import "./globals.css";
import { TransitProvider } from "@/lib/state/TransitProvider";
import { ServiceWorkerRegister } from "@/components/layout/ServiceWorkerRegister";

export const metadata: Metadata = {
  title: "GatiSync — Live Transit",
  description:
    "Ultra-light real-time public transit tracking for Tier-2 and Tier-3 cities.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "GatiSync",
  },
  icons: {
    icon: "/icons/icon-192.png",
    apple: "/icons/icon-192.png",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f5f3" },
    { media: "(prefers-color-scheme: dark)", color: "#0d0f14" },
  ],
};

// Runs before hydration so the correct theme applies on first paint —
// no flash of the wrong palette while React boots.
const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem('gatisync-theme');
    var theme = stored === 'light' || stored === 'dark'
      ? stored
      : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-full flex flex-col overscroll-none" suppressHydrationWarning>
        <TransitProvider>{children}</TransitProvider>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
