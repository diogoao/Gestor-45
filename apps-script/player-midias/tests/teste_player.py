import json, re, sys, time, pathlib
AQUI = pathlib.Path(__file__).resolve().parent
REPO = AQUI.parents[2]
DIR = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/p45teste')
from playwright.sync_api import sync_playwright
PLAYER = (AQUI.parent / 'Player.html').read_text(encoding='utf-8')
JSPDF = (REPO / 'Gestor MP' / 'vendor' / 'jspdf.umd.min.js').read_text(encoding='utf-8')
CARREGAR = json.load(open(DIR / 'carregar.json'))
atos = json.load(open(REPO / 'Gestor MP' / 'atos-importados.json'))
atos['events'].append({"number": "0054293-43.2024.8.17.2001", "date": "2026-11-18", "time": "09:00", "day": 18, "category": "audiencias"})
indice = json.load(open(REPO / 'Gestor MP' / 'indice-processos.json'))
indice['processos'].append({"numero": "0054293-43.2024.8.17.2001", "url": "https://drive.google.com/drive/folders/" + CARREGAR['pasta']['id']})
publicacao = {"version": 1, "events": atos['events'], "processos": indice['processos']}
OUT = (DIR / 'saida'); OUT.mkdir(exist_ok=True)

PDFJS = REPO / 'Gestor MP' / 'vendor' / 'pdfjs'
MOCK = """
window.P45_TESTE = { driveApi: 'http://127.0.0.1:8766', pdfjs: [{ lib: '/pdfjs/pdf.min.mjs', worker: '/pdfjs/pdf.worker.min.mjs' }] };
window.__chamadas = [];
window.__marcas = JSON.parse(sessionStorage.getItem('mock_marcas') || '{}');
(function(){
  const dados = %s;
  const backend = {
    carregarProcesso: (n, pasta) => { window.__chamadas.push(['carregarProcesso', n, pasta]); return new Promise(r => setTimeout(() => r(dados), 300)); },
    tokenDrive: () => ({ token: 'token-de-teste', email: 'teste@mppe.mp.br' }),
    lerMarcas: (n) => window.__marcas[n] || {},
    salvarMarcas: (n, d) => { window.__chamadas.push(['salvarMarcas', n, JSON.parse(JSON.stringify(d))]); window.__marcas[n] = d; sessionStorage.setItem('mock_marcas', JSON.stringify(window.__marcas)); return true; },
    salvarPdf: (p, nome, b64) => { window.__chamadas.push(['salvarPdf', p, nome, b64.length]); return { url: 'https://drive.google.com/file/d/x', nome }; },
  };
  function runner(ok, falha) {
    return new Proxy({}, { get(_, nome) {
      if (nome === 'withSuccessHandler') return (f) => runner(f, falha);
      if (nome === 'withFailureHandler') return (f) => runner(ok, f);
      return (...args) => { Promise.resolve().then(() => backend[nome](...args)).then(v => ok && ok(v), e => falha && falha(e)); };
    }});
  }
  window.google = { script: { run: runner(null, null), url: { getLocation: (cb) => cb({ parameter: {} }) }, history: { replace(){} } } };
})();
"""
SO_PDF = dict(CARREGAR, transcricoes=[])     # pasta só com os PDFs das transcrições (sem os .txt)

