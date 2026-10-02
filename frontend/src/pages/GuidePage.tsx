import { Link } from "react-router-dom";

const STEPS = [
  {
    n: 1,
    title: "Register as Master (creates the event)",
    points: [
      "Go to Setup and enter your name, email, phone (+CC-XXXXXXXXXX), and a 2-digit Event ID (e.g. 42).",
      "Submitting creates your master account and the event, and logs you in.",
      "The Event ID must be unique — if taken, choose another. Share it with your volunteers.",
    ],
    to: "/setup",
    linkLabel: "Open Setup",
  },
  {
    n: 2,
    title: "Volunteers register themselves",
    points: [
      "A volunteer opens Volunteers and enters name, phone, optional email, and your Event ID.",
      "In demo mode they are auto-approved and can log in immediately.",
      "An Event ID that does not exist is rejected.",
    ],
    to: "/volunteers",
    linkLabel: "Open Volunteers",
  },
  {
    n: 3,
    title: "Register guests (Master or Volunteer)",
    points: [
      "Log in, then go to Register and enter the guest's details and category.",
      "Guests attach to your event automatically — no event selection needed.",
      "See everyone under Guests.",
    ],
    to: "/guests/register",
    linkLabel: "Register a guest",
  },
  {
    n: 4,
    title: "Check guests in and out",
    points: [
      "Go to Check-In, search a guest by name, then Check In or Check Out.",
      "Duplicate check-ins are flagged; VIP/Speaker and dietary/accessibility needs are highlighted.",
    ],
    to: "/check-in",
    linkLabel: "Open Check-In",
  },
  {
    n: 5,
    title: "Monitor the event",
    points: [
      "Dashboard shows live counts (present, departed, not checked in, peak) with category and capacity breakdowns.",
      "Analytics shows totals, per-category stats, and an hourly check-in chart.",
    ],
    to: "/dashboard",
    linkLabel: "Open Dashboard",
  },
];

export default function GuidePage() {
  return (
    <div className="page">
      <h1>How to use the app</h1>
      <p className="page-intro">
        Five steps from setting up an event to monitoring attendance. Each user
        only sees the data for the event they belong to.
      </p>

      {STEPS.map((s) => (
        <div className="card" key={s.n}>
          <h2 className="guide-step-title">
            <span className="step-num">{s.n}</span> {s.title}
          </h2>
          <ul className="guide-points">
            {s.points.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
          <Link className="btn btn-sm btn-primary" to={s.to}>
            {s.linkLabel} →
          </Link>
        </div>
      ))}

      <p className="muted">
        Demo note: one-time passwords (OTP) are currently bypassed, so login and
        registration need no verification code.
      </p>
    </div>
  );
}
