/**
 * Player de mídias das audiências — 45ª Promotoria de Justiça Criminal da Capital.
 *
 * App da Web do Google Apps Script, publicado numa conta Google pessoal com
 * a pasta "Material de Preparação" do MPPE compartilhada com ela:
 *   Executar como: "Usuário que acessa o app da Web"
 *   Quem pode acessar: "Qualquer pessoa com Conta do Google"
 * Cada pessoa entra com a própria conta e só enxerga o que essa conta já
 * enxerga no Drive. Quem abrir o endereço sem ter a pasta compartilhada não
 * vê nada. Nenhuma mídia ou transcrição fica pública.
 *
 * O que o servidor faz:
 *   - acha a pasta do processo (link do índice da página inicial, pasta raiz
 *     sincronizada ou busca pelo nome) e lista mídias e transcrições;
 *   - lê o texto das transcrições (.txt);
 *   - entrega à página o token da própria pessoa, para ela baixar a mídia
 *     direto do Drive;
 *   - guarda as marcações de trechos por pessoa (valem em qualquer computador);
 *   - salva o PDF de trechos na pasta do processo, quando pedido.
 */

/** Pasta "Material de Preparação" (a mesma sincronizada com o computador e
    compartilhada com a conta pessoal). Se a conta não tiver acesso a ela, o
    app ainda acha os processos pelo índice da página inicial e pela busca. */
var PASTA_RAIZ = '1WvZVfl0Ej6-fvP5pYQAqR20ah2rvCQsw';

var EXT_VIDEO = ['mp4', 'm4v', 'mov', 'webm', 'mkv', 'avi', 'mpg', 'mpeg', 'wmv', 'asf', '3gp'];
var EXT_AUDIO = ['mp3', 'm4a', 'wav', 'ogg', 'oga', 'aac', 'opus', 'wma'];
/* Pastas que só guardam PDFs dos autos: não precisam ser percorridas. */
var PASTAS_IGNORADAS = ['ocr', 'processo fracionado'];
var LIMITE_TXT = 5 * 1024 * 1024;

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Player')
    .setTitle('Mídias das audiências • 45ª Promotoria')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}

/** Token OAuth de quem está usando a página (nunca o do autor do script). */
function tokenDrive() {
  return { token: ScriptApp.getOAuthToken(), email: Session.getActiveUser().getEmail() };
}

function numeroCanonico(valor) {
  var m = String(valor || '').match(/(\d{1,7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})/);
  if (!m) {
    var d = String(valor || '').replace(/\D/g, '');
    if (d.length !== 20) return '';
    m = [d, d.slice(0, 7), d.slice(7, 9), d.slice(9, 13), d.slice(13, 14), d.slice(14, 16), d.slice(16, 20)];
  }
  return ('0000000' + m[1]).slice(-7) + '-' + m[2] + '.' + m[3] + '.' + m[4] + '.' + m[5] + '.' + m[6];
}

