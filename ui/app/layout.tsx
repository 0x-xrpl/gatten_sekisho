import "./globals.css";

export const metadata = {
  title: "GATTEN SEKISHO — Demo",
  description: "A Digital Checkpoint for Final AI Decisions",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
