// File: /frontend/app/page.tsx
// Purpose: Displays the temporary Next.js foundation status page.

import styles from "./page.module.css";

const foundationChecks = [
  "Next.js application created",
  "TypeScript enabled",
  "App Router enabled",
  "ESLint configured",
  "CSS Modules working",
  "Tailwind removed",
];

export default function HomePage() {
  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <p className={styles.eyebrow}>
          Phase 1C
        </p>

        <h1 className={styles.title}>
          STS Capstone Project
        </h1>

        <p className={styles.description}>
          The initial Next.js frontend foundation is ready.
          Mantine and the complete design system will be added in
          the next micro-phase.
        </p>

        <ul className={styles.statusList}>
          {foundationChecks.map((check) => (
            <li className={styles.statusItem} key={check}>
              <span
                className={styles.statusDot}
                aria-hidden="true"
              />

              <span>{check}</span>
            </li>
          ))}
        </ul>

        <p className={styles.note}>
          Temporary project name: STS Capstone Project
        </p>
      </section>
    </main>
  );
}