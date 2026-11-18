"""Grava a transcrição de exemplo (formato do painel) na pasta indicada."""
import sys, os
TEXTO = 'ARQUIVO: 00542934320248172001_2026_02_26_0001\nPROCESSO: 0054293-43.2024.8.17.2001\nDATA: 2026-02-26\nTIPO: TESTEMUNHA\nDEPOENTE: MARIA JOSE DA SILVA\n[PRESENTES]\nMaria José da Silva | Testemunha\nDr. Antônio Arroxelas | Promotor de Justiça\n[RESUMO]\nA testemunha afirmou ter visto o acusado atacar a vítima com uma faca perto da parada de ônibus e o reconheceu em audiência; disse que a distância era de cerca de dez metros, com iluminação de poste.\n[TRECHOS]\n00:00:27 | Reconhecimento do acusado em audiência\n00:00:34 | Distância e iluminação\n[CONFISSAO]\nNAO_APLICA\n[TRANSCRICAO]\n00:00:02 | Juiz | Bom dia. Declaro aberta a audiência de instrução e julgamento. Presentes o Ministério Público, a defesa e o acusado.\n00:00:05 | Juiz | A testemunha está compromissada a dizer a verdade. Pode começar, Doutor.\n00:00:09 | Promotor | A senhora estava na Rua da Aurora na noite de 12 de março de 2024?\n00:00:12 | Testemunha (MARIA JOSÉ DA SILVA) | Estava, sim. Eu voltava do trabalho, por volta das dez da noite.\n00:00:16 | Promotor | O que a senhora viu?\n00:00:20 | Testemunha (MARIA JOSÉ DA SILVA) | Vi dois rapazes discutindo perto da parada de ônibus. Um deles puxou uma faca e foi pra cima do outro.\n00:00:23 | Promotor | A senhora reconhece algum deles aqui na sala?\n00:00:27 | Testemunha (MARIA JOSÉ DA SILVA) | Reconheço. É o rapaz de camisa azul, ali, [[RISCO]]sentado ao lado do advogado[[/RISCO]].\n00:00:30 | Promotor | Qual era a distância entre a senhora e os dois?\n00:00:34 | Testemunha (MARIA JOSÉ DA SILVA) | Uns dez metros, mais ou menos. Tinha um poste aceso bem em cima.\n00:00:38 | Promotor | Sem mais perguntas, Excelência.\n00:00:41 | Juiz | Com a palavra a defesa.\n00:00:45 | Defensor | A senhora usa óculos? Estava de óculos naquela noite?\n00:00:48 | Testemunha (MARIA JOSÉ DA SILVA) | Uso só pra ler. Pra longe eu enxergo bem.\n00:00:52 | Defensor | A senhora conhecia o acusado antes desse dia?\n00:00:56 | Testemunha (MARIA JOSÉ DA SILVA) | Conhecia de vista, do bairro. [inaudível] Nunca falei com ele.\n00:00:59 | Defensor | Quanto tempo durou a briga, mais ou menos?\n00:01:03 | Testemunha (MARIA JOSÉ DA SILVA) | Foi rápido. Uns dois minutos, se tanto. Depois ele saiu correndo pela ponte.\n00:01:06 | Defensor | Nada mais, Excelência.\n00:01:10 | Juiz | Dispensada a testemunha. Obrigado, dona Maria. [[IDENTIFICACAO]]conferir identificação[[/IDENTIFICACAO]]\n00:01:14 | Juiz | Vamos ouvir agora a próxima testemunha arrolada pela acusação.\n00:01:17 | Oficial de Justiça | A testemunha seguinte não compareceu, Excelência.\n00:01:21 | Juiz | Registre-se a ausência. Ministério Público, insiste na oitiva?\n00:01:24 | Promotor | Insisto, Excelência. Requeiro a condução coercitiva para a próxima data.\n'
NOME = '0054293-43.2024.8.17.2001 - MARIA JOSE DA SILVA - 00542934320248172001_2026_02_26_0001.txt'
open(os.path.join(sys.argv[1], NOME), 'w', encoding='utf-8').write(TEXTO)
# Segunda mídia do mesmo processo: outra pessoa, só com mp3.
TEXTO2 = '''ARQUIVO: 00542934320248172001_2026_02_26_0002
PROCESSO: 0054293-43.2024.8.17.2001
DATA: 2026-02-26
TIPO: VITIMA
DEPOENTE: JOAO PEREIRA DOS SANTOS
[PRESENTES]
João Pereira dos Santos | Vítima
[TRANSCRICAO]
00:00:03 | Juiz | O senhor é a vítima neste processo?
00:00:09 | Vítima (JOÃO PEREIRA DOS SANTOS) | Sou, sim. Fui esfaqueado no braço perto da parada.
00:00:20 | Promotor | O senhor viu quem foi?
00:00:26 | Vítima (JOÃO PEREIRA DOS SANTOS) | Vi. Era o rapaz que morava na rua de trás, conhecido como Galego.
00:00:40 | Defensor | Estava escuro?
00:00:45 | Vítima (JOÃO PEREIRA DOS SANTOS) | Tinha o poste aceso. Deu pra ver bem o rosto dele.
'''
open(os.path.join(sys.argv[1], '0054293-43.2024.8.17.2001 - JOAO PEREIRA DOS SANTOS - 00542934320248172001_2026_02_26_0002.txt'), 'w', encoding='utf-8').write(TEXTO2)
