// The site-wide Go-to (round 3): every page's header opens the reader's own
// palette, by its control or by Cmd/Ctrl+K, and loads it only when asked.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { initGoto } from '../lib/goto';

const flush = () => new Promise((r) => setTimeout(r, 0));

describe('site-wide Go-to', () => {
  let trigger: HTMLAnchorElement;
  let teardown: () => void;
  let opened: number;
  let load: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    document.body.innerHTML = '<a id="go" href="/search" data-goto>Go to</a><input id="field" />';
    trigger = document.getElementById('go') as HTMLAnchorElement;
    opened = 0;
    load = vi.fn(async () => ({ open: () => { opened++; } }));
  });
  afterEach(() => { teardown?.(); document.body.innerHTML = ''; });

  it('loads nothing until it is asked for', () => {
    teardown = initGoto({ triggers: [trigger], load });
    expect(load).not.toHaveBeenCalled();
  });

  it('a click opens the palette instead of following the link to /search', async () => {
    teardown = initGoto({ triggers: [trigger], work: 'odyssey', load });
    const click = new MouseEvent('click', { bubbles: true, cancelable: true });
    trigger.dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);
    await flush();
    expect(load).toHaveBeenCalledTimes(1);
    expect(load).toHaveBeenCalledWith('odyssey');
    expect(opened).toBe(1);
  });

  it('a modified click keeps the link (open /search in a new tab)', async () => {
    teardown = initGoto({ triggers: [trigger], load });
    const click = new MouseEvent('click', { bubbles: true, cancelable: true, metaKey: true });
    trigger.dispatchEvent(click);
    expect(click.defaultPrevented).toBe(false);
    await flush();
    expect(load).not.toHaveBeenCalled();
  });

  it('Ctrl+K and Cmd+K open it from anywhere, a text field included', async () => {
    teardown = initGoto({ triggers: [trigger], load });
    const field = document.getElementById('field') as HTMLInputElement;
    field.focus();
    const key = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true, cancelable: true });
    field.dispatchEvent(key);
    expect(key.defaultPrevented).toBe(true);
    await flush();
    expect(opened).toBe(1);
  });

  it('once the palette is mounted its own shortcut handler is the only one', async () => {
    teardown = initGoto({ triggers: [trigger], load });
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'K', metaKey: true, cancelable: true }));
    await flush();
    expect(opened).toBe(1);
    // The mounted palette toggles itself on the next press; this module must
    // not also call open(), or one press would open and close together.
    const second = new KeyboardEvent('keydown', { key: 'k', metaKey: true, cancelable: true });
    window.dispatchEvent(second);
    await flush();
    expect(opened).toBe(1);
    expect(second.defaultPrevented).toBe(false);
    expect(load).toHaveBeenCalledTimes(1);
  });

  it('warms the module on pointer or focus, and still loads it once', async () => {
    teardown = initGoto({ triggers: [trigger], load });
    trigger.dispatchEvent(new Event('pointerenter'));
    trigger.dispatchEvent(new FocusEvent('focus'));
    await flush();
    expect(load).toHaveBeenCalledTimes(1);
    expect(opened).toBe(0);
    trigger.click();
    await flush();
    expect(load).toHaveBeenCalledTimes(1);
    expect(opened).toBe(1);
  });

  it('a failed load is retried on the next press', async () => {
    let fail = true;
    const flaky = vi.fn(async () => {
      if (fail) throw new Error('offline');
      return { open: () => { opened++; } };
    });
    teardown = initGoto({ triggers: [trigger], load: flaky });
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, cancelable: true }));
    await flush();
    expect(opened).toBe(0);
    fail = false;
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, cancelable: true }));
    await flush();
    expect(flaky).toHaveBeenCalledTimes(2);
    expect(opened).toBe(1);
  });

  it('other keys and plain K are left alone', async () => {
    teardown = initGoto({ triggers: [trigger], load });
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', cancelable: true }));
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'j', ctrlKey: true, cancelable: true }));
    await flush();
    expect(load).not.toHaveBeenCalled();
  });
});
