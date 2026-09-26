"use client";

import { useEffect, useState } from "react";
import {
  getKnowledgeDocuments,
  getKnowledgeDocument,
  createKnowledgeDocument,
  updateKnowledgeDocument,
  reindexKnowledgeDocument,
  deleteKnowledgeDocument,
  KnowledgeDocumentListItem,
} from "@/lib/api";

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<
    KnowledgeDocumentListItem[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showAddForm, setShowAddForm] = useState(false);

  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [content, setContent] = useState("");

  const [saving, setSaving] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [loadingEdit, setLoadingEdit] = useState(false);

  async function loadDocuments() {
    try {
      setError(null);

      const data = await getKnowledgeDocuments();

      setDocuments(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load knowledge documents."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleEdit(documentId: number) {
    try {
      setLoadingEdit(true);
      setError(null);
      const document = await getKnowledgeDocument(documentId);
      setEditingId(document.id);
      setTitle(document.title);
      setSource(document.source);
      setContent(document.content);
      setShowAddForm(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load document."
      );
    } finally {
      setLoadingEdit(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleSave() {
    if (!title.trim() || !source.trim() || !content.trim()) {
      setError("Title, source, and content are required.");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      if (editingId !== null) {
        await updateKnowledgeDocument(editingId, {
          title: title.trim(),
          source: source.trim(),
          content: content.trim(),
        });
      } else {
        await createKnowledgeDocument({
          title: title.trim(),
          source: source.trim(),
          content: content.trim(),
        });
      }

      setTitle("");
      setSource("");
      setContent("");
      setEditingId(null);
      setShowAddForm(false);

      await loadDocuments();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to save document."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleReindex(documentId: number) {
    try {
      setActionId(documentId);
      setError(null);

      await reindexKnowledgeDocument(documentId);

      await loadDocuments();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to reindex document."
      );
    } finally {
      setActionId(null);
    }
  }

  async function handleDelete(documentId: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this knowledge document?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionId(documentId);
      setError(null);

      await deleteKnowledgeDocument(documentId);

      await loadDocuments();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete document."
      );
    } finally {
      setActionId(null);
    }
  }

  if (loading) {
    return (
      <p className="text-gray-500">
        Loading knowledge documents...
      </p>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            Knowledge
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Manage the information used by your AI receptionist.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setError(null);
            setShowAddForm((value) => !value);
          }}
          className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          {showAddForm ? "Cancel" : "Add document"}
        </button>
      </div>

      {error && (
        <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {showAddForm && (
        <div className="mb-6 rounded-xl border bg-white p-6">
          <h2 className="text-lg font-semibold">
            Add knowledge document
          </h2>

          <div className="mt-5 space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">
                Title
              </label>

              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="AI Automation Services"
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:border-gray-900"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">
                Source
              </label>

              <input
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="services.md"
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:border-gray-900"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">
                Content
              </label>

              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter the business information..."
                rows={10}
                className="w-full resize-y rounded-lg border px-3 py-2 text-sm outline-none focus:border-gray-900"
              />
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                disabled={saving}
                onClick={handleSave}
                className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving
                  ? "Saving..."
                  : editingId !== null
                    ? "Save changes"
                    : "Create document"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border bg-white">
        {documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No knowledge documents found.
          </div>
        ) : (
          <div className="divide-y">
            {documents.map((document) => {
              const busy = actionId === document.id;

              return (
                <div
                  key={document.id}
                  className="p-5 hover:bg-gray-50"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h2 className="font-semibold">
                        {document.title}
                      </h2>

                      <p className="mt-1 text-sm text-gray-500">
                        Source: {document.source}
                      </p>
                    </div>

                    <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium">
                      {document.chunk_count} chunks
                    </span>
                  </div>

                  <div className="mt-4 flex gap-2">
                  <button
                    type="button"
                    disabled={busy || loadingEdit}
                    onClick={() => handleEdit(document.id)}
                    className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-green-100 disabled:opacity-50"
                  >
                    {loadingEdit && editingId === document.id
                      ? "Loading..."
                      : "Edit"}
                  </button>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        handleReindex(document.id)
                      }
                      className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-gray-100 disabled:opacity-50"
                    >
                      {busy ? "Working..." : "Reindex"}
                    </button>

                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        handleDelete(document.id)
                      }
                      className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}