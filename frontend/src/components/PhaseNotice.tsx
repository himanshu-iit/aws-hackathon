interface PhaseNoticeProps {
  phase: string;
  feature: string;
}

/**
 * Shown on screens whose backend endpoints are still stubbed (HTTP 501).
 * Keeps the UI honest about what is wired up vs. coming in a later phase.
 */
export default function PhaseNotice({ phase, feature }: PhaseNoticeProps) {
  return (
    <div className="phase-notice">
      <strong>{feature}</strong> is built on the frontend and calls the real
      API, but the backend endpoint is still a stub (returns HTTP 501). It will
      go live when <strong>{phase}</strong> of the backend is implemented. Submit
      the form below to see the live API response.
    </div>
  );
}
