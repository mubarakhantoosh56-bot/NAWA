"use client";

import { FormEvent, useEffect, useId, useState } from "react";

import { useLanguage } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import {
  changeActionAssignee,
  changeActionStatus,
  createAction,
  getAction,
  listActionsForDecision,
} from "@/lib/api/actions";
import { listCompanyMembers } from "@/lib/api/company-members";
import type {
  ActionAssignableMember,
  ActionChangeEvent,
  ActionDetailResponse,
  ActionResponse,
  ActionStatus,
} from "@/lib/types";

// M9 Slice 3: inline Actions panel, anchored to one recorded Decision -
// styled consistently with RecordDecision/RecordOutcome (same container
// conventions, no modal/dialog infrastructure). Visibility (canRecordDecisions
// + a non-null decisionMemoryId) is decided by the caller (ChatPanel), same
// gating pattern as RecordOutcome.
//
// Core product law: an Action always displays its parent decision context
// (this panel only ever renders attached to one Decision) - there is no
// standalone/global Actions surface anywhere in this frontend.
//
// Member source (Founder-approved completion pass, M9 Slice 3): the
// assignee selector is backed by GET /company/members
// (lib/api/company-members.ts) - the bounded, read-only, company-scoped
// source added specifically to serve this selector (see
// docs/execution/m9/M9_SLICE3_FRONTEND_GOLDEN_PATH.md). Members are
// fetched once per mount, independent of the Action list. If that fetch
// fails, the rest of this panel keeps working - only the named-person
// picking capability is hidden, falling back to a plain Unassign control
// for an already-assigned Action (a pure null transition needing no name
// resolution) and Unassigned-only creation. A raw assigned_user_id/
// changed_by_user_id UUID is never rendered as visible text - an
// assignee/actor who cannot be resolved against the current active
// member list (e.g. no longer an active member) always falls back to a
// generic, non-identifying label instead.
type ActionsPanelProps = {
  token: string;
  decisionMemoryId: string;
};

const NEXT_STATUSES: Record<ActionStatus, ActionStatus[]> = {
  pending: ["in_progress", "completed", "cancelled"],
  in_progress: ["completed", "cancelled"],
  completed: [],
  cancelled: [],
};

