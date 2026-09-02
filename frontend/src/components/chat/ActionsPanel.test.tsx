import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ActionsPanel } from "@/components/chat/ActionsPanel";
import { LanguageProvider } from "@/components/i18n/LanguageProvider";
import { ApiError } from "@/lib/api/client";
import type { ActionAssignableMember, ActionDetailResponse, ActionResponse } from "@/lib/types";

// M9 Slice 3 (+ Founder-approved member-source completion pass):
// self-contained component test for the Actions panel anchored to a
// recorded Decision. Mirrors the mocking conventions established in
// ChatPanel.wiring.test.tsx (vi.mock the API modules, render the real
// component wrapped only in LanguageProvider, assert on real DOM/network
// calls) rather than deeply extending that file's own suite.

vi.mock("@/lib/api/actions", () => ({
  createAction: vi.fn(),
  listActionsForDecision: vi.fn(),
  getAction: vi.fn(),
  changeActionStatus: vi.fn(),
  changeActionAssignee: vi.fn(),
}));

vi.mock("@/lib/api/company-members", () => ({
  listCompanyMembers: vi.fn(),
}));

import {
  changeActionAssignee,
  changeActionStatus,
  createAction,
  getAction,
  listActionsForDecision,
} from "@/lib/api/actions";
import { listCompanyMembers } from "@/lib/api/company-members";

const MEMBER_A: ActionAssignableMember = {
  id: "00000000-0000-0000-0000-0000000000aa",
  full_name: "Huda Saleh",
  email: "huda@example.com",
};
const MEMBER_B: ActionAssignableMember = {
  id: "00000000-0000-0000-0000-0000000000bb",
  full_name: "Omar Faris",
  email: "omar@example.com",
};

function action(overrides: Partial<ActionResponse> = {}): ActionResponse {
  return {
    id: "action-1",
    decision_memory_id: "decision-1",
    title: "Draft the vendor renewal proposal",
    instructions: null,
    status: "pending",
    assigned_user_id: null,
    created_by_user_id: "00000000-0000-0000-0000-000000000001",
    created_at: "2026-08-25T00:00:00Z",
    updated_at: "2026-08-25T00:00:00Z",
    completed_at: null,
    cancelled_at: null,
    ...overrides,
  };
}

function detail(base: ActionResponse, events: ActionDetailResponse["events"] = []): ActionDetailResponse {
  return { ...base, events };
}

function renderPanel(decisionMemoryId = "decision-1") {
  return render(
    <LanguageProvider>
      <ActionsPanel token="tok-abc" decisionMemoryId={decisionMemoryId} />
    </LanguageProvider>,
  );
}

// The assignee <select> renders member names/"Unassigned" as <option> text
// too, so a plain screen.getByText("Huda Saleh") is ambiguous whenever a
// selector is on screen (badge + option both match). Scope to the badge
// specifically wherever that collision is possible.
function badgeTexts(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll(".nawa-badge")).map((el) => el.textContent ?? "");
}

beforeEach(() => {
  vi.mocked(createAction).mockReset();
  vi.mocked(listActionsForDecision).mockReset();
  vi.mocked(getAction).mockReset();
  vi.mocked(changeActionStatus).mockReset();
  vi.mocked(changeActionAssignee).mockReset();
  vi.mocked(listCompanyMembers).mockReset();
  vi.mocked(listActionsForDecision).mockResolvedValue([]);
  vi.mocked(listCompanyMembers).mockResolvedValue([MEMBER_A, MEMBER_B]);
});

// UI RESILIENCE ---------------------------------------------------------

describe("Actions panel - loading / empty / error", () => {
  it("shows a loading state while the list request is in flight", async () => {
    let resolveList: (value: ActionResponse[]) => void = () => undefined;
    vi.mocked(listActionsForDecision).mockReturnValue(
      new Promise((resolve) => {
        resolveList = resolve;
      }),
    );

    renderPanel();
    expect(screen.getByText("Loading actions...")).toBeInTheDocument();

    resolveList([]);
    await waitFor(() => {
      expect(screen.queryByText("Loading actions...")).not.toBeInTheDocument();
    });
  });

  it("shows an empty state when no actions exist for this decision", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([]);
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText("No actions recorded for this decision yet.")).toBeInTheDocument();
    });
  });

  it("shows a safe error message on list failure, never a raw backend detail", async () => {
    vi.mocked(listActionsForDecision).mockRejectedValue(new ApiError(500, "internal trace leak"));
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText("Unable to load actions.")).toBeInTheDocument();
    });
    expect(document.body.textContent).not.toContain("internal trace leak");
  });
});

