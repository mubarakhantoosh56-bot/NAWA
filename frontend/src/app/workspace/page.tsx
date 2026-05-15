import { RequireAuth } from "@/components/auth/RequireAuth";
import { WorkspaceShell } from "@/components/layout/WorkspaceShell";

export default function WorkspacePage() {
  return (
    <RequireAuth>
      <WorkspaceShell />
    </RequireAuth>
  );
}