export function ActionsPanel({ token, decisionMemoryId }: ActionsPanelProps) {
  const { t, language } = useLanguage();
  const titleFieldId = useId();
  const instructionsFieldId = useId();
  const assigneeFieldId = useId();

  const [actions, setActions] = useState<ActionResponse[] | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  const [members, setMembers] = useState<ActionAssignableMember[] | null>(null);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [membersError, setMembersError] = useState<string | null>(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [instructions, setInstructions] = useState("");
  const [createAssigneeId, setCreateAssigneeId] = useState("");
  const [isSubmittingCreate, setIsSubmittingCreate] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [expandedActionId, setExpandedActionId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ActionDetailResponse | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [mutatingActionId, setMutatingActionId] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoadingList(true);
    setListError(null);

    listActionsForDecision(token, decisionMemoryId)
      .then((response) => {
        if (!cancelled) {
          setActions(response);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setListError(mapListError(caught, t));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingList(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, decisionMemoryId, refreshToken, t]);

  useEffect(() => {
    let cancelled = false;
    setIsLoadingMembers(true);
    setMembersError(null);

    listCompanyMembers(token)
      .then((response) => {
        if (!cancelled) {
          setMembers(response);
        }
      })
      .catch(() => {
        if (!cancelled) {
          // Never surface a raw backend detail here - a generic, safe
          // notice is enough, and the rest of the panel keeps working.
          setMembersError(t("unableLoadMembers"));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingMembers(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, t]);

  function reload() {
    setRefreshToken((current) => current + 1);
  }

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle || isSubmittingCreate) {
      return;
    }

    setIsSubmittingCreate(true);
    setCreateError(null);

    try {
      await createAction(token, {
        decision_memory_id: decisionMemoryId,
        title: trimmedTitle,
        instructions: instructions.trim() || null,
        ...(createAssigneeId ? { assigned_user_id: createAssigneeId } : {}),
      });
      setTitle("");
      setInstructions("");
      setCreateAssigneeId("");
      setIsCreateOpen(false);
      reload();
    } catch (caught) {
      setCreateError(mapCreateError(caught, t));
    } finally {
      setIsSubmittingCreate(false);
    }
  }

  function handleCreateCancel() {
    setIsCreateOpen(false);
    setTitle("");
    setInstructions("");
    setCreateAssigneeId("");
    setCreateError(null);
  }

  async function toggleHistory(actionId: string) {
    if (expandedActionId === actionId) {
      setExpandedActionId(null);
      setDetail(null);
      setDetailError(null);
      return;
    }

    setExpandedActionId(actionId);
    setDetail(null);
    setDetailError(null);
    setIsLoadingDetail(true);
    try {
      const response = await getAction(token, actionId);
      setDetail(response);
    } catch (caught) {
      setDetailError(mapDetailError(caught, t));
    } finally {
      setIsLoadingDetail(false);
    }
  }

  async function handleStatusChange(actionId: string, nextStatus: ActionStatus) {
    if (mutatingActionId) {
      return;
    }
    setMutatingActionId(actionId);
    setMutationError(null);
    try {
      await changeActionStatus(token, actionId, nextStatus);
      reload();
      if (expandedActionId === actionId) {
        const refreshedDetail = await getAction(token, actionId);
        setDetail(refreshedDetail);
      }
    } catch (caught) {
      setMutationError(mapMutationError(caught, t));
      if (caught instanceof ApiError && caught.status === 409) {
        reload();
      }
    } finally {
      setMutatingActionId(null);
    }
  }

  async function handleAssigneeChange(actionId: string, nextAssignedUserId: string | null) {
    if (mutatingActionId) {
      return;
    }
    setMutatingActionId(actionId);
    setMutationError(null);
    try {
      await changeActionAssignee(token, actionId, nextAssignedUserId);
      reload();
      if (expandedActionId === actionId) {
        const refreshedDetail = await getAction(token, actionId);
        setDetail(refreshedDetail);
      }
    } catch (caught) {
      setMutationError(mapMutationError(caught, t));
      if (caught instanceof ApiError && caught.status === 409) {
        reload();
      }
    } finally {
      setMutatingActionId(null);
    }
  }

  return (
    <div className="mt-3 space-y-2 rounded-md border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="executive-label">{t("actionsTitle")}</div>
        {!isCreateOpen ? (
          <button
            type="button"
            className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink transition hover:border-accent hover:bg-blue-50"
            onClick={() => setIsCreateOpen(true)}
          >
            {t("createAction")}
          </button>
        ) : null}
      </div>

      {membersError ? <div className="text-xs text-muted">{membersError}</div> : null}

      {isCreateOpen ? (
        <form onSubmit={handleCreateSubmit} className="space-y-2 rounded-md border border-line bg-white p-3">
          {createError ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              {createError}
            </div>
          ) : null}

          <div>
            <label htmlFor={titleFieldId} className="text-xs font-semibold text-muted">
              {t("actionTitleLabel")}
            </label>
            <input
              id={titleFieldId}
              type="text"
              className="input mt-1 w-full text-sm leading-6"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              disabled={isSubmittingCreate}
            />
          </div>

          <div>
            <label htmlFor={instructionsFieldId} className="text-xs font-semibold text-muted">
              {t("actionInstructionsLabel")}
            </label>
            <textarea
              id={instructionsFieldId}
              className="input mt-1 min-h-12 w-full resize-none text-sm leading-6"
              value={instructions}
              onChange={(event) => setInstructions(event.target.value)}
              disabled={isSubmittingCreate}
            />
          </div>

          {!membersError ? (
            <div>
              <label htmlFor={assigneeFieldId} className="text-xs font-semibold text-muted">
                {t("assigneeLabel")}
              </label>
              <select
                id={assigneeFieldId}
                className="input mt-1 w-full text-sm leading-6"
                value={createAssigneeId}
                onChange={(event) => setCreateAssigneeId(event.target.value)}
                disabled={isSubmittingCreate || isLoadingMembers}
              >
                <option value="">{t("actionUnassigned")}</option>
                {(members ?? []).map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.full_name || member.email}
                  </option>
                ))}
              </select>
              {isLoadingMembers ? <div className="mt-1 text-xs text-muted">{t("loadingMembers")}</div> : null}
            </div>
          ) : null}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink"
              onClick={handleCreateCancel}
              disabled={isSubmittingCreate}
            >
              {t("cancel")}
            </button>
            <button
              type="submit"
              className="button-primary px-3 py-1.5 text-xs"
              disabled={isSubmittingCreate || !title.trim()}
            >
              {isSubmittingCreate ? t("creatingAction") : t("createAction")}
            </button>
          </div>
        </form>
      ) : null}

      {mutationError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {mutationError}
        </div>
      ) : null}

      {isLoadingList ? <div className="text-xs text-muted">{t("loadingActions")}</div> : null}
      {listError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{listError}</div>
      ) : null}
      {!isLoadingList && !listError && actions && actions.length === 0 ? (
        <div className="text-xs text-muted">{t("noActionsYet")}</div>
      ) : null}

      {actions && actions.length > 0 ? (
        <ul className="space-y-2">
          {actions.map((action) => {
            const isNonTerminal = NEXT_STATUSES[action.status].length > 0;
            return (
              <li key={action.id} className="rounded-md border border-line bg-white p-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-ink">{action.title}</div>
                    <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-muted">
                      <StatusBadge status={action.status} t={t} />
                      <span className="nawa-badge">{assigneeDisplayLabel(action.assigned_user_id, members, t)}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="shrink-0 rounded-md border border-line bg-white px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-accent hover:bg-blue-50"
                    onClick={() => toggleHistory(action.id)}
                  >
                    {expandedActionId === action.id ? t("hideActionHistory") : t("viewActionHistory")}
                  </button>
                </div>

                {isNonTerminal ? (
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    {NEXT_STATUSES[action.status].map((nextStatus) => (
                      <button
                        key={nextStatus}
                        type="button"
                        className="rounded-md border border-line bg-white px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-accent hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                        onClick={() => handleStatusChange(action.id, nextStatus)}
                        disabled={mutatingActionId === action.id}
                      >
                        {mutatingActionId === action.id
                          ? t("updatingActionStatus")
                          : statusActionLabel(nextStatus, t)}
                      </button>
                    ))}
                    {membersError ? (
                      action.assigned_user_id ? (
                        <button
                          type="button"
                          className="rounded-md border border-line bg-white px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-accent hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                          onClick={() => handleAssigneeChange(action.id, null)}
                          disabled={mutatingActionId === action.id}
                        >
                          {mutatingActionId === action.id ? t("unassigningAction") : t("unassignAction")}
                        </button>
                      ) : null
                    ) : (
                      <label className="flex items-center gap-1.5 text-xs text-muted">
                        {t("assigneeLabel")}
                        <select
                          aria-label={t("assigneeLabel")}
                          className="input py-1 text-xs leading-5"
                          value={action.assigned_user_id ?? ""}
                          onChange={(event) => {
                            const nextValue = event.target.value || null;
                            if (nextValue === action.assigned_user_id) {
                              return;
                            }
                            handleAssigneeChange(action.id, nextValue);
                          }}
                          disabled={mutatingActionId === action.id || isLoadingMembers}
                        >
                          <option value="">{t("actionUnassigned")}</option>
                          {action.assigned_user_id &&
                          !(members ?? []).some((member) => member.id === action.assigned_user_id) ? (
                            <option value={action.assigned_user_id} disabled>
                              {t("actionAssignedFallback")}
                            </option>
                          ) : null}
                          {(members ?? []).map((member) => (
                            <option key={member.id} value={member.id}>
                              {member.full_name || member.email}
                            </option>
                          ))}
                        </select>
                      </label>
                    )}
                  </div>
                ) : null}

                {expandedActionId === action.id ? (
                  <div className="mt-2 rounded-md border border-line bg-surface p-2">
                    <div className="text-xs font-semibold text-muted">{t("actionHistoryTitle")}</div>
                    {isLoadingDetail ? (
                      <div className="mt-1 text-xs text-muted">{t("loadingActionHistory")}</div>
                    ) : null}
                    {detailError ? (
                      <div className="mt-1 rounded-md border border-red-200 bg-red-50 px-2 py-1.5 text-xs text-red-700">
                        {detailError}
                      </div>
                    ) : null}
                    {!isLoadingDetail && !detailError && detail ? (
                      <ul className="mt-1 space-y-1">
                        {detail.events.map((changeEvent) => (
                          <li key={changeEvent.id} className="text-xs leading-5 text-ink">
                            <HistoryLine event={changeEvent} members={members} language={language} t={t} />
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

function StatusBadge({ status, t }: { status: ActionStatus; t: (key: string) => string }) {
  return <span className="nawa-badge">{statusLabel(status, t)}</span>;
}

function HistoryLine({
  event,
  members,
  language,
  t,
}: {
  event: ActionChangeEvent;
  members: ActionAssignableMember[] | null;
  language: "en" | "ar";
  t: (key: string) => string;
}) {
  const timestamp = formatDateTime(event.changed_at, language);
  const actor = actorDisplayLabel(event.changed_by_user_id, members, t);

  if (event.change_type === "status") {
    const from = statusLabelOrInitial(event.from_status, t);
    const to = statusLabelOrInitial(event.to_status, t);
    return (
      <span>
        {t("actionStatusChangeLabel")}: {from} {"→"} {to} &middot; {timestamp} &middot; {actor}
      </span>
    );
  }

  const from = assigneeDisplayLabel(event.from_assigned_user_id, members, t);
  const to = assigneeDisplayLabel(event.to_assigned_user_id, members, t);
  return (
    <span>
      {t("actionAssignmentChangeLabel")}: {from} {"→"} {to} &middot; {timestamp} &middot; {actor}
    </span>
  );
}

// Assignment-state semantics: null always means Unassigned. A non-null id
// resolves to the matching active member's display name when possible,
// and to a generic, non-identifying fallback (never a raw UUID) when the
// member list hasn't loaded or the user is no longer an active member.
function assigneeDisplayLabel(
  userId: string | null,
  members: ActionAssignableMember[] | null,
  t: (key: string) => string,
): string {
  if (!userId) {
    return t("actionUnassigned");
  }
  const member = members?.find((candidate) => candidate.id === userId);
  if (member) {
    return member.full_name || member.email;
  }
  return t("actionAssignedFallback");
}

// changed_by_user_id is always present (never null) - resolves to the
// actor's display name when possible, generic fallback otherwise. Never a
// raw UUID.
function actorDisplayLabel(
  userId: string,
  members: ActionAssignableMember[] | null,
  t: (key: string) => string,
): string {
  const member = members?.find((candidate) => candidate.id === userId);
  if (member) {
    return `${t("actionChangedByPrefix")} ${member.full_name || member.email}`;
  }
  return t("actionChangedByTeamMember");
}

function statusLabel(status: ActionStatus, t: (key: string) => string): string {
  if (status === "pending") {
    return t("actionStatusPending");
  }
  if (status === "in_progress") {
    return t("actionStatusInProgress");
  }
  if (status === "completed") {
    return t("actionStatusCompleted");
  }
  return t("actionStatusCancelled");
}

// Status-domain semantics only: null means "no prior status because this
// is the initial status event" (Founder correction #2) - never rendered
// as "Unassigned", which belongs to the assignment domain.
function statusLabelOrInitial(status: ActionStatus | null, t: (key: string) => string): string {
  if (status === null) {
    return t("actionStatusInitial");
  }
  return statusLabel(status, t);
}

function statusActionLabel(nextStatus: ActionStatus, t: (key: string) => string): string {
  if (nextStatus === "in_progress") {
    return t("startAction");
  }
  if (nextStatus === "completed") {
    return t("completeAction");
  }
  return t("cancelAction");
}

function formatDateTime(iso: string, language: "en" | "ar"): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) {
    return iso;
  }
  return parsed.toLocaleString(language === "ar" ? "ar" : "en", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function mapListError(caught: unknown, t: (key: string) => string): string {
  if (caught instanceof ApiError && caught.status === 403) {
    return t("createActionPermissionDenied");
  }
  return t("unableLoadActions");
}

function mapCreateError(caught: unknown, t: (key: string) => string): string {
  if (caught instanceof ApiError) {
    if (caught.status === 403) {
      return t("createActionPermissionDenied");
    }
    if (caught.status === 404) {
      return t("createActionDecisionUnavailable");
    }
    if (caught.status === 422) {
      return t("createActionInvalid");
    }
  }
  return t("createActionFailed");
}

function mapDetailError(caught: unknown, t: (key: string) => string): string {
  if (caught instanceof ApiError && caught.status === 404) {
    return t("actionNotFound");
  }
  return t("unableLoadActionHistory");
}

function mapMutationError(caught: unknown, t: (key: string) => string): string {
  if (caught instanceof ApiError) {
    if (caught.status === 404) {
      return t("actionNotFound");
    }
    if (caught.status === 409) {
      return t("actionConflict");
    }
  }
  return t("actionStatusUpdateFailed");
}
