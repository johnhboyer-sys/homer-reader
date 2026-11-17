// Homer's own address parameters on the new search page: the book searched
// within one poem (b), whose words (spk, spo, and the old so=1), and the old
// one-book grammar link (gr), read as a lone grammar term.
import { describe, expect, it } from 'vitest';
import { decodeSearchUrl, encodeSearchUrl, emptyUrlSearch } from '../lib/search-url';

const ALL = ['iliad', 'odyssey'];
const read = (qs: string) => decodeSearchUrl(qs, ALL);
const write = (qs: string) => encodeSearchUrl(read(qs), ALL);

describe('b: one book of one poem', () => {
  it('reads a book when one poem is searched', () => {
    expect(read('g=μῆνις&w=iliad&b=9').book).toBe(9);
  });
  it('ignores a book with both poems, out of range, or not a whole number', () => {
    expect(read('g=μῆνις&b=9').book).toBeNull();
    expect(read('g=μῆνις&w=iliad&b=25').book).toBeNull();
    expect(read('g=μῆνις&w=iliad&b=0').book).toBeNull();
    expect(read('g=μῆνις&w=iliad&b=x').book).toBeNull();
    expect(read('g=μῆνις&w=iliad&b=2.5').book).toBeNull();
  });
  it('writes it back, and drops it once both poems are searched', () => {
    expect(write('g=μῆνις&w=iliad&b=9')).toBe('g=%CE%BC%E1%BF%86%CE%BD%CE%B9%CF%82&w=iliad&b=9');
    const s = read('g=μῆνις&w=iliad&b=9');
    expect(encodeSearchUrl({ ...s, works: ALL }, ALL)).not.toContain('b=');
  });
});

describe('spk, spo and the old so=1', () => {
  it('reads one speaker', () => {
    expect(read('g=μῆνις&spk=achilles').speech).toEqual({ kind: 'speaker', id: 'achilles' });
  });
  it('reads speeches only from spo=1', () => {
    expect(read('g=μῆνις&spo=1').speech).toEqual({ kind: 'speeches' });
  });
  it('reads the old so=1 as speeches only, and leaves the sort at its default', () => {
    const s = read('g=μῆνις&so=1');
    expect(s.speech).toEqual({ kind: 'speeches' });
    expect(s.sort).toBe('page');
  });
  it('still reads so as the sort order when it names one', () => {
    const s = read('g=μῆνις&so=form');
    expect(s.sort).toBe('form');
    expect(s.speech).toBeNull();
  });
  it('writes spo, never so, for speeches only', () => {
    expect(write('g=μῆνις&so=1')).toMatch(/&spo=1$/);
    expect(write('g=μῆνις&so=1')).not.toMatch(/(^|&)so=/);
  });
  it('writes spk for a speaker, and a speaker wins over spo', () => {
    expect(write('g=μῆνις&spk=achilles')).toMatch(/&spk=achilles$/);
    expect(read('g=μῆνις&spk=achilles&spo=1').speech).toEqual({ kind: 'speaker', id: 'achilles' });
  });
  it('writes nothing for the filter when there is no search', () => {
    expect(encodeSearchUrl({ ...emptyUrlSearch(ALL), speech: { kind: 'speeches' } }, ALL)).toBe('');
  });
});

describe('gr: the old one-book grammar link', () => {
  it('reads as a lone grammar term, with its poem and book', () => {
    const s = read('w=iliad&b=1&gr=case:gen,number:pl');
    expect(s.combo?.slots).toEqual([{ kind: 'grammatical', relation: 'near', text: '', picked: [], grammar: { case: 'gen', number: 'pl' } }]);
    expect(s.works).toEqual(['iliad']);
    expect(s.book).toBe(1);
  });
  it('is written back as the new page writes a grammar term', () => {
    expect(write('w=iliad&b=1&gr=case:gen,number:pl')).toBe('c=g:case.gen,number.pl&w=iliad&b=1');
  });
  it('gives way to c when both are present, and asks nothing when empty', () => {
    expect(read('c=g:mood.opt&gr=case:gen&w=iliad&b=1').combo?.slots[0].grammar).toEqual({ mood: 'opt' });
    expect(read('gr=&w=iliad&b=1').combo).toBeNull();
    expect(read('gr=junk&w=iliad&b=1').combo).toBeNull();
  });
});
