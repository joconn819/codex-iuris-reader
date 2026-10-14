import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildIndex,normalize,searchEntries,getOccurrences,csv} from '../dist/engine.js';
const corpus=JSON.parse(readFileSync(new URL('../dist/data/corpus.json',import.meta.url)));
const index=buildIndex(corpus);
test('Every canon has both languages and valid, non-overlapping Latin token offsets',()=>{
 assert.equal(corpus.canons.length,1752);
 corpus.canons.forEach((c,i)=>{assert.equal(c.n,i+1);assert.ok(c.la.length>10);assert.ok(c.en.length>10);let end=0;for(const t of c.tokens){assert.ok(t[0]>=end);assert.ok(t[1]>t[0]&&t[1]<=c.la.length);assert.match(c.la.slice(t[0],t[1]),/^\p{L}+$/u);assert.ok(t[2]);end=t[1];}});
});
test('Irregular noun declensions and verb conjugations are grouped',()=>{
 for(const [lemma,forms] of [['lex',['lex','leges','legibus']],['sum',['est','sunt','sit']],['ius',['ius','iuris','iure']]]){const found=index.lemmas.get(lemma);assert.ok(found,lemma);for(const f of forms)assert.ok(found.forms.has(f),`${lemma} should include ${f}`);}
});
test('Context-specific correction keeps preposition ab under one part of speech',()=>{
 const entry=index.lemmas.get('ab');assert.ok(entry);assert.equal(entry.pos.size,1);assert.ok(entry.pos.has('ADP'));
 const token=corpus.canons[394].tokens.find(t=>corpus.canons[394].la.slice(t[0],t[1])==='A');
 assert.ok(token);assert.equal(token[2],'ab');assert.equal(token[3],'ADP');
});
test('Frequency, form totals, and concordance counts agree across all books',()=>{
 const total=corpus.canons.reduce((n,c)=>n+c.tokens.length,0);
 assert.equal([...index.lemmas.values()].reduce((n,e)=>n+e.occurrences.length,0),total);
 const entry=index.lemmas.get('lex');assert.equal([...entry.forms.values()].reduce((a,b)=>a+b,0),entry.occurrences.length);
 assert.equal(getOccurrences(index,'lex').length,entry.occurrences.length);
 assert.equal(corpus.books.reduce((n,b)=>n+getOccurrences(index,'lex',b.id).length,0),entry.occurrences.length);
});
test('An inflected form resolves to its lemma; exact mode returns only that form',()=>{
 assert.ok(searchEntries(index,'legibus').some(e=>e.lemma==='lex'));
 const rows=getOccurrences(index,'legibus',0,'form');assert.ok(rows.length);assert.ok(rows.every(o=>o.form==='legibus'));
 assert.equal(rows.length,corpus.canons.flatMap(c=>c.tokens.map(t=>normalize(c.la.slice(t[0],t[1])))).filter(f=>f==='legibus').length);
 assert.ok(getOccurrences(index,'lex',1).every(o=>o.book===1));
 assert.equal(searchEntries(index,'zzzzzzz').length,0);
});
test('Source boundary cases and amended Book VI are retained',()=>{
 assert.match(corpus.canons[1666].la,/Probationibus collectis/);
 assert.match(corpus.canons[1310].la,/§ 2/);
 assert.match(corpus.canons[1310].en,/§2|§ 2/);
 assert.match(corpus.canons[5].la,/4°/);
 assert.match(corpus.canons[1751].la,/salute animarum/);
});
test('CSV preserves quotes and multiline text',()=>{assert.equal(csv([['a"b','line\nbreak']]),'"a""b","line\nbreak"');assert.equal(normalize('JŪRIS'),'iuris');});
