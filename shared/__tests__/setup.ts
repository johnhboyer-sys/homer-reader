import '@testing-library/jest-dom/vitest';

// happy-dom never computes real layout, so this mock never fires on its
// own — but it stamps its callback onto every observed element as
// `__resizeCallback` (Reader.svelte's applyPlateCamera is the only current
// consumer that needs a resize refit under test) so a test can invoke it
// directly to simulate a real resize, e.g.
// `(el as any).__resizeCallback?.()`.
class ResizeObserverMock {
  constructor(private callback: ResizeObserverCallback) {}
  observe(target: Element) {
    (target as unknown as { __resizeCallback?: () => void }).__resizeCallback = () =>
      this.callback([] as unknown as ResizeObserverEntry[], this as unknown as ResizeObserver);
  }
  unobserve() {}
  disconnect() {}
}

class IntersectionObserverMock {
  readonly root = null;
  readonly rootMargin = '';
  readonly thresholds = [];

  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return []; }
}

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: ResizeObserverMock,
});

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: IntersectionObserverMock,
});

Element.prototype.scrollIntoView = vi.fn();

// happy-dom does not implement the Web Animations API; components that call
// `element.animate(...)` (e.g. WordPopup) would throw. Stub a minimal
// Animation-like object so those code paths run under test.
Element.prototype.animate = vi.fn(() => ({
  finished: Promise.resolve(),
  cancel() {},
  finish() {},
  play() {},
  pause() {},
  onfinish: null,
  addEventListener() {},
  removeEventListener() {},
})) as unknown as Element['animate'];
