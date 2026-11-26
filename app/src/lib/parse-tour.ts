// The /start funnel's parse tour (ParsePopupTour.svelte) only ever shows on a
// reader URL carrying ?tour=parse, so it is fetched only then: no reader pays
// for it in its first load. The component keeps its own gates (the query
// param, and whether the tour was dismissed before).

const defaultLoad = async (): Promise<void> => {
  const [{ mount }, { default: ParsePopupTour }] = await Promise.all([
    import('svelte'),
    import('../components/ParsePopupTour.svelte'),
  ]);
  mount(ParsePopupTour, { target: document.body });
};

export function initParseTour(search: string, load: () => Promise<void> = defaultLoad): Promise<void> | null {
  if (new URLSearchParams(search).get('tour') !== 'parse') return null;
  return load();
}
