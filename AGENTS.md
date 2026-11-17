# Página inicial do Painel da Promotoria

Por determinação do usuário, toda alteração na página inicial do painel local deve ser refletida nesta versão pública no GitHub, na mesma tarefa.

- Arquivo publicado: `Gestor MP/index.html`; produção: https://gestor45.vercel.app/.
- Compare a versão atual do GitHub com a versão local antes de editar; preserve mudanças de outros colaboradores.
- Sincronize comportamento, aparência e correções da página inicial. Preserve as fontes públicas de dados do site; não copie endpoints locais, credenciais ou documentos privados.
- O módulo de navegação ao fim do HTML corresponde a `web/home_materials.js` do painel local. Mantenha ambos iguais. As funções de renderização de Próximos Atos vêm de `web/dashboard.js`.
- Valide abrir data, abrir link do processo, fechar, voltar e o limite inclusivo de cinco dias.
- Publique no GitHub e confira o resultado no Vercel antes de encerrar. Se faltar acesso, informe expressamente o que ficou sem publicar.

## Player de mídias das audiências

- O player roda no Google Apps Script da conta do MPPE (executa como quem acessa, só para o domínio), para abrir mídias e transcrições do Drive sem torná-las públicas. Código em `apps-script/player-midias/` (`Code.gs`, `Player.html`, `appsscript.json`); como publicar está no `LEIA-ME.md` de lá.
- Mudar esses arquivos no GitHub não atualiza o player: é preciso colá-los no projeto do Apps Script e publicar uma nova versão.
- Na página inicial, o ícone `#midiasBtn` (cabeçalho de Próximos Atos) abre `Gestor MP/midias.html`, que só repassa para o endereço do app (`PLAYER_URL`).
- `Player.html` copia de `index.html` as funções que montam os Próximos Atos (`canonicalProcess`, `pautaTime`, `pautaEvents`, `validateImportedActs`, corte de 5 dias). Se essa regra mudar na página inicial, mude lá também.
- Testes: `apps-script/player-midias/tests/rodar.sh` (Node, Python, Playwright e Google Chrome).
