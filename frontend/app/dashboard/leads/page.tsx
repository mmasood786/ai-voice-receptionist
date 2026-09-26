"use client";

import { useEffect, useState } from "react";
import {
  getDashboardLeads,
  DashboardLeadItem,
} from "@/lib/api";

export default function LeadsPage() {
  const [items, setItems] = useState<DashboardLeadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getDashboardLeads();
        setItems(data.items);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load leads."
        );
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return <p className="text-gray-500">Loading leads...</p>;
  }

  if (error) {
    return <p className="text-red-600">{error}</p>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Leads</h1>

        <p className="mt-1 text-sm text-gray-500">
          View qualified leads and their sales information.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border bg-white">
        {items.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No leads found.
          </div>
        ) : (
          <div className="divide-y">
            {items.map((lead) => (
              <div
                key={lead.id}
                className="p-5 hover:bg-gray-50"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold">
                      Lead #{lead.id}
                    </p>

                    <p className="mt-1 text-sm text-gray-500">
                      Customer:{" "}
                      {lead.customer_id ?? "Unknown"}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {lead.lead_score !== null && (
                      <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                        Score: {lead.lead_score}
                      </span>
                    )}

                    <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium">
                      {lead.status ?? "Unknown"}
                    </span>
                  </div>
                </div>

                <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400">
                      Service
                    </p>
                    <p className="mt-1 text-sm text-gray-700">
                      {lead.service_interest ?? "—"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400">
                      Urgency
                    </p>
                    <p className="mt-1 text-sm text-gray-700">
                      {lead.urgency ?? "—"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400">
                      Budget
                    </p>
                    <p className="mt-1 text-sm text-gray-700">
                      {lead.budget ?? "—"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400">
                      Timeline
                    </p>
                    <p className="mt-1 text-sm text-gray-700">
                      {lead.timeline ?? "—"}
                    </p>
                  </div>
                </div>

                <p className="mt-4 text-xs text-gray-400">
                  Created{" "}
                  {new Date(
                    lead.created_at
                  ).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}