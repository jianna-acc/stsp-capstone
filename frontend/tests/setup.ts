// File: /frontend/tests/setup.ts
// Purpose: Loads shared DOM matchers and browser API mocks
// for frontend Vitest and React Testing Library tests.

import "@testing-library/jest-dom/vitest";

import {
  cleanup,
} from "@testing-library/react";
import {
  afterEach,
  vi,
} from "vitest";

afterEach(() => {
  cleanup();

  /*
   * Mantine Select dropdowns are rendered in shared portal
   * nodes outside the React Testing Library container.
   * Remove them so they do not remain between tests.
   */
  document
    .querySelectorAll(
      "[data-mantine-shared-portal-node]",
    )
    .forEach((portalNode) => {
      portalNode.remove();
    });
});

Object.defineProperty(
  window,
  "matchMedia",
  {
    configurable: true,
    writable: true,

    value: vi.fn().mockImplementation(
      (
        query: string,
      ): MediaQueryList => ({
        matches: false,
        media: query,
        onchange: null,

        addListener: vi.fn(),
        removeListener: vi.fn(),

        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),

        dispatchEvent: vi.fn(
          () => false,
        ),
      }),
    ),
  },
);

/*
 * Mantine's autosizing Textarea listens for browser font
 * loading events through document.fonts. jsdom does not
 * provide the FontFaceSet API, so tests need a safe mock.
 */
Object.defineProperty(
  document,
  "fonts",
  {
    configurable: true,

    value: {
      status: "loaded",

      ready: Promise.resolve(),

      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),

      check: vi.fn(
        () => true,
      ),

      load: vi.fn(
        async () => [],
      ),

      forEach: vi.fn(),
    },
  },
);

class ResizeObserverMock
  implements ResizeObserver {
  disconnect(): void {
    return;
  }

  observe(): void {
    return;
  }

  unobserve(): void {
    return;
  }
}

vi.stubGlobal(
  "ResizeObserver",
  ResizeObserverMock,
);

Object.defineProperty(
  window,
  "scrollTo",
  {
    configurable: true,
    writable: true,
    value: vi.fn(),
  },
);

Object.defineProperties(
  HTMLElement.prototype,
  {
    scrollIntoView: {
      configurable: true,
      writable: true,
      value: vi.fn(),
    },

    hasPointerCapture: {
      configurable: true,
      writable: true,
      value: vi.fn(
        () => false,
      ),
    },

    setPointerCapture: {
      configurable: true,
      writable: true,
      value: vi.fn(),
    },

    releasePointerCapture: {
      configurable: true,
      writable: true,
      value: vi.fn(),
    },
  },
);