erros = []
with sync_playwright() as p:
    nav = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--autoplay-policy=no-user-gesture-required', '--disable-features=LocalNetworkAccessChecks,PrivateNetworkAccessSendPreflights,PrivateNetworkAccessRespectPreflightResults,BlockInsecurePrivateNetworkRequests'])
    ctx = nav.new_context(viewport={'width': 1440, 'height': 900}, accept_downloads=True, timezone_id='America/Recife')
    ctx.add_init_script(MOCK % json.dumps(CARREGAR))
    def rotas(route):
        u = route.request.url
        if u.startswith('http://127.0.0.1:8767/pdfjs/'): return route.fulfill(body=(PDFJS / u.rsplit('/', 1)[-1]).read_bytes(), content_type='text/javascript')
        if u.startswith('http://127.0.0.1:8767/'): return route.fulfill(body=PLAYER, content_type='text/html; charset=utf-8')
        if 'getAtosPublicados' in u: return route.fulfill(body=json.dumps(publicacao), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        if 'getPauta' in u: return route.fulfill(body=json.dumps({"error": "teste"}), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        if 'jspdf.umd.min.js' in u: return route.fulfill(body=JSPDF, content_type='application/javascript')
        if 'fonts.g' in u or 'raw.githubusercontent' in u: return route.abort()
        return route.continue_()
    ctx.route('**/*', rotas)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and erros.append('console: ' + m.text))
    pg.goto('http://127.0.0.1:8767/player.html')
    pg.wait_for_selector('.proc')
    nums = pg.eval_on_selector_all('.proc', 'els => els.map(e => e.dataset.chave)')
    datas = sorted({c.split('|')[1] for c in nums})
    print('processos na lista:', len(nums), '| datas:', datas[0], '→', datas[-1])
    import datetime, zoneinfo
    hoje = datetime.datetime.now(zoneinfo.ZoneInfo('America/Fortaleza')).date()
    corte = (hoje - datetime.timedelta(days=5)).isoformat()
    esperados = sorted({'|'.join([e['number'], e['date'], e.get('time', '')]) for e in publicacao['events'] if e['date'] >= corte})
    assert sorted(nums) == esperados, 'lista = atos de %s em diante (corte inclusivo de 5 dias)' % corte
    print('corte inclusivo de 5 dias: desde', corte)
    pg.screenshot(path=str(OUT / '01-lista.png'))

    pg.click('.proc[data-numero="0054293-43.2024.8.17.2001"]')
    pg.wait_for_selector('.midia')
    print('mídias:', pg.eval_on_selector_all('.midia', 'els => els.map(e => e.innerText.replace(/\\n+/g," | "))'))
    nomes = pg.eval_on_selector_all('.midia-nome', 'els => els.map(e => e.textContent)')
    assert nomes == ['Maria José da Silva', 'João Pereira dos Santos'], ('nomes das mídias', nomes)
    chamada = pg.evaluate('window.__chamadas[0]')
    assert chamada[2] == CARREGAR['pasta']['id'], 'passa a pasta do índice ao servidor'
    try:
        pg.wait_for_function("document.querySelector('#video').dataset.modo === 'audio' && document.querySelector('#video').readyState >= 1", timeout=15000)
    except Exception:
        print('TOASTS:', pg.inner_text('#toasts'), '| baixando:', pg.inner_text('#baixando'), '| erros:', erros); raise
    print('falas:', pg.locator('.fala').count(), '| baixando:', pg.inner_text('#baixando'))
    assert pg.locator('.fala').count() == 24 and pg.inner_text('.fala[data-i="0"] .quem') == 'Juiz', 'usa a transcrição, não o relatório de verificação'
    assert not pg.locator('#capa').is_hidden(), 'capa de áudio visível enquanto o vídeo baixa'
    pg.screenshot(path=str(OUT / '02-audio-baixando.png'))

    # Clicar na fala das 00:00:27 (reconhecimento)
    pg.click('.fala[data-i="7"] .texto')
    time.sleep(0.6)
    t = pg.evaluate('document.querySelector("#video").currentTime')
    ativo = pg.evaluate('document.querySelector(".fala.atual").dataset.i')
    print('após clicar na fala 7: currentTime=%.2f, card atual=%s, tocando=%s' % (t, ativo, not pg.evaluate('document.querySelector("#video").paused')))
    assert 27 <= t < 29.5 and ativo == '7'

    # Troca para o vídeo no mesmo ponto
    pg.wait_for_function("document.querySelector('#video').dataset.modo === 'video' && document.querySelector('#video').videoWidth > 0", timeout=30000)
    time.sleep(0.8)
    t2 = pg.evaluate('document.querySelector("#video").currentTime')
    print('trocou para o vídeo: currentTime=%.2f, largura=%s, capa escondida=%s' % (t2, pg.evaluate('document.querySelector("#video").videoWidth'), pg.locator('#capa').is_hidden()))
    assert t2 >= 27, 'a troca manteve o ponto'
    pg.screenshot(path=str(OUT / '03-video.png'))

    # Velocidade 2x: o tempo anda o dobro e a lista sobe sozinha
    pg.click('#velocidades button[data-v="2"]')
    v0, s0, i0 = pg.evaluate('[document.querySelector("#video").currentTime, document.querySelector("#falas").scrollTop, document.querySelector(".fala.atual").dataset.i]')
    time.sleep(4)
    v1, s1, i1, taxa = pg.evaluate('[document.querySelector("#video").currentTime, document.querySelector("#falas").scrollTop, document.querySelector(".fala.atual").dataset.i, document.querySelector("#video").playbackRate]')
    print('2x: %.1fs de vídeo em 4s reais | card %s → %s | rolagem %d → %d px | taxa=%s' % (v1 - v0, i0, i1, s0, s1, taxa))
    assert taxa == 2 and 6.5 <= v1 - v0 <= 9 and int(i1) > int(i0) and s1 > s0
    assert pg.get_attribute('#velocidades button[data-v="2"]', 'aria-pressed') == 'true'

    # Rolagem manual solta o acompanhamento; o botão volta a acompanhar
    pg.hover('#falas'); pg.mouse.wheel(0, -400); time.sleep(0.5)
    assert pg.locator('#seguirBtn').is_visible()
    s_parado = pg.evaluate('document.querySelector("#falas").scrollTop'); time.sleep(1.5)
    assert abs(pg.evaluate('document.querySelector("#falas").scrollTop') - s_parado) < 2, 'não briga com a rolagem manual'
    pg.click('#seguirBtn'); time.sleep(0.6)
    assert pg.locator('#seguirBtn').is_hidden()
    print('rolagem manual: acompanhamento suspenso e retomado ok')

    # 1,5x
    pg.click('#velocidades button[data-v="1.5"]')
    assert pg.evaluate('document.querySelector("#video").playbackRate') == 1.5
    # Próxima/anterior
    i_antes = int(pg.evaluate('document.querySelector(".fala.atual").dataset.i'))
    pg.click('#proxBtn'); time.sleep(0.4)
    assert int(pg.evaluate('document.querySelector(".fala.atual").dataset.i')) == i_antes + 1
    pg.evaluate('document.querySelector("#video").pause()')

    # Marcar três falas e gerar o PDF
    for i in (3, 7, 9):
        pg.click('.fala[data-i="%d"] .marcar' % i)
    pg.wait_for_function("window.__chamadas.some(c => c[0] === 'salvarMarcas')", timeout=5000)
    print('rodapé:', pg.inner_text('#contaMarcas'), '| servidor recebeu:', pg.evaluate("window.__chamadas.filter(c => c[0] === 'salvarMarcas').pop()[2]"))
    pg.click('.fala[data-i="9"] .marcar'); pg.click('.fala[data-i="9"] .marcar')   # desmarca e marca de novo
    assert pg.locator('.fala.marcada').count() == 3
    pg.screenshot(path=str(OUT / '04-marcados.png'))
    # Segunda mídia (outra pessoa, só áudio): marcar duas falas
    pg.click('.midia:has-text("João Pereira")')
    pg.wait_for_function("document.querySelectorAll('.fala').length === 6 && document.querySelector('#contaFalas').textContent.startsWith('6')", timeout=10000)
    for i in (1, 3):
        pg.click('.fala[data-i="%d"] .marcar' % i)
    print('rodapé com duas mídias:', pg.inner_text('#contaMarcas'))
    assert '5 trechos marcados no processo (2 nesta mídia)' in pg.inner_text('#contaMarcas')
    # layout: dias com o tipo à direita, vídeos dentro do processo aberto, prévia do PDF com todos os depoentes
    tipos = pg.eval_on_selector_all('.dia', 'els => els.map(e => [e.querySelector(".dia-data").textContent, [...e.querySelectorAll(".tipo")].map(t => t.textContent + ":" + t.className).join(",")])')
    assert tipos and all(t[1] for t in tipos) and all(('juri' in t[1]) == ('Júri' in t[1]) for t in tipos), tipos
    assert pg.evaluate('document.querySelector("#midias").previousElementSibling.dataset.numero') == '0054293-43.2024.8.17.2001'
    assert pg.locator('#conta').count() == 0, 'e-mail fora do cabeçalho'
    previa = pg.inner_text('#previa')
    for esperado in ('Prévia do PDF', '5 trechos marcados · 2 depoentes · 2 mídias', 'Maria José da Silva', 'João Pereira dos Santos', 'Mídia original: 00542934320248172001_2026_02_26_0001.mp4', 'Gerar PDF'):
        assert esperado in previa, ('faltou na prévia', esperado)
    assert pg.locator('#previa .previa-fala').count() == 5
    assert set(pg.evaluate('[...document.querySelectorAll("#ficha dt")].map(e => e.textContent)')) == {'Depoente', 'Data da audiência', 'Arquivo'}
    pg.click('.proc.ativo'); assert not pg.locator('#midias').is_visible(), 'clicar no processo aberto recolhe os vídeos'
    pg.click('.proc.ativo'); assert pg.locator('#midias').is_visible()
    print('layout: dias', len(tipos), '| prévia com', pg.locator('#previa .previa-fala').count(), 'trechos de 2 depoentes | recolher/abrir ok')
    with pg.expect_download() as d:
        pg.click('#pdfBtn')
    dl = d.value
    destino = OUT / dl.suggested_filename
    dl.save_as(str(destino))
    print('PDF baixado:', dl.suggested_filename)
    import subprocess
    texto = subprocess.run(['pdftotext', '-layout', str(destino), '-'], capture_output=True, text=True).stdout
    for esperado in ('Maria José da Silva', 'João Pereira dos Santos', '00542934320248172001_2026_02_26_0001.mp4', '00542934320248172001_2026_02_26_0002.mp3', '5 trechos · 2 depoentes · 2 mídias'):
        assert esperado in texto, ('faltou no PDF', esperado)
    assert texto.index('Maria José da Silva') < texto.index('João Pereira dos Santos')
    print('PDF: um arquivo para o processo, separado por depoente, com o arquivo original de cada trecho')
    pg.click('.toast button:has-text("Salvar na pasta")')
    pg.wait_for_function("window.__chamadas.some(c => c[0] === 'salvarPdf')", timeout=5000)
    print('salvar no Drive:', pg.evaluate("window.__chamadas.filter(c => c[0] === 'salvarPdf')[0]"))

    # Recarregar: marcações voltam do servidor e a posição é retomada
    pg.evaluate('localStorage.clear()')
    pg.reload(); pg.click('.proc[data-numero="0054293-43.2024.8.17.2001"]')
    pg.wait_for_selector('.fala')
    n_marc = pg.locator('.fala.marcada').count(); print('depois de recarregar (sem cache local): marcados =', n_marc); assert n_marc == 3
    pdf_visivel = pg.evaluate('(() => { const r = document.querySelector("#contaMarcas").getBoundingClientRect(); return r.bottom <= innerHeight && r.top >= 0; })()')
    print('faixa de trechos marcados visível sem rolar a página:', pdf_visivel); assert pdf_visivel
    print('nome da mídia:', pg.inner_text('.midia-nome'))

    # Tema escuro
    pg.click('#temaBtn'); time.sleep(0.4)
    pg.wait_for_function("document.querySelector('#video').readyState >= 1", timeout=15000)
    pg.screenshot(path=str(OUT / '05-escuro.png'))
    # Prévia do PDF: folha branca também no tema escuro
    assert pg.evaluate("getComputedStyle(document.querySelector('#previa')).backgroundColor") == 'rgb(255, 255, 255)'
    # Janela larga: processos e vídeo travam na largura; as falas ficam com o que sobra
    larg = lambda: pg.evaluate("['.lateral','#conteudo','.col-falas'].map(q=>Math.round(document.querySelector(q).getBoundingClientRect().width))")
    pg.set_viewport_size({'width': 1600, 'height': 900}); time.sleep(0.4); l1 = larg()
    pg.set_viewport_size({'width': 2200, 'height': 1000}); time.sleep(0.4); l2 = larg()
    pg.screenshot(path=str(OUT / '08-larga.png'))
    assert l1[:2] == l2[:2] == [315, 790] and l2[2] - l1[2] == 600, (l1, l2)
    print('janela larga: colunas', l1, '→', l2)
    # Tela estreita
    pg.set_viewport_size({'width': 820, 'height': 1000}); time.sleep(0.5)
    pg.screenshot(path=str(OUT / '06-estreita.png'), full_page=False)

    # ---------- Pasta só com os PDFs das transcrições (sem TXT) ----------
    ctx2 = nav.new_context(viewport={'width': 1440, 'height': 900}, accept_downloads=True, timezone_id='America/Recife')
    ctx2.add_init_script(MOCK % json.dumps(SO_PDF))
    ctx2.route('**/*', rotas)
    pg = ctx2.new_page()
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and erros.append('console: ' + m.text))
    pg.goto('http://127.0.0.1:8767/player.html')
    pg.wait_for_selector('.proc')
    t0 = time.time()
    pg.click('.proc[data-numero="0054293-43.2024.8.17.2001"]')
    pg.wait_for_selector('.midia')
    assert '2 mídias · 2 transcrições' in pg.inner_text('#procStatus'), pg.inner_text('#procStatus')
    assert pg.locator('.selo-p.alerta').count() == 0, 'nenhuma mídia aparece como "sem transcrição"'
    pg.wait_for_selector('.fala', timeout=20000)
    print('só PDF: falas na tela %.1f s depois do clique no processo | %s' % (time.time() - t0, pg.inner_text('#contaFalas')))
    assert pg.locator('.fala').count() == 24 and 'lidas do PDF' in pg.inner_text('#contaFalas')
    assert pg.inner_text('.fala[data-i="0"] .quem') == 'Juiz' and pg.inner_text('.fala[data-i="0"] .hora') == '00:00:02'
    assert 'Declaro aberta a audiência de instrução e julgamento' in pg.inner_text('.fala[data-i="0"] .texto')
    assert pg.inner_text('.fala[data-i="7"] .quem') == 'MARIA JOSÉ DA SILVA' and 'dep' in pg.get_attribute('.fala[data-i="7"] .quem', 'class')
    assert 'sentado ao lado do advogado' in pg.inner_text('.fala[data-i="7"] .risco'), 'trecho de risco marcado'
    assert not pg.evaluate('document.querySelector("#resumoBox").hidden') and 'dez metros' in pg.evaluate('document.querySelector("#resumoTxt").textContent')
    assert pg.locator('.fala .tag-resumo').count() == 2, 'trechos relevantes do PDF'
    pg.wait_for_function("document.querySelector('#video').readyState >= 1", timeout=15000)
    pg.click('.fala[data-i="7"] .texto'); time.sleep(0.6)
    t = pg.evaluate('document.querySelector("#video").currentTime')
    assert 27 <= t < 29.5 and pg.evaluate('document.querySelector(".fala.atual").dataset.i') == '7'
    pg.evaluate('document.querySelector("#video").pause()')
    for i in (3, 7):
        pg.click('.fala[data-i="%d"] .marcar' % i)
    # a outra mídia foi lida em segundo plano: as falas aparecem na hora
    pg.wait_for_function("window.P45_TESTE && document.querySelectorAll('.midia').length === 2")
    t1 = time.time(); pg.click('.midia:has-text("Joao Pereira")')   # nome vem do arquivo PDF (aqui sem acento)
    pg.wait_for_function("document.querySelectorAll('.fala').length === 6", timeout=10000)
    print('só PDF: segunda mídia com as falas em %.2f s' % (time.time() - t1))
    assert pg.inner_text('.fala[data-i="1"] .quem') == 'JOÃO PEREIRA DOS SANTOS'
    pg.click('.fala[data-i="1"] .marcar')
    assert '3 trechos marcados no processo (1 nesta mídia)' in pg.inner_text('#contaMarcas'), pg.inner_text('#contaMarcas')
    # recarregar e gerar o PDF sem abrir a primeira mídia: ele espera a leitura dos PDFs
    pg.reload(); pg.click('.proc[data-numero="0054293-43.2024.8.17.2001"]')
    pg.wait_for_function("document.querySelector('#pdfBtn') && !document.querySelector('#pdfBtn').disabled", timeout=20000)
    with pg.expect_download() as d:
        pg.click('#pdfBtn')
    destino = OUT / ('so-pdf-' + d.value.suggested_filename); d.value.save_as(str(destino))
    texto = subprocess.run(['pdftotext', '-layout', str(destino), '-'], capture_output=True, text=True).stdout
    for esperado in ('Maria Jose da Silva', 'Joao Pereira dos Santos', '00542934320248172001_2026_02_26_0001.mp4', '3 trechos · 2 depoentes · 2 mídias', 'sentado ao lado do advogado', '(risco de erro)', 'Fui esfaqueado no braço'):
        assert esperado in texto, ('faltou no PDF (só PDF)', esperado)
    print('só PDF: PDF dos trechos gerado a partir das transcrições em PDF')
    pg.screenshot(path=str(OUT / '07-so-pdf.png'))
    nav.close()
print('erros na página:', erros or 'nenhum')
