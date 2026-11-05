import "@testing-library/jest-dom/vitest";

// happy-dom lacks these browser APIs; Mantine needs them. Nothing is laid out in the tests, so
// listening, observing and scrolling do nothing.
const noop = () => undefined;

window.matchMedia = (query: string): MediaQueryList => ({
  matches: false,
  media: query,
  onchange: null,
  addEventListener: noop,
  removeEventListener: noop,
  // eslint-disable-next-line @typescript-eslint/no-deprecated -- required by the MediaQueryList type
  addListener: noop,
  // eslint-disable-next-line @typescript-eslint/no-deprecated -- required by the MediaQueryList type
  removeListener: noop,
  dispatchEvent: () => false,
});

window.ResizeObserver = class {
  observe = noop;
  unobserve = noop;
  disconnect = noop;
};

window.HTMLElement.prototype.scrollIntoView = noop;
