import { Link } from "react-router-dom";

interface Step {
  n: number;
  title: string;
  body: string;
  to?: string;
  linkLabel?: string;
}

const STEPS: Step[] = [
  {
    n: 1,
    title: "Register as Master",
    body: "Create your master account and a new 2-digit Event ID. Share that ID with your volunteers.",
    to: "/setup",
    linkLabel: "Go to Setup",
  },
  {
    n: 2,
    title: "Volunteers join",
    body: "Volunteers register themselves using the Event ID you gave them.",
    to: "/volunteers",
    linkLabel: "Volunteers",
  },
  {
    n: 3,
    title: "Register guests",
    body: "Master or volunteer adds guests — they attach to your event automatically.",
    to: "/guests/register",
    linkLabel: "Register guest",
  },
  {
    n: 4,
    title: "Check in / out",
    body: "Find a guest by name and check them in or out at the event.",
    to: "/check-in",
    linkLabel: "Check-In",
  },
  {
    n: 5,
    title: "Monitor",
    body: "Watch live attendance and trends on the dashboard and analytics.",
    to: "/dashboard",
    linkLabel: "Dashboard",
  },
];

export default function StepsGuide() {
  return (
    <aside className="steps-guide" aria-label="How to use the app">
      <h2 className="steps-title">How it works</h2>
      <ol className="steps-list">
        {STEPS.map((s) => (
          <li className="step-item" key={s.n}>
            <span className="step-num">{s.n}</span>
            <div className="step-content">
              <div className="step-head">{s.title}</div>
              <p className="step-body">{s.body}</p>
              {s.to && (
                <Link className="step-link" to={s.to}>
                  {s.linkLabel} →
                </Link>
              )}
            </div>
          </li>
        ))}
      </ol>
    </aside>
  );
}
