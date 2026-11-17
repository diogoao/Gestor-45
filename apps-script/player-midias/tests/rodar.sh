#!/bin/sh
# Roda os testes do player: servidor (Node) e página (Chrome + Playwright).
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"; DIR="${1:-/tmp/p45teste}"
"$AQUI/gerar_amostras.sh" "$DIR"
node "$AQUI/teste_code_gs.cjs" "$DIR"
python3 "$AQUI/servidor_drive.py" "$DIR" 8766 & SERV=$!
trap 'kill $SERV' EXIT
sleep 1
python3 "$AQUI/teste_player.py" "$DIR"
