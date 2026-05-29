import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { MainLayout } from "@/components/layout/main-layout";

export default function HomePage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        <PageHeader
          title="Frontend Setup Complete"
          description="Foundation providers, API client, route guards, and reusable components are in place."
        />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard title="Environment" value="Next.js 15" subtitle="App Router + TypeScript" />
          <StatCard title="State" value="React Query" subtitle="staleTime: 30s, retry: 1" />
          <StatCard title="Auth" value="JWT + RBAC" subtitle="Cookie + localStorage flow" />
        </div>
      </div>
    </MainLayout>
  );
}
