<div align="center">

# FPS ASCII

### FPS de sobrevivência em Python com estética de terminal

Um jogo em primeira pessoa ambientado em uma LAN house de 2001,  
renderizado inteiramente com caracteres ASCII.

<br>

![Python](https://img.shields.io/badge/Python-238636?style=for-the-badge&logo=python&logoColor=white)
![pygame-ce](https://img.shields.io/badge/pygame--ce-238636?style=for-the-badge&logo=pygame&logoColor=white)
![Raycasting](https://img.shields.io/badge/Raycasting-238636?style=for-the-badge)
![ASCII](https://img.shields.io/badge/ASCII-238636?style=for-the-badge&logo=windowsterminal&logoColor=white)
![Git](https://img.shields.io/badge/Git-238636?style=for-the-badge&logo=git&logoColor=white)

</div>

---

## Sobre o projeto

**FPS ASCII** é um FPS de sobrevivência desenvolvido em Python utilizando `pygame-ce`.

O jogo se passa em uma LAN house no ano de **2001** e possui uma estética inspirada em terminais e computadores antigos.

Paredes, chão, teto, computadores, inimigos, armas, HUD e menus são representados utilizando caracteres ASCII.

A sensação de profundidade é criada através de um sistema de **raycasting DDA**, sem utilização de sprites tradicionais para construir o cenário.

O projeto foi desenvolvido com o objetivo de praticar conceitos de:

- Programação Orientada a Objetos;
- Organização de projetos Python;
- Raycasting;
- Matemática aplicada a jogos;
- Colisão;
- Inteligência de inimigos;
- Gerenciamento de estados;
- Renderização;
- Testes automatizados.

---

## Demonstração

<div align="center">

![FPS ASCII](docs/demo.png)

</div>

---

## Principais funcionalidades

- Renderização de cenário utilizando caracteres ASCII;
- Raycasting DDA;
- Sistema de profundidade e oclusão;
- Diferentes tipos de inimigos;
- IA com navegação pelo mapa;
- Sistema progressivo de ondas;
- Chefes especiais;
- Diferentes armas;
- Sistema de munição;
- Recarga;
- Corrida;
- Pulo;
- Agachamento;
- Slide;
- Sistema de energia;
- Minimap;
- HUD;
- Diferentes paletas de cores;
- Scanlines;
- Sons sintetizados pelo próprio jogo;
- Menus;
- Pausa automática;
- Tela cheia;
- Modo headless;
- Modo de demonstração;
- Testes automatizados.

---

## Inimigos

### ILOVEYOU

Persegue o jogador e realiza ataques de curta distância.

### WannaCry

Ao ser derrotado pode gerar novos inimigos, criando pressão durante as ondas.

### Mydoom

Ataca à distância utilizando projéteis que respeitam paredes e obstáculos.

### Boss

A cada três ondas surge um chefe mais resistente, com ataques próprios e maior quantidade de vida.

---

## Armas

| Arma | Característica |
|---|---|
| Pistol | Arma inicial com boa quantidade de munição |
| Rifle | Disparo automático |
| Shotgun | Alto dano a curta distância |
| Sniper | Alto dano e modo de mira |
| Sword | Ataque corpo a corpo sem munição |

---

## Controles

| Ação | Tecla |
|---|---|
| Movimento | `W A S D` |
| Girar pelo teclado | `← →` |
| Olhar | `Mouse` |
| Olhar verticalmente | `Page Up / Page Down` |
| Atirar | `Botão esquerdo / F` |
| Mira da Sniper | `Botão direito / Q` |
| Trocar arma | `1 - 5 / Scroll` |
| Recarregar | `R` |
| Correr | `Shift` |
| Pular | `Espaço` |
| Agachar / Slide | `Ctrl / C` |
| Mostrar mapa | `Tab` |
| Pausar | `Esc` |
| Ajuda | `F1` |
| Alterar paleta | `F2` |
| Scanlines | `F3` |
| Som | `F4` |
| Tela cheia | `F11` |
| Sensibilidade | `- / =` |

---

## Tecnologias

<div align="center">

![Python](https://img.shields.io/badge/Python-238636?style=for-the-badge&logo=python&logoColor=white)
![pygame](https://img.shields.io/badge/pygame--ce-238636?style=for-the-badge&logo=pygame&logoColor=white)
![Git](https://img.shields.io/badge/Git-238636?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-238636?style=for-the-badge&logo=github&logoColor=white)

</div>

---

## Estrutura do projeto

```text
FPS/
│
├── fps_ascii/
│   │
│   ├── engine/
│   │   ├── buffer.py
│   │   └── raycaster.py
│   │
│   ├── ui/
│   │   └── hud.py
│   │
│   ├── __main__.py
│   ├── app.py
│   ├── audio.py
│   ├── enemies.py
│   ├── game.py
│   ├── maps.py
│   ├── player.py
│   ├── weapons.py
│   └── waves.py
│
├── tests/
├── docs/
│
├── jogar.py
├── iniciar_fps.bat
├── requirements.txt
└── README.md
```

---

## Organização do código

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Janela, eventos, menus, pausa e loop principal |
| `game.py` | Integração da lógica e estados do jogo |
| `engine/raycaster.py` | Raycasting DDA e projeção do cenário |
| `engine/buffer.py` | Renderização e gerenciamento dos caracteres ASCII |
| `player.py` | Movimento, colisão, vida, energia, pulo e slide |
| `weapons.py` | Armas, disparos, munição e recarga |
| `enemies.py` | IA, ataques, projéteis e chefes |
| `waves.py` | Progressão das ondas |
| `maps.py` | Construção do mapa e navegação |
| `ui/hud.py` | HUD, minimapa e menus |
| `audio.py` | Efeitos sonoros |
| `tests/` | Testes da lógica e renderização |

---

## Raycasting

A renderização utiliza o algoritmo **DDA (Digital Differential Analyzer)** para lançar raios a partir da posição do jogador.

Cada raio percorre o mapa até encontrar uma parede.

A distância encontrada é utilizada para calcular a altura da parede projetada na tela.

```text
PLAYER
   \
    \
     \
      \       █
       \      █
        \     █
         \    █
          \   █
           \  █
            \ █
             \█
```

O sistema também utiliza um buffer de profundidade para impedir que inimigos ou outros elementos sejam renderizados através das paredes.

---

## Como executar

### Requisitos

- Python 3.10 ou superior

### 1. Clone o projeto

```bash
git clone https://github.com/DutraBrun0/FPS.git
```

Entre na pasta:

```bash
cd FPS
```

### 2. Crie o ambiente virtual

```bash
python -m venv .venv
```

### 3. Ative o ambiente

No Windows:

```bash
.venv\Scripts\activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Execute

```bash
python -m fps_ascii
```

Também é possível executar:

```bash
python jogar.py
```

No Windows, outra opção é executar:

```text
iniciar_fps.bat
```

---

## Configurações

### Alterar paleta

```bash
python -m fps_ascii --palette amber
```

### Executar sem áudio

```bash
python -m fps_ascii --no-audio
```

### Alterar resolução

```bash
python -m fps_ascii --size 1440x900
```

---

## Testes

Execute todos os testes com:

```bash
python -B -m unittest discover -s tests -v
```

Também existe um modo **headless**, que permite executar o jogo sem abrir uma janela:

```bash
python -B -m fps_ascii --headless --demo --frames 360 --no-audio
```

É possível gerar uma captura automaticamente:

```bash
python -B -m fps_ascii --headless --demo --frames 180 --screenshot docs/demo.png
```

---

## O que aprendi

Durante o desenvolvimento deste projeto pude praticar:

- Estruturação de projetos Python;
- Programação Orientada a Objetos;
- Game loops;
- Controle de tempo e FPS;
- Vetores e trigonometria;
- Raycasting;
- Colisões;
- Inteligência artificial básica;
- Navegação em mapas;
- Gerenciamento de estados;
- Testes automatizados;
- Git e GitHub.

---

## Desenvolvimento com auxílio de IA

<div align="center">

![OpenAI Codex](https://img.shields.io/badge/OpenAI_Codex-238636?style=for-the-badge&logo=openai&logoColor=white)

</div>

O projeto foi desenvolvido por **Bruno Dutra com auxílio do OpenAI Codex** durante partes do processo de implementação, revisão, depuração e organização do código.

A ferramenta foi utilizada como apoio durante o desenvolvimento, enquanto o projeto também serviu como forma de estudo dos conceitos e implementações utilizadas.

---

## Autor

<div align="center">

### Bruno Dutra

[![GitHub](https://img.shields.io/badge/GitHub-238636?style=for-the-badge&logo=github&logoColor=white)](https://github.com/DutraBrun0)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-238636?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/brunodutraaa/)

</div>

---

<div align="center">

`FPS ASCII — sobreviva à LAN house de 2001.`

</div>