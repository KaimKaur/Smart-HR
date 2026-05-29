import { MainLayout } from "@/components/layout/main-layout";

export default function ManagerLayout({ children }: { children: React.ReactNode }) {
  return <MainLayout>{children}</MainLayout>;
}