function semAcento(texto) {
  return String(texto || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
}

function extensao(nome) {
  var m = /\.([a-z0-9]{1,5})$/i.exec(nome || '');
  return m ? m[1].toLowerCase() : '';
}

/* Relatório "<mídia> - verificação.txt" do painel: tem linhas no formato das
   falas ("HH:MM:SS | Horário aproximado | ..."), mas não é a transcrição. */
function ehRelatorio(nome, texto) {
  return /verificacao/.test(semAcento(nome)) || /^\s*VERIFICA(?:C|Ç)(?:A|Ã)O DA TRANSCRI/i.test(texto || '');
}

/**
 * Separa mídias, transcrições e PDFs de transcrição.
 * lerTexto(a) devolve o conteúdo de um .txt. Os PDFs voltam só quando o nome
 * contém o nome de uma mídia ("NOME DO DEPOENTE-<mídia>.pdf"): é de onde a
 * página tira o nome de quem depõe.
 */
function classificar(lista, lerTexto) {
  var midias = [], transcricoes = [], pdfs = [];
  lista.forEach(function (a) {
    var ext = extensao(a.nome);
    var info = { id: a.id, nome: a.nome, tipo: a.tipo, tamanho: a.tamanho, atualizado: a.atualizado, pasta: a.pasta };
    if (EXT_VIDEO.indexOf(ext) !== -1 || /^video\//.test(a.tipo)) { info.kind = 'video'; midias.push(info); }
    else if (EXT_AUDIO.indexOf(ext) !== -1 || /^audio\//.test(a.tipo)) { info.kind = 'audio'; midias.push(info); }
    else if (ext === 'pdf') pdfs.push(info);
    else if (ext === 'txt' || a.tipo === 'text/plain') {
      if (/resumido\.txt$/i.test(a.nome) || a.tamanho > LIMITE_TXT || ehRelatorio(a.nome)) return;
      var texto = lerTexto(a);
      if (ehRelatorio(a.nome, texto) || !pareceTranscricao(texto)) return;
      info.texto = texto;
      transcricoes.push(info);
    }
  });
  var nomesMidia = midias.map(function (m) { return semAcento(m.nome.replace(/\.[a-z0-9]{1,5}$/i, '')); });
  pdfs = pdfs.filter(function (p) {
    var n = semAcento(p.nome);
    return nomesMidia.some(function (m) { return m && n.indexOf(m) !== -1; });
  });
  return { midias: midias, transcricoes: transcricoes, pdfs: pdfs };
}

function pareceTranscricao(texto) {
  if (/^\s*\[TRANSCRI(?:C|Ç)(?:A|Ã)O\]\s*$/mi.test(texto)) return true;
  var falas = texto.match(/^\s*\d{1,2}:\d{2}(?::\d{2})?\s*\|[^|\n]*\|/gm);
  return !!falas && falas.length >= 3;
}

/* Pastas "Processos" e "Fora de Pauta" da raiz: descobertas uma vez e
   guardadas por 6 horas (os IDs não mudam quando as pastas são movidas). */
function pastasBase() {
  var cache = CacheService.getScriptCache();
  var guardado = cache.get('pastas-base');
  if (guardado) {
    var ids = JSON.parse(guardado);
    var pastas = [];
    ids.forEach(function (id) { try { pastas.push(DriveApp.getFolderById(id)); } catch (e) {} });
    if (pastas.length) return pastas;
  }
  var raiz;
  try { raiz = DriveApp.getFolderById(PASTA_RAIZ); } catch (e) { return []; }
  var achadas = [raiz];
  var procurar = function (pasta) {
    ['Processos', 'Fora de Pauta'].forEach(function (nome) {
      var it = pasta.getFoldersByName(nome);
      while (it.hasNext()) achadas.push(it.next());
    });
  };
  procurar(raiz);
  if (achadas.length === 1) {
    /* A raiz pode estar um nível acima de "Material de Preparação". */
    var filhas = raiz.getFolders(), k = 0;
    while (filhas.hasNext() && k++ < 40) procurar(filhas.next());
  }
  cache.put('pastas-base', JSON.stringify(achadas.map(function (p) { return p.getId(); })), 21600);
  return achadas;
}

function percorrer(pasta, nivel, adicionar) {
  var arquivos = pasta.getFiles();
  while (arquivos.hasNext()) adicionar(arquivos.next(), pasta.getName());
  if (nivel >= 3) return;
  var filhas = pasta.getFolders();
  while (filhas.hasNext()) {
    var filha = filhas.next();
    if (PASTAS_IGNORADAS.indexOf(semAcento(filha.getName())) !== -1) continue;
    percorrer(filha, nivel + 1, adicionar);
  }
}

/* ------------------------------------------------------------------
   Leitura pela Drive API (serviço avançado "Drive"): traz a pasta inteira
   em uma consulta, em vez de um pedido por arquivo do DriveApp. Cai para o
   DriveApp só se o serviço avançado não estiver ativado no projeto.
   ------------------------------------------------------------------ */
var MIME_PASTA = 'application/vnd.google-apps.folder';
var MIME_ATALHO = 'application/vnd.google-apps.shortcut';
var CAMPOS_LISTA = 'nextPageToken, files(id, name, mimeType, size, modifiedTime, parents, trashed, shortcutDetails, webViewLink)';
var CAMPOS_ITEM = 'id, name, mimeType, size, modifiedTime, parents, trashed, shortcutDetails, webViewLink';

function temDriveApi() {
  return typeof Drive !== 'undefined' && Drive.Files && typeof Drive.Files.list === 'function';
}
function aspas(texto) { return String(texto).replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }
function listarDrive(q) {
  var saida = [], pagina;
  do {
    var r = Drive.Files.list({ q: q, fields: CAMPOS_LISTA, pageSize: 1000, pageToken: pagina, supportsAllDrives: true, includeItemsFromAllDrives: true });
    (r.files || []).forEach(function (f) { saida.push(f); });
    pagina = r.nextPageToken;
  } while (pagina && saida.length < 5000);
  return saida;
}
/** Itens dentro de várias pastas de uma vez (40 pastas por consulta). */
function filhosDe(ids, extra) {
  var saida = [];
  for (var i = 0; i < ids.length; i += 40) {
    var q = '(' + ids.slice(i, i + 40).map(function (id) { return "'" + aspas(id) + "' in parents"; }).join(' or ') + ') and trashed = false';
    saida = saida.concat(listarDrive(extra ? q + ' and ' + extra : q));
  }
  return saida;
}
function itemDrive(id) {
  try { return Drive.Files.get(id, { fields: CAMPOS_ITEM, supportsAllDrives: true }); } catch (e) { return null; }
}
/* IDs das pastas "Processos" e "Fora de Pauta", guardados por 6 horas. */
function basesApi() {
  var cache = CacheService.getScriptCache(), guardado = cache.get('pastas-base-api');
  if (guardado) return JSON.parse(guardado);
  var nomes = "(name = 'Processos' or name = 'Fora de Pauta') and mimeType = '" + MIME_PASTA + "'";
  var achadas = filhosDe([PASTA_RAIZ], nomes);
  if (!achadas.length) {
    /* A raiz pode estar um nível acima de "Material de Preparação". */
    var filhas = filhosDe([PASTA_RAIZ], "mimeType = '" + MIME_PASTA + "'").slice(0, 40).map(function (f) { return f.id; });
    if (filhas.length) achadas = filhosDe(filhas, nomes);
  }
  var ids = [PASTA_RAIZ].concat(achadas.map(function (f) { return f.id; }));
  cache.put('pastas-base-api', JSON.stringify(ids), 21600);
  return ids;
}

function carregarProcessoApi(n, pastaId) {
  var digitos = n.replace(/\D/g, '');
  var pastas = [];
  var addPasta = function (f, origem) {
    if (!f || f.trashed || f.mimeType !== MIME_PASTA) return;
    if (pastas.some(function (p) { return p.id === f.id; })) return;
    pastas.push({ id: f.id, nome: f.name, url: f.webViewLink || 'https://drive.google.com/drive/folders/' + f.id, origem: origem });
  };
  if (pastaId && /^[A-Za-z0-9_-]{10,200}$/.test(pastaId)) addPasta(itemDrive(pastaId), 'indice');
  if (!pastas.length) {
    filhosDe(basesApi(), "name = '" + aspas(n) + "' and mimeType = '" + MIME_PASTA + "'").forEach(function (f) { addPasta(f, 'raiz'); });
  }
  if (!pastas.length) {
    listarDrive("name = '" + aspas(n) + "' and mimeType = '" + MIME_PASTA + "' and trashed = false").slice(0, 10).forEach(function (f) { addPasta(f, 'busca'); });
  }

  var nomesPasta = {}, arquivos = {};
  pastas.forEach(function (p) { nomesPasta[p.id] = p.nome; });
  var adicionar = function (f) {
    if (f.mimeType === MIME_ATALHO) {
      var alvo = f.shortcutDetails && f.shortcutDetails.targetId ? itemDrive(f.shortcutDetails.targetId) : null;
      if (!alvo) return;
      alvo.parents = f.parents;
      f = alvo;
    }
    if (f.trashed || f.mimeType === MIME_PASTA || arquivos[f.id]) return;
    arquivos[f.id] = {
      id: f.id, nome: f.name, tipo: f.mimeType, tamanho: Number(f.size) || 0,
      atualizado: Date.parse(f.modifiedTime) || 0,
      pasta: nomesPasta[(f.parents || [])[0]] || ''
    };
  };
  /* Pasta do processo e subpastas, um nível por consulta (até 3 níveis). */
  var nivel = pastas.map(function (p) { return p.id; });
  for (var prof = 0; prof <= 3 && nivel.length; prof++) {
    var proximo = [];
    filhosDe(nivel).forEach(function (f) {
      if (f.mimeType === MIME_PASTA) {
        if (PASTAS_IGNORADAS.indexOf(semAcento(f.name)) === -1 && !nomesPasta[f.id]) { nomesPasta[f.id] = f.name; proximo.push(f.id); }
        return;
      }
      adicionar(f);
    });
    nivel = proximo;
  }
  /* Arquivos com o número no nome em qualquer pasta (pastas de ato depois
     de "distribuir", com mídias de vários processos juntas). */
  listarDrive("name contains '" + digitos.slice(0, 7) + "' and trashed = false and mimeType != '" + MIME_PASTA + "'").forEach(function (f) {
    if (f.name.indexOf(n) !== -1 || f.name.indexOf(digitos) !== -1) adicionar(f);
  });

  var c = classificar(Object.keys(arquivos).map(function (id) { return arquivos[id]; }), function (a) {
    return DriveApp.getFileById(a.id).getBlob().getDataAsString('UTF-8');
  });
  var principal = pastas[0] || null;
  return {
    numero: n,
    pasta: principal ? { id: principal.id, nome: principal.nome, url: principal.url } : null,
    pastas: pastas.map(function (p) { return { id: p.id, nome: p.nome, origem: p.origem }; }),
    midias: c.midias,
    transcricoes: c.transcricoes,
    pdfs: c.pdfs,
    email: Session.getActiveUser().getEmail()
  };
}

/**
 * Mídias e transcrições de um processo.
 * @param {string} numero número do processo (com ou sem máscara)
 * @param {string} pastaId ID da pasta do processo, vindo do índice da página inicial (opcional)
 */
function carregarProcesso(numero, pastaId) {
  var n = numeroCanonico(numero);
  if (!n) throw new Error('Número de processo inválido.');
  return temDriveApi() ? carregarProcessoApi(n, pastaId) : carregarProcessoDriveApp(n, pastaId);
}

/* Caminho antigo (DriveApp), mais lento: um pedido ao Drive por arquivo. */
function carregarProcessoDriveApp(numero, pastaId) {
  var n = numeroCanonico(numero);
  if (!n) throw new Error('Número de processo inválido.');
  var digitos = n.replace(/\D/g, '');

  var pastas = [], vistas = {};
  var addPasta = function (pasta, origem) {
    if (!pasta || pasta.isTrashed() || vistas[pasta.getId()]) return;
    vistas[pasta.getId()] = true;
    pastas.push({ pasta: pasta, origem: origem });
  };
  if (pastaId && /^[A-Za-z0-9_-]{10,200}$/.test(pastaId)) {
    try { addPasta(DriveApp.getFolderById(pastaId), 'indice'); } catch (e) {}
  }
  if (!pastas.length) {
    pastasBase().forEach(function (base) {
      var it = base.getFoldersByName(n);
      while (it.hasNext()) addPasta(it.next(), 'raiz');
    });
  }
  if (!pastas.length) {
    var busca = DriveApp.searchFolders("title = '" + n + "' and trashed = false"), k = 0;
    while (busca.hasNext() && k++ < 10) addPasta(busca.next(), 'busca');
  }

  var arquivos = {};
  var adicionar = function (arquivo, nomePasta) {
    if (arquivo.getMimeType() === 'application/vnd.google-apps.shortcut') {
      try { arquivo = DriveApp.getFileById(arquivo.getTargetId()); } catch (e) { return; }
    }
    var id = arquivo.getId();
    if (arquivos[id] || arquivo.isTrashed()) return;
    arquivos[id] = {
      id: id,
      nome: arquivo.getName(),
      tipo: arquivo.getMimeType(),
      tamanho: arquivo.getSize(),
      atualizado: arquivo.getLastUpdated().getTime(),
      pasta: nomePasta || '',
      arquivo: arquivo
    };
  };
  pastas.forEach(function (p) { percorrer(p.pasta, 0, adicionar); });

  /* Depois de "distribuir", mídias de vários processos podem dividir a mesma
     pasta do ato (Audiências/DD-MM/HHhMM). Elas levam o número no nome. */
  var soltos = DriveApp.searchFiles("title contains '" + digitos.slice(0, 7) + "' and trashed = false"), j = 0;
  while (soltos.hasNext() && j++ < 300) {
    var f = soltos.next(), nome = f.getName();
    if (nome.indexOf(n) === -1 && nome.indexOf(digitos) === -1) continue;
    var nomePasta = '';
    try { var pais = f.getParents(); if (pais.hasNext()) nomePasta = pais.next().getName(); } catch (e) {}
    adicionar(f, nomePasta);
  }

  var c = classificar(Object.keys(arquivos).map(function (id) { return arquivos[id]; }), function (a) {
    return a.arquivo.getBlob().getDataAsString('UTF-8');
  });

  var principal = pastas.length ? pastas[0].pasta : null;
  return {
    numero: n,
    pasta: principal ? { id: principal.getId(), nome: principal.getName(), url: principal.getUrl() } : null,
    pastas: pastas.map(function (p) { return { id: p.pasta.getId(), nome: p.pasta.getName(), origem: p.origem }; }),
    midias: c.midias,
    transcricoes: c.transcricoes,
    pdfs: c.pdfs,
    email: Session.getActiveUser().getEmail()
  };
}

/* Marcações de trechos: guardadas na conta de cada pessoa (Propriedades do
   usuário), por processo. Valem em qualquer computador. */
function lerMarcas(numero) {
  var n = numeroCanonico(numero);
  if (!n) return {};
  var valor = PropertiesService.getUserProperties().getProperty('marcas:' + n);
  return valor ? JSON.parse(valor) : {};
}

function salvarMarcas(numero, dados) {
  var n = numeroCanonico(numero);
  if (!n) throw new Error('Número de processo inválido.');
  var limpo = {};
  Object.keys(dados || {}).forEach(function (midia) {
    if (!Array.isArray(dados[midia]) || String(midia).length > 200) return;
    var chaves = dados[midia].filter(function (c) { return typeof c === 'string' && c.length <= 40; });
    if (chaves.length) limpo[midia] = chaves;
  });
  var json = JSON.stringify(limpo);
  var props = PropertiesService.getUserProperties();
  if (json === '{}') { props.deleteProperty('marcas:' + n); return true; }
  if (json.length > 8500) throw new Error('Há marcações demais para guardar neste processo.');
  props.setProperty('marcas:' + n, json);
  return true;
}

/** Salva o PDF de trechos na pasta do processo. */
function salvarPdf(pastaId, nome, base64) {
  if (!/^[A-Za-z0-9_-]{10,200}$/.test(String(pastaId || ''))) throw new Error('Pasta do processo inválida.');
  nome = String(nome || 'trechos selecionados').replace(/[\\/:*?"<>|]+/g, '-').slice(0, 180);
  if (!/\.pdf$/i.test(nome)) nome += '.pdf';
  var blob = Utilities.newBlob(Utilities.base64Decode(base64), 'application/pdf', nome);
  var arquivo = DriveApp.getFolderById(pastaId).createFile(blob);
  return { url: arquivo.getUrl(), nome: arquivo.getName() };
}
