// Drive simulado para exercitar Code.gs fora do Google.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const path = require('path');
const DIR = process.argv[2] || '/tmp/p45teste';
let seq = 0; const porId = {};
const it = (arr) => { let i = 0; return { hasNext: () => i < arr.length, next: () => arr[i++] }; };
function pasta(nome, pai) {
  const f = { tipo: 'pasta', id: 'pasta' + String(++seq).padStart(12, '0'), nome, filhos: [], pai };
  if (nome === 'RAIZ') f.id = '1WvZVfl0Ej6-fvP5pYQAqR20ah2rvCQsw';
  porId[f.id] = f; if (pai) pai.filhos.push(f); return f;
}
function arq(nome, pai, conteudo, mime) {
  const f = { tipo: 'arq', id: 'arq' + String(++seq).padStart(14, '0'), nome, pai, conteudo: conteudo || Buffer.from('x'), mime: mime || 'application/octet-stream' };
  porId[f.id] = f; pai.filhos.push(f); return f;
}
const embrulhar = (f) => f.tipo === 'pasta' ? Pasta(f) : Arquivo(f);
const Pasta = (f) => ({
  getId: () => f.id, getName: () => f.nome, getUrl: () => 'https://drive.google.com/drive/folders/' + f.id, isTrashed: () => false,
  getFiles: () => it(f.filhos.filter(x => x.tipo === 'arq').map(Arquivo)),
  getFolders: () => it(f.filhos.filter(x => x.tipo === 'pasta').map(Pasta)),
  getFoldersByName: (n) => it(f.filhos.filter(x => x.tipo === 'pasta' && x.nome === n).map(Pasta)),
  createFile: (blob) => Arquivo(arq(blob.nome, f, blob.bytes, blob.mime)),
});
const Arquivo = (f) => ({
  getId: () => f.id, getName: () => f.nome, getMimeType: () => f.mime, getSize: () => f.conteudo.length,
  getLastUpdated: () => new Date(2026, 10, 1), isTrashed: () => false, getParents: () => it([Pasta(f.pai)]),
  getBlob: () => ({ getDataAsString: () => f.conteudo.toString('utf8') }), getTargetId: () => f.alvo, getUrl: () => 'https://drive.google.com/file/d/' + f.id,
});
const raiz = pasta('RAIZ');
const processos = pasta('Processos', raiz);
const p1 = pasta('0054293-43.2024.8.17.2001', processos);
const midias = pasta('Mídias', p1), mp3 = pasta('Mp3', p1), transc = pasta('Transcrições', p1), txt = pasta('TXT', p1), ocr = pasta('OCR', p1);
const nomeTxt = '0054293-43.2024.8.17.2001 - MARIA JOSE DA SILVA - 00542934320248172001_2026_02_26_0001.txt';
arq('00542934320248172001_2026_02_26_0001.mp4', midias, fs.readFileSync(DIR + '/00542934320248172001_2026_02_26_0001.mp4'), 'video/mp4');
arq('00542934320248172001_2026_02_26_0001.mp3', mp3, fs.readFileSync(DIR + '/00542934320248172001_2026_02_26_0001.mp3'), 'audio/mpeg');
arq(nomeTxt, transc, fs.readFileSync(DIR + '/' + nomeTxt), 'text/plain');
arq('MARIA JOSE DA SILVA-00542934320248172001_2026_02_26_0001.pdf', transc, null, 'application/pdf');
const nomeTxt2 = '0054293-43.2024.8.17.2001 - JOAO PEREIRA DOS SANTOS - 00542934320248172001_2026_02_26_0002.txt';
arq('00542934320248172001_2026_02_26_0002.mp3', mp3, fs.readFileSync(DIR + '/00542934320248172001_2026_02_26_0002.mp3'), 'audio/mpeg');
arq(nomeTxt2, transc, fs.readFileSync(DIR + '/' + nomeTxt2), 'text/plain');
arq('0054293-43.2024.8.17.2001 resumido.txt', txt, Buffer.from('RESUMO AIJ\n[RESUMO]\ntexto'), 'text/plain');
arq('autos.pdf', ocr, null, 'application/pdf');
// pasta de ato depois de "distribuir": arquivos de outro processo soltos
const aud = pasta('Audiências', raiz), dia = pasta('12-11', aud), hora = pasta('08h30', dia);
arq('00951113720248172001_2026_11_12_0001.mp4', hora, Buffer.from('video'), 'video/mp4');
arq('0095111-37.2024.8.17.2001 - JOAO - 00951113720248172001_2026_11_12_0001.txt', hora,
  Buffer.from('ARQUIVO: 00951113720248172001_2026_11_12_0001\n[TRANSCRICAO]\n00:00:01 | Juiz | a\n00:00:02 | MP | b\n00:00:03 | Juiz | c\n'), 'text/plain');
arq('0099999-99.2024.8.17.2001 outro.mp4', hora, Buffer.from('x'), 'video/mp4');

