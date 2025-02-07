import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

export const metadata = {
  title: "Job Info Hunter",
  description: "Job Info Hunter - 职位信息采集系统",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