// CREATE ACTION -----------------------------------------------------------

describe("Actions panel - create Action", () => {
  it("shows a Create Action entry point and opens a blank form (no AI prefill), with the member source loaded and Unassigned as default", async () => {
    const user = userEvent.setup();
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText("No actions recorded for this decision yet.")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    const titleField = screen.getByLabelText("Title") as HTMLInputElement;
    const instructionsField = screen.getByLabelText("Instructions (optional)") as HTMLTextAreaElement;
    expect(titleField.value).toBe("");
    expect(instructionsField.value).toBe("");

    await waitFor(() => {
      expect(listCompanyMembers).toHaveBeenCalledWith("tok-abc");
    });
    const assigneeField = (await screen.findByLabelText("Assignee")) as HTMLSelectElement;
    expect(assigneeField.value).toBe("");
    expect(screen.getByRole("option", { name: "Huda Saleh" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Omar Faris" })).toBeInTheDocument();
  });

  it("disables submit while title is blank, and instructions are optional", async () => {
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    const submitButtons = () => screen.getAllByRole("button", { name: "Create Action" });
    // Two "Create Action" buttons exist once the form is open: none, since
    // the entry-point button hides itself while the form is open.
    expect(submitButtons()).toHaveLength(1);
    expect(submitButtons()[0]).toBeDisabled();

    await user.type(screen.getByLabelText("Title"), "Draft the renewal proposal");
    expect(submitButtons()[0]).not.toBeDisabled();
  });

  it("submits exactly decision_memory_id/title/instructions when Unassigned is left selected - no company_id, created_by_user_id, status, or assignee (server-derived fields)", async () => {
    vi.mocked(createAction).mockResolvedValue(action());
    const user = userEvent.setup();
    renderPanel("decision-77");
    await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    await user.type(screen.getByLabelText("Title"), "  Draft the renewal proposal  ");
    await user.type(screen.getByLabelText("Instructions (optional)"), "Include the Q3 pricing tiers.");
    await user.click(screen.getByRole("button", { name: "Create Action" }));

    await waitFor(() => {
      expect(createAction).toHaveBeenCalledTimes(1);
    });
    const [token, payload] = vi.mocked(createAction).mock.calls[0];
    expect(token).toBe("tok-abc");
    expect(payload).toEqual({
      decision_memory_id: "decision-77",
      title: "Draft the renewal proposal",
      instructions: "Include the Q3 pricing tiers.",
    });
    for (const forbidden of ["company_id", "created_by_user_id", "status"]) {
      expect(payload).not.toHaveProperty(forbidden);
    }
  });

  it("sends the selected member's id as assigned_user_id when a human explicitly picks one", async () => {
    vi.mocked(createAction).mockResolvedValue(action({ assigned_user_id: MEMBER_A.id }));
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    await user.type(screen.getByLabelText("Title"), "Draft the renewal proposal");
    const assigneeField = await screen.findByLabelText("Assignee");
    await user.selectOptions(assigneeField, MEMBER_A.id);
    await user.click(screen.getByRole("button", { name: "Create Action" }));

    await waitFor(() => expect(createAction).toHaveBeenCalledTimes(1));
    const [, payload] = vi.mocked(createAction).mock.calls[0];
    expect(payload.assigned_user_id).toBe(MEMBER_A.id);
  });

  it("blank instructions submit as null, not an empty string", async () => {
    vi.mocked(createAction).mockResolvedValue(action());
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    await user.type(screen.getByLabelText("Title"), "Draft the renewal proposal");
    await user.click(screen.getByRole("button", { name: "Create Action" }));

    await waitFor(() => expect(createAction).toHaveBeenCalledTimes(1));
    const [, payload] = vi.mocked(createAction).mock.calls[0];
    expect(payload.instructions).toBeNull();
  });

  it("on success, closes the form and the new Action appears via a real list refresh", async () => {
    vi.mocked(createAction).mockResolvedValue(action({ id: "action-42", title: "Draft the renewal proposal" }));
    vi.mocked(listActionsForDecision)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([action({ id: "action-42", title: "Draft the renewal proposal" })]);
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    await user.type(screen.getByLabelText("Title"), "Draft the renewal proposal");
    await user.click(screen.getByRole("button", { name: "Create Action" }));

    await waitFor(() => {
      expect(screen.getByText("Draft the renewal proposal")).toBeInTheDocument();
    });
    expect(listActionsForDecision).toHaveBeenCalledTimes(2);
    expect(screen.queryByLabelText("Title")).not.toBeInTheDocument();
  });

  it("on failure, shows a safe message and does not falsely display success", async () => {
    vi.mocked(createAction).mockRejectedValue(new ApiError(422, "internal validation detail"));
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    await user.type(screen.getByLabelText("Title"), "Draft the renewal proposal");
    await user.click(screen.getByRole("button", { name: "Create Action" }));

    await waitFor(() => {
      expect(screen.getByText("Please enter a title for this action.")).toBeInTheDocument();
    });
    expect(document.body.textContent).not.toContain("internal validation detail");
    // The form remains open and usable - no false "created" state anywhere.
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(listActionsForDecision).toHaveBeenCalledTimes(1);
  });

  it("maps 403/404/generic create failures to safe messages", async () => {
    const cases: [unknown, string][] = [
      [new ApiError(403, "x"), "You don't have permission to create actions."],
      [new ApiError(404, "x"), "This decision is no longer available to create an action against."],
      [new Error("network down"), "Unable to create action. Please try again."],
    ];

    for (const [rejection, expectedMessage] of cases) {
      vi.mocked(createAction).mockReset();
      vi.mocked(createAction).mockRejectedValue(rejection);
      const user = userEvent.setup();
      const { unmount } = renderPanel();
      await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

      await user.click(screen.getByRole("button", { name: "Create Action" }));
      await user.type(screen.getByLabelText("Title"), "Draft the renewal proposal");
      await user.click(screen.getByRole("button", { name: "Create Action" }));

      await waitFor(() => {
        expect(screen.getByText(expectedMessage)).toBeInTheDocument();
      });
      unmount();
    }
  });

  it("member-source failure still allows Unassigned creation, and shows a safe notice instead of a picker", async () => {
    vi.mocked(listCompanyMembers).mockRejectedValue(new ApiError(500, "internal member detail"));
    vi.mocked(createAction).mockResolvedValue(action());
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText("No actions recorded for this decision yet."));

    await user.click(screen.getByRole("button", { name: "Create Action" }));
    await waitFor(() => {
      expect(screen.getByText("Unable to load company members.")).toBeInTheDocument();
    });
    expect(document.body.textContent).not.toContain("internal member detail");
    expect(screen.queryByLabelText("Assignee")).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("Title"), "Draft the renewal proposal");
    await user.click(screen.getByRole("button", { name: "Create Action" }));

    await waitFor(() => expect(createAction).toHaveBeenCalledTimes(1));
    const [, payload] = vi.mocked(createAction).mock.calls[0];
    expect(payload).not.toHaveProperty("assigned_user_id");
  });
});

// STATUS ------------------------------------------------------------------

describe("Actions panel - status transitions", () => {
  it("a pending Action shows exactly Start, Complete, and Cancel Action - no others", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ status: "pending" })]);
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Complete" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel Action" })).toBeInTheDocument();
  });

  it("an in_progress Action shows only Complete and Cancel Action - no Start", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ status: "in_progress" })]);
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    expect(screen.queryByRole("button", { name: "Start" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Complete" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel Action" })).toBeInTheDocument();
  });

  it("completed and cancelled Actions show no status controls and no reopen control", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([
      action({ id: "action-completed", status: "completed" }),
      action({ id: "action-cancelled", status: "cancelled", title: "A cancelled action" }),
    ]);
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    expect(screen.queryByRole("button", { name: "Start" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Complete" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancel Action" })).not.toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Cancelled")).toBeInTheDocument();
  });

  it("a successful status mutation calls the PATCH endpoint and refreshes the list", async () => {
    vi.mocked(listActionsForDecision)
      .mockResolvedValueOnce([action({ status: "pending" })])
      .mockResolvedValueOnce([action({ status: "in_progress" })]);
    vi.mocked(changeActionStatus).mockResolvedValue(action({ status: "in_progress" }));
    const user = userEvent.setup();
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await user.click(screen.getByRole("button", { name: "Start" }));

    await waitFor(() => {
      expect(changeActionStatus).toHaveBeenCalledWith("tok-abc", "action-1", "in_progress");
    });
    await waitFor(() => {
      expect(listActionsForDecision).toHaveBeenCalledTimes(2);
    });
  });

  it("a 409 conflict on status change shows a safe message, not a raw backend error", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ status: "pending" })]);
    vi.mocked(changeActionStatus).mockRejectedValue(new ApiError(409, "internal conflict detail"));
    const user = userEvent.setup();
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await user.click(screen.getByRole("button", { name: "Start" }));

    await waitFor(() => {
      expect(screen.getByText("This action was already updated by someone else. Refreshing...")).toBeInTheDocument();
    });
    expect(document.body.textContent).not.toContain("internal conflict detail");
  });
});

