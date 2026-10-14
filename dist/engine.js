export function normalize(value) {
  return value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/j/g, 'i').trim();
}
export function buildIndex(corpus) {
  const lemmas = new Map(), forms = new Map();
  for (const canon of corpus.canons) for (const [i, token] of canon.tokens.entries()) {
    const [start, end, lemma, pos] = token;
    const form = normalize(canon.la.slice(start, end));
    if (!lemmas.has(lemma)) lemmas.set(lemma, {lemma, occurrences: [], forms: new Map(), pos: new Set()});
    const entry = lemmas.get(lemma);
    entry.occurrences.push({canon: canon.n, book: canon.book, i, start, end, form});
    entry.forms.set(form, (entry.forms.get(form) || 0) + 1);
    entry.pos.add(pos);
    if (!forms.has(form)) forms.set(form, new Set());
    forms.get(form).add(lemma);
  }
  return {lemmas, forms};
}
export function searchEntries(index, query, book = 0, mode = 'lemma') {
  const q = normalize(query), uv = s => s.replace(/v/g,'u'), exact = new Set([...(index.forms.get(q)||[]), ...[...index.forms].filter(([f])=>uv(f)===uv(q)).flatMap(([,ls])=>[...ls])]);
  const entries = mode === 'form' ? [...index.forms.keys()].map(form => ({lemma:form, occurrences:[...index.forms.get(form)].flatMap(l=>index.lemmas.get(l).occurrences.filter(o=>o.form===form))})) : [...index.lemmas.values()];
  return entries.filter(e => !q || uv(e.lemma).includes(uv(q)) || (mode==='lemma' && exact.has(e.lemma)))
    .map(e=>({...e, occurrences:e.occurrences.filter(o=>!book || o.book===book)}))
    .filter(e=>e.occurrences.length)
    .sort((a,b)=> (Number(b.lemma===q)-Number(a.lemma===q)) || b.occurrences.length-a.occurrences.length || a.lemma.localeCompare(b.lemma));
}
export function getOccurrences(index, word, book=0, mode='lemma', form='') {
  let list = mode==='lemma' ? (index.lemmas.get(word)?.occurrences || []) : [...(index.forms.get(word)||[])].flatMap(l=>index.lemmas.get(l).occurrences.filter(o=>o.form===word));
  return list.filter(o=>(!book || o.book===book)&&(!form || o.form===form)).sort((a,b)=>a.canon-b.canon || a.start-b.start);
}
export function csv(rows) {return rows.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n');}
