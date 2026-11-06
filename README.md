# ⛏️ CPUMiner Live Mission Control

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge&logo=linux&logoColor=white)](#requisitos-e-instalação)
[![Terminal](https://img.shields.io/badge/Interface-Terminal%20TUI%20%2B%20Web%20Dashboard-00f0ff?style=for-the-badge)](#visão-geral)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stable%20Production-00ff88?style=for-the-badge)](#)

**Suíte Universal de Monitoramento, Telemetria em Tempo Real e Controle Remoto para `cpuminer`**  
*Desenvolvido por **Luan Quaresma***

[Recursos](#-recursos-principais) •
[Instalação](#-requisitos-e-instalação) •
[Como Usar](#-início-rápido) •
[Manual do Terminal](#-manual-do-terminal-tui) •
[Manual Web](#-manual-da-interface-web) •
[Radar DNS](#-radar-global-de-dns--ping-de-pools) •
[Parâmetros CLI](#-referência-completa-de-parâmetros-cli) •
[Dicas & Otimizações](#-dicas-de-performance--otimização) •
[Apoie](#-doações--apoio-ao-projeto)

</div>

---

## 🌟 Visão Geral

O **CPUMiner Live Mission Control** (`monitor_miner.py`) é uma plataforma completa de supervisão, telemetria e gerenciamento em tempo real para mineradores de CPU baseados no `cpuminer` (`cpuminer-opt`, `cpuminer-multi`, `cpuminer-gr`, etc.). 

A aplicação opera tanto através de um **Terminal TUI cinematográfico de alta densidade** (via biblioteca `rich`) quanto por um **Web Dashboard responsivo com visual Cyberpunk**, permitindo monitorar e controlar remotamente a sua mineração a partir de qualquer dispositivo conectado na rede local ou via internet.

```
   ____ ____  _   _ __  __ ___ _   _ _____ ____  
  / ___|  _ \| | | |  \/  |_ _| \ | | ____|  _ \ 
 | |   | |_) | | | | |\/| || ||  \| |  _| | |_) |
 | |___|  __/| |_| | |  | || || |\  | |___|  _ < 
  \____|_|    \___/|_|  |_|___|_| \_|_____|_| \_\
   UNIVERSAL LIVE MISSION CONTROL · TERMINAL & WEB
```

---

## 🚀 Recursos Principais

### 🎛️ 1. Duas Interfaces em Perfeita Sincronia
- **Terminal TUI (Rich):** Animações suaves, logo ASCII em banner neon, tabelas de telemetria por thread/núcleo de CPU, osciloscópio ASCII com médias móveis, gráfico espectral de ping, matriz de blocos e console de eventos coloridos.
- **Web Dashboard (Mission Control):** Interface moderna com glassmorphism, 5 abas de navegação (Geral, Hashrate, Pool/Blockchain, Hardware, Logs), osciloscópio vetorial SVG, espectro de ping Stratum, matriz viva de 120 slots de shares e 4 gauges radiais.

### ⚡ 2. Telemetria de Hashrate & Eficiência
- **Hashrate Atual, Médio e Pico:** Cálculo contínuo de hashrate instantâneo, média de 1 minuto, 5 minutos e média geral acumulada da sessão.
- **Estabilidade & Eficiência (%):** Desvio padrão e cálculo percentual de estabilidade de hashrate e taxa de aceitação de shares (`Accepted` vs `Rejected`).
- **Cadência de Mineração:** Métricas preditivas de shares por minuto (`spm`), shares por hora (`sph`), estimativa de shares por dia (`spd`) e tempo médio por share.

### 🌐 3. Radar Global de DNS & Ping TCP Stratum
- **46+ Pools Globais Pré-configuradas:** Teste de latência com suporte nativo a DigiByte (DGB), Bitcoin (BTC), Litecoin (LTC), Doge e moedas CPU (Yespower, Yescrypt, Qubit, Skein, RandomX).
- **Benchmark Concorrente Ultrarrápido:** Medição paralela de resolução DNS e handshake TCP via `ThreadPoolExecutor` com 24 workers em ~2 segundos.
- **Gráfico de Qualidade de Latência:**
  - 🟢 **Excelente:** `< 100 ms`
  - 🟢 **Bom:** `100 - 180 ms`
  - 🟡 **Médio:** `180 - 300 ms`
  - 🔴 **Alto / Perda:** `> 300 ms`
- **Aplicação com 1 Clique:** Selecione qualquer pool no Radar e o sistema atualiza as configurações e reinicia o cpuminer automaticamente.
- **Hosts Customizados:** Adicione URLs ou nós P2Pool personalizados diretamente pela interface.

### 🧠 4. Monitoramento Detalhado por Núcleo de CPU
- Supervisão individual de cada thread lógica com hashrate individual, percentual relativo, uso de CPU e frequência em MHz.
- Detecção automática de modo de mineração (hashrate por thread real ou modo distribuído/estimado).
- Alertas de estrangulamento térmico e sobrecarga de CPU.

### ⚙️ 5. Central Comparativa de Configuração
- Editor interativo que compara visualmente as **Configurações Ativas vs Novas** com badges dinâmicos (`● ALTERADO` / `mantido`).
- Suporte a alteração em tempo de execução de: Binário, Algoritmo, Pool, Carteira/Worker, Senha, Contagem de Threads e Política de Auto-Restart.
- Opção de salvar sem reiniciar ou salvar e reiniciar o processo imediatamente.

### 🌍 6. Suporte 100% Bilíngue & Temas Visuais
- **Idiomas:** Português do Brasil (PT-BR) e Inglês (EN) com alternância instantânea sem necessidade de reiniciar.
- **6 Temas Visuais Exclusivos:**
  1. 🟣 **Cyberpunk Neon:** Ciano vibrante, verde neon, magenta e amarelo.
  2. 🟢 **Matrix Hacker Green:** Tons escuros com verde fósforo terminal.
  3. 🟡 **Bitcoin Gold:** Dourado nobre, âmbar e tons quentes.
  4. 🔵 **Ocean Blue:** Azul profundo, ciano água e azul marinho.
  5. 🟣 **Dracula Purple:** Roxo suave, rosa elétrico e ciano escuro.
  6. 🔴 **Crimson Red:** Vermelho escarlate, rubi e tons de alerta.

---

## 📦 Requisitos e Instalação

### Pré-requisitos
- **Python 3.8** ou superior instalado.
- Binário do **cpuminer** compilado ou baixado no seu sistema (ex: `cpuminer.exe`, `cpuminer-sse2.exe`, `cpuminer-avx2`, etc.).
- Conexão de rede ativa para conexão à pool Stratum.

### Instalação das Dependências

Clone este repositório ou baixe o arquivo `monitor_miner.py`:

```bash
git clone https://github.com/seu-usuario/cpuminer-live-dashboard.git
cd cpuminer-live-dashboard
```

Instale as bibliotecas necessárias via `pip`:

```bash
pip install rich psutil
```

> **Nota:** As bibliotecas padrão `socket`, `threading`, `json`, `argparse`, `http.server`, `urllib` e `subprocess` já acompanham o Python.

---

## 🏁 Início Rápido

### 1. Início Rápido (Modo Interativo com Menu)
Basta executar o script com Python. O Menu Principal será aberto:

```bash
python monitor_miner.py
```

### 2. Início Rápido com Servidor Web Ativo
Para acessar a interface gráfica no navegador:

```bash
python monitor_miner.py --web --web-port 8080
```
Em seguida, abra no seu navegador: **`http://localhost:8080`** (ou use o IP local da máquina para acessar pelo celular ou outro PC).

### 3. Exemplo para Mineração de DigiByte (DGB - sha256d)
```bash
python monitor_miner.py \
  --bin "cpuminer-avx2.exe" \
  -a sha256d \
  -o "stratum+tcp://dgb.fusionpool.pro:3332" \
  -u "DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9.worker1" \
  -p "c=DGB" \
  -t 8 \
  --web
```

### 4. Exemplo para Mineração de Scrypt (Litecoin / DGB / Doge)
```bash
python monitor_miner.py \
  -a scrypt \
  -o "stratum+tcp://americas.mining-dutch.nl:3437" \
  -u "SuaCarteiraOuUsername.worker1" \
  -p "x" \
  --web
```

### 5. Exemplo para Mineração em CPU com Yespower / Yescrypt
```bash
python monitor_miner.py \
  -a yespower \
  -o "stratum+tcp://yespower.eu.mine.zergpool.com:6533" \
  -u "SuaCarteira" \
  -p "c=DGB,m=solo" \
  --theme matrix \
  --web
```

---

## 📟 Manual do Terminal (TUI)

Ao iniciar o programa sem `--auto-start`, você verá o **Menu Principal Interativo**:

```
+-----------------------------------------------------------------------+
|  [0] ▶ INICIAR MINERAÇÃO          |  [1] ⚙️ CONFIGURAÇÃO & TEMAS       |
|  [2] 🌍 RADAR DNS & PING POOLS    |  [3] 💝 DOAÇÃO & APOIAR PROJETO   |
|  [4] ℹ️ SOBRE O PROJETO           |  [5] ✖ SAIR DO MONITOR            |
+-----------------------------------------------------------------------+
```

### Controles no Menu
| Tecla | Ação |
|---|---|
| `↑` / `↓` / `←` / `→` | Navega entre os botões do menu |
| `Enter` | Executa a ação do botão selecionado |
| `1` a `6` | Atalho direto para os botões |
| `L` | Alterna instantaneamente o idioma entre Português e Inglês |
| `T` | Alterna para o próximo tema visual |
| `Ctrl + C` | Encerra a aplicação de forma segura |

### Controles Durante a Mineração ao Vivo
| Tecla | Ação |
|---|---|
| `Q` | Pausa a mineração e retorna ao Menu Principal sem fechar o processo |
| `Ctrl + C` | Encerra o minerador e finaliza o monitor |

### Painéis de Telemetria do Terminal:
1. **Header da Missão:** Estado da conexão, uptime, algoritmo, pool, threads e relógio do servidor.
2. **Card de Hashrate Total:** Valor instantâneo, pico histórico, médias de 1m/5m/geral e sparkline ASCII.
3. **Desempenho por Núcleo:** Lista tabular das threads de CPU, hashrate individual, barra de uso e frequência.
4. **Telemetria Stratum & Pool:** Status de conexão, latência TCP em ms, gráfico espectral de barras coloridas, dificuldade da pool e contador de blocos/jobs.
5. **Shares & Eficiência:** Contadores de aceitos e rejeitados com taxa percentual de acerto e tempo desde o último share.
6. **Matriz Cyber de Shares:** Mapa dinâmico de blocos (`★` Novo, `■` Aceito, `✖` Rejeitado, `❖` Minerando, `▸` Scanner).
7. **Telemetria de Sistema:** Uso total de CPU, RAM, Memória Swap, Bateria, Temperatura e Taxas de Rede (Download/Upload).
8. **Log de Eventos do cpuminer:** Últimas mensagens filtradas do terminal do minerador.

---

## 🌐 Manual da Interface Web

O Web Dashboard foi construído para fornecer um centro de comando profissional acessível através do navegador.

### Abas de Navegação (Workspace Switcher)
- **🎛️ Mission Control (Completo):** Exibe todos os painéis e métricas simultaneamente em layout bento grid.
- **📈 Hashrate & Núcleos CPU:** Foco no osciloscópio de velocidade e desempenho por thread de processador.
- **🌐 Pool, Shares & Blockchain:** Foco na telemetria Stratum, espectro de ping, matriz de shares e cadeia de blocos.
- **🖥 Hardware & Processo:** Foco nas medições térmicas, gauges de CPU, RAM, Swap e consumo do processo.
- **📜 Console Terminal:** Visualizador em tela cheia com filtros por tag (`Todos`, `Shares`, `Jobs`, `Erros`), busca de texto e botão para download do arquivo `.log`.

### Controles Remotos do Minerador
Localizados na barra superior:
- **▶ Iniciar / Retomar:** Inicia ou retoma a execução do processo cpuminer.
- **⏸ Pausar:** Interrompe temporariamente a mineração economizando energia e liberando CPU.
- **🔄 Reiniciar Miner:** Reinicia o processo do zero (útil após troca de pool ou algoritmo).

### Segurança com Token Web (`--web-token`)
Para proteger o painel quando exposto na internet:
```bash
python monitor_miner.py --web --web-token "senha_secreta_123"
```
O painel solicitará a chave de autenticação ao carregar ou pode ser acessado diretamente com:
`http://seu-ip:8080/?token=senha_secreta_123`

### Endpoints da API REST Integrada
| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/state` | Retorna o JSON completo com telemetria, hardware, shares e logs |
| `POST` | `/api/control` | Controla o minerador (`{"action": "start"|"pause"|"resume"|"restart"|"clear_logs"}`) |
| `POST` | `/api/config` | Atualiza parâmetros, tema (`theme`), idioma (`lang`) ou reinicia o minerador |
| `GET` | `/api/dns_test` | Executa ou recupera o benchmark de latência das pools globais |
| `POST` | `/api/dns_hosts`| Adiciona ou remove hosts customizados no radar DNS |

---

## 🌍 Radar Global de DNS & Ping de Pools

A ferramenta possui um radar embutido com **mais de 46 pools globais** testadas em paralelo via TCP connect de baixa sobrecarga:

### Algumas das Pools Nativas Monitoradas:
- **M2Pool (`m2pool.com`):** Global multi-algo (DGB, Qubit, Skein, Odocrypt).
- **Mining-Dutch (`mining-dutch.nl`):** Pools Europa e Américas com suporte a multi-coin, D-PPS, PROP e SOLO.
- **SoloPool (`solopool.org` / `solopool.eu`):** Mineração solo para SHA-256 e Scrypt.
- **Zpool (`zpool.ca`):** Hub multi-moedas com servidores em SA (Brasil), NA (América do Norte) e EU (Europa).
- **P2Pool Network (`p2p-spb.xyz`):** Nós descentralizados P2Pool para DigiByte.
- **MolePool (`molepool.com`):** Opções voltadas para Scrypt/SHA-256 e merged mining.
- **DigiByte.io (`digibyte.io`):** Nós centrais da rede DigiByte.
- **FenixPool (`fenixpool.com`):** Servidores globais dedicados a DGB SHA-256, Scrypt e Qubit.
- **Kryptex (`kryptex.network`):** Pool global para SHA-256.
- **Mining-Pool.io (`mining-pool.io`):** Servidores Qubit e Scrypt.
- **HuurreXPool (`huurrexpool.com`):** Servidor europeu para DGB SHA-256.
- **KriptoKyng (`kriptokyng.com`):** Pool otimizada para SHA-256.
- **FusionPool (`fusionpool.pro`):** Servidor DGB porta 3332.
- **2Miners (`2miners.com`):** Pool global de alto volume para SHA-256.
- **ViaBTC (`viabtc.io`):** Smart mining multi-algo.
- **Zergpool (`zergpool.com`):** Mineração CPU com Yespower e pagamento automático.
- **Rplant (`rplant.xyz`):** Pools europeias de CPU.
- **Unmineable (`unmineable.com`):** Mineração RandomX/CPU com pagamento em diversas moedas.

### Como Usar o Radar
1. Clique no botão **🌍 Radar DNS & Ping** no cabeçalho Web ou escolha **[2]** no Terminal.
2. A lista será ordenada pela **menor latência (ping em milissegundos)**.
3. Para ativar uma pool, clique em **✔ Usar Pool**. A configuração será salva e o cpuminer apontará para o novo servidor automaticamente!

---

## 📋 Referência Completa de Parâmetros CLI

Todos os parâmetros podem ser passados via linha de comando ou configurados nas telas interativas:

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `--bin` | `cpuminer-avx2.exe` | Caminho do executável do cpuminer |
| `-a`, `--algo` | `sha256d` | Algoritmo de mineração (`sha256d`, `scrypt`, `yescrypt`, `qubit`, etc.) |
| `-o`, `--pool` | `stratum+tcp://dgb.fusionpool.pro:3332` | URL Stratum da pool de mineração |
| `-u`, `--user` | *(carteira DGB)* | Carteira e nome do worker (`carteira.worker`) |
| `-p`, `--password` | `c=DGB` | Senha ou parâmetros de dificuldade da pool |
| `-t`, `--threads` | `0` | Quantidade de threads de CPU (`0` = automático pelo cpuminer) |
| `--theme` | `cyberpunk` | Tema visual inicial (`cyberpunk`, `matrix`, `bitcoin_gold`, `ocean`, `dracula`, `crimson`) |
| `--lang` | `pt` | Idioma da interface: `pt` (Português) ou `en` (English) |
| `--web` | `False` | Habilita o servidor Web Dashboard integrado |
| `--web-host` | `0.0.0.0` | Endereço de escuta do servidor Web (`0.0.0.0` para rede local/externa) |
| `--web-port` | `8080` | Porta TCP do servidor Web |
| `--web-token` | `""` | Senha/Token de acesso para proteger a interface Web |
| `--no-restart` | `False` | Não reinicia o cpuminer automaticamente em caso de falha |
| `--auto-start` | `False` | Pula o menu do terminal e inicia a mineração imediatamente |
| `--extra` | `[]` | Argumentos extras adicionais repassados diretamente ao executável do cpuminer |

### Exemplo Avançado de Linha de Comando:
```bash
python monitor_miner.py \
  --bin "C:\Miners\cpuminer-opt\cpuminer-avx512.exe" \
  -a sha256d \
  -o "stratum+tcp://sha256.sa.mine.zpool.ca:3333" \
  -u "DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9.rig01" \
  -p "c=DGB,zap=DGB" \
  -t 12 \
  --theme matrix \
  --lang en \
  --web \
  --web-port 9090 \
  --web-token "super_secret_key" \
  --auto-start
```

---

## 💡 Dicas de Performance & Otimização

1. **Escolha o Conjunto de Instruções Correto:**
   - Para processadores Intel e AMD modernos, sempre dê preferência a binários compilados com suporte a **AVX2**, **AVX-512** ou **SHA Extensions** (`cpuminer-zen`, `cpuminer-avx2`, `cpuminer-sha`). A diferença de velocidade pode passar de **300%** em relação ao SSE2 tradicional!
2. **Definição de Threads (`-t`):**
   - Deixar `-t 0` permite que o cpuminer detecte todos os núcleos disponíveis.
   - Em processadores com Hyper-Threading / SMT, testar o número de núcleos físicos reais (ex: 8 threads em processador de 8 cores / 16 threads) frequentemente gera hashrate similar com temperatura substancialmente mais baixa.
3. **Redução de Latência de Rede:**
   - Utilize o **Radar DNS** periodicamente para escolher servidores geograficamente mais próximos (preferencialmente abaixo de 100ms). Menor latência reduz drasticamente a ocorrência de *stale shares* (shares rejeitados por atraso).
4. **Gerenciamento Térmico:**
   - Monitore a temperatura da CPU através do card de hardware. Temperaturas sustentadas acima de 80°C ativam o thermal throttling do processador, reduzindo a frequência de clock e o hashrate efetivo.

---

## ❓ Solução de Problemas Frequentes (FAQ)

### 1. O painel diz "Binário não encontrado: cpuminer..."
> **Solução:** Acesse a **Central de Configuração** (tecla `1` no menu ou modal Web) e informe o caminho completo onde está localizado o seu executável (exemplo: `C:\Miner\cpuminer-avx2.exe` ou `/usr/local/bin/cpuminer`).

### 2. A página Web não abre no navegador de outro computador/celular
> **Solução:** 
> 1. Certifique-se de que iniciou com a flag `--web` ou ativou a opção Web nas configurações.
> 2. Verifique se o Firewall do Windows ou Linux permite conexões de entrada na porta configurada (padrão: `8080`).
> 3. No outro dispositivo, use o IP da máquina na rede local (ex: `http://192.168.1.50:8080`).

### 3. Mensagem "401 Unauthorized" ao abrir a Web
> **Solução:** Você definiu um `--web-token`. Informe o token no prompt do navegador ou acesse usando o parâmetro na URL: `http://ip:8080/?token=SEU_TOKEN`.

### 4. Como mudar o idioma para Inglês?
> - **No Terminal:** Pressione a tecla `L` no menu principal.
> - **Na Web:** Selecione **🇺🇸 English** no menu seletor de idiomas no topo da página. A mudança é instantânea em toda a interface.

---

## 💝 Doações & Apoio ao Projeto

Este projeto é desenvolvido com dedicação e disponibilizado de forma **100% gratuita e de código aberto** para a comunidade mineradora mundial.

Se o **CPUMiner Live Mission Control** ajuda na sua operação de mineração, agregou valor ao seu setup ou aumentou sua produtividade, considere apoiar o desenvolvimento com qualquer quantia:

<div align="center">

### ₿ Bitcoin (BTC · SegWit Nativo)
`bc1qlk6dt8hj4tkf7wqgcfcsctuzgkwa0afzxpqku0`

---

### 💎 DigiByte (DGB · Rede Principal)
`DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9`

</div>

---

## 📜 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para mais detalhes.

```
Copyright (c) 2026 Luan Quaresma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">
Feito com ☕ e código aberto por <b>Luan Quaresma</b>.
</div>

