# Player de mídias das audiências (Google Apps Script)

Página para assistir às mídias das audiências com a transcrição ao lado:

- lista os mesmos processos dos **Próximos Atos** da página inicial (dos últimos 5 dias em diante), ou outro processo pelo número;
- mostra as mídias da pasta do processo no Drive (`Mídias`, `Mp3`, `Transcrições`);
- transforma a transcrição (`HH:MM:SS | quem | fala`) em cards clicáveis: o clique leva o vídeo ao horário da fala;
- destaca a fala que está tocando e rola a lista no ritmo do vídeo (1x, 1,5x, 2x);
- toca o **mp3 na hora** e baixa o vídeo por trás; quando o vídeo chega, troca para ele no mesmo segundo;
- marca trechos (as marcações ficam na conta de cada pessoa e valem em qualquer computador) e gera um PDF só com eles.

## Por que no Apps Script, numa conta pessoal

A conta do MPPE não permite Apps Script nem criar autenticação própria. Por isso a pasta **Material de Preparação**
foi compartilhada, a partir da conta do MPPE, com a conta Google pessoal, e o app é publicado nessa conta pessoal.

O app roda como **a pessoa que está acessando**: cada um entra com a própria conta Google e só enxerga o que essa
conta já enxerga no Drive. Quem abrir o endereço sem ter a pasta compartilhada não vê nada. Nenhum arquivo fica
público e não é preciso criar nada no Google Cloud. Arquivos novos que o painel grava na pasta aparecem sozinhos.

## Publicar (uma vez)

1. Entre em <https://script.google.com> com a **conta pessoal** (a que recebeu o compartilhamento) e clique em **Novo projeto**. Dê o nome "Player de mídias 45ª".
2. Em **Configurações do projeto** (engrenagem), marque **Mostrar o arquivo de manifesto "appsscript.json" no editor**.
3. Volte ao **Editor**:
   - em `Código.gs`, apague tudo e cole o conteúdo de [`Code.gs`](Code.gs);
   - em `appsscript.json`, apague tudo e cole o conteúdo de [`appsscript.json`](appsscript.json);
   - clique em **+** ao lado de "Arquivos" → **HTML**, dê o nome `Player` (sem ".html") e cole o conteúdo de [`Player.html`](Player.html).
4. Clique em **Salvar**. Em **Serviços** deve aparecer **Drive**. Se não aparecer, clique em **+** em Serviços, escolha **Drive API** e **Adicionar**.
5. **Implantar → Nova implantação** → em "Selecionar tipo", **App da Web**:
   - Executar como: **Usuário que acessa o app da Web**
   - Quem pode acessar: **Qualquer pessoa com Conta do Google**
6. Clique em **Implantar** e depois em **Autorizar acesso**. Escolha a conta pessoal. O Google mostra
   **"O Google não verificou este app"**, porque o app é seu e não passou pela revisão do Google: clique em
   **Avançado → Acessar Player de mídias 45ª (não seguro)** e depois em **Permitir**.
7. Copie o **URL do app da Web** (termina em `/exec`) e coloque-o em `PLAYER_URL`, no arquivo `Gestor MP/midias.html`.
   A partir daí o ícone de play no cabeçalho de "Próximos Atos" da página inicial abre o player.

Na primeira vez que cada pessoa abrir o player, o Google pede a mesma autorização (com o mesmo aviso). A autorização
pede acesso ao Drive porque o app lê as mídias e as transcrições e, se a pessoa quiser, salva o PDF de trechos na pasta
do processo. Para outra pessoa usar, a pasta precisa estar compartilhada com a conta Google dela.

## Atualizar depois

Cole os arquivos novos no editor e use **Implantar → Gerenciar implantações → lápis (editar) → Versão: Nova versão → Implantar**.
O endereço `/exec` continua o mesmo.

## Onde o app procura os arquivos

1. pasta do processo indicada no índice de links da página inicial (`indice-processos.json` / publicação do painel);
2. `Processos/<número>` ou `Fora de Pauta/<número>` dentro da pasta sincronizada (`PASTA_RAIZ` em `Code.gs`);
3. busca de uma pasta com o número do processo no nome;
4. arquivos com o número no nome em qualquer pasta (pastas de ato depois de "distribuir").

Mídia e transcrição são ligadas pelo campo `ARQUIVO:` do TXT (nome da mídia sem extensão). O mp3 da pasta `Mp3`
com o mesmo nome é usado para começar a tocar na hora.

## Testes

`tests/` (fora do Apps Script) roda o `Code.gs` contra um Drive simulado e a página no Chrome com uma Drive API falsa.
