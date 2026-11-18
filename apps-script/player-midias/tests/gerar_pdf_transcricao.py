"""Gera, para cada transcrição de exemplo, um PDF com a mesma disposição do
PDF que o painel salva na pasta Transcrições ("NOME-<mídia>.pdf"): ficha,
resumo, trechos, título "Transcrição integral" e uma fala por bloco, com o
horário numa coluna à esquerda, texto justificado com hifenização e o rodapé
"Processo nº … · data   N / M" em todas as páginas."""
import html, pathlib, re, sys
from playwright.sync_api import sync_playwright
DIR = pathlib.Path(sys.argv[1]); SAIDA = DIR / 'pdf'; SAIDA.mkdir(exist_ok=True)
CSS = """
@page { size: A4; margin: 17mm 0 19mm 0;
  @bottom-left { content: "RODAPE"; font: 7pt "Liberation Sans", Arial, sans-serif; padding-left: 20mm; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 7pt "Liberation Sans", Arial, sans-serif; padding-right: 20mm; } }
body { margin: 0 20mm; font: 9.6pt/1.48 "Liberation Serif", "Times New Roman", serif; }
.k { font: 600 7pt "Liberation Sans", Arial, sans-serif; letter-spacing: .28em; text-transform: uppercase; }
h1 { font-size: 22pt; margin: 0 0 6mm; } h2 { font-size: 19pt; margin: 0 0 8mm; }
p { margin: 0; text-align: justify; hyphens: auto; }
.tr, .fala { display: grid; grid-template-columns: 16mm 1fr; column-gap: 3.2mm; padding: 1.3mm 0; break-inside: avoid; }
.t { font: 600 7.6pt "Liberation Sans", Arial, sans-serif; padding-top: .5mm; }
.q { font: 700 8.2pt "Liberation Sans", Arial, sans-serif; margin-right: 1.3mm; }
.parte { break-before: page; }
"""
def esc(t):
    t = re.sub(r"\s*\[\[TEMPO\]\].*?\[\[/TEMPO\]\]", "", t, flags=re.S)
    t = html.escape(t)
    t = re.sub(r"\[\[RISCO\]\](.*?)\[\[/RISCO\]\]", r'<span style="color:#b42318">\1 <b><i>(conferir fala)</i></b></span>', t, flags=re.S)
    return re.sub(r"\[\[(IDENTIFICACAO|REVISAO)\]\](.*?)\[\[/\1\]\]", r'<span style="color:#777;font-size:8pt">(\2)</span>', t, flags=re.S)
def falante(quem):
    m = re.fullmatch(r"(.+?)\s+\(([^()]+)\)", quem)
    return m.group(2).strip() if m and len(m.group(2).split()) >= 2 else quem
def montar(texto):
    campos, sec, resumo, trechos, falas = {}, None, '', [], []
    for linha in texto.splitlines():
        s = linha.strip()
        if not s: continue
        m = re.fullmatch(r"\[([A-Z]+)\]", s)
        if m: sec = m.group(1); continue
        if sec is None: k, _, v = s.partition(':'); campos[k.strip()] = v.strip()
        elif sec == 'RESUMO': resumo += s
        elif sec == 'TRECHOS': trechos.append([x.strip() for x in s.split('|', 1)])
        elif sec == 'TRANSCRICAO': falas.append([x.strip() for x in s.split('|', 2)])
    a, m_, d = campos['DATA'].split('-')
    rodape = "Processo nº %s · %s/%s/%s" % (campos['PROCESSO'], d, m_, a)
    corpo = ['<div class="k">Degravação de audiência</div><h1>Transcrição de Audiência</h1>',
             '<div class="k">Processo</div><p>%s</p><div class="k">Vídeo transcrito</div><p>%s</p>' % (campos['PROCESSO'], campos['ARQUIVO'])]
    if resumo: corpo.append('<div class="k">02 Resumo do ato</div><p>%s</p>' % esc(resumo))
    if trechos:
        corpo.append('<div class="k">Trechos mais relevantes para a tese acusatória</div>')
        corpo += ['<div class="tr"><span class="t">%s</span><p>%s</p></div>' % (t, esc(x)) for t, x in trechos]
    corpo.append('<div class="parte"><div class="k">Parte II</div><h2>Transcrição integral</h2></div>')
    corpo += ['<div class="fala"><span class="t">%s</span><p><span class="q">%s:</span>%s</p></div>' % (t, html.escape(falante(q)), esc(f)) for t, q, f in falas]
    return '<!DOCTYPE html><html lang="pt-BR"><meta charset="utf-8"><style>%s</style><body>%s</body></html>' % (CSS.replace('RODAPE', rodape), ''.join(corpo)), campos['ARQUIVO']
NOMES = {'0001': 'MARIA JOSE DA SILVA', '0002': 'JOAO PEREIRA DOS SANTOS'}
with sync_playwright() as p:
    nav = p.chromium.launch(executable_path='/usr/bin/google-chrome'); pg = nav.new_page()
    for txt in sorted(DIR.glob('0054293-43.2024.8.17.2001 - *.txt')):
        pagina, midia = montar(txt.read_text(encoding='utf-8'))
        pg.set_content(pagina)
        destino = SAIDA / ('%s-%s.pdf' % (NOMES[midia[-4:]], midia))
        pg.pdf(path=str(destino), print_background=True, prefer_css_page_size=True)
        print('PDF de transcrição de exemplo:', destino.name)
    nav.close()
