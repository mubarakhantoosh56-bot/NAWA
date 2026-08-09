// Demo mode is OFF unless explicitly enabled at build time. When off, no
// component may substitute fabricated/demo content for an empty real result.
export function isDemoModeEnabled(): boolean {
  return process.env.NEXT_PUBLIC_DEMO_MODE === "true";
}
