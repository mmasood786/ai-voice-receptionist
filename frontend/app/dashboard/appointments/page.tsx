"use client";

import { useEffect, useState } from "react";
import {
  getDashboardAppointments,
  DashboardAppointmentItem,
} from "@/lib/api";

export default function AppointmentsPage() {
  const [items, setItems] = useState<DashboardAppointmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getDashboardAppointments();
        setItems(data.items);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load appointments."
        );
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return (
      <p className="text-gray-500">
        Loading appointments...
      </p>
    );
  }

  if (error) {
    return (
      <p className="text-red-600">
        {error}
      </p>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">
          Appointments
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          View scheduled customer appointments and bookings.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border bg-white">
        {items.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No appointments found.
          </div>
        ) : (
          <div className="divide-y">
            {items.map((appointment) => (
              <div
                key={appointment.id}
                className="p-5 hover:bg-gray-50"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold">
                      Appointment #{appointment.id}
                    </p>

                    <p className="mt-1 text-sm text-gray-500">
                      Customer:{" "}
                      {appointment.customer_id ?? "Unknown"}
                    </p>
                  </div>

                  <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium">
                    {appointment.status ?? "Unknown"}
                  </span>
                </div>

                <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400">
                      Start
                    </p>

                    <p className="mt-1 text-sm text-gray-700">
                      {new Date(
                        appointment.start_time
                      ).toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400">
                      End
                    </p>

                    <p className="mt-1 text-sm text-gray-700">
                      {new Date(
                        appointment.end_time
                      ).toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400">
                      Timezone
                    </p>

                    <p className="mt-1 text-sm text-gray-700">
                      {appointment.time_zone ?? "—"}
                    </p>
                  </div>
                </div>

                <p className="mt-4 text-xs text-gray-400">
                  Created{" "}
                  {new Date(
                    appointment.created_at
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