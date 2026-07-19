import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import BekkerJump from '../components/BekkerJump.svelte';

// BekkerJump is scheme-aware (shared/lib/citation.ts): its placeholder, label,
// and parse behavior all come from the work's citation scheme, not a
// hardcoded Bekker grammar. No stephanus work is in the registry yet (Plato
// works land in a later phase), so a fake work id + a mocked getWork stands in
// for one here.
vi.mock('../lib/works', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/works')>();
  return {
    ...actual,
    getWork: (id: string) =>
      id === 'StephWork'
        ? ({ id: 'StephWork', title: 'Test Dialogue', citation: { scheme: 'stephanus' } } as ReturnType<typeof actual.getWork>)
        : actual.getWork(id),
  };
});

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchColumns: vi.fn(async (work: string) => {
      if (work === 'StephWork') return { '34b': [{ book: 1, lo: 1, hi: 20 }] };
      // Real verse-line registry works (iliad/odyssey) — one column per book,
      // matching the real columns.json shape (see shared/lib/citation.ts).
      if (work === 'iliad') return { '1': [{ book: 1, lo: 1, hi: 611 }] };
      if (work === 'odyssey') return { '9': [{ book: 9, lo: 1, hi: 566 }] };
      return { '1097a': [{ book: 1, lo: 1, hi: 20 }] };
    }),
  };
});

describe('BekkerJump — scheme-aware citation entry', () => {
  it('shows the Bekker placeholder/label for a bekker work (default scheme)', async () => {
    render(BekkerJump, { props: { work: 'EN', inputId: 'bk-en' } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to Bekker citation/ }));
    expect(screen.getByPlaceholderText('e.g. 1097a15')).toBeInTheDocument();
    expect(screen.getByLabelText('Bekker citation')).toBeInTheDocument();
  });

  it('shows the Stephanus placeholder/label and accepts a bare column, calling onJump with a null line', async () => {
    const onJump = vi.fn();
    render(BekkerJump, { props: { work: 'StephWork', inputId: 'bk-steph', onJump } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to Stephanus page/ }));
    expect(screen.getByPlaceholderText('e.g. 34b')).toBeInTheDocument();

    const input = screen.getByLabelText('Jump to a Stephanus page');
    await fireEvent.input(input, { target: { value: '34b' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Go' }));

    expect(onJump).toHaveBeenCalledWith(1, '34b', null);
  });

  it('rejects a trailing-digits citation for a lineless (stephanus) scheme', async () => {
    const onJump = vi.fn();
    render(BekkerJump, { props: { work: 'StephWork', inputId: 'bk-steph-bad', onJump } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to Stephanus page/ }));

    const input = screen.getByLabelText('Jump to a Stephanus page');
    await fireEvent.input(input, { target: { value: '34b12' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Go' }));

    expect(onJump).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('stephanus page');
  });

  it('still resolves a full bekker citation (column + line) via onJump', async () => {
    const onJump = vi.fn();
    render(BekkerJump, { props: { work: 'EN', inputId: 'bk-en-full', onJump } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to Bekker citation/ }));

    const input = screen.getByLabelText('Jump to a Bekker citation');
    await fireEvent.input(input, { target: { value: '1097a15' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Go' }));

    expect(onJump).toHaveBeenCalledWith(1, '1097a', 15);
  });
});

describe('BekkerJump — verse-line (Homer) cross-work citation entry', () => {
  it('shows the verse-line placeholder/label, matching the ⌘K palette grammar', async () => {
    render(BekkerJump, { props: { work: 'odyssey', inputId: 'bk-od' } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to verse citation/ }));
    expect(screen.getByPlaceholderText('e.g. Od. 9.366')).toBeInTheDocument();
    expect(screen.getByLabelText('verse citation')).toBeInTheDocument();
  });

  it('accepts a bare book.line in the current work\'s context', async () => {
    const onJump = vi.fn();
    render(BekkerJump, { props: { work: 'odyssey', inputId: 'bk-od-bare', onJump } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to verse citation/ }));

    const input = screen.getByLabelText('Jump to a verse citation');
    await fireEvent.input(input, { target: { value: '9.366' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Go' }));

    expect(onJump).toHaveBeenCalledWith(9, '9', 366);
  });

  it('accepts the work-prefixed form the placeholder advertises ("Od. 9.366")', async () => {
    const onJump = vi.fn();
    render(BekkerJump, { props: { work: 'odyssey', inputId: 'bk-od-prefixed', onJump } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to verse citation/ }));

    const input = screen.getByLabelText('Jump to a verse citation');
    await fireEvent.input(input, { target: { value: 'Od. 9.366' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Go' }));

    expect(onJump).toHaveBeenCalledWith(9, '9', 366);
  });

  it('resolves a cross-work citation ("Il. 1.1") typed from an Odyssey-mounted box', async () => {
    const { fetchColumns } = await import('../lib/data');
    const onJump = vi.fn();
    render(BekkerJump, { props: { work: 'odyssey', inputId: 'bk-od-cross', onJump } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to verse citation/ }));

    const input = screen.getByLabelText('Jump to a verse citation');
    await fireEvent.input(input, { target: { value: 'Il. 1.1' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Go' }));

    expect(fetchColumns).toHaveBeenCalledWith('iliad');
    expect(onJump).toHaveBeenCalledWith(1, '1', 1);
  });

  it('rejects an out-of-range book and never calls onJump', async () => {
    const onJump = vi.fn();
    render(BekkerJump, { props: { work: 'iliad', inputId: 'bk-il-bad', onJump } });
    await fireEvent.click(screen.getByRole('button', { name: /Go to verse citation/ }));

    const input = screen.getByLabelText('Jump to a verse citation');
    await fireEvent.input(input, { target: { value: '99.1' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Go' }));

    expect(onJump).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('verse citation');
  });
});
