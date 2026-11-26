// Review finding (round 5): at phone width, Go to in the Menu sheet closed the
// <details> and then the palette saved document.activeElement -- the Go-to
// link, now hidden inside the closed sheet -- so Escape had nowhere visible to
// return focus. Focus moves to the sheet's Menu summary first, and the palette
// hands it back there.
import { describe, it, expect, afterEach } from 'vitest';
import { closeSheetOnGoto } from '../lib/site-menu';
import { initGoto } from '../lib/goto';

describe('Go to from the phone Menu sheet', () => {
  let teardown: (() => void)[] = [];
  afterEach(() => { teardown.forEach((f) => f()); teardown = []; document.body.innerHTML = ''; });

  it('closes the sheet and leaves focus on the Menu summary for the palette to restore', async () => {
    document.body.innerHTML = `
      <details class="sh-mobile" open>
        <summary aria-label="Menu">Menu</summary>
        <nav class="sh-sheet"><a class="sh-sheet-goto" href="/search" data-goto>Go to</a></nav>
      </details>`;
    const sheet = document.querySelector('details') as HTMLDetailsElement;
    const summary = sheet.querySelector('summary') as HTMLElement;
    const go = sheet.querySelector<HTMLElement>('[data-goto]')!;
    let saved: Element | null = null;
    teardown.push(closeSheetOnGoto(sheet, [go]));
    teardown.push(initGoto({
      triggers: [go],
      load: async () => ({ open: () => { saved = document.activeElement; } }),
    }));

    go.focus();
    go.click();
    await new Promise((r) => setTimeout(r, 0));

    expect(sheet.open).toBe(false);
    expect(saved).toBe(summary);
    expect(document.activeElement).toBe(summary);
  });

  it('leaves focus alone for a Go to outside the sheet', () => {
    document.body.innerHTML = `
      <a id="bar-go" href="/search" data-goto>Go to</a>
      <details class="sh-mobile"><summary>Menu</summary><nav></nav></details>`;
    const sheet = document.querySelector('details') as HTMLDetailsElement;
    const go = document.getElementById('bar-go')!;
    teardown.push(closeSheetOnGoto(sheet, [go]));
    go.focus();
    go.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(go);
  });
});