// ASSIGNMENT / REASSIGNMENT ---------------------------------------------------

describe("Actions panel - assignment", () => {
  it("shows a generic Unassigned badge and never renders a raw assigned_user_id", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: null })]);
    const { container } = renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await waitFor(() => {
      expect(badgeTexts(container)).toContain("Unassigned");
    });
    expect(screen.queryByText(/00000000-0000/)).not.toBeInTheDocument();
  });

  it("shows the resolved member name for a known current assignee, not a raw UUID", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: MEMBER_A.id })]);
    const { container } = renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await waitFor(() => {
      expect(badgeTexts(container)).toContain("Huda Saleh");
    });
    expect(document.body.textContent).not.toContain(MEMBER_A.id);
  });

  it("falls back to a generic label for a current assignee no longer in the active member list - never a raw UUID", async () => {
    const staleId = "00000000-0000-0000-0000-0000000000ff";
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: staleId })]);
    const { container } = renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await waitFor(() => {
      expect(listCompanyMembers).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(badgeTexts(container)).toContain("Assigned team member");
    });
    expect(document.body.textContent).not.toContain(staleId);
  });

  it("offers a member selector (Unassigned + active members) for a non-terminal Action", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: null, status: "pending" })]);
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    const selector = (await screen.findByRole("combobox", { name: "Assignee" })) as HTMLSelectElement;
    expect(selector.value).toBe("");
    expect(screen.getByRole("option", { name: "Huda Saleh" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Omar Faris" })).toBeInTheDocument();
  });

  it("does not show any assignee mutation control for a terminal Action, even when assigned", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([
      action({ assigned_user_id: MEMBER_A.id, status: "completed" }),
    ]);
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await waitFor(() => screen.getByText("Huda Saleh"));
    expect(screen.queryByRole("combobox", { name: "Assignee" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Unassign" })).not.toBeInTheDocument();
  });

  it("assigns Unassigned -> user by selecting a member, sending that member's id", async () => {
    vi.mocked(listActionsForDecision)
      .mockResolvedValueOnce([action({ assigned_user_id: null })])
      .mockResolvedValueOnce([action({ assigned_user_id: MEMBER_A.id })]);
    vi.mocked(changeActionAssignee).mockResolvedValue(action({ assigned_user_id: MEMBER_A.id }));
    const user = userEvent.setup();
    const { container } = renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    const selector = await screen.findByRole("combobox", { name: "Assignee" });
    await user.selectOptions(selector, MEMBER_A.id);

    await waitFor(() => {
      expect(changeActionAssignee).toHaveBeenCalledWith("tok-abc", "action-1", MEMBER_A.id);
    });
    await waitFor(() => {
      expect(badgeTexts(container)).toContain("Huda Saleh");
    });
  });

  it("reassigns user A -> user B by selecting a different member", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: MEMBER_A.id })]);
    vi.mocked(changeActionAssignee).mockResolvedValue(action({ assigned_user_id: MEMBER_B.id }));
    const user = userEvent.setup();
    renderPanel();

    const selector = (await screen.findByRole("combobox", { name: "Assignee" })) as HTMLSelectElement;
    await waitFor(() => expect(selector.value).toBe(MEMBER_A.id));
    await user.selectOptions(selector, MEMBER_B.id);

    await waitFor(() => {
      expect(changeActionAssignee).toHaveBeenCalledWith("tok-abc", "action-1", MEMBER_B.id);
    });
  });

  it("unassigns user -> Unassigned via the selector, sending an explicit null (never an empty payload)", async () => {
    vi.mocked(listActionsForDecision)
      .mockResolvedValueOnce([action({ assigned_user_id: MEMBER_A.id })])
      .mockResolvedValueOnce([action({ assigned_user_id: null })]);
    vi.mocked(changeActionAssignee).mockResolvedValue(action({ assigned_user_id: null }));
    const user = userEvent.setup();
    const { container } = renderPanel();

    const selector = (await screen.findByRole("combobox", { name: "Assignee" })) as HTMLSelectElement;
    await waitFor(() => expect(selector.value).toBe(MEMBER_A.id));
    await user.selectOptions(selector, "");

    await waitFor(() => {
      expect(changeActionAssignee).toHaveBeenCalledWith("tok-abc", "action-1", null);
    });
    expect(vi.mocked(changeActionAssignee).mock.calls[0]).toHaveLength(3);
    await waitFor(() => {
      expect(badgeTexts(container)).toContain("Unassigned");
    });
  });

  it("does not call the backend for a no-op selection (re-selecting the already-current assignee)", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: MEMBER_A.id })]);
    const user = userEvent.setup();
    renderPanel();

    const selector = (await screen.findByRole("combobox", { name: "Assignee" })) as HTMLSelectElement;
    await waitFor(() => expect(selector.value).toBe(MEMBER_A.id));
    await user.selectOptions(selector, MEMBER_A.id);

    expect(changeActionAssignee).not.toHaveBeenCalled();
  });

  it("a failed reassignment shows a safe message and does not falsely update the displayed assignee", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: null })]);
    vi.mocked(changeActionAssignee).mockRejectedValue(new ApiError(404, "internal detail"));
    const user = userEvent.setup();
    const { container } = renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    const selector = await screen.findByRole("combobox", { name: "Assignee" });
    await user.selectOptions(selector, MEMBER_A.id);

    await waitFor(() => {
      expect(screen.getByText("This action is no longer available.")).toBeInTheDocument();
    });
    expect(document.body.textContent).not.toContain("internal detail");
    // Still shows Unassigned - the failed mutation never took visual effect.
    expect(badgeTexts(container)).toContain("Unassigned");
  });

  it("member-source failure falls back to a plain Unassign button (no picker) for an already-assigned, non-terminal Action", async () => {
    vi.mocked(listCompanyMembers).mockRejectedValue(new ApiError(500, "internal detail"));
    vi.mocked(listActionsForDecision)
      .mockResolvedValueOnce([action({ assigned_user_id: MEMBER_A.id })])
      .mockResolvedValueOnce([action({ assigned_user_id: null })]);
    vi.mocked(changeActionAssignee).mockResolvedValue(action({ assigned_user_id: null }));
    const user = userEvent.setup();
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Unassign" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("combobox", { name: "Assignee" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Unassign" }));
    await waitFor(() => {
      expect(changeActionAssignee).toHaveBeenCalledWith("tok-abc", "action-1", null);
    });
  });

  it("member-source failure hides any mutation control for an Unassigned Action (nothing to assign to)", async () => {
    vi.mocked(listCompanyMembers).mockRejectedValue(new ApiError(500, "internal detail"));
    vi.mocked(listActionsForDecision).mockResolvedValue([action({ assigned_user_id: null })]);
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await waitFor(() => {
      expect(screen.getByText("Unable to load company members.")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Unassign" })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Assignee" })).not.toBeInTheDocument();
  });
});

