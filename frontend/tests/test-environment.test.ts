// File: /frontend/tests/test-environment.test.ts
// Purpose: Verifies that Vitest, jsdom, and the shared
// Testing Library matchers are configured correctly.

import {
  describe,
  expect,
  it,
} from "vitest";

describe(
  "frontend test environment",
  () => {
    it(
      "provides a working jsdom document",
      () => {
        const heading =
          document.createElement("h1");

        heading.textContent =
          "Study Assistant";

        document.body.append(heading);

        expect(
          heading,
        ).toBeInTheDocument();

        expect(
          heading,
        ).toHaveTextContent(
          "Study Assistant",
        );
      },
    );

    it(
      "provides the required browser mocks",
      () => {
        expect(
          window.matchMedia,
        ).toBeTypeOf("function");

        expect(
          globalThis.ResizeObserver,
        ).toBeDefined();

        expect(
          window.scrollTo,
        ).toBeTypeOf("function");
      },
    );
  },
);