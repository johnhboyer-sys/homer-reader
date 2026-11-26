// The site header's Atlas / People / Language triggers are disclosures: the
// state a screen reader hears (aria-expanded) is the state on screen
// (is-open), Enter/Space/click toggle it, Escape closes and hands focus back,
// and a click elsewhere closes. (Round-2 review finding: they used to open
// only on :hover / :focus-within, with no state and no way to dismiss.)
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { initSiteMenus } from '../lib/site-menu';

const markup = `
  <header class="sh">
    <nav>
      <div class="sh-group">
        <button type="button" class="sh-group-btn" aria-controls="sh-menu-atlas">Atlas</button>
        <div class="sh-menu" id="sh-menu-atlas"><a href="/maps/">Maps</a><a href="/places/">Places</a></div>
      </div>
      <div class="sh-group">
        <button type="button" class="sh-group-btn" aria-controls="sh-menu-people">People</button>
        <div class="sh-menu" id="sh-menu-people"><a href="/characters/">Characters</a></div>
      </div>
    </nav>
    <a id="outside" href="/about">About</a>
  </header>`;

describe('site header menus', () => {
  let header: HTMLElement;
  let teardown: () => void;
  let atlas: HTMLButtonElement;
  let people: HTMLButtonElement;
  const group = (b: HTMLElement) => b.closest('.sh-group') as HTMLElement;

  beforeEach(() => {
    document.body.innerHTML = markup;
    header = document.querySelector('header.sh') as HTMLElement;
    teardown = initSiteMenus(header);
    [atlas, people] = Array.from(header.querySelectorAll<HTMLButtonElement>('.sh-group-btn'));
  });
  afterEach(() => { teardown(); document.body.innerHTML = ''; });

  it('marks the header scripted and every trigger collapsed', () => {
    expect(header.classList.contains('sh-js')).toBe(true);
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
    expect(people.getAttribute('aria-expanded')).toBe('false');
    expect(document.getElementById(atlas.getAttribute('aria-controls')!)).not.toBeNull();
  });

  it('a click opens, a second click closes, and aria-expanded follows', () => {
    atlas.click();
    expect(atlas.getAttribute('aria-expanded')).toBe('true');
    expect(group(atlas).classList.contains('is-open')).toBe(true);
    atlas.click();
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
    expect(group(atlas).classList.contains('is-open')).toBe(false);
  });

  it('opening one menu closes the other', () => {
    atlas.click();
    people.click();
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
    expect(people.getAttribute('aria-expanded')).toBe('true');
  });

  it('Escape closes the open menu and returns focus to its trigger', () => {
    atlas.click();
    const link = group(atlas).querySelector('a') as HTMLAnchorElement;
    link.focus();
    link.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(atlas);
  });

  it('a click outside closes', () => {
    atlas.click();
    (document.getElementById('outside') as HTMLElement).dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
  });

  it('focus leaving the group closes it', () => {
    atlas.click();
    const link = group(atlas).querySelector('a') as HTMLAnchorElement;
    link.dispatchEvent(new FocusEvent('focusout', { bubbles: true, relatedTarget: document.getElementById('outside') }));
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
  });

  it('hover opens without pinning; a click then keeps it open past mouseleave', () => {
    const g = group(atlas);
    g.dispatchEvent(new MouseEvent('mouseenter'));
    expect(atlas.getAttribute('aria-expanded')).toBe('true');
    g.dispatchEvent(new MouseEvent('mouseleave'));
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
    g.dispatchEvent(new MouseEvent('mouseenter'));
    atlas.click();
    g.dispatchEvent(new MouseEvent('mouseleave'));
    expect(atlas.getAttribute('aria-expanded')).toBe('true');
  });

  // Round-2 review finding M2: a hover-opened menu closed on mouseleave even
  // with keyboard focus on one of its links, which then sat focused and hidden.
  it('a hover-opened menu stays open on mouseleave while focus is inside it, and closes when focus leaves', () => {
    const g = group(atlas);
    g.dispatchEvent(new MouseEvent('mouseenter'));
    const link = g.querySelector('a') as HTMLAnchorElement;
    link.focus();
    expect(document.activeElement).toBe(link);
    g.dispatchEvent(new MouseEvent('mouseleave'));
    expect(atlas.getAttribute('aria-expanded')).toBe('true');
    expect(g.classList.contains('is-open')).toBe(true);
    link.dispatchEvent(new FocusEvent('focusout', { bubbles: true, relatedTarget: document.getElementById('outside') }));
    expect(atlas.getAttribute('aria-expanded')).toBe('false');
  });
});