// DETAIL / HISTORY ----------------------------------------------------------

describe("Actions panel - detail / history", () => {
  it("renders the initial status event as Initial -> Pending, never Unassigned -> Pending, with a visible timestamp", async () => {
    const baseAction = action();
    vi.mocked(listActionsForDecision).mockResolvedValue([baseAction]);
    vi.mocked(getAction).mockResolvedValue(
      detail(baseAction, [
        {
          id: "event-1",
          change_type: "status",
          from_status: null,
          to_status: "pending",
          from_assigned_user_id: null,
          to_assigned_user_id: null,
          changed_by_user_id: "00000000-0000-0000-0000-000000000001",
          changed_at: "2026-08-25T10:15:00Z",
        },
      ]),
    );
    const user = userEvent.setup();
    const { container } = renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await user.click(screen.getByRole("button", { name: "View history" }));

    await waitFor(() => {
      expect(getAction).toHaveBeenCalledWith("tok-abc", "action-1");
    });
    await waitFor(() => {
      expect(screen.getByText(/Status:/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Status: Initial . Pending/)).toBeInTheDocument();
    expect(screen.queryByText(/Status: Unassigned/)).not.toBeInTheDocument();
    // changed_at is rendered in some human-readable form - loosely assert
    // the event's year appears, without pinning an exact locale format.
    expect(container.textContent).toMatch(/2026/);
    expect(container.querySelector("pre")).toBeNull();
    expect(container.textContent).not.toContain("00000000-0000-0000-0000-000000000001");
    expect(container.textContent).not.toContain("event-1");

    await user.click(screen.getByRole("button", { name: "Hide history" }));
    expect(screen.queryByText(/Status:/)).not.toBeInTheDocument();
  });

  it("renders an assignment change event in human-readable form, Unassigned -> resolved member name", async () => {
    const baseAction = action({ assigned_user_id: MEMBER_A.id });
    vi.mocked(listActionsForDecision).mockResolvedValue([baseAction]);
    vi.mocked(getAction).mockResolvedValue(
      detail(baseAction, [
        {
          id: "event-2",
          change_type: "assignment",
          from_status: null,
          to_status: null,
          from_assigned_user_id: null,
          to_assigned_user_id: MEMBER_A.id,
          changed_by_user_id: "00000000-0000-0000-0000-000000000001",
          changed_at: "2026-08-25T00:05:00Z",
        },
      ]),
    );
    const user = userEvent.setup();
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await user.click(screen.getByRole("button", { name: "View history" }));

    await waitFor(() => {
      expect(screen.getByText(/Assignment: Unassigned . Huda Saleh/)).toBeInTheDocument();
    });
  });

  it("resolves a known actor's name and falls back safely for an unknown actor - never a raw UUID", async () => {
    const baseAction = action();
    vi.mocked(listActionsForDecision).mockResolvedValue([baseAction]);
    vi.mocked(getAction).mockResolvedValue(
      detail(baseAction, [
        {
          id: "event-1",
          change_type: "status",
          from_status: null,
          to_status: "pending",
          from_assigned_user_id: null,
          to_assigned_user_id: null,
          changed_by_user_id: MEMBER_A.id,
          changed_at: "2026-08-25T00:00:00Z",
        },
        {
          id: "event-2",
          change_type: "status",
          from_status: "pending",
          to_status: "in_progress",
          from_assigned_user_id: null,
          to_assigned_user_id: null,
          changed_by_user_id: "00000000-0000-0000-0000-0000000000zz".replace("zz", "ee"),
          changed_at: "2026-08-25T01:00:00Z",
        },
      ]),
    );
    const user = userEvent.setup();
    const { container } = renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await user.click(screen.getByRole("button", { name: "View history" }));

    await waitFor(() => {
      expect(screen.getByText(/by Huda Saleh/)).toBeInTheDocument();
    });
    expect(screen.getByText(/by a team member/)).toBeInTheDocument();
    expect(container.textContent).not.toContain("00000000-0000-0000-0000-0000000000ee");
  });

  it("shows a safe message when history fails to load", async () => {
    vi.mocked(listActionsForDecision).mockResolvedValue([action()]);
    vi.mocked(getAction).mockRejectedValue(new ApiError(500, "internal detail"));
    const user = userEvent.setup();
    renderPanel();

    await waitFor(() => screen.getByText("Draft the vendor renewal proposal"));
    await user.click(screen.getByRole("button", { name: "View history" }));

    await waitFor(() => {
      expect(screen.getByText("Unable to load action history.")).toBeInTheDocument();
    });
    expect(document.body.textContent).not.toContain("internal detail");
  });
});
