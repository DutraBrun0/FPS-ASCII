# FPS ASCII

FPS de sobrevivência em Python ambientado em uma LAN house de 2001.
Paredes, chão, teto, monitores CRT, inimigos, armas e menus são desenhados
com caracteres ASCII. O pygame-ce abre a janela e desenha os glifos;
não há imagens de cenário nem sprites gráficos.

## Jogar no Windows

Dê dois cliques em **iniciar_fps.bat**, ou execute no terminal desta pasta:

```powershell
.\.venv\Scripts\python.exe -m fps_ascii
```

O arquivo **jogar.py** também inicia o jogo pelo editor. Selecione o
interpretador `.venv\Scripts\python.exe` no VS Code.

Para instalar em outra máquina (Python 3.10 ou superior):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m fps_ascii
```

Linux/macOS: use `python3 -m venv .venv` e substitua o executável
por `.venv/bin/python`. Essa execução foi validada no Windows com Python 3.13;
os outros sistemas não foram testados.

## Controles

| Ação | Tecla |
| --- | --- |
| Mover / deslocar de lado | W A S D |
| Mover / virar pelo teclado | Setas |
| Olhar | Mouse; Page Up/Down para olhar na vertical pelo teclado |
| Disparar | Botão esquerdo ou F |
| Mira da Sniper | Segurar botão direito ou Q |
| Trocar arma | 1–5 ou roda do mouse |
| Recarregar | R |
| Correr | Shift + movimento para frente |
| Pular | Espaço |
| Agachar / iniciar slide em movimento | Ctrl ou C |
| Mostrar mapa | Tab |
| Pausar / liberar o mouse | Esc |
| Ajuda | F1 |
| Alternar verde, âmbar e gelo | F2 |
| Scanlines | F3 |
| Ativar / desativar som | F4 |
| Tela cheia | F11 |
| Sensibilidade do mouse | - / = |
| Navegar no menu | W/S ou setas; Enter confirma |

O mouse fica capturado durante a partida. Esc libera o cursor.
Ao perder o foco da janela, o jogo pausa automaticamente.

## Sobrevivência

Todas as armas estão disponíveis desde o início. A Pistol tem bastante
munição; Rifle, Shotgun e Sniper exigem gerenciamento de carregador e reserva.
O Rifle dispara continuamente ao segurar o botão. As outras armas disparam
uma vez por clique. A Sword funciona sem munição.

- **ILOVEYOU** corre atrás do jogador e ataca de perto.
- **WannaCry** gera descendentes ao morrer; a multiplicação é limitada.
- **Mydoom** lança projéteis que respeitam as paredes.
- A cada **três ondas** surge um chefe com mais vida e ataques anunciados.
- A quantidade, a resistência e a velocidade dos inimigos aumentam.
- Limpar a onda concede recuperação e munição antes da próxima.
- Corrida, pulo e slide gastam energia. Ela se recupera ao descansar.
- Pulo e agachamento alteram a altura do jogador e a exposição a projéteis.

O mapa é conectado e os inimigos usam navegação em grade para contornar PCs
e paredes. O minimapa marca o jogador, inimigos e chefes.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `fps_ascii/app.py` | Janela, eventos, pausa, menus e loop |
| `fps_ascii/game.py` | Integração da simulação, mensagens e feedback |
| `fps_ascii/engine/raycaster.py` | Raycasting DDA, piso/teto e projeção com oclusão |
| `fps_ascii/engine/buffer.py` | Grade ASCII, paletas e cache de glifos |
| `fps_ascii/player.py` | Colisão, movimento, pulo, slide, vida e energia |
| `fps_ascii/weapons.py` | Estatísticas, tiros, recargas e desenhos das armas |
| `fps_ascii/enemies.py` | IA, ataques, projéteis, divisão e chefes |
| `fps_ascii/waves.py` | Progressão, intervalo e recompensas |
| `fps_ascii/maps.py` | LAN house, decoração, colisão, raycast e navegação |
| `fps_ascii/ui/hud.py` | HUD, mira, minimapa, menus e manual |
| `fps_ascii/audio.py` | Efeitos sonoros sintetizados, sem arquivos externos |
| `tests/` | Testes de simulação, renderização e integração |

A simulação usa passos fixos de 1/120 s, com renderização limitada a 60 FPS.
A grade padrão contém 160 × 60 células. Os raios usam o plano da câmera para
evitar distorção de olho de peixe. As paredes usam o gradiente
` .:-=+*#%@`, iluminação direcional e detalhes de terminal. Um buffer de
profundidade oculta sprites atrás das paredes. O desenho de caracteres usa
um cache por glifo/cor e blits em lote.

As scanlines são variações na luminosidade das linhas de texto.
Os únicos preenchimentos gráficos são o fundo preto e as superfícies
internas usadas para armazenar os glifos.

## Configuração e testes

```powershell
# Paleta âmbar, sem som
.\.venv\Scripts\python.exe -m fps_ascii --palette amber --no-audio

# Outra resolução
.\.venv\Scripts\python.exe -m fps_ascii --size 1440x900

# Todos os testes, sem janela e sem pacotes adicionais de teste
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v

# Loop completo em SDL virtual; sem abrir janela
.\.venv\Scripts\python.exe -B -m fps_ascii --headless --demo --frames 360 --no-audio

# Salvar a última tela para inspeção
.\.venv\Scripts\python.exe -B -m fps_ascii --headless --demo --frames 180 --screenshot docs/demo.png
```

`--demo` controla mira/disparo automaticamente e restaura a vida para permitir
verificações repetíveis; esse auxílio fica restrito ao modo de demonstração.
`--headless` usa tempo simulado de 1/60 s por frame e encerra após 180 frames
por padrão. A captura em PNG é uma saída de depuração, não um recurso gráfico
carregado pelo jogo.

Para balancear armas, altere suas definições em `weapons.py`; para ajustar
vida/velocidade/comportamento de inimigos, use `enemies.py`; as recompensas
e pausas ficam em `waves.py`. Novos mapas devem preservar portas largas,
pontos de surgimento livres e conectividade.

## Referências técnicas

- [pygame-ce: mouse e captura de entrada](https://pyga.me/docs/ref/mouse.html)
- [pygame-ce: renderização de fontes](https://pyga.me/docs/ref/font.html)

