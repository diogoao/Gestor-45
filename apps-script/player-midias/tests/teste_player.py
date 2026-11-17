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

MOCK = """
window.P45_TESTE = { driveApi: 'http://127.0.0.1:8766' };
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
""" % json.dumps(CARREGAR)

erros = []
with sync_playwright() as p:
    nav = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--autoplay-policy=no-user-gesture-required', '--disable-features=LocalNetworkAccessChecks,PrivateNetworkAccessSendPreflights,PrivateNetworkAccessRespectPreflightResults,BlockInsecurePrivateNetworkRequests'])
    ctx = nav.new_context(viewport={'width': 1440, 'height': 900}, accept_downloads=True, timezone_id='America/Recife')
    ctx.add_init_script(MOCK)
    def rotas(route):
        u = route.request.url
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
    assert datas[0] == '2026-11-12', 'corte de 5 dias inclusivo (hoje 17/11 → desde 12/11)'
    assert not any('2026-11-1' + d in c for c in nums for d in '01'), 'atos de 10 e 11/11 ficam fora'
    pg.screenshot(path=str(OUT / '01-lista.png'))

    pg.click('.proc[data-numero="0054293-43.2024.8.17.2001"]')
    pg.wait_for_selector('.midia')
    print('mídias:', pg.eval_on_selector_all('.midia', 'els => els.map(e => e.innerText.replace(/\\n+/g," | "))'))
    chamada = pg.evaluate('window.__chamadas[0]')
    assert chamada[2] == CARREGAR['pasta']['id'], 'passa a pasta do índice ao servidor'
    try:
        pg.wait_for_function("document.querySelector('#video').dataset.modo === 'audio' && document.querySelector('#video').readyState >= 1", timeout=15000)
    except Exception:
        print('TOASTS:', pg.inner_text('#toasts'), '| baixando:', pg.inner_text('#baixando'), '| erros:', erros); raise
    print('falas:', pg.locator('.fala').count(), '| baixando:', pg.inner_text('#baixando'))
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
    with pg.expect_download() as d:
        pg.click('#pdfBtn')
    dl = d.value
    destino = OUT / dl.suggested_filename
    dl.save_as(str(destino))
    print('PDF baixado:', dl.suggested_filename)
    pg.click('.toast button:has-text("Salvar na pasta")')
    pg.wait_for_function("window.__chamadas.some(c => c[0] === 'salvarPdf')", timeout=5000)
    print('salvar no Drive:', pg.evaluate("window.__chamadas.filter(c => c[0] === 'salvarPdf')[0]"))

    # Recarregar: marcações voltam do servidor e a posição é retomada
    pg.evaluate('localStorage.clear()')
    pg.reload(); pg.click('.proc[data-numero="0054293-43.2024.8.17.2001"]')
    pg.wait_for_selector('.fala')
    n_marc = pg.locator('.fala.marcada').count(); print('depois de recarregar (sem cache local): marcados =', n_marc); assert n_marc == 3
    pdf_visivel = pg.evaluate('(() => { const r = document.querySelector("#pdfBtn").getBoundingClientRect(); return r.bottom <= innerHeight && r.top >= 0; })()')
    print('botão PDF visível sem rolar a página:', pdf_visivel); assert pdf_visivel
    print('nome da mídia:', pg.inner_text('.midia-nome'))

    # Tema escuro
    pg.click('#temaBtn'); time.sleep(0.4)
    pg.wait_for_function("document.querySelector('#video').readyState >= 1", timeout=15000)
    pg.screenshot(path=str(OUT / '05-escuro.png'))
    # Tela estreita
    pg.set_viewport_size({'width': 820, 'height': 1000}); time.sleep(0.5)
    pg.screenshot(path=str(OUT / '06-estreita.png'), full_page=False)
    nav.close()
print('erros na página:', erros or 'nenhum')
