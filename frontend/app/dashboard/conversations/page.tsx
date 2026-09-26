"use client";

import { useEffect, useState } from "react";
import {
  getDashboardConversations,
  DashboardConversationItem,
} from "@/lib/api";

export default function ConversationsPage() {
  const [items, setItems] = useState<DashboardConversationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  function formatMessagePreview(message: string | null): string {
    if (!message) {
      return "No messages available.";
    }
  
    const cleaned = message
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/\|/g, " ")
      .replace(/\*\*/g, "")
      .replace(/__/g, "")
      .replace(/^#+\s*/gm, "")
      .replace(/^-{3,}$/gm, "")
      .replace(/\s+/g, " ")
      .trim();
  
    return cleaned.length > 250
      ? `${cleaned.slice(0, 250)}...`
      : cleaned;
  }

  useEffect(() => {
    async function load() {
      try {
        const data = await getDashboardConversations();
        setItems(data.items);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load conversations."
        );
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return <p className="text-gray-500">Loading conversations...</p>;
  }

  if (error) {
    return <p className="text-red-600">{error}</p>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Conversations</h1>
        <p className="mt-1 text-sm text-gray-500">
          View customer conversations and recent messages.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border bg-white">
        {items.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No conversations found.
          </div>
        ) : (
          <div className="divide-y">
            {items.map((conversation) => (
              <div
                key={conversation.id}
                className="p-5 hover:bg-gray-50"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      Conversation #{conversation.id}
                    </p>

                    <p className="mt-1 text-sm text-gray-500">
                      Customer:{" "}
                      {conversation.customer_id ?? "Unknown"}
                    </p>
                  </div>

                  <span className="rounded-full bg-gray-100 px-3 py-1 text-xs">
                    {conversation.status ?? "Unknown"}
                  </span>
                </div>

                <p className="mt-3 text-sm leading-6 text-gray-600">
                  {formatMessagePreview(conversation.latest_message)}
                </p>

                <p className="mt-2 text-xs text-gray-400">
                  {new Date(
                    conversation.created_at
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