const J = (x) => JSON.parse(JSON.stringify(x));
const todos = () => Object.values(porId);
const props = {}, cache = {};
const ctx = {
  DriveApp: {
    getFolderById: (id) => { const f = porId[id]; if (!f || f.tipo !== 'pasta') throw new Error('nao achei'); return Pasta(f); },
    getFileById: (id) => { const f = porId[id]; if (!f || f.tipo !== 'arq') throw new Error('nao achei'); return Arquivo(f); },
    searchFolders: (q) => { const n = /title = '(.*)' and/.exec(q)[1]; return it(todos().filter(f => f.tipo === 'pasta' && f.nome === n).map(Pasta)); },
    searchFiles: (q) => { const n = /title contains '(.*)' and/.exec(q)[1]; ctx.__buscas.push(n); return it(todos().filter(f => f.tipo === 'arq' && f.nome.indexOf(n) === 0).map(Arquivo)); },
  },
  CacheService: { getScriptCache: () => ({ get: (k) => cache[k] || null, put: (k, v) => { cache[k] = v; } }) },
  PropertiesService: { getUserProperties: () => ({ getProperty: (k) => props[k] || null, setProperty: (k, v) => { props[k] = v; }, deleteProperty: (k) => { delete props[k]; } }) },
  Session: { getActiveUser: () => ({ getEmail: () => 'teste@mppe.mp.br' }) },
  ScriptApp: { getOAuthToken: () => 'token-de-teste' },
  Utilities: { newBlob: (bytes, mime, nome) => ({ bytes: Buffer.from(bytes), mime, nome }), base64Decode: (b) => Buffer.from(b, 'base64') },
  HtmlService: { XFrameOptionsMode: { DEFAULT: 'D' }, createHtmlOutputFromFile: (n) => { const o = { setTitle: () => o, addMetaTag: () => o, setXFrameOptionsMode: () => o, arquivo: n }; return o; } },
  __buscas: [],
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Code.gs'), 'utf8'), ctx);

// 1. processo na pasta Processos (sem link do índice)
let r = J(ctx.carregarProcesso('0054293-43.2024.8.17.2001', ''));
assert.strictEqual(r.numero, '0054293-43.2024.8.17.2001');
assert.ok(r.pasta && r.pasta.id === p1.id, 'achou a pasta do processo pela raiz');
assert.deepStrictEqual(r.midias.map(m => m.kind + ':' + m.pasta).sort(), ['audio:Mp3', 'audio:Mp3', 'video:Mídias']);
assert.strictEqual(r.transcricoes.length, 2, 'só as transcrições (não o resumido.txt)');
assert.ok(r.transcricoes[0].texto.includes('[TRANSCRICAO]'));
assert.ok(!JSON.stringify(r).includes('autos.pdf'), 'OCR não é percorrida');
assert.strictEqual(r.email, 'teste@mppe.mp.br');
console.log('1 ok: pasta pela raiz', r.midias.length, 'mídias,', r.transcricoes.length, 'transcrição');

// 2. link do índice tem prioridade
r = J(ctx.carregarProcesso('00542934320248172001', p1.id));
assert.strictEqual(r.pastas[0].origem, 'indice');
console.log('2 ok: número sem máscara + link do índice');

// 3. arquivos soltos numa pasta de ato (sem pasta do processo)
r = J(ctx.carregarProcesso('0095111-37.2024.8.17.2001', ''));
assert.strictEqual(r.pasta, null);
assert.deepStrictEqual(r.midias.map(m => m.nome), ['00951113720248172001_2026_11_12_0001.mp4']);
assert.strictEqual(r.transcricoes.length, 1);
assert.strictEqual(r.midias[0].pasta, '08h30');
console.log('3 ok: arquivos soltos pela busca do número; outro processo ignorado');

// 4. número inválido
assert.throws(() => ctx.carregarProcesso('123', ''), /inválido/);
// 5. marcações
assert.deepStrictEqual(JSON.parse(JSON.stringify(ctx.lerMarcas('0054293-43.2024.8.17.2001'))), {});
ctx.salvarMarcas('0054293-43.2024.8.17.2001', { 'midia a': ['27-abc', '34-def', 5], 'vazia': [] });
assert.deepStrictEqual(JSON.parse(JSON.stringify(ctx.lerMarcas('0054293-43.2024.8.17.2001'))), { 'midia a': ['27-abc', '34-def'] });
ctx.salvarMarcas('0054293-43.2024.8.17.2001', {});
assert.strictEqual(props['marcas:0054293-43.2024.8.17.2001'], undefined);
const muitas = { m: Array.from({ length: 900 }, (_, i) => i + '-abcdefg') };
assert.throws(() => ctx.salvarMarcas('0054293-43.2024.8.17.2001', muitas), /demais/);
console.log('5 ok: marcações por usuário');
// 6. salvar PDF
const s = ctx.salvarPdf(p1.id, 'a/b: trechos', Buffer.from('%PDF-1.4 teste').toString('base64'));
assert.strictEqual(s.nome, 'a-b- trechos.pdf');
assert.ok(p1.filhos.some(f => f.nome === 'a-b- trechos.pdf' && f.conteudo.toString().startsWith('%PDF')));
assert.throws(() => ctx.salvarPdf('../x', 'n', 'AA=='), /inválida/);
console.log('6 ok: PDF salvo na pasta');
// 7. doGet e token
assert.strictEqual(ctx.doGet().arquivo, 'Player');
assert.strictEqual(ctx.tokenDrive().token, 'token-de-teste');
console.log('7 ok: doGet/token');
fs.writeFileSync(path.join(DIR, 'carregar.json'), JSON.stringify(ctx.carregarProcesso('0054293-43.2024.8.17.2001', p1.id)));
console.log('TODOS OS TESTES DO SERVIDOR PASSARAM');
