"use client";

import { useEffect, useState } from "react";
import {
  getDashboardOverview,
  getRecentActivity,
  type DashboardOverview,
  type DashboardActivityItem,
} from "@/lib/api";

import StatCard from "@/components/dashboard/StatCard";

export default function DashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [activities, setActivities] = useState<DashboardActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [overviewData, activityData] = await Promise.all([
          getDashboardOverview(),
          getRecentActivity(),
        ]);

        setOverview(overviewData);
        setActivities(activityData.items);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load dashboard"
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
        <div className="mx-auto max-w-7xl p-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-4 text-gray-500">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
        <div className="mx-auto max-w-7xl p-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  return (
      <div className="mx-auto max-w-7xl">
        <h1 className="text-3xl font-bold">Dashboard</h1>

        <p className="mt-2 text-gray-500">
          Overview of your AI receptionist activity.
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard
            title="Customers"
            value={overview?.customers ?? 0}
          />

          <StatCard
            title="Leads"
            value={overview?.leads ?? 0}
          />

          <StatCard
            title="Conversations"
            value={overview?.conversations ?? 0}
          />

          <StatCard
            title="Appointments"
            value={overview?.appointments ?? 0}
          />

          <StatCard
            title="Knowledge"
            value={overview?.knowledge_documents ?? 0}
          />
        </div>

        <section className="mt-8 rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">
            Recent Activity
          </h2>

          {activities.length === 0 ? (
            <p className="mt-4 text-gray-500">
              No recent activity.
            </p>
          ) : (
            <div className="mt-4 divide-y">
              {activities.map((activity) => (
                <div
                  key={`${activity.type}-${activity.id}`}
                  className="py-4"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">
                      {activity.title}
                    </h3>

                    <span className="text-sm text-gray-400">
                      {new Date(
                        activity.created_at
                      ).toLocaleString()}
                    </span>
                  </div>

                  {activity.description && (
                    <p className="mt-1 text-sm text-gray-500">
                      {activity.description}
                    </p>
                  )}

                  <span className="mt-2 inline-block rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                    {activity.type}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
  );
}

