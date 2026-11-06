#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPUMiner Live Dashboard - Universal Multi-Algo Edition (Terminal TUI + Web Dashboard)
Developed by / Desenvolvido por Luan Quaresma

Runs cpuminer in the background, parses real-time stdout (per-core hashrate,
accepted/rejected shares, difficulty, reconnects...) and displays a complete
dashboard both in the Terminal (Rich TUI) and via an embedded Web Server.

Usage / Uso:
    python3 monitor_miner.py
    python3 monitor_miner.py --web --web-host 0.0.0.0 --web-port 8080 --web-token luan
"""

import argparse
import collections
import hashlib
import json
import os
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

try:
    import psutil
except ImportError:
    psutil = None

console = Console()

# --------------------------------------------------------------------------
# Carteiras de Doacao do Projeto / Project Donation Wallets
# --------------------------------------------------------------------------
DONATE_BTC = "bc1qlk6dt8hj4tkf7wqgcfcsctuzgkwa0afzxpqku0"
DONATE_DGB = "DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9"

# --------------------------------------------------------------------------
# Dicionario Internacional de Idiomas (PT-BR & EN-US)
# --------------------------------------------------------------------------
LANG_KEYS = ["pt", "en"]

I18N = {
    "pt": {
        "lang_label": "🇧🇷 Português (BR)",
        "subtitle_edition": "LIVE DASHBOARD · UNIVERSAL MULTI-ALGO (TERMINAL & WEB)",
        "dev_by": "Desenvolvido por Luan Quaresma",
        "main_menu_title": "💠 MENU PRINCIPAL",
        "ready_summary_title": "⚡ Resumo da Configuração Pronta para Iniciar",
        "active_pool": "Pool Ativa:",
        "algorithm": "Algoritmo:",
        "wallet": "Carteira:",
        "worker": "Worker:",
        "cpu_threads": "Threads CPU:",
        "active_theme": "Tema Ativo:",
        "language": "Idioma:",
        "web_panel": "Painel Web:",
        "auto": "Automático",
        "auto_0": "Automático (0)",
        "enabled": "Ativado",
        "disabled": "Desativado",
        "btn1_title": "[1] INICIAR (TERMINAL + WEB)",
        "btn1_desc": "Executar cpuminer, painel de terminal e servidor web",
        "btn2_title": "[2] CONFIGURAÇÕES & TEMAS",
        "btn2_desc": "Editar pool, carteira, web, idioma e tema",
        "btn3_title": "[3] RADAR DE DNS & PING",
        "btn3_desc": "Gráfico de latência das pools mundiais",
        "btn4_title": "[4] DOAÇÃO (BTC / DGB)",
        "btn4_desc": "Apoiar o projeto (Bitcoin ou DigiByte)",
        "btn5_title": "[5] ABOUT (SOBRE)",
        "btn5_desc": "Créditos — Desenvolvido por Luan Quaresma",
        "btn6_title": "[6] SAIR DO SISTEMA",
        "btn6_desc": "Encerrar o painel",
        "donate_Validate_btc": "💝 Doação BTC:",
        "donate_Validate_dgb": "💎 Doação DGB:",
        "menu_nav_help": "[dim]Setas [bold cyan]↑ ↓ ← →[/] movem · [bold bright_green]Enter[/] seleciona · Atalhos [bold cyan]1-6[/] · Tecla [bold yellow]L[/] muda Idioma (PT/EN)[/]",
        "bye_msg": "Até logo! Programa finalizado.",
        "cancelled_msg": "Operação cancelada pelo usuário.",
        "cfg_old_title": "⏪ CONFIGURAÇÃO ANTERIOR (Ativa antes da edição)",
        "cfg_new_title": "🆕 NOVA CONFIGURAÇÃO (Use ↑/↓ e Enter para editar · ◀/▶ muda Tema/Idioma)",
        "cfg_center_title": "⚙️  CENTRAL DE CONFIGURAÇÃO, WEB, IDIOMA & TEMAS",
        "cfg_col_param": "Parâmetro",
        "cfg_col_old": "Valor Anterior",
        "cfg_col_new": "Novo Valor (Configurar)",
        "cfg_col_status": "Status",
        "cfg_changed": "● ALTERADO",
        "cfg_kept": "mantido",
        "fld_bin": "Caminho do Binário",
        "fld_algo": "Algoritmo (-a)",
        "fld_pool": "URL da Pool (-o)",
        "fld_user": "Carteira.Worker (-u)",
        "fld_pass": "Senha da Pool (-p)",
        "fld_threads": "Threads CPU (-t)",
        "fld_restart": "Auto-Restart",
        "fld_theme": "Tema Visual do Painel",
        "fld_lang": "Idioma / Language",
        "fld_web": "Servidor Web (--web)",
        "fld_web_port": "Porta Web (--web-port)",
        "fld_web_token": "Token Web (--web-token)",
        "btn_save_act": " ✔ SALVAR E APLICAR NOVAS CONFIGS ",
        "btn_save_idle": "✔ Salvar e Aplicar Novas Configs",
        "btn_cancel_act": " ✖ DESCARTAR E VOLTAR ",
        "btn_cancel_idle": "✖ Descartar Alterações e Voltar",
        "cfg_nav_help": "[dim]Navegação: [bold cyan]↑ / ↓[/] seleciona · [bold cyan]Enter[/] edita/alterna · [bold cyan]← / →[/] troca Tema/Idioma · [bold cyan]ESC[/] volta[/]",
        "prompt_old_val": "Valor anterior de",
        "prompt_new_val": "Digite o novo valor para",
        "cfg_saved_ok": "✔ Novas configurações salvas em",
        "dns_testing_spinner": "🌍 Testando resolução DNS e gráfico de latência Stratum das pools globais...",
        "dns_col_pool": "Pool",
        "dns_col_region": "Região",
        "dns_col_host": "Host : Porta",
        "dns_col_dns": "DNS",
        "dns_col_ping": "Ping Médio",
        "dns_col_graph": "Gráfico Dinâmico de Ping (Cores)",
        "dns_best_ok": "🏆 Melhor Latência Detectada:",
        "dns_best_fail": "⚠ Nenhuma pool respondeu ao teste TCP no momento.",
        "dns_legend": "[dim]Legenda de Cores do Ping:[/] [bold bright_green]█ < 100ms (Excelente)[/] · [bold green]█ 100-180ms (Bom)[/] · [bold yellow]█ 180-300ms (Médio)[/] · [bold red]█ > 300ms (Alto/Perda)[/]",
        "dns_nav_help": "[dim]Controles: [bold cyan]↑ / ↓[/] seleciona pool · [bold bright_green]Enter[/] aplica pool · [bold yellow]R[/] testar novamente · [bold red]ESC / Q[/] voltar[/]",
        "dns_title": "🌐 RADAR GLOBAL DE DNS & GRÁFICO DE LATÊNCIA STRATUM",
        "dns_subtitle": "★ = Pool atualmente configurada",
        "dns_pool_updated": "✔ Pool alterada e salva:",
        "custom_pool_name": "Pool Atual (Custom)",
        "custom_pool_reg": "Configurada",
        "dns_fail": "Falha DNS",
        "ping_exc": "EXCELENTE",
        "ping_good": "BOM",
        "ping_med": "MÉDIO",
        "ping_high": "ALTO",
        "ping_wait": "aguardando amostras de ping...",
        "don_intro": "\n[bold bright_yellow]💝 APOIE O DESENVOLVIMENTO OPEN-SOURCE![/]\n[white]Este painel é 100% gratuito e de código aberto para toda a comunidade mundial de mineração.\nSe a ferramenta ajudou você, considere apoiar o projeto com uma doação:[/]\n",
        "don_btc_header": "₿ BITCOIN (BTC - Rede Nativa SegWit)",
        "don_dgb_header": "💎 DIGIBYTE (DGB - Rede Principal)",
        "don_press_btc": " ❯ PRESSIONE ENTER PARA COPIAR ENDEREÇO BTC ❮ ",
        "don_press_dgb": " ❯ PRESSIONE ENTER PARA COPIAR ENDEREÇO DGB ❮ ",
        "don_select_hint": "Selecione e pressione Enter para copiar",
        "don_btc_box": "🪙 Carteira Bitcoin (BTC)",
        "don_dgb_box": "💠 Carteira DigiByte (DGB)",
        "don_mouse_hint": "Você também pode selecionar o endereço direto no terminal com o mouse/toque.",
        "don_nav_help": "[dim]Controles: [bold cyan]↑ / ↓[/] escolhe moeda · [bold bright_green]Enter[/] copia carteira · [bold red]ESC / Q[/] voltar ao menu[/]",
        "don_title": "💝 DOAÇÃO & APOIO AO PROJETO — LUAN QUARESMA",
        "don_copied_ok": "✔ Endereço copiado para a área de transferência:",
        "don_copied_manual": "📋 Endereço destacado para cópia manual:",
        "about_sub": "Monitoramento em Tempo Real (Terminal & Web) para todas as criptomoedas do cpuminer",
        "about_dev": "Desenvolvido por:",
        "about_body": "Suíte completa em terminal e navegador web que supervisiona o cpuminer em segundo plano,\nanalisando a saída real por núcleo, shares aceitos e rejeitados, dificuldade,\ngráfico dinâmico de ping por cores, mapa animado de shares em tempo real,\ntemas personalizáveis, suporte bilíngue (PT/EN) e controle remoto via Web.",
        "about_wallets": "💝 Carteiras para Doação:",
        "about_title": "ℹ️  SOBRE O DESENVOLVEDOR & SISTEMA",
        "about_footer": "Pressione Enter ou ESC para voltar ao menu principal",
        "st_starting": "Iniciando",
        "st_connecting": "Conectando",
        "st_mining": "Minerando",
        "st_stopped": "Parado",
        "st_error": "Erro",
        "hr_cur": "Atual",
        "hr_peak": "Pico",
        "hr_min": "Mínimo",
        "hr_avg1": "Média 1 min",
        "hr_avg5": "Média 5 min",
        "hr_avg_all": "Média geral",
        "hr_spark_lbl": "Hashrate total (últimos segundos):",
        "hr_title": "📈 Hashrate Total",
        "core_col_id": "Núcleo",
        "core_col_hr": "Hashrate",
        "core_col_rel": "Relativo",
        "core_col_cpu": "Uso CPU",
        "core_col_freq": "Freq",
        "core_col_st": "Estado",
        "core_est": "ESTIMADO",
        "core_act": "ATIVO",
        "core_nodata": "SEM DADOS",
        "core_title": "🧠 Desempenho por Núcleo (CPU)",
        "core_sub_est": "cpuminer informa só o total · valor por núcleo = média",
        "pool_testing": "testando...",
        "pool_offline": "offline / sem resposta",
        "pool_collecting": "coletando...",
        "pool_cur_ping": "Ping Atual",
        "pool_ping_graph": "Gráfico Ping",
        "pool_latency": "Latência",
        "pool_diff": "Dificuldade",
        "pool_jobs": "Jobs/Blocos",
        "pool_acc_rej": "Aceitos / Rej.",
        "pool_rej_reasons": "Motivos Rej.",
        "pool_acc_rate": "Taxa de aceite",
        "pool_rate_sh": "Ritmo Shares",
        "pool_last_sh": "Último share",
        "pool_acc_word": "aceito",
        "pool_rej_word": "rejeitado",
        "pool_rep_hr": "Hash reportado",
        "pool_err_rest": "Erros / Rein.",
        "pool_title": "🌐 Pool, Ping Dinâmico & Shares",
        "sys_title": "🖥  Sistema",
        "sys_no_psutil": "não instalado — pip install psutil",
        "sys_cpu_tot": "CPU total",
        "sys_temp": "Temperatura",
        "sys_bat": "Bateria",
        "sys_charging": "carregando",
        "sys_discharging": "descarregando",
        "sys_net": "Rede",
        "sys_proc_na": "processo indisponível",
        "blk_new": "» NOVO «",
        "blk_rej": "rejeitado",
        "blk_info": "cada bloco = 1 share enviado · ✓ aceito ✗ rejeitado · bloco atual {prog:.0f}% · média {avg:.1f}s",
        "blk_title": "⛓  Corrente de Shares (ao vivo)",
        "grid_waiting": "aguardando",
        "grid_legend": "[bold bright_green]■[/] aceitos [bold green]{acc}[/]   [bold red]■[/] rejeitados [bold red]{rej}[/]   [bold yellow]{pulse}[/] minerando ({spin} {since})   [dim]· exibindo {shown} de {tot} shares · eficiência {rate:.1f}%[/]",
        "grid_title": "🟩 Mapa de Shares em Tempo Real",
        "log_waiting": "Aguardando saída do cpuminer...",
        "log_title": "📜 Eventos do Minerador",
        "footer_live": "[bold yellow]Q[/]: Menu Principal · Ctrl+C: encerrar · Web: [bold cyan]{web}[/] · Tema: [bold]{theme}[/] · BTC: [yellow]{btc}[/] · DGB: [cyan]{dgb}[/]",
        "bin_not_found": "Binário do cpuminer não encontrado:",
        "starting_bg": "Iniciando o cpuminer em segundo plano...",
        "stopping_miner": "Encerrando o cpuminer...",
        "sum_title": "Resumo da Sessão",
        "sum_uptime": "Tempo ativo:",
        "sum_shares": "Shares:",
        "sum_acc_of": "aceitos de",
        "sum_sent": "enviados",
        "sum_peak": "Pico de hashrate:",
        "sum_support": "💝 Apoie o projeto:",
        "miner_safe_exit": "Minerador finalizado com segurança.",
    },
    "en": {
        "lang_label": "🇺🇸 English (Global)",
        "subtitle_edition": "LIVE DASHBOARD · UNIVERSAL MULTI-ALGO (TERMINAL & WEB)",
        "dev_by": "Developed by Luan Quaresma",
        "main_menu_title": "💠 MAIN MENU",
        "ready_summary_title": "⚡ Active Configuration Summary (Ready to Start)",
        "active_pool": "Active Pool:",
        "algorithm": "Algorithm:",
        "wallet": "Wallet:",
        "worker": "Worker:",
        "cpu_threads": "CPU Threads:",
        "active_theme": "Active Theme:",
        "language": "Language:",
        "web_panel": "Web Panel:",
        "auto": "Automatic",
        "auto_0": "Automatic (0)",
        "enabled": "Enabled",
        "disabled": "Disabled",
        "btn1_title": "[1] START (TERMINAL + WEB)",
        "btn1_desc": "Launch cpuminer, terminal TUI and web server",
        "btn2_title": "[2] SETTINGS & THEMES",
        "btn2_desc": "Edit pool, wallet, web server, language & theme",
        "btn3_title": "[3] DNS & PING RADAR",
        "btn3_desc": "Color latency graph across global pools",
        "btn4_title": "[4] DONATE (BTC / DGB)",
        "btn4_desc": "Support the project (Bitcoin or DigiByte)",
        "btn5_title": "[5] ABOUT",
        "btn5_desc": "Credits — Developed by Luan Quaresma",
        "btn6_title": "[6] EXIT",
        "btn6_desc": "Close dashboard",
        "donate_Validate_btc": "💝 Donate BTC:",
        "donate_Validate_dgb": "💎 Donate DGB:",
        "menu_nav_help": "[dim]Arrows [bold cyan]↑ ↓ ← →[/] move · [bold bright_green]Enter[/] select · Keys [bold cyan]1-6[/] · Press [bold yellow]L[/] to switch Language (EN/PT)[/]",
        "bye_msg": "Goodbye! Program terminated.",
        "cancelled_msg": "Operation cancelled by user.",
        "cfg_old_title": "⏪ PREVIOUS CONFIGURATION (Active before editing)",
        "cfg_new_title": "🆕 NEW CONFIGURATION (Use ↑/↓ & Enter to edit · ◀/▶ changes Theme/Language)",
        "cfg_center_title": "⚙️  CONFIGURATION, WEB, LANGUAGE & THEME CENTER",
        "cfg_col_param": "Parameter",
        "cfg_col_old": "Previous Value",
        "cfg_col_new": "New Value (Configure)",
        "cfg_col_status": "Status",
        "cfg_changed": "● MODIFIED",
        "cfg_kept": "unchanged",
        "fld_bin": "Binary Path",
        "fld_algo": "Algorithm (-a)",
        "fld_pool": "Pool URL (-o)",
        "fld_user": "Wallet.Worker (-u)",
        "fld_pass": "Pool Password (-p)",
        "fld_threads": "CPU Threads (-t)",
        "fld_restart": "Auto-Restart",
        "fld_theme": "Dashboard Visual Theme",
        "fld_lang": "Language / Idioma",
        "fld_web": "Web Server (--web)",
        "fld_web_port": "Web Port (--web-port)",
        "fld_web_token": "Web Token (--web-token)",
        "btn_save_act": " ✔ SAVE & APPLY NEW SETTINGS ",
        "btn_save_idle": "✔ Save & Apply New Settings",
        "btn_cancel_act": " ✖ DISCARD & GO BACK ",
        "btn_cancel_idle": "✖ Discard Changes & Go Back",
        "cfg_nav_help": "[dim]Navigation: [bold cyan]↑ / ↓[/] select · [bold cyan]Enter[/] edit/toggle · [bold cyan]← / →[/] change Theme/Language · [bold cyan]ESC[/] back[/]",
        "prompt_old_val": "Previous value for",
        "prompt_new_val": "Enter new value for",
        "cfg_saved_ok": "✔ New settings saved to",
        "dns_testing_spinner": "🌍 Testing DNS resolution and Stratum latency graph across global pools...",
        "dns_col_pool": "Pool",
        "dns_col_region": "Region",
        "dns_col_host": "Host : Port",
        "dns_col_dns": "DNS",
        "dns_col_ping": "Avg Ping",
        "dns_col_graph": "Dynamic Ping Graph (Color-Coded)",
        "dns_best_ok": "🏆 Lowest Latency Detected:",
        "dns_best_fail": "⚠ No pool responded to TCP probe at this moment.",
        "dns_legend": "[dim]Ping Color Legend:[/] [bold bright_green]█ < 100ms (Excellent)[/] · [bold green]█ 100-180ms (Good)[/] · [bold yellow]█ 180-300ms (Medium)[/] · [bold red]█ > 300ms (High/Loss)[/]",
        "dns_nav_help": "[dim]Controls: [bold cyan]↑ / ↓[/] select pool · [bold bright_green]Enter[/] apply pool · [bold yellow]R[/] re-test · [bold red]ESC / Q[/] back[/]",
        "dns_title": "🌐 GLOBAL DNS RADAR & STRATUM LATENCY GRAPH",
        "dns_subtitle": "★ = Currently configured pool",
        "dns_pool_updated": "✔ Pool updated and saved:",
        "custom_pool_name": "Current Pool (Custom)",
        "custom_pool_reg": "Configured",
        "dns_fail": "DNS Failed",
        "ping_exc": "EXCELLENT",
        "ping_good": "GOOD",
        "ping_med": "MEDIUM",
        "ping_high": "HIGH",
        "ping_wait": "waiting for ping samples...",
        "don_intro": "\n[bold bright_yellow]💝 SUPPORT OPEN-SOURCE DEVELOPMENT![/]\n[white]This dashboard is 100% free and open-source for the worldwide mining community.\nIf this tool helped you, please consider supporting the project with a donation:[/]\n",
        "don_btc_header": "₿ BITCOIN (BTC - Native SegWit Network)",
        "don_dgb_header": "💎 DIGIBYTE (DGB - Mainnet)",
        "don_press_btc": " ❯ PRESS ENTER TO COPY BTC ADDRESS ❮ ",
        "don_press_dgb": " ❯ PRESS ENTER TO COPY DGB ADDRESS ❮ ",
        "don_select_hint": "Select and press Enter to copy",
        "don_btc_box": "🪙 Bitcoin Wallet (BTC)",
        "don_dgb_box": "💠 DigiByte Wallet (DGB)",
        "don_mouse_hint": "You can also highlight and copy the wallet address directly in the terminal.",
        "don_nav_help": "[dim]Controls: [bold cyan]↑ / ↓[/] select coin · [bold bright_green]Enter[/] copy address · [bold red]ESC / Q[/] back to menu[/]",
        "don_title": "💝 DONATE & SUPPORT THE PROJECT — LUAN QUARESMA",
        "don_copied_ok": "✔ Address copied to clipboard:",
        "don_copied_manual": "📋 Address highlighted for manual copy:",
        "about_sub": "Real-Time Telemetry (Terminal & Web) for all cpuminer cryptocurrencies",
        "about_dev": "Developed by:",
        "about_body": "Complete terminal and web suite supervising cpuminer in the background,\nparsing real per-core output, accepted and rejected shares, difficulty,\ndynamic color-coded ping graph, animated real-time share map,\ncustomizable themes, bilingual support (EN/PT), and remote Web control.",
        "about_wallets": "💝 Donation Wallets:",
        "about_title": "ℹ️  ABOUT THE DEVELOPER & SYSTEM",
        "about_footer": "Press Enter or ESC to return to the main menu",
        "st_starting": "Starting",
        "st_connecting": "Connecting",
        "st_mining": "Mining",
        "st_stopped": "Stopped",
        "st_error": "Error",
        "hr_cur": "Current",
        "hr_peak": "Peak",
        "hr_min": "Minimum",
        "hr_avg1": "1m Average",
        "hr_avg5": "5m Average",
        "hr_avg_all": "Overall Avg",
        "hr_spark_lbl": "Total Hashrate (last seconds):",
        "hr_title": "📈 Total Hashrate",
        "core_col_id": "Core",
        "core_col_hr": "Hashrate",
        "core_col_rel": "Relative",
        "core_col_cpu": "CPU Load",
        "core_col_freq": "Freq",
        "core_col_st": "State",
        "core_est": "ESTIMATED",
        "core_act": "ACTIVE",
        "core_nodata": "NO DATA",
        "core_title": "🧠 Per-Core Performance (CPU)",
        "core_sub_est": "cpuminer reports total only · per-core value = average",
        "pool_testing": "testing...",
        "pool_offline": "offline / no response",
        "pool_collecting": "collecting...",
        "pool_cur_ping": "Current Ping",
        "pool_ping_graph": "Ping Graph",
        "pool_latency": "Latency",
        "pool_diff": "Difficulty",
        "pool_jobs": "Jobs/Blocks",
        "pool_acc_rej": "Accepted/Rej.",
        "pool_rej_reasons": "Reject Reason",
        "pool_acc_rate": "Accept Rate",
        "pool_rate_sh": "Share Rate",
        "pool_last_sh": "Last Share",
        "pool_acc_word": "accepted",
        "pool_rej_word": "rejected",
        "pool_rep_hr": "Reported Hash",
        "pool_err_rest": "Errors / Rest.",
        "pool_title": "🌐 Pool, Dynamic Ping & Shares",
        "sys_title": "🖥  System Telemetry",
        "sys_no_psutil": "not installed — pip install psutil",
        "sys_cpu_tot": "Total CPU",
        "sys_temp": "Temperature",
        "sys_bat": "Battery",
        "sys_charging": "charging",
        "sys_discharging": "discharging",
        "sys_net": "Network",
        "sys_proc_na": "process unavailable",
        "blk_new": "» NEW «",
        "blk_rej": "rejected",
        "blk_info": "each block = 1 share sent · ✓ accepted ✗ rejected · current {prog:.0f}% · avg {avg:.1f}s",
        "blk_title": "⛓  Live Share Chain",
        "grid_waiting": "waiting",
        "grid_legend": "[bold bright_green]■[/] accepted [bold green]{acc}[/]   [bold red]■[/] rejected [bold red]{rej}[/]   [bold yellow]{pulse}[/] mining ({spin} {since})   [dim]· showing {shown} of {tot} shares · efficiency {rate:.1f}%[/]",
        "grid_title": "🟩 Real-Time Share Map",
        "log_waiting": "Waiting for cpuminer output...",
        "log_title": "📜 Miner Event Log",
        "footer_live": "[bold yellow]Q[/]: Main Menu · Ctrl+C: quit · Web: [bold cyan]{web}[/] · Theme: [bold]{theme}[/] · BTC: [yellow]{btc}[/] · DGB: [cyan]{dgb}[/]",
        "bin_not_found": "cpuminer binary not found:",
        "starting_bg": "Starting cpuminer in the background...",
        "stopping_miner": "Stopping cpuminer...",
        "sum_title": "Session Summary",
        "sum_uptime": "Uptime:",
        "sum_shares": "Shares:",
        "sum_acc_of": "accepted out of",
        "sum_sent": "submitted",
        "sum_peak": "Peak hashrate:",
        "sum_support": "💝 Support the project:",
        "miner_safe_exit": "Miner safely terminated.",
    },
}


def tr(args, key):
    lang = getattr(args, "lang", "pt")
    table = I18N.get(lang, I18N["pt"])
    return table.get(key, I18N["pt"].get(key, key))


# --------------------------------------------------------------------------
# Temas Visuais Disponiveis (Terminal & Web CSS Variables)
# --------------------------------------------------------------------------
THEMES = {
    "cyberpunk": {
        "label": "Cyberpunk Neon",
        "primary": "bright_cyan",
        "secondary": "bright_green",
        "accent": "magenta",
        "warn": "yellow",
        "header_border": "bright_blue",
        "hash_border": "bright_green",
        "cores_border": "bright_cyan",
        "pool_border": "magenta",
        "sys_border": "yellow",
        "grid_border": "bright_green",
        "blocks_border": "yellow",
        "log_border": "bright_blue",
        "web_bg": "#080b12",
        "web_card": "#101726",
        "web_primary": "#00f0ff",
        "web_secondary": "#00ff88",
        "web_accent": "#ff00a0",
    },
    "matrix": {
        "label": "Matrix Hacker Green",
        "primary": "bright_green",
        "secondary": "green",
        "accent": "bright_green",
        "warn": "yellow",
        "header_border": "bright_green",
        "hash_border": "green",
        "cores_border": "bright_green",
        "pool_border": "green",
        "sys_border": "bright_green",
        "grid_border": "bright_green",
        "blocks_border": "green",
        "log_border": "green",
        "web_bg": "#030a04",
        "web_card": "#07170a",
        "web_primary": "#00ff41",
        "web_secondary": "#00cc33",
        "web_accent": "#39ff14",
    },
    "bitcoin_gold": {
        "label": "Bitcoin Gold & Amber",
        "primary": "bright_yellow",
        "secondary": "yellow",
        "accent": "dark_orange",
        "warn": "bright_red",
        "header_border": "yellow",
        "hash_border": "bright_yellow",
        "cores_border": "yellow",
        "pool_border": "dark_orange",
        "sys_border": "yellow",
        "grid_border": "bright_yellow",
        "blocks_border": "dark_orange",
        "log_border": "yellow",
        "web_bg": "#110d05",
        "web_card": "#1d1608",
        "web_primary": "#f7931a",
        "web_secondary": "#ffd700",
        "web_accent": "#ffae00",
    },
    "ocean": {
        "label": "Ocean Deep Blue",
        "primary": "bright_cyan",
        "secondary": "cyan",
        "accent": "dodger_blue1",
        "warn": "yellow",
        "header_border": "dodger_blue1",
        "hash_border": "bright_cyan",
        "cores_border": "cyan",
        "pool_border": "dodger_blue1",
        "sys_border": "cyan",
        "grid_border": "bright_cyan",
        "blocks_border": "dodger_blue1",
        "log_border": "cyan",
        "web_bg": "#04101c",
        "web_card": "#092038",
        "web_primary": "#38bdf8",
        "web_secondary": "#2dd4bf",
        "web_accent": "#0284c7",
    },
    "dracula": {
        "label": "Dracula Purple",
        "primary": "bright_magenta",
        "secondary": "magenta",
        "accent": "medium_purple1",
        "warn": "bright_yellow",
        "header_border": "medium_purple1",
        "hash_border": "bright_magenta",
        "cores_border": "magenta",
        "pool_border": "medium_purple1",
        "sys_border": "bright_magenta",
        "grid_border": "bright_magenta",
        "blocks_border": "magenta",
        "log_border": "medium_purple1",
        "web_bg": "#13111c",
        "web_card": "#1e1b2e",
        "web_primary": "#bd93f9",
        "web_secondary": "#50fa7b",
        "web_accent": "#ff79c6",
    },
    "crimson": {
        "label": "Crimson Red",
        "primary": "bright_red",
        "secondary": "red",
        "accent": "yellow",
        "warn": "bright_yellow",
        "header_border": "bright_red",
        "hash_border": "red",
        "cores_border": "bright_red",
        "pool_border": "yellow",
        "sys_border": "red",
        "grid_border": "bright_red",
        "blocks_border": "yellow",
        "log_border": "red",
        "web_bg": "#140507",
        "web_card": "#24090d",
        "web_primary": "#ff3355",
        "web_secondary": "#ffaa00",
        "web_accent": "#ff0033",
    },
}
THEME_KEYS = list(THEMES.keys())

# --------------------------------------------------------------------------
# Configuracao padrao e Pools Mundiais Multi-Algoritmo
# --------------------------------------------------------------------------
DEFAULT_BIN = "./cpuminer"
DEFAULT_ALGO = "sha256d"
DEFAULT_POOL = "stratum+tcp://dgb.fusionpool.pro:3332"
DEFAULT_USER = "DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9.cel1"
DEFAULT_PASS = "d=st,password=x"
DEFAULT_THEME = "cyberpunk"
DEFAULT_LANG = "pt"
DEFAULT_WEB_HOST = "0.0.0.0"
DEFAULT_WEB_PORT = 8080
LOG_FILE = "cpuminer_dashboard.log"
CONFIG_FILE = "miner_config.json"

KNOWN_POOLS = [
    # --- Pools Solicitadas pelo Usuário (DGB & Multi-Algo) ---
    ("M2Pool DGB", "Global (Multi-Algo)", "stratum+tcp://m2pool.com:3333"),
    ("M2Pool DGB Alt", "Global (Odo/Qubit/Skein)", "stratum+tcp://dgb.m2pool.com:3333"),
    ("Mining-Dutch", "Europe (NL Scrypt)", "stratum+tcp://europe.mining-dutch.nl:3437"),
    ("Mining-Dutch", "Americas (Scrypt)", "stratum+tcp://americas.mining-dutch.nl:3437"),
    ("Mining-Dutch Hub", "Europe (Multi-Coin)", "stratum+tcp://hub.mining-dutch.nl:3333"),
    ("SoloPool DGB", "Europe (SHA-256)", "stratum+tcp://dgb.solopool.eu:3335"),
    ("SoloPool DGB", "Europe (Scrypt)", "stratum+tcp://dgb.solopool.eu:3349"),
    ("SoloPool Org", "Global Solo (SHA/Scrypt)", "stratum+tcp://dgb.solopool.org:3335"),
    ("Zpool SHA256", "South America (BR)", "stratum+tcp://sha256.sa.mine.zpool.ca:3333"),
    ("Zpool SHA256", "North America (US)", "stratum+tcp://sha256.na.mine.zpool.ca:3333"),
    ("Zpool SHA256", "Europe (EU)", "stratum+tcp://sha256.eu.mine.zpool.ca:3333"),
    ("Zpool SHA256", "Asia (SEA)", "stratum+tcp://sha256.sea.mine.zpool.ca:3333"),
    ("Zpool Scrypt", "North America", "stratum+tcp://scrypt.na.mine.zpool.ca:3433"),
    ("Zpool Yescrypt", "Global (CPU)", "stratum+tcp://yescrypt.eu.mine.zpool.ca:6233"),
    ("Zpool Qubit", "North America (CPU/ASIC)", "stratum+tcp://qubit.na.mine.zpool.ca:4733"),
    ("Zpool Skein", "North America (CPU/ASIC)", "stratum+tcp://skein.na.mine.zpool.ca:4933"),
    ("P2Pool Network", "Decentralized (SPB)", "stratum+tcp://p2p-spb.xyz:5027"),
    ("P2Pool Network Alt", "Decentralized (Global)", "stratum+tcp://p2p-spb.xyz:5024"),
    ("MolePool DGB", "Europe Solo (SHA-256)", "stratum+tcp://eu.molepool.com:7451"),
    ("MolePool Merged", "Europe (DGB+DOGE Scrypt)", "stratum+tcp://eu.molepool.com:4601"),
    ("DigiByte.io Seed", "Global / Seed Nodes", "stratum+tcp://digibyte.io:3333"),
    ("TheBeePool DGB", "Global / Europe", "stratum+tcp://thebeepool.com:3333"),
    ("TheBeePool Stratum", "Europe Sub", "stratum+tcp://dgb.thebeepool.com:3333"),
    ("FenixPool DGB", "Global (SHA-256 Solo)", "stratum+tcp://fenixpool.com:6666"),
    ("FenixPool Scrypt", "Global (DGB+DOGE)", "stratum+tcp://fenixpool.com:6668"),
    ("FenixPool Qubit", "Global (CPU/ASIC)", "stratum+tcp://fenixpool.com:6660"),
    ("FenixPool Skein", "Global (CPU/ASIC)", "stratum+tcp://fenixpool.com:6661"),
    ("FenixPool Odocrypt", "Global (FPGA/GPU)", "stratum+tcp://fenixpool.com:6680"),
    ("Kryptex DGB", "Global (SHA-256)", "stratum+tcp://dgb.kryptex.network:7037"),
    ("Kryptex DGB Alt", "Europe / Global", "stratum+tcp://dgb.kryptex.network:7777"),
    ("Mining-Pool.io", "Europe (Qubit CPU)", "stratum+tcp://mining-pool.io:4073"),
    ("Mining-Pool.io", "Europe (Scrypt)", "stratum+tcp://mining-pool.io:4071"),
    ("HuurreXPool DGB", "Europe (SHA-256)", "stratum+tcp://huurrexpool.com:3333"),
    ("KriptoKyng DGB", "Global (SHA-256)", "stratum+tcp://stratum.kriptokyng.com:3312"),

    # --- Pools Famosas e Consagradas para CPUMiner e Multi-Algoritmo ---
    ("FusionPool DGB", "Global / Auto", "stratum+tcp://dgb.fusionpool.pro:3332"),
    ("ViaBTC DGB", "Global Smart", "stratum+tcp://dgb.viabtc.io:3333"),
    ("2Miners DGB", "Europe / Global", "stratum+tcp://dgb-sha256.2miners.com:3030"),
    ("Prohashing DGB", "USA (East Multi-Algo)", "stratum+tcp://prohashing.com:3335"),
    ("Prohashing Europe", "Europe (Multi-Algo)", "stratum+tcp://eu.prohashing.com:3335"),
    ("Zergpool Yespower", "Europe (CPU)", "stratum+tcp://yespower.eu.mine.zergpool.com:6533"),
    ("Zergpool SHA256", "North America", "stratum+tcp://sha256.na.mine.zergpool.com:3333"),
    ("Zergpool SHA256", "Europe", "stratum+tcp://sha256.eu.mine.zergpool.com:3333"),
    ("Zergpool SHA256", "Asia", "stratum+tcp://sha256.asia.mine.zergpool.com:3333"),
    ("Rplant Pool", "Europe (CPU Multi-Algo)", "stratum+tcp://stratum-eu.rplant.xyz:7042"),
    ("Unmineable CPU", "Global Auto (RX)", "stratum+tcp://rx.unmineable.com:3333"),
    ("Suprnova DGB", "Global", "stratum+tcp://dgbg.suprnova.cc:5222"),
]

SPARK = "▁▂▃▄▅▆▇█"
UNITS = {"": 1.0, "k": 1e3, "m": 1e6, "g": 1e9, "t": 1e12, "p": 1e15}

RE_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
RE_TS = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s*")
RE_CPU = re.compile(r"CPU\s*#(\d+):\s*([\d.]+)\s*([kmgtp]?)h(?:ash)?/s", re.I)
RE_THREAD = re.compile(r"thread\s+(\d+):.*?([\d.]+)\s*([kmgtp]?)hash/s", re.I)
RE_SHARE = re.compile(
    r"accepted:\s*(\d+)\s*/\s*(\d+)"
    r"(?:\s*\(([\d.]+)%\))?"
    r"(?:\s*\(diff\s*([\d.]+)\))?"
    r"\s*,?\s*([\d.]+)\s*([kmgtp]?)h(?:ash)?/s",
    re.I,
)
RE_REJECT = re.compile(r"reject(?:ed)?\s+reason:\s*(.+)", re.I)
RE_DIFF = re.compile(r"difficulty\s+(?:set to|changed to|is)?\s*([\d.]+)", re.I)
RE_JOB = re.compile(r"work restart|new block|new job|detected new block", re.I)
RE_ERR = re.compile(
    r"fail|error|interrupted|retry|timeout|timed out|unable|refused|reset|could not|denied",
    re.I,
)


def get_theme(args):
    tname = getattr(args, "theme", DEFAULT_THEME)
    return THEMES.get(tname, THEMES[DEFAULT_THEME])


# --------------------------------------------------------------------------
# Leitura de Teclado Multiplataforma
# --------------------------------------------------------------------------
def read_key():
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            ch2 = msvcrt.getch()
            return {b"H": "UP", b"P": "DOWN", b"K": "LEFT", b"M": "RIGHT"}.get(ch2, "")
        if ch in (b"\r", b"\n"):
            return "ENTER"
        if ch == b"\x1b":
            return "ESC"
        if ch == b"\x03":
            raise KeyboardInterrupt
        return ch.decode("utf-8", errors="ignore").lower()
    else:
        import select
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = os.read(fd, 1)
            if ch == b"\x03":
                raise KeyboardInterrupt
            if ch == b"\x1b":
                if select.select([fd], [], [], 0.04)[0]:
                    ch2 = os.read(fd, 1)
                    if ch2 in (b"[", b"O") and select.select([fd], [], [], 0.04)[0]:
                        ch3 = os.read(fd, 1)
                        return {
                            b"A": "UP",
                            b"B": "DOWN",
                            b"C": "RIGHT",
                            b"D": "LEFT",
                        }.get(ch3, "ESC")
                return "ESC"
            if ch in (b"\r", b"\n"):
                return "ENTER"
            return ch.decode("utf-8", errors="ignore").lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def poll_key_nonblocking():
    """Lê uma tecla sem bloquear o loop Live do terminal (usado para detectar 'Q' durante a mineração)."""
    if os.name == "nt":
        import msvcrt
        if not msvcrt.kbhit():
            return ""
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            if msvcrt.kbhit():
                msvcrt.getch()
            return ""
        if ch == b"\x03":
            raise KeyboardInterrupt
        return ch.decode("utf-8", errors="ignore").lower()
    else:
        import select
        try:
            fd = sys.stdin.fileno()
            if select.select([fd], [], [], 0)[0]:
                ch = os.read(fd, 1)
                if ch == b"\x03":
                    raise KeyboardInterrupt
                return ch.decode("utf-8", errors="ignore").lower()
        except Exception:
            pass
        return ""


# --------------------------------------------------------------------------
# Persistencia de Configuracao
# --------------------------------------------------------------------------
def load_saved_config(args, cli_argv):
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "--bin" not in cli_argv and "bin" in data:
            args.bin = data["bin"]
        if "-a" not in cli_argv and "--algo" not in cli_argv and "algo" in data:
            args.algo = data["algo"]
        if "-o" not in cli_argv and "--pool" not in cli_argv and "pool" in data:
            args.pool = data["pool"]
        if "-u" not in cli_argv and "--user" not in cli_argv and "user" in data:
            args.user = data["user"]
        if "-p" not in cli_argv and "--password" not in cli_argv and "password" in data:
            args.password = data["password"]
        if "-t" not in cli_argv and "--threads" not in cli_argv and "threads" in data:
            args.threads = int(data["threads"])
        if "--no-restart" not in cli_argv and "no_restart" in data:
            args.no_restart = bool(data["no_restart"])
        if "--theme" not in cli_argv and "theme" in data and data["theme"] in THEMES:
            args.theme = data["theme"]
        if "--lang" not in cli_argv and "lang" in data and data["lang"] in LANG_KEYS:
            args.lang = data["lang"]
        if "--web" not in cli_argv and "web" in data:
            args.web = bool(data["web"])
        if "--web-host" not in cli_argv and "web_host" in data:
            args.web_host = str(data["web_host"])
        if "--web-port" not in cli_argv and "web_port" in data:
            args.web_port = int(data["web_port"])
        if "--web-token" not in cli_argv and "web_token" in data:
            args.web_token = str(data["web_token"])
        if "custom_pools" in data and isinstance(data["custom_pools"], list):
            args.custom_pools = [
                tuple(item[:3]) for item in data["custom_pools"]
                if isinstance(item, (list, tuple)) and len(item) >= 3
            ]
    except Exception:
        pass


def save_config(args):
    data = {
        "bin": args.bin,
        "algo": args.algo,
        "pool": args.pool,
        "user": args.user,
        "password": args.password,
        "threads": args.threads,
        "no_restart": args.no_restart,
        "theme": getattr(args, "theme", DEFAULT_THEME),
        "lang": getattr(args, "lang", DEFAULT_LANG),
        "web": getattr(args, "web", False),
        "web_host": getattr(args, "web_host", DEFAULT_WEB_HOST),
        "web_port": getattr(args, "web_port", DEFAULT_WEB_PORT),
        "web_token": getattr(args, "web_token", ""),
        "custom_pools": [list(x[:3]) for x in getattr(args, "custom_pools", [])],
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------
# Helpers de Ping Dinamico Colorido e Formatacao
# --------------------------------------------------------------------------
def ping_color(ms):
    if ms is None or ms <= 0:
        return "red"
    if ms < 100:
        return "bright_green"
    if ms < 180:
        return "green"
    if ms < 300:
        return "yellow"
    return "red"


def colored_ping_sparkline(history, args, width=26):
    if not history:
        return Text(tr(args, "ping_wait"), style="dim")
    items = list(history)[-width:]
    valid = [x for x in items if x is not None and x > 0]
    if not valid:
        return Text("✖" * len(items), style="bold red")

    lo = min(valid)
    hi = max(valid)
    span = max(hi - lo, 25.0)

    t = Text()
    for ms in items:
        if ms is None or ms <= 0:
            t.append("✖", style="bold red")
        else:
            norm = min(1.0, max(0.0, (ms - lo) / span))
            idx = int(norm * (len(SPARK) - 1))
            t.append(SPARK[idx], style=f"bold {ping_color(ms)}")
    return t


def ping_bar_meter(ms, args, width=16):
    if ms is None or ms <= 0:
        return Text("░░░░░░░░░░░░░░░░ OFFLINE", style="bold red")
    c = ping_color(ms)
    ratio = min(1.0, max(0.08, ms / 400.0))
    filled = int(round(width * ratio))
    bar_str = "█" * filled + "░" * (width - filled)
    label = (
        tr(args, "ping_exc")
        if ms < 100
        else tr(args, "ping_good")
        if ms < 180
        else tr(args, "ping_med")
        if ms < 300
        else tr(args, "ping_high")
    )
    return Text.from_markup(f"[bold {c}]{bar_str}[/] [{c}]{ms:.0f}ms ({label})[/]")


def fmt_hash(h):
    if h is None:
        return "—"
    for unit, div in (("GH/s", 1e9), ("MH/s", 1e6), ("kH/s", 1e3)):
        if h >= div:
            return f"{h / div:,.2f} {unit}"
    return f"{h:,.2f} H/s"


def fmt_dur(seconds):
    seconds = int(max(0, seconds))
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    if d:
        return f"{d}d {h:02d}h {m:02d}m {s:02d}s"
    return f"{h:02d}h {m:02d}m {s:02d}s"


def fmt_ago(ts, args):
    if not ts:
        return "—"
    dur = fmt_dur(time.time() - ts)
    if getattr(args, "lang", "pt") == "en":
        return f"{dur} ago"
    return f"há {dur}"


def fmt_bytes(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


def sparkline(values, width):
    if not values:
        return "—"
    values = list(values)[-width:]
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return SPARK[3] * len(values)
    return "".join(SPARK[int((v - lo) / (hi - lo) * (len(SPARK) - 1))] for v in values)


def bar(pct, width=12):
    pct = max(0.0, min(100.0, pct))
    filled = int(round(width * pct / 100))
    return "█" * filled + "░" * (width - filled)


def color_pct(pct, warn=60, crit=85):
    if pct >= crit:
        return "red"
    if pct >= warn:
        return "yellow"
    return "green"


def short_wallet(w, keep=10):
    if len(w) <= keep * 2 + 3:
        return w
    return f"{w[:keep]}…{w[-keep:]}"


# --------------------------------------------------------------------------
# Tela de Configuracao (Anterior vs Nova + Web + Temas + Idiomas PT/EN)
# --------------------------------------------------------------------------
def screen_config(args):
    old_cfg = {
        "bin": args.bin,
        "algo": args.algo,
        "pool": args.pool,
        "user": args.user,
        "password": args.password,
        "threads": args.threads,
        "auto_restart": not args.no_restart,
        "web": getattr(args, "web", False),
        "web_port": getattr(args, "web_port", DEFAULT_WEB_PORT),
        "web_token": getattr(args, "web_token", ""),
        "theme": getattr(args, "theme", DEFAULT_THEME),
        "lang": getattr(args, "lang", DEFAULT_LANG),
    }
    new_cfg = dict(old_cfg)

    idx = 0
    total_items = 12 + 2

    while True:
        console.clear()
        args.lang = new_cfg["lang"]
        cur_theme = THEMES.get(new_cfg["theme"], THEMES[DEFAULT_THEME])

        fields = [
            ("bin", tr(args, "fld_bin"), "str"),
            ("algo", tr(args, "fld_algo"), "str"),
            ("pool", tr(args, "fld_pool"), "str"),
            ("user", tr(args, "fld_user"), "str"),
            ("password", tr(args, "fld_pass"), "str"),
            ("threads", tr(args, "fld_threads"), "int"),
            ("auto_restart", tr(args, "fld_restart"), "bool"),
            ("web", tr(args, "fld_web"), "bool"),
            ("web_port", tr(args, "fld_web_port"), "int"),
            ("web_token", tr(args, "fld_web_token"), "str"),
            ("theme", tr(args, "fld_theme"), "theme"),
            ("lang", tr(args, "fld_lang"), "lang"),
        ]

        old_table = Table(box=box.SIMPLE, expand=True, show_header=False, padding=(0, 1))
        old_table.add_column("Campo 1", style="dim cyan", width=20)
        old_table.add_column("Valor 1", style="grey70", overflow="fold")
        old_table.add_column("Campo 2", style="dim cyan", width=20)
        old_table.add_column("Valor 2", style="grey70", overflow="fold")

        old_table.add_row(tr(args, "fld_bin") + ":", old_cfg["bin"], tr(args, "fld_algo") + ":", old_cfg["algo"])
        old_table.add_row(
            tr(args, "fld_pool") + ":",
            old_cfg["pool"],
            tr(args, "fld_threads") + ":",
            tr(args, "auto_0") if old_cfg["threads"] == 0 else str(old_cfg["threads"]),
        )
        old_table.add_row(
            tr(args, "fld_user") + ":",
            old_cfg["user"],
            tr(args, "fld_web") + ":",
            f"{tr(args, 'enabled')} (:{old_cfg['web_port']})" if old_cfg["web"] else tr(args, "disabled"),
        )
        old_table.add_row(
            tr(args, "fld_theme") + ":",
            THEMES.get(old_cfg["theme"], THEMES[DEFAULT_THEME])["label"],
            tr(args, "fld_lang") + ":",
            I18N.get(old_cfg["lang"], I18N["pt"])["lang_label"],
        )

        panel_old = Panel(
            old_table,
            title=f"[bold yellow]{tr(args, 'cfg_old_title')}[/]",
            border_style="yellow",
            box=box.ROUNDED,
        )

        new_table = Table(
            box=box.SIMPLE_HEAD,
            expand=True,
            header_style=f"bold {cur_theme['primary']}",
            padding=(0, 1),
        )
        new_table.add_column("", width=3, justify="center")
        new_table.add_column(tr(args, "cfg_col_param"), width=25)
        new_table.add_column(tr(args, "cfg_col_old"), style="dim", overflow="fold")
        new_table.add_column(tr(args, "cfg_col_new"), overflow="fold")
        new_table.add_column(tr(args, "cfg_col_status"), width=14, justify="center")

        for i, (key, label, ftype) in enumerate(fields):
            sel = idx == i
            ov = old_cfg[key]
            nv = new_cfg[key]
            changed = ov != nv

            if ftype == "bool":
                ov_str = tr(args, "enabled") if ov else tr(args, "disabled")
                nv_str = tr(args, "enabled") if nv else tr(args, "disabled")
            elif ftype == "theme":
                ov_str = THEMES.get(ov, THEMES[DEFAULT_THEME])["label"]
                nv_str = f"🎨 {THEMES.get(nv, THEMES[DEFAULT_THEME])['label']} (◀/▶)"
            elif ftype == "lang":
                ov_str = I18N.get(ov, I18N["pt"])["lang_label"]
                nv_str = f"🌐 {I18N.get(nv, I18N['pt'])['lang_label']} (◀/▶)"
            elif key == "threads":
                ov_str = tr(args, "auto_0") if ov == 0 else str(ov)
                nv_str = tr(args, "auto_0") if nv == 0 else str(nv)
            else:
                ov_str = str(ov) if ov != "" else "(vazio)"
                nv_str = str(nv) if nv != "" else "(vazio)"

            pointer = f"[bold {cur_theme['secondary']}]❯[/]" if sel else " "
            lbl_style = f"bold bright_white on {cur_theme['header_border']}" if sel else "bold white"
            val_style = "bold bright_yellow" if changed else (f"bold {cur_theme['secondary']}" if sel else "white")
            badge = f"[bold yellow]{tr(args, 'cfg_changed')}[/]" if changed else f"[dim]{tr(args, 'cfg_kept')}[/]"

            new_table.add_row(
                pointer,
                Text(f" {label} ", style=lbl_style),
                ov_str,
                Text(nv_str, style=val_style),
                badge,
            )

        panel_new = Panel(
            new_table,
            title=f"[bold {cur_theme['secondary']}]{tr(args, 'cfg_new_title')}[/]",
            border_style=cur_theme["secondary"],
            box=box.ROUNDED,
        )

        sel_save = idx == len(fields)
        sel_cancel = idx == len(fields) + 1

        btn_save = Panel(
            Align.center(
                f"[bold black on bright_green]{tr(args, 'btn_save_act')}[/]"
                if sel_save
                else f"[bold green]{tr(args, 'btn_save_idle')}[/]"
            ),
            border_style="bright_green" if sel_save else "green",
            box=box.HEAVY if sel_save else box.ROUNDED,
        )
        btn_cancel = Panel(
            Align.center(
                f"[bold white on red]{tr(args, 'btn_cancel_act')}[/]"
                if sel_cancel
                else f"[bold red]{tr(args, 'btn_cancel_idle')}[/]"
            ),
            border_style="bright_red" if sel_cancel else "red",
            box=box.HEAVY if sel_cancel else box.ROUNDED,
        )

        act_grid = Table.grid(expand=True, padding=(0, 2))
        act_grid.add_column(ratio=1)
        act_grid.add_column(ratio=1)
        act_grid.add_row(btn_save, btn_cancel)

        help_txt = Align.center(Text.from_markup(tr(args, "cfg_nav_help")))

        console.print(
            Panel(
                Group(panel_old, Text(""), panel_new, Text(""), act_grid, Text(""), help_txt),
                title=f"[bold white]{tr(args, 'cfg_center_title')} ({cur_theme['label']})[/]",
                border_style=cur_theme["header_border"],
                box=box.DOUBLE,
                padding=(1, 2),
            )
        )

        k = read_key()
        if k == "UP":
            idx = (idx - 1) % total_items
        elif k == "DOWN":
            idx = (idx + 1) % total_items
        elif k in ("LEFT", "RIGHT"):
            if idx < len(fields) and fields[idx][2] == "theme":
                cur_idx = THEME_KEYS.index(new_cfg["theme"]) if new_cfg["theme"] in THEME_KEYS else 0
                step = 1 if k == "RIGHT" else -1
                new_cfg["theme"] = THEME_KEYS[(cur_idx + step) % len(THEME_KEYS)]
            elif idx < len(fields) and fields[idx][2] == "lang":
                cur_idx = LANG_KEYS.index(new_cfg["lang"]) if new_cfg["lang"] in LANG_KEYS else 0
                new_cfg["lang"] = LANG_KEYS[(cur_idx + 1) % len(LANG_KEYS)]
            elif idx < len(fields) and fields[idx][2] == "bool":
                new_cfg[fields[idx][0]] = not new_cfg[fields[idx][0]]
            elif idx >= len(fields):
                idx = len(fields) + 1 if idx == len(fields) else len(fields)
        elif k == "ESC":
            args.lang = old_cfg["lang"]
            return
        elif k == "ENTER":
            if idx < len(fields):
                key, label, ftype = fields[idx]
                if ftype == "bool":
                    new_cfg[key] = not new_cfg[key]
                elif ftype == "theme":
                    cur_idx = THEME_KEYS.index(new_cfg["theme"]) if new_cfg["theme"] in THEME_KEYS else 0
                    new_cfg["theme"] = THEME_KEYS[(cur_idx + 1) % len(THEME_KEYS)]
                elif ftype == "lang":
                    cur_idx = LANG_KEYS.index(new_cfg["lang"]) if new_cfg["lang"] in LANG_KEYS else 0
                    new_cfg["lang"] = LANG_KEYS[(cur_idx + 1) % len(LANG_KEYS)]
                elif ftype == "int":
                    console.print(f"\n[dim]{tr(args, 'prompt_old_val')} {label}:[/] [yellow]{old_cfg[key]}[/]")
                    new_cfg[key] = IntPrompt.ask(
                        f"[bold bright_cyan]{tr(args, 'prompt_new_val')} {label}[/]",
                        default=new_cfg[key],
                    )
                else:
                    console.print(f"\n[dim]{tr(args, 'prompt_old_val')} {label}:[/] [yellow]{old_cfg[key]}[/]")
                    new_cfg[key] = Prompt.ask(
                        f"[bold bright_cyan]{tr(args, 'prompt_new_val')} {label}[/]",
                        default=str(new_cfg[key]),
                    ).strip()
            elif idx == len(fields):
                args.bin = new_cfg["bin"]
                args.algo = new_cfg["algo"]
                args.pool = new_cfg["pool"]
                args.user = new_cfg["user"]
                args.password = new_cfg["password"]
                args.threads = int(new_cfg["threads"])
                args.no_restart = not bool(new_cfg["auto_restart"])
                args.web = bool(new_cfg["web"])
                args.web_port = int(new_cfg["web_port"])
                args.web_token = str(new_cfg["web_token"])
                args.theme = new_cfg["theme"]
                args.lang = new_cfg["lang"]
                save_config(args)
                console.print(f"\n[bold green]{tr(args, 'cfg_saved_ok')} {CONFIG_FILE}![/]")
                time.sleep(1.0)
                return
            else:
                args.lang = old_cfg["lang"]
                return


# --------------------------------------------------------------------------
# Tela de Teste de DNS e Latencia Stratum com Grafico Colorido Dinamico
# --------------------------------------------------------------------------
_GLOBAL_DNS_CACHE = {"timestamp": 0.0, "results": []}


def probe_single_pool(name, region, url, dns_fail_txt="Falha DNS", samples=2):
    raw_url = str(url or "").strip()
    try:
        u = urlparse(raw_url if "://" in raw_url else "tcp://" + raw_url)
        host = u.hostname or ""
        port = u.port or 3333
    except Exception:
        host = raw_url
        port = 3333

    try:
        port = int(port)
    except Exception:
        port = 3333

    res = {
        "name": str(name),
        "region": str(region),
        "url": raw_url,
        "host": str(host),
        "port": port,
        "ip": "—",
        "dns_ms": None,
        "tcp_ms": None,
        "pings": [],
        "status": "...",
        "ok": False,
    }

    if not host:
        res["status"] = dns_fail_txt
        return res

    t0 = time.perf_counter()
    try:
        infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        dns_ms = (time.perf_counter() - t0) * 1000.0
        ip = infos[0][4][0] if infos else "—"
        res["ip"] = ip
        res["dns_ms"] = round(dns_ms, 1)
    except Exception:
        res["status"] = dns_fail_txt
        return res

    ok_pings = []
    # Teste de latência TCP Stratum com timeout ágil de 1.5s por amostra
    sample_count = max(1, min(samples, 2))
    for _ in range(sample_count):
        t1 = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=1.5):
                ms = (time.perf_counter() - t1) * 1000.0
                res["pings"].append(round(ms, 1))
                ok_pings.append(ms)
        except Exception:
            res["pings"].append(None)

    if ok_pings:
        res["tcp_ms"] = round(sum(ok_pings) / len(ok_pings), 1)
        res["ok"] = True
        res["status"] = "ONLINE"
    else:
        res["status"] = "Timeout / Offline"

    return res


def normalize_pool_url(raw_url):
    u_str = str(raw_url or "").strip()
    if not u_str:
        return ""
    if "://" not in u_str:
        u_str = "stratum+tcp://" + u_str
    parsed = urlparse(u_str)
    if not parsed.port:
        u_str = u_str.rstrip("/") + ":3333"
    return u_str


def run_all_pools_probe(args, force_refresh=True):
    global _GLOBAL_DNS_CACHE
    now = time.time()
    if not force_refresh and (now - _GLOBAL_DNS_CACHE["timestamp"] < 12.0) and _GLOBAL_DNS_CACHE["results"]:
        return list(_GLOBAL_DNS_CACHE["results"])

    custom_list = list(getattr(args, "custom_pools", []) or [])
    custom_urls = {str(c[2]).lower() for c in custom_list if len(c) >= 3}
    pools_to_test = []

    for c in custom_list:
        if len(c) >= 3 and not any(p[2].lower() == str(c[2]).lower() for p in pools_to_test):
            pools_to_test.append((str(c[0]), str(c[1]), str(c[2])))

    for p in KNOWN_POOLS:
        if not any(x[2].lower() == p[2].lower() for x in pools_to_test):
            pools_to_test.append(p)

    cur_pool = str(getattr(args, "pool", "") or "").strip()
    if cur_pool and not any(p[2].lower() == cur_pool.lower() for p in pools_to_test):
        pools_to_test.insert(0, (tr(args, "custom_pool_name"), tr(args, "custom_pool_reg"), cur_pool))

    results = []
    dns_fail_txt = tr(args, "dns_fail")

    def worker(item):
        try:
            r = probe_single_pool(item[0], item[1], item[2], dns_fail_txt=dns_fail_txt)
            r["custom"] = r["url"].lower() in custom_urls
            return r
        except Exception:
            return {
                "name": str(item[0] if len(item) > 0 else "Unknown"),
                "region": str(item[1] if len(item) > 1 else "—"),
                "url": str(item[2] if len(item) > 2 else ""),
                "host": "",
                "port": 3333,
                "ip": "—",
                "dns_ms": None,
                "tcp_ms": None,
                "pings": [],
                "status": dns_fail_txt,
                "ok": False,
                "custom": False,
            }

    max_workers = min(24, max(4, len(pools_to_test)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, p): p for p in pools_to_test}
        try:
            for fut in as_completed(futures, timeout=12.0):
                try:
                    res = fut.result()
                    results.append(res)
                except Exception:
                    pass
        except Exception:
            # Em caso de timeout global, colhe os resultados que já finalizaram
            for fut in futures:
                if fut.done() and not fut.cancelled():
                    try:
                        results.append(fut.result())
                    except Exception:
                        pass

    # Garante que qualquer pool que não finalizou entre como Offline para não sumir da lista
    tested_urls = {r["url"].lower() for r in results}
    for p in pools_to_test:
        if p[2].lower() not in tested_urls:
            results.append({
                "name": str(p[0]),
                "region": str(p[1]),
                "url": str(p[2]),
                "host": "",
                "port": 3333,
                "ip": "—",
                "dns_ms": None,
                "tcp_ms": None,
                "pings": [],
                "status": "Timeout / Offline",
                "ok": False,
                "custom": p[2].lower() in custom_urls,
            })

    results.sort(key=lambda r: (0 if r.get("ok") else 1, r.get("tcp_ms") if r.get("tcp_ms") is not None else 99999))
    _GLOBAL_DNS_CACHE["timestamp"] = time.time()
    _GLOBAL_DNS_CACHE["results"] = results
    return results


def screen_dns_test(args):
    theme = get_theme(args)
    while True:
        console.clear()
        with console.status(
            f"[bold {theme['primary']}]{tr(args, 'dns_testing_spinner')}[/]",
            spinner="earth",
        ):
            results = run_all_pools_probe(args)

        sel = 0
        while True:
            console.clear()
            tb = Table(
                box=box.SIMPLE_HEAD,
                expand=True,
                header_style=f"bold {theme['primary']}",
                padding=(0, 1),
            )
            tb.add_column("", width=2, justify="center")
            tb.add_column("#", width=3, justify="right", style="dim")
            tb.add_column(tr(args, "dns_col_pool"), width=18, no_wrap=True)
            tb.add_column(tr(args, "dns_col_region"), width=19, no_wrap=True)
            tb.add_column(tr(args, "dns_col_host"), overflow="fold")
            tb.add_column(tr(args, "dns_col_dns"), width=8, justify="right")
            tb.add_column(tr(args, "dns_col_ping"), width=10, justify="right")
            tb.add_column(tr(args, "dns_col_graph"), width=30, no_wrap=True)

            for i, r in enumerate(results):
                is_sel = i == sel
                is_cur = r["url"].lower() == args.pool.lower()
                ptr = f"[bold {theme['secondary']}]❯[/]" if is_sel else " "

                dns_txt = f"{r['dns_ms']:.0f} ms" if r["dns_ms"] is not None else "—"
                if r["ok"]:
                    ms = r["tcp_ms"]
                    c = ping_color(ms)
                    tcp_txt = f"[bold {c}]{ms:.0f} ms[/]"
                    graph_cell = ping_bar_meter(ms, args, width=12)
                else:
                    tcp_txt = "[red]—[/]"
                    graph_cell = Text(f"✖ {r['status']}", style="bold red")

                name_label = r["name"] + (" [bold yellow]★[/]" if is_cur else "")
                row_style = "on grey19" if is_sel else ""

                tb.add_row(
                    ptr,
                    str(i + 1),
                    name_label,
                    r["region"],
                    f"{r['host']}:{r['port']}",
                    dns_txt,
                    tcp_txt,
                    graph_cell,
                    style=row_style,
                )

            best = results[0] if results and results[0]["ok"] else None
            best_banner = (
                f"[bold green]{tr(args, 'dns_best_ok')}[/] [bold white]{best['name']} ({best['region']})[/] "
                f"— [bright_green]{best['tcp_ms']:.0f} ms[/] ([cyan]{best['url']}[/])"
                if best
                else f"[bold red]{tr(args, 'dns_best_fail')}[/]"
            )

            legend_ping = Text.from_markup(tr(args, "dns_legend"))
            footer_help = Text.from_markup(tr(args, "dns_nav_help"))

            console.print(
                Panel(
                    Group(
                        Panel(Align.center(best_banner), border_style="green", box=box.ROUNDED),
                        tb,
                        Text(""),
                        Align.center(legend_ping),
                        Align.center(footer_help),
                    ),
                    title=f"[bold {theme['primary']}]{tr(args, 'dns_title')}[/]",
                    subtitle=f"[dim]{tr(args, 'dns_subtitle')} ({args.pool})[/]",
                    border_style=theme["primary"],
                    box=box.DOUBLE,
                    padding=(1, 2),
                )
            )

            k = read_key()
            if k == "UP":
                sel = (sel - 1) % len(results)
            elif k == "DOWN":
                sel = (sel + 1) % len(results)
            elif k == "r":
                break
            elif k in ("ESC", "q"):
                return
            elif k == "ENTER":
                chosen = results[sel]
                args.pool = chosen["url"]
                save_config(args)
                console.print(
                    f"\n[bold green]{tr(args, 'dns_pool_updated')} {chosen['name']} ({chosen['url']})![/]"
                )
                time.sleep(1.2)
                return


# --------------------------------------------------------------------------
# Tela de Doacao (Bitcoin & DigiByte)
# --------------------------------------------------------------------------
def copy_to_clipboard(text):
    cmds = [
        ["termux-clipboard-set"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
        ["wl-copy"],
        ["pbcopy"],
        ["clip"],
    ]
    for cmd in cmds:
        if shutil.which(cmd[0]):
            try:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, close_fds=True)
                p.communicate(input=text.encode("utf-8"), timeout=2)
                if p.returncode == 0:
                    return True
            except Exception:
                pass
    return False


def screen_donate(args):
    theme = get_theme(args)
    sel = 0
    msg_feedback = ""

    while True:
        console.clear()
        intro = Text.from_markup(tr(args, "don_intro"))
        btc_selected = sel == 0
        dgb_selected = sel == 1

        btc_panel = Panel(
            Align.center(
                Text.from_markup(
                    f"[bold bright_yellow]{tr(args, 'don_btc_header')}[/]\n\n"
                    f"[bold bright_white on grey19]  {DONATE_BTC}  [/]\n\n"
                    + (
                        f"[bold black on bright_yellow]{tr(args, 'don_press_btc')}[/]"
                        if btc_selected
                        else f"[dim]{tr(args, 'don_select_hint')}[/]"
                    )
                )
            ),
            title=f"[bold yellow]{tr(args, 'don_btc_box')}[/]",
            border_style="bright_yellow" if btc_selected else "yellow",
            box=box.HEAVY if btc_selected else box.ROUNDED,
            padding=(1, 2),
        )

        dgb_panel = Panel(
            Align.center(
                Text.from_markup(
                    f"[bold bright_cyan]{tr(args, 'don_dgb_header')}[/]\n\n"
                    f"[bold bright_white on grey19]  {DONATE_DGB}  [/]\n\n"
                    + (
                        f"[bold black on bright_cyan]{tr(args, 'don_press_dgb')}[/]"
                        if dgb_selected
                        else f"[dim]{tr(args, 'don_select_hint')}[/]"
                    )
                )
            ),
            title=f"[bold bright_cyan]{tr(args, 'don_dgb_box')}[/]",
            border_style="bright_cyan" if dgb_selected else "cyan",
            box=box.HEAVY if dgb_selected else box.ROUNDED,
            padding=(1, 2),
        )

        feedback_line = (
            Align.center(Text.from_markup(msg_feedback))
            if msg_feedback
            else Align.center(Text.from_markup(f"[dim]{tr(args, 'don_mouse_hint')}[/]"))
        )

        help_nav = Align.center(Text.from_markup(tr(args, "don_nav_help")))

        console.print(
            Panel(
                Group(
                    Align.center(intro),
                    btc_panel,
                    Text(""),
                    dgb_panel,
                    Text(""),
                    feedback_line,
                    Text(""),
                    help_nav,
                ),
                title=f"[bold {theme['primary']}]{tr(args, 'don_title')}[/]",
                border_style=theme["primary"],
                box=box.DOUBLE,
                padding=(1, 3),
            )
        )

        k = read_key()
        if k in ("UP", "DOWN", "LEFT", "RIGHT"):
            sel = 1 - sel
        elif k in ("ESC", "q"):
            break
        elif k == "ENTER":
            addr = DONATE_BTC if sel == 0 else DONATE_DGB
            coin = "Bitcoin (BTC)" if sel == 0 else "DigiByte (DGB)"
            if copy_to_clipboard(addr):
                msg_feedback = f"[bold bright_green]{tr(args, 'don_copied_ok')} ({coin}) {addr}[/]"
            else:
                msg_feedback = f"[bold yellow]{tr(args, 'don_copied_manual')} ({coin})[/] [bold white]{addr}[/]"


# --------------------------------------------------------------------------
# Tela Sobre (About)
# --------------------------------------------------------------------------
def screen_about(args):
    theme = get_theme(args)
    console.clear()
    about_text = Text.from_markup(
        f"\n[bold {theme['secondary']}]⛏  CPUMINER LIVE DASHBOARD · UNIVERSAL MULTI-ALGO EDITION[/]\n"
        f"[dim]{tr(args, 'about_sub')}[/]\n\n"
        f"👨‍💻 [bold white]{tr(args, 'about_dev')}[/] [bold {theme['primary']}]Luan Quaresma[/]\n\n"
        f"[white]{tr(args, 'about_body')}[/]\n\n"
        f"[bold yellow]{tr(args, 'about_wallets')}[/]\n"
        f"[bold bright_yellow]• BTC:[/] [white]{DONATE_BTC}[/]\n"
        f"[bold bright_cyan]• DGB:[/] [white]{DONATE_DGB}[/]\n\n"
        "[dim]Architecture: Python 3 · Rich Live TUI · Embedded HTTP/JSON Web Dashboard · Psutil[/]\n"
    )
    panel = Panel(
        Align.center(about_text),
        title=f"[bold {theme['primary']}]{tr(args, 'about_title')}[/]",
        subtitle=f"[dim]{tr(args, 'about_footer')}[/]",
        border_style=theme["primary"],
        box=box.DOUBLE,
        padding=(1, 4),
    )
    console.print(panel)
    while True:
        if read_key() in ("ENTER", "ESC", "q"):
            break


# --------------------------------------------------------------------------
# Menu Principal
# --------------------------------------------------------------------------
def show_start_menu(args):
    sel = 0
    total_btns = 6

    while True:
        console.clear()
        theme = get_theme(args)

        ascii_logo = (
            f"[bold {theme['secondary']}]   ____ ____  _   _ __  __ ___ _   _ _____ ____  [/]\n"
            f"[bold {theme['secondary']}]  / ___|  _ \\| | | |  \\/  |_ _| \\ | | ____|  _ \\ [/]\n"
            f"[bold {theme['primary']}] | |   | |_) | | | | |\\/| || ||  \\| |  _| | |_) |[/]\n"
            f"[bold {theme['primary']}] | |___|  __/| |_| | |  | || || |\\  | |___|  _ < [/]\n"
            f"[bold {theme['accent']}]  \\____|_|    \\___/|_|  |_|___|_| \\_|_____|_| \\_\\[/]"
        )

        header_grid = Table.grid(expand=True)
        header_grid.add_column(justify="center")
        header_grid.add_row(ascii_logo)
        header_grid.add_row(f"[bold white]{tr(args, 'subtitle_edition')}[/]")
        header_grid.add_row(f"[italic {theme['primary']}]{tr(args, 'dev_by')} · {tr(args, 'lang_label')}[/]")

        u = urlparse(args.pool if "://" in args.pool else "tcp://" + args.pool)
        cfg_summary = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 1))
        cfg_summary.add_column("K1", style=f"bold {theme['primary']}", width=14)
        cfg_summary.add_column("V1", style="white", overflow="fold")
        cfg_summary.add_column("K2", style=f"bold {theme['primary']}", width=14)
        cfg_summary.add_column("V2", style="white", overflow="fold")

        web_status = (
            f"[bold bright_green]http://{args.web_host}:{args.web_port}[/]"
            if getattr(args, "web", False)
            else f"[dim]{tr(args, 'disabled')} (--web)[/]"
        )

        cfg_summary.add_row(
            tr(args, "active_pool"),
            f"[bold {theme['secondary']}]{u.hostname}:{u.port}[/]",
            tr(args, "algorithm"),
            f"[yellow]{args.algo}[/]",
        )
        cfg_summary.add_row(
            tr(args, "wallet"),
            short_wallet(args.user.split(".")[0], 12),
            tr(args, "worker"),
            args.user.split(".", 1)[1] if "." in args.user else "default",
        )
        cfg_summary.add_row(
            tr(args, "cpu_threads"),
            tr(args, "auto") if args.threads == 0 else f"{args.threads} threads",
            "Auto-Restart:",
            f"[red]{tr(args, 'disabled')}[/]" if args.no_restart else f"[green]{tr(args, 'enabled')}[/]",
        )
        cfg_summary.add_row(
            tr(args, "web_panel"),
            web_status,
            tr(args, "language"),
            f"[bold yellow]{tr(args, 'lang_label')}[/] [dim](L) · {theme['label']}[/]",
        )

        def make_btn(idx, icon, title, desc, color):
            active = sel == idx
            if active:
                content = Text.from_markup(
                    f"[bold black on {color}] ❯ {icon}  {title} ❮ [/]\n"
                    f"[bold {color}]{desc}[/]"
                )
                return Panel(
                    Align.center(content),
                    border_style=f"bold {color}",
                    box=box.HEAVY,
                    padding=(0, 1),
                )
            else:
                content = Text.from_markup(
                    f"[bold {color}]{icon}  {title}[/]\n[dim]{desc}[/]"
                )
                return Panel(
                    Align.center(content),
                    border_style="grey37",
                    box=box.ROUNDED,
                    padding=(0, 1),
                )

        b0 = make_btn(0, "▶", tr(args, "btn1_title"), tr(args, "btn1_desc"), "bright_green")
        b1 = make_btn(1, "⚙️", tr(args, "btn2_title"), tr(args, "btn2_desc"), "yellow")
        b2 = make_btn(2, "🌍", tr(args, "btn3_title"), tr(args, "btn3_desc"), "bright_cyan")
        b3 = make_btn(3, "💝", tr(args, "btn4_title"), tr(args, "btn4_desc"), "bright_yellow")
        b4 = make_btn(4, "ℹ️", tr(args, "btn5_title"), tr(args, "btn5_desc"), "magenta")
        b5 = make_btn(5, "✖", tr(args, "btn6_title"), tr(args, "btn6_desc"), "bright_red")

        btns_grid = Table.grid(expand=True, padding=(0, 1))
        btns_grid.add_column(ratio=1)
        btns_grid.add_column(ratio=1)
        btns_grid.add_row(b0, b1)
        btns_grid.add_row(b2, b3)
        btns_grid.add_row(b4, b5)

        donate_footer = Panel(
            Align.center(
                Text.from_markup(
                    f"[bold yellow]{tr(args, 'donate_Validate_btc')}[/] [white]{DONATE_BTC}[/]   "
                    f"[bold bright_cyan]{tr(args, 'donate_Validate_dgb')}[/] [white]{DONATE_DGB}[/]"
                )
            ),
            border_style="grey35",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        footer_nav = Align.center(Text.from_markup(tr(args, "menu_nav_help")))

        console.print(
            Panel(
                Group(
                    Panel(header_grid, border_style=theme["header_border"], box=box.ROUNDED),
                    Panel(
                        cfg_summary,
                        title=f"[bold white]{tr(args, 'ready_summary_title')}[/]",
                        border_style=theme["primary"],
                        box=box.ROUNDED,
                    ),
                    btns_grid,
                    donate_footer,
                    footer_nav,
                ),
                title=f"[bold bright_white]{tr(args, 'main_menu_title')} · {theme['label'].upper()} · {tr(args, 'lang_label')}[/]",
                border_style=theme["primary"],
                box=box.DOUBLE,
                padding=(1, 2),
            )
        )

        k = read_key()
        if k == "UP":
            sel = (sel - 2) % total_btns
        elif k == "DOWN":
            sel = (sel + 2) % total_btns
        elif k == "LEFT":
            sel = (sel - 1) % total_btns
        elif k == "RIGHT":
            sel = (sel + 1) % total_btns
        elif k == "l":
            args.lang = "en" if getattr(args, "lang", "pt") == "pt" else "pt"
            save_config(args)
        elif k in ("1", "2", "3", "4", "5", "6"):
            sel = int(k) - 1
            k = "ENTER"
        elif k in ("q", "ESC"):
            sel = 5
            k = "ENTER"

        if k == "ENTER":
            if sel == 0:
                break
            elif sel == 1:
                screen_config(args)
            elif sel == 2:
                screen_dns_test(args)
            elif sel == 3:
                screen_donate(args)
            elif sel == 4:
                screen_about(args)
            elif sel == 5:
                console.print(f"\n[yellow]{tr(args, 'bye_msg')}[/yellow]")
                sys.exit(0)


# --------------------------------------------------------------------------
# Estatisticas do minerador
# --------------------------------------------------------------------------
class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.cores = {}
        self.history = collections.deque(maxlen=600)
        self.accepted = 0
        self.total_shares = 0
        self.last_share_ts = None
        self.last_share_ok = None
        self.share_times = collections.deque(maxlen=500)
        self.reported_hash = None
        self.best_hash = 0.0
        self.difficulty = None
        self.jobs = 0
        self.errors = 0
        self.restarts = 0
        self.state = "starting"
        self.pid = None
        self.fatal = None
        self.events = collections.deque(maxlen=300)
        self.logfile = None
        self.pool_latency = None
        self.pool_online = None
        self.ping_history = collections.deque(maxlen=60)
        self.blocks = collections.deque(maxlen=50)
        self.share_diff = None
        self.reject_reasons = collections.Counter()
        self.share_log = collections.deque(maxlen=20000)

    def event(self, text, style=""):
        with self.lock:
            self.events.append((datetime.now().strftime("%H:%M:%S"), text, style))

    def feed(self, raw):
        line = RE_ANSI.sub("", raw).rstrip()
        if not line:
            return
        if self.logfile:
            try:
                self.logfile.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")
                self.logfile.flush()
            except Exception:
                pass
        line = RE_TS.sub("", line)
        now = time.time()

        m = RE_SHARE.search(line)
        if m:
            acc, tot = int(m.group(1)), int(m.group(2))
            sdiff = float(m.group(4)) if m.group(4) else None
            hr = float(m.group(5)) * UNITS[m.group(6).lower()]
            tail = line.lower()
            ok_text = any(k in tail for k in ("yay", "yes"))
            bad_text = any(k in tail for k in ("boo", "no!", "reject"))
            with self.lock:
                if ok_text or bad_text:
                    ok = ok_text and not bad_text
                else:
                    ok = acc > self.accepted
                self.accepted, self.total_shares = acc, tot
                self.last_share_ts = now
                self.last_share_ok = ok
                self.share_times.append(now)
                self.reported_hash = hr
                self.best_hash = max(self.best_hash, hr)
                if sdiff is not None:
                    self.share_diff = sdiff
                self.state = "mining"
                digest = hashlib.sha256(f"{tot}:{now}".encode()).hexdigest()[:12]
                self.blocks.append((tot, ok, digest, now))
                self.share_log.append((ok, now))
            self.event(line, "green" if ok else "red")
            return

        m = RE_CPU.search(line) or RE_THREAD.search(line)
        if m:
            idx = int(m.group(1))
            hr = float(m.group(2)) * UNITS[m.group(3).lower()]
            with self.lock:
                self.cores[idx] = (hr, now)
                self.state = "mining"
            return

        m = RE_REJECT.search(line)
        if m:
            reason = m.group(1).strip().lower()
            with self.lock:
                self.reject_reasons[reason] += 1
            self.event(line, "red")
            return

        m = RE_DIFF.search(line)
        if m and "difficulty" in line.lower():
            with self.lock:
                try:
                    self.difficulty = float(m.group(1))
                except ValueError:
                    pass
            self.event(line, "yellow")
            return

        if RE_JOB.search(line):
            with self.lock:
                self.jobs += 1
            self.event(line, "cyan")
            return

        if RE_ERR.search(line):
            with self.lock:
                self.errors += 1
            self.event(line, "red")
            return

        self.event(line, "dim")

    def total_hashrate(self):
        now = time.time()
        with self.lock:
            fresh = [hr for hr, ts in self.cores.values() if now - ts < 120]
            if fresh:
                return sum(fresh)
            if self.reported_hash and self.last_share_ts and now - self.last_share_ts < 180:
                return self.reported_hash
            return 0.0

    def sample(self):
        total = self.total_hashrate()
        with self.lock:
            self.history.append(total)
            if total > self.best_hash:
                self.best_hash = total


# --------------------------------------------------------------------------
# Supervisor do processo cpuminer (Suporta Reinicio Dinamico via Web/Terminal)
# --------------------------------------------------------------------------
class Miner:
    def __init__(self, args, stats):
        self.args = args
        self.stats = stats
        self.proc = None
        self.stop_evt = threading.Event()
        self.restart_req = threading.Event()
        self.paused = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self._started = False

    def build_cmd(self):
        binary = self.args.bin
        if not os.path.exists(binary):
            found = shutil.which(os.path.basename(binary))
            if found:
                binary = found
        cmd = [
            binary,
            "-a",
            self.args.algo,
            "-o",
            self.args.pool,
            "-u",
            self.args.user,
            "-p",
            self.args.password,
        ]
        if self.args.threads > 0:
            cmd += ["-t", str(self.args.threads)]
        cmd += getattr(self.args, "extra", [])
        return cmd

    def start(self):
        self.paused.clear()
        if not self._started:
            self._started = True
            self.thread.start()

    def pause(self):
        """Pausa o processo cpuminer sem encerrar o painel."""
        self.paused.set()
        p = self.proc
        if p and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
        self.stats.cores.clear()
        self.stats.state = "stopped"
        self.stats.event("Minerador pausado pelo usuário (Web/Painel).", "yellow")

    def resume(self):
        """Retoma o processo cpuminer caso esteja pausado ou parado."""
        if not self._started:
            self.start()
            return
        if self.paused.is_set():
            self.paused.clear()
            self.stats.event("Retomando mineração...", "green")
        else:
            self.trigger_restart()

    def trigger_restart(self):
        """Reinicia o processo cpuminer imediatamente quando as configs mudam via Web."""
        self.paused.clear()
        if not self._started:
            self.start()
            return
        self.restart_req.set()
        p = self.proc
        if p and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass

    def _run(self):
        st = self.stats
        while not self.stop_evt.is_set():
            if self.paused.is_set():
                st.state = "stopped"
                if self.stop_evt.wait(0.4):
                    break
                continue
            self.restart_req.clear()
            cmd = self.build_cmd()
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    errors="replace",
                    start_new_session=True,
                )
            except Exception as e:
                st.fatal = f"Error launching cpuminer: {e}"
                st.state = "error"
                st.event(st.fatal, "red")
                if self.stop_evt.wait(5):
                    break
                continue
            st.pid = self.proc.pid
            st.state = "connecting"
            st.event(f"cpuminer started (PID {self.proc.pid}) -> {self.args.pool}", "green")
            try:
                for line in self.proc.stdout:
                    st.feed(line)
            except Exception as e:
                st.event(f"Error reading miner stdout: {e}", "red")
            rc = self.proc.wait()
            st.cores.clear()
            st.state = "stopped"
            if self.stop_evt.is_set():
                break
            if self.paused.is_set():
                continue
            if self.restart_req.is_set():
                st.restarts += 1
                st.event("Aplicando nova configuração e reiniciando cpuminer...", "yellow")
                continue
            st.event(f"cpuminer exited (code {rc}).", "red")
            if self.args.no_restart:
                break
            st.restarts += 1
            st.event("Restarting in 5 seconds...", "yellow")
            if self.stop_evt.wait(5):
                break

    def stop(self):
        self.stop_evt.set()
        p = self.proc
        if p and p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass


# --------------------------------------------------------------------------
# Latencia do pool (TCP connect) em thread separada
# --------------------------------------------------------------------------
def pool_probe(stats, args, stop_evt):
    while not stop_evt.is_set():
        u = urlparse(args.pool if "://" in args.pool else "tcp://" + args.pool)
        host, port = u.hostname, u.port or 3333
        t0 = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=4):
                ms = (time.perf_counter() - t0) * 1000.0
                with stats.lock:
                    stats.pool_latency = ms
                    stats.pool_online = True
                    stats.ping_history.append(round(ms, 1))
        except Exception:
            with stats.lock:
                stats.pool_latency = None
                stats.pool_online = False
                stats.ping_history.append(None)
        stop_evt.wait(5)


# --------------------------------------------------------------------------
# Metricas do sistema
# --------------------------------------------------------------------------
class SysInfo:
    def __init__(self, pid_getter):
        self.pid_getter = pid_getter
        self.proc = None
        self.proc_pid = None
        self.net_prev = None
        self.net_rate = (0.0, 0.0)
        self.net_totals = (0, 0)
        self.cpu_percpu = []
        self.cpu_total = 0.0
        self.freqs = []
        if psutil:
            try:
                psutil.cpu_percent(percpu=True)
            except Exception:
                pass

    def temperature(self):
        temps = []
        if psutil and hasattr(psutil, "sensors_temperatures"):
            try:
                for entries in psutil.sensors_temperatures().values():
                    temps += [e.current for e in entries if e.current]
            except Exception:
                pass
        if not temps:
            try:
                base = "/sys/class/thermal"
                for name in os.listdir(base):
                    if name.startswith("thermal_zone"):
                        with open(f"{base}/{name}/temp") as f:
                            v = float(f.read().strip())
                        v = v / 1000 if v > 200 else v
                        if 0 < v < 150:
                            temps.append(v)
            except Exception:
                pass
        return max(temps) if temps else None

    def update(self):
        if not psutil:
            return
        try:
            self.cpu_percpu = psutil.cpu_percent(percpu=True)
            self.cpu_total = sum(self.cpu_percpu) / len(self.cpu_percpu) if self.cpu_percpu else 0.0
        except Exception:
            pass
        try:
            fr = psutil.cpu_freq(percpu=True)
            self.freqs = [f.current for f in fr] if fr else []
        except Exception:
            self.freqs = []
        try:
            io = psutil.net_io_counters()
            now = time.time()
            self.net_totals = (io.bytes_recv, io.bytes_sent)
            if self.net_prev:
                dt = max(now - self.net_prev[0], 1e-6)
                self.net_rate = (
                    (io.bytes_recv - self.net_prev[1]) / dt,
                    (io.bytes_sent - self.net_prev[2]) / dt,
                )
            self.net_prev = (now, io.bytes_recv, io.bytes_sent)
        except Exception:
            pass
        pid = self.pid_getter()
        if pid and pid != self.proc_pid:
            try:
                self.proc = psutil.Process(pid)
                self.proc.cpu_percent(None)
                self.proc_pid = pid
            except Exception:
                self.proc = None


# --------------------------------------------------------------------------
# SERVIDOR WEB EMBUTIDO (HTML5 / CSS3 / JS SPA + REST JSON API)
# --------------------------------------------------------------------------
WEB_HTML = r"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CPUMiner Live Dashboard · Mission Control</title>
<style>
:root {
  --bg: #080b12;
  --card: #101726;
  --card-alt: #0b101b;
  --primary: #00f0ff;
  --secondary: #00ff88;
  --accent: #ff00a0;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --danger: #ff3355;
  --warn: #fbbf24;
  --border: rgba(255,255,255,0.1);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
::-webkit-scrollbar { width: 7px; height: 7px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
body {
  background: var(--bg);
  background-image:
    radial-gradient(circle at 12% 10%, rgba(0,240,255,0.06), transparent 32%),
    radial-gradient(circle at 88% 85%, rgba(0,255,136,0.05), transparent 32%),
    linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 28px 28px, 28px 28px;
  color: var(--text);
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.mono { font-family: 'JetBrains Mono', 'Cascadia Code', Consolas, monospace; }

/* TOP COMMAND HEADER */
.cmd-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(16, 23, 38, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--primary);
  box-shadow: 0 4px 24px rgba(0,0,0,0.55);
  padding: 10px 18px;
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;
}
.brand-wrap { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.brand-logo {
  width: 38px; height: 38px; border-radius: 9px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #000; font-weight: 900; font-size: 1.25rem;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 14px rgba(0,240,255,0.35);
}
.brand-titles h1 {
  font-size: 1.08rem; font-weight: 800; letter-spacing: 0.7px;
  color: var(--secondary); display: flex; align-items: center; gap: 8px;
}
.brand-sub { font-size: 0.73rem; color: var(--muted); }
.status-pill {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 4px 12px; border-radius: 999px; font-weight: 800; font-size: 0.76rem;
  text-transform: uppercase; letter-spacing: 0.6px;
  background: rgba(0,255,136,0.14); color: var(--secondary); border: 1px solid var(--secondary);
}
.status-pill.warn { background: rgba(251,191,36,0.15); color: var(--warn); border-color: var(--warn); }
.status-pill.err { background: rgba(255,51,85,0.16); color: var(--danger); border-color: var(--danger); }
.led-dot {
  width: 8px; height: 8px; border-radius: 50%; background: currentColor;
  box-shadow: 0 0 8px currentColor; animation: blinkLed 1.1s infinite alternate;
}
@keyframes blinkLed { from { opacity: 0.35; } to { opacity: 1; } }

.header-meta {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  font-size: 0.78rem; color: var(--muted);
}
.meta-chip {
  background: rgba(0,0,0,0.4); border: 1px solid var(--border);
  padding: 4px 10px; border-radius: 6px; display: inline-flex; align-items: center; gap: 6px;
}
.meta-chip b { color: var(--text); }

.header-actions { display: flex; flex-wrap: wrap; gap: 7px; align-items: center; }
button, select, input {
  background: #090d16; color: var(--text); border: 1px solid rgba(255,255,255,0.18);
  padding: 6px 11px; border-radius: 6px; font-size: 0.8rem; cursor: pointer;
  transition: all 0.18s ease;
}
button:hover, select:hover { border-color: var(--primary); box-shadow: 0 0 10px rgba(0,240,255,0.2); }
.btn-primary { background: rgba(0,240,255,0.14); border-color: var(--primary); color: var(--primary); font-weight: 700; }
.btn-primary:hover { background: var(--primary); color: #000; }
.btn-success { background: rgba(0,255,136,0.14); border-color: var(--secondary); color: var(--secondary); font-weight: 700; }
.btn-success:hover { background: var(--secondary); color: #000; }
.btn-warn { background: rgba(251,191,36,0.14); border-color: var(--warn); color: var(--warn); font-weight: 700; }
.btn-warn:hover { background: var(--warn); color: #000; }
.btn-danger { background: rgba(255,51,85,0.14); border-color: var(--danger); color: var(--danger); font-weight: 700; }
.btn-danger:hover { background: var(--danger); color: #fff; }

/* WORKSPACE NAVIGATION RIBBON */
.workspace-nav {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
  padding: 8px 18px; background: rgba(9, 13, 22, 0.85);
  border-bottom: 1px solid var(--border); gap: 10px;
}
.nav-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.nav-tab {
  background: transparent; border: 1px solid transparent; color: var(--muted);
  padding: 6px 13px; border-radius: 6px; font-weight: 600; font-size: 0.8rem;
}
.nav-tab.active {
  background: rgba(0,240,255,0.14); border-color: var(--primary); color: var(--primary);
  box-shadow: inset 0 -2px 0 var(--primary);
}
.proc-controls { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

/* MAIN CONTAINER */
.container { padding: 14px 18px; flex: 1; display: flex; flex-direction: column; gap: 14px; max-width: 1920px; width: 100%; margin: 0 auto; }

/* 6-KPI TOP TELEMETRY STRIP */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(235px, 1fr));
  gap: 12px;
}
.kpi-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--primary);
  border-radius: 10px;
  padding: 12px 14px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 6px 18px rgba(0,0,0,0.28);
}
.kpi-card.sec { border-left-color: var(--secondary); }
.kpi-card.warn { border-left-color: var(--warn); }
.kpi-card.acc { border-left-color: var(--accent); }
.kpi-top { display: flex; justify-content: space-between; align-items: center; font-size: 0.74rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-main { font-size: 1.42rem; font-weight: 800; color: var(--text); margin: 5px 0 4px; letter-spacing: -0.3px; }
.kpi-sub { font-size: 0.75rem; color: var(--muted); display: flex; justify-content: space-between; gap: 6px; flex-wrap: wrap; }
.mini-bar { height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; margin-top: 7px; }
.mini-bar > div { height: 100%; background: linear-gradient(90deg, var(--primary), var(--secondary)); transition: width 0.35s; }

/* BENTO COMPLEX GRID */
.bento-row-2 {
  display: grid;
  grid-template-columns: 1.65fr 1fr;
  gap: 14px;
  min-width: 0;
}
.bento-row-3 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  min-width: 0;
}
.bento-row-bottom {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr 1.15fr;
  gap: 14px;
  min-width: 0;
}
@media (max-width: 1320px) {
  .bento-row-2, .bento-row-3, .bento-row-bottom { grid-template-columns: 1fr; }
}

.panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-top: 2px solid var(--primary);
  border-radius: 11px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}
.panel.sec { border-top-color: var(--secondary); }
.panel.warn { border-top-color: var(--warn); }
.panel.acc { border-top-color: var(--accent); }

.panel-head {
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.07); padding-bottom: 8px; flex-wrap: wrap; gap: 8px;
}
.panel-title {
  font-size: 0.92rem; font-weight: 700; color: var(--primary);
  display: flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.5px;
}
.panel-badges { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; font-size: 0.74rem; }
.tag {
  padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.07);
  color: var(--text); font-size: 0.72rem; font-weight: 600;
}

/* SVG OSCILLOSCOPE CHART */
.chart-wrap {
  background: rgba(5, 8, 15, 0.72);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 8px;
  padding: 8px;
  position: relative;
  height: 215px;
}
.chart-svg { width: 100%; height: 100%; display: block; overflow: visible; }
.metric-strip-6 {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(115px, 1fr)); gap: 8px;
}
.m-cell {
  background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 7px; padding: 7px 9px;
}
.m-cell .lbl { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; }
.m-cell .val { font-size: 0.96rem; font-weight: 700; color: var(--secondary); margin-top: 2px; }

/* PING SPECTRUM & POOL DETAILS */
.ping-spectrum {
  display: flex; align-items: flex-end; gap: 3px; height: 76px;
  padding: 8px 6px 4px; background: rgba(5, 8, 15, 0.72);
  border: 1px solid rgba(255,255,255,0.07); border-radius: 8px;
}
.p-bar { flex: 1; min-width: 4px; border-radius: 2px 2px 0 0; transition: height 0.25s; }
.kv-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px 12px; font-size: 0.8rem;
}
.kv-item {
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px dashed rgba(255,255,255,0.07); padding: 4px 0; gap: 8px;
}
.kv-item span:first-child { color: var(--muted); }
.kv-item span:last-child { font-weight: 600; text-align: right; word-break: break-all; }

/* DYNAMIC 3-ROW CYBER SHARE MATRIX */
.share-matrix {
  display: grid;
  gap: 4px;
  padding: 10px;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  background: rgba(5, 8, 15, 0.75);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
}
.sh-cell {
  height: 22px; min-width: 0; border-radius: 4px; display: flex; align-items: center;
  justify-content: center; font-size: 10px; font-weight: 700; user-select: none;
  transition: transform 0.15s;
}
.sh-cell:hover { transform: scale(1.25); z-index: 5; }
.sh-ok { background: rgba(0, 200, 83, 0.85); color: #022c10; box-shadow: 0 0 6px rgba(0,200,83,0.45); }
.sh-fresh { background: #00ff88; color: #000; animation: pulseNew 0.65s infinite alternate; box-shadow: 0 0 14px #00ff88; }
.sh-rej { background: #ff1744; color: #fff; box-shadow: 0 0 8px #ff1744; }
.sh-active { background: var(--warn); color: #000; animation: spinPulse 0.9s infinite ease-in-out; box-shadow: 0 0 12px var(--warn); }
.sh-scan { background: rgba(0, 240, 255, 0.28); border: 1px solid var(--primary); color: var(--primary); }
.sh-empty { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.18); }
@keyframes pulseNew { from { transform: scale(1); } to { transform: scale(1.2); } }
@keyframes spinPulse { 0% { opacity: 0.45; transform: scale(0.88); } 50% { opacity: 1; transform: scale(1.14); } 100% { opacity: 0.45; transform: scale(0.88); } }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* LIVE SHARE BLOCKCHAIN (COMPACT & CONTAINED) */
.chain-stream {
  display: flex; align-items: center; gap: 5px;
  width: 100%; max-width: 100%; overflow-x: auto;
  padding: 6px 8px; background: rgba(5, 8, 15, 0.75);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;
}
.chain-arrow { color: var(--primary); font-weight: 900; font-size: 0.78rem; user-select: none; flex-shrink: 0; }
.blk-node {
  width: 112px; min-width: 112px; max-width: 112px;
  background: rgba(16, 23, 38, 0.95);
  border: 1px solid var(--secondary); border-radius: 7px; padding: 5px 7px;
  font-size: 0.7rem; flex-shrink: 0; position: relative; overflow: hidden;
}
.blk-node.rej { border-color: var(--danger); }
.blk-node.fresh { box-shadow: 0 0 12px rgba(0,255,136,0.45); }
.blk-node.mining { border-color: var(--warn); animation: pulseBorder 1.1s infinite alternate; }
@keyframes pulseBorder { from { box-shadow: 0 0 3px var(--warn); } to { box-shadow: 0 0 12px var(--warn); } }

/* CPU CORES MATRIX & TABLE */
.cores-cards-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
  gap: 8px; max-height: 310px; overflow-y: auto; padding-right: 3px;
}
.core-card {
  background: rgba(5, 8, 15, 0.7); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px; padding: 8px 10px; display: flex; flex-direction: column; gap: 4px;
}
.core-card.inactive { opacity: 0.55; }
.core-card-top { display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; }
.core-hr { font-size: 0.95rem; font-weight: 800; color: var(--secondary); }
.table-scroll { max-height: 310px; overflow-y: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
th, td { padding: 6px 8px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); }
th { color: var(--primary); position: sticky; top: 0; background: var(--card); z-index: 2; font-size: 0.74rem; text-transform: uppercase; }
.bar-bg { width: 100%; background: rgba(255,255,255,0.09); height: 7px; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--secondary); transition: width 0.3s; }

/* RADIAL HARDWARE GAUGES */
.gauges-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
}
.gauge-box {
  background: rgba(5, 8, 15, 0.65); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px; padding: 8px 4px; text-align: center;
}
.gauge-svg { width: 68px; height: 68px; transform: rotate(-90deg); }
.gauge-bg { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 8; }
.gauge-fg { fill: none; stroke: var(--secondary); stroke-width: 8; stroke-linecap: round; transition: stroke-dashoffset 0.4s ease; }
.gauge-lbl { font-size: 0.72rem; color: var(--muted); margin-top: 3px; }
.gauge-val { font-size: 0.85rem; font-weight: 800; color: var(--text); }

/* TERMINAL LOG CONSOLE */
.console-toolbar { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; justify-content: space-between; }
.filter-pills { display: flex; gap: 4px; flex-wrap: wrap; }
.filter-pill {
  padding: 3px 9px; font-size: 0.72rem; border-radius: 99px;
  background: rgba(255,255,255,0.06); border: 1px solid transparent; color: var(--muted);
}
.filter-pill.active { background: rgba(0,240,255,0.16); border-color: var(--primary); color: var(--primary); font-weight: 700; }
.log-box {
  background: #04060b; border: 1px solid rgba(255,255,255,0.09);
  font-size: 0.77rem; height: 255px; overflow-y: auto; padding: 9px; border-radius: 7px;
  line-height: 1.45;
}
.log-line { margin-bottom: 3px; white-space: pre-wrap; word-break: break-all; border-left: 2px solid transparent; padding-left: 6px; }
.log-line.green { border-left-color: #00ff88; }
.log-line.red { border-left-color: #ff3355; background: rgba(255,51,85,0.05); }
.log-line.yellow { border-left-color: #fbbf24; }

.cmd-box {
  background: #05070d; border: 1px dashed rgba(0,240,255,0.35);
  border-radius: 6px; padding: 7px 10px; font-size: 0.75rem;
  display: flex; justify-content: space-between; align-items: center; gap: 8px;
  word-break: break-all; color: var(--primary);
}

/* MODALS */
.modal-backdrop {
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.82);
  backdrop-filter: blur(5px); z-index: 200; justify-content: center; align-items: center; padding: 16px;
}
.modal-backdrop.active { display: flex; }
.modal {
  background: var(--card); border: 2px solid var(--primary); border-radius: 12px;
  max-width: 900px; width: 100%; max-height: 92vh; overflow-y: auto; padding: 20px;
  box-shadow: 0 0 40px rgba(0,240,255,0.22);
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 14px;
}
.modal-head h3 { color: var(--secondary); font-size: 1.05rem; }
.cmp-badge-mod { background: rgba(251,191,36,0.2); color: var(--warn); border: 1px solid var(--warn); padding: 2px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; }
.cmp-badge-kept { color: var(--muted); font-size: 0.72rem; }
.wallet-box {
  background: #060911; border: 1px dashed var(--warn); padding: 14px;
  border-radius: 8px; margin-bottom: 12px; text-align: center; word-break: break-all;
}
.footer {
  text-align: center; font-size: 0.76rem; color: var(--muted);
  padding: 12px 18px; border-top: 1px solid var(--border); background: rgba(8,11,18,0.9);
}
.hidden-view { display: none !important; }
</style>
</head>
<body>

<!-- STICKY MISSION CONTROL HEADER -->
<header class="cmd-header">
  <div class="brand-wrap">
    <div class="brand-logo">⛏</div>
    <div class="brand-titles">
      <h1>CPUMINER LIVE <span id="st-badge" class="status-pill"><i class="led-dot"></i> <span id="st-text">MINING</span></span></h1>
      <div class="brand-sub" id="sub-edition" data-i18n="dev_by">Desenvolvido por Luan Quaresma</div>
    </div>
  </div>

  <div class="header-meta mono">
    <div class="meta-chip">⏱ <span id="lbl-uptime" data-i18n="uptime_lbl">Uptime:</span> <b id="v-uptime">00h 00m 00s</b></div>
    <div class="meta-chip">⚡ <span data-i18n="algo_lbl">Algo:</span> <b id="v-top-algo" style="color:var(--warn)">sha256d</b></div>
    <div class="meta-chip">🌐 <span data-i18n="pool_lbl">Pool:</span> <b id="v-top-pool" style="color:var(--primary)">—</b></div>
    <div class="meta-chip">🆔 PID: <b id="v-top-pid">—</b></div>
    <div class="meta-chip">🕒 <b id="v-server-time">--:--:--</b></div>
  </div>

  <div class="header-actions">
    <select id="sel-lang" onchange="changeLang(this.value)" title="Language / Idioma">
      <option value="pt">🇧🇷 Português</option>
      <option value="en">🇺🇸 English</option>
    </select>
    <select id="sel-theme" onchange="changeTheme(this.value)" title="Visual Theme">
      <option value="cyberpunk">🎨 Cyberpunk Neon</option>
      <option value="matrix">🎨 Matrix Green</option>
      <option value="bitcoin_gold">🎨 Bitcoin Gold</option>
      <option value="ocean">🎨 Ocean Blue</option>
      <option value="dracula">🎨 Dracula Purple</option>
      <option value="crimson">🎨 Crimson Red</option>
    </select>
    <button class="btn-primary" onclick="openModal('modal-cfg')" id="btn-cfg" data-i18n="btn_cfg">⚙️ Config Center</button>
    <button class="btn-primary" onclick="openDnsModal()" id="btn-dns" data-i18n="btn_dns">🌍 Radar DNS & Ping</button>
    <button class="btn-warn" onclick="openModal('modal-donate')" id="btn-don" data-i18n="btn_don">💝 Doação</button>
  </div>
</header>

<!-- WORKSPACE SWITCHER & PROCESS CONTROLS -->
<nav class="workspace-nav">
  <div class="nav-tabs">
    <button class="nav-tab active" onclick="switchView('all', this)" id="tab-all" data-i18n="tab_all">🎛️ Mission Control (Completo)</button>
    <button class="nav-tab" onclick="switchView('hash', this)" id="tab-hash" data-i18n="tab_hash">📈 Hashrate & Núcleos CPU</button>
    <button class="nav-tab" onclick="switchView('pool', this)" id="tab-pool" data-i18n="tab_pool">🌐 Pool, Shares & Blockchain</button>
    <button class="nav-tab" onclick="switchView('sys', this)" id="tab-sys" data-i18n="tab_sys">🖥 Hardware & Processo</button>
    <button class="nav-tab" onclick="switchView('log', this)" id="tab-log"><span data-i18n="tab_log">📜 Console Terminal</span> (<span id="v-log-cnt">0</span>)</button>
  </div>
  <div class="proc-controls">
    <span style="font-size:0.75rem;color:var(--muted)" id="lbl-remote" data-i18n="lbl_remote">Controle Remoto:</span>
    <button class="btn-success" onclick="controlMiner('resume')" id="btn-start" data-i18n="btn_start">▶ Iniciar / Retomar</button>
    <button class="btn-danger" onclick="controlMiner('pause')" id="btn-pause" data-i18n="btn_pause">⏸ Pausar</button>
    <button class="btn-warn" onclick="controlMiner('restart')" id="btn-restart" data-i18n="btn_restart">🔄 Reiniciar Miner</button>
  </div>
</nav>

<main class="container">

  <!-- ROW 1: 6-KPI HIGH-DENSITY TELEMETRY STRIP -->
  <section class="kpi-strip">
    <div class="kpi-card sec">
      <div class="kpi-top"><span id="k1-title" data-i18n="k1_title">⚡ Hashrate Atual</span> <span class="tag" id="k1-stab">Estab: 100%</span></div>
      <div class="kpi-main mono" id="k1-val" style="color:var(--secondary)">—</div>
      <div class="kpi-sub"><span><span data-i18n="pool_rep_lbl">Reportado Pool:</span> <b id="k1-rep">—</b></span> <span id="k1-pct">0% do Pico</span></div>
      <div class="mini-bar"><div id="k1-bar" style="width:0%"></div></div>
    </div>

    <div class="kpi-card">
      <div class="kpi-top"><span id="k2-title" data-i18n="k2_title">🏆 Pico & Médias</span> <span class="tag">M1 / M5</span></div>
      <div class="kpi-main mono" id="k2-val" style="color:var(--warn)">—</div>
      <div class="kpi-sub"><span>1m: <b id="k2-m1">—</b></span> <span>5m: <b id="k2-m5">—</b></span> <span><span data-i18n="lbl_overall">Geral:</span> <b id="k2-all">—</b></span></div>
      <div class="mini-bar"><div id="k2-bar" style="width:100%;background:var(--warn)"></div></div>
    </div>

    <div class="kpi-card sec">
      <div class="kpi-top"><span id="k3-title" data-i18n="k3_title">✅ Shares & Eficiência</span> <span class="tag" id="k3-tot">0 total</span></div>
      <div class="kpi-main mono" id="k3-val">0 / 0</div>
      <div class="kpi-sub"><span id="k3-rate">Eficiência: 0.00%</span> <span id="k3-last">Último: —</span></div>
      <div class="mini-bar"><div id="k3-bar" style="width:0%"></div></div>
    </div>

    <div class="kpi-card acc">
      <div class="kpi-top"><span id="k4-title" data-i18n="k4_title">🚀 Cadência de Shares</span> <span class="tag" id="k4-avg-t">~10.0s/sh</span></div>
      <div class="kpi-main mono" id="k4-val" style="color:var(--primary)">0.00 /min</div>
      <div class="kpi-sub"><span><span data-i18n="lbl_hour">Hora:</span> <b id="k4-sph">0.0/h</b></span> <span><span data-i18n="lbl_est_day">Est. Dia:</span> <b id="k4-spd">0/d</b></span></div>
      <div class="mini-bar"><div id="k4-bar" style="width:0%;background:var(--accent)"></div></div>
    </div>

    <div class="kpi-card warn">
      <div class="kpi-top"><span id="k5-title" data-i18n="k5_title">🌐 Latência Stratum</span> <span class="tag" id="k5-qual">PING</span></div>
      <div class="kpi-main mono" id="k5-val">— ms</div>
      <div class="kpi-sub"><span>Diff: <b id="k5-diff">—</b></span> <span>Jobs: <b id="k5-jobs">0</b></span> <span>Jitter: <b id="k5-jit">0ms</b></span></div>
      <div class="mini-bar"><div id="k5-bar" style="width:0%"></div></div>
    </div>

    <div class="kpi-card">
      <div class="kpi-top"><span id="k6-title" data-i18n="k6_title">🖥 Carga de Hardware</span> <span class="tag" id="k6-temp">— °C</span></div>
      <div class="kpi-main mono" id="k6-val">CPU 0%</div>
      <div class="kpi-sub"><span>RAM: <b id="k6-ram">0%</b></span> <span><span data-i18n="lbl_cores">Cores:</span> <b id="k6-cores">0/0</b></span></div>
      <div class="mini-bar"><div id="k6-bar" style="width:0%"></div></div>
    </div>
  </section>

  <!-- ROW 2: DUAL INTERACTIVE SVG CHARTS (HASHRATE OSCILLOSCOPE + STRATUM PING SPECTRUM) -->
  <section class="bento-row-2" id="sec-charts">
    <!-- Hashrate Oscilloscope -->
    <div class="panel sec" id="pnl-hash">
      <div class="panel-head">
        <div class="panel-title" id="t-hash" data-i18n="t_hash">📈 Osciloscópio de Hashrate em Tempo Real</div>
        <div class="panel-badges">
          <span class="tag" style="color:var(--secondary)" data-i18n="badge_cur">━ Atual</span>
          <span class="tag" style="color:var(--primary)" data-i18n="badge_ma">┅ Média Móvel</span>
          <span class="tag" style="color:var(--warn)" data-i18n="badge_peak">┈ Pico</span>
        </div>
      </div>

      <div class="metric-strip-6 mono">
        <div class="m-cell"><div class="lbl" id="l-cur" data-i18n="l_cur">Atual</div><div class="val" id="v-cur">—</div></div>
        <div class="m-cell"><div class="lbl" id="l-peak" data-i18n="l_peak">Pico Máx</div><div class="val" id="v-peak" style="color:var(--warn)">—</div></div>
        <div class="m-cell"><div class="lbl" id="l-min" data-i18n="l_min">Mínimo</div><div class="val" id="v-min" style="color:var(--text)">—</div></div>
        <div class="m-cell"><div class="lbl" id="l-avg1" data-i18n="l_avg1">Média 1m</div><div class="val" id="v-avg1" style="color:var(--primary)">—</div></div>
        <div class="m-cell"><div class="lbl" id="l-avg5" data-i18n="l_avg5">Média 5m</div><div class="val" id="v-avg5" style="color:var(--primary)">—</div></div>
        <div class="m-cell"><div class="lbl" id="l-avgall" data-i18n="l_avgall">Média Geral</div><div class="val" id="v-avgall" style="color:var(--text)">—</div></div>
      </div>

      <div class="chart-wrap">
        <svg class="chart-svg" id="svg-hashrate" viewBox="0 0 760 195" preserveAspectRatio="none"></svg>
      </div>
    </div>

    <!-- Stratum Pool & Ping Spectrum -->
    <div class="panel" id="pnl-pool">
      <div class="panel-head">
        <div class="panel-title" id="t-pool" data-i18n="t_pool">🌐 Telemetria Stratum, Pool & Espectro de Ping</div>
        <div class="panel-badges">
          <span class="tag" id="v-pool-status-tag">ONLINE</span>
          <button onclick="openDnsModal()" style="padding:2px 8px;font-size:0.72rem;" data-i18n="btn_pool_dns">🌍 Testar / ➕ Add Host DNS</button>
        </div>
      </div>

      <div class="ping-spectrum" id="ping-graph"></div>
      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;font-size:0.73rem;color:var(--muted);gap:6px;">
        <span>
          <b style="color:#00ff88">█ &lt;100ms</b> ·
          <b style="color:#22c55e">█ 100-180ms</b> ·
          <b style="color:#fbbf24">█ 180-300ms</b> ·
          <b style="color:#ff3355">█ &gt;300ms</b>
        </span>
        <span class="mono" id="v-ping-stats">min — · avg — · max — · jitter —</span>
      </div>

      <div class="kv-grid mono" style="margin-top:4px;">
        <div class="kv-item"><span data-i18n="kv_pool_host">Pool Host:</span><span id="v-p-host" style="color:var(--secondary)">—</span></div>
        <div class="kv-item"><span data-i18n="kv_algo">Algoritmo:</span><span id="v-p-algo" style="color:var(--warn)">—</span></div>
        <div class="kv-item"><span data-i18n="kv_wallet">Carteira:</span><span id="v-p-wallet" title="Clique para copiar" data-i18n-title="click_copy" style="cursor:pointer;color:var(--primary)" onclick="copyCurrentWallet()">—</span></div>
        <div class="kv-item"><span>Worker:</span><span id="v-p-worker">—</span></div>
        <div class="kv-item"><span data-i18n="kv_diff">Diff Pool / Share:</span><span id="v-p-diff">—</span></div>
        <div class="kv-item"><span data-i18n="kv_jobs">Jobs / Blocos:</span><span id="v-p-jobs">0</span></div>
        <div class="kv-item"><span data-i18n="kv_accrej">Aceitos / Rejeitados:</span><span id="v-p-accrej">0 / 0</span></div>
        <div class="kv-item"><span data-i18n="kv_err">Erros / Reinícios:</span><span id="v-p-err">0 / 0</span></div>
      </div>
      <div id="v-rej-reasons" style="font-size:0.74rem;color:var(--danger);min-height:16px;"></div>
    </div>
  </section>

  <!-- ROW 3: LIVE BLOCKCHAIN STREAM (COMPACT ON TOP) + REAL-TIME 120-CELL SHARE MATRIX (BELOW) -->
  <section class="bento-row-3" id="sec-visualizers">
    <!-- Live Share Blockchain (Compact on Top) -->
    <div class="panel warn" style="padding:10px 14px;gap:6px;">
      <div class="panel-head" style="padding-bottom:5px;">
        <div class="panel-title" id="t-chain" data-i18n="t_chain" style="font-size:0.85rem;">⛓ Corrente de Blocos / Shares Minerados (Ao Vivo)</div>
        <div class="panel-badges mono">
          <span class="tag" id="v-chain-avg">Média: ~10.0s</span>
          <span class="tag" id="v-chain-meta" style="color:var(--warn)">Bloco Atual: 0%</span>
        </div>
      </div>
      <div class="chain-stream mono" id="chain-row"></div>
    </div>

    <!-- Dynamic 3-Row Share Map (Below) -->
    <div class="panel sec">
      <div class="panel-head">
        <div class="panel-title" id="t-grid" data-i18n="t_grid">🟩 Matriz Cyber de Shares em Tempo Real</div>
        <div class="panel-badges mono" id="v-grid-meta">✓ 0 | ✗ 0 | 0.0%</div>
      </div>
      <div class="share-matrix mono" id="share-map"></div>
      <div style="display:flex;justify-content:space-between;font-size:0.73rem;color:var(--muted);flex-wrap:wrap;gap:8px;">
        <span id="legend-shares" data-i18n-html="legend_shares"><b style="color:#00ff88">★ Novo Share</b> · <b style="color:#00c853">■ Aceito</b> · <b style="color:#ff1744">✖ Rejeitado</b> · <b style="color:var(--warn)">❖ Minerando</b> · <b style="color:var(--primary)">▸ Scanner</b></span>
        <span class="mono" id="v-grid-timer">Desde último share: —</span>
      </div>
    </div>
  </section>

  <!-- ROW 4: PER-CORE CPU MATRIX + HARDWARE RADIAL GAUGES + INTERACTIVE CONSOLE -->
  <section class="bento-row-bottom" id="sec-bottom">

    <!-- Per-Core CPU Performance Matrix -->
    <div class="panel" id="pnl-cores">
      <div class="panel-head">
        <div class="panel-title" id="t-cores" data-i18n="t_cores">🧠 Desempenho por Núcleo (CPU Threads)</div>
        <div class="panel-badges">
          <span class="tag mono" id="v-cores-summary">0 ativos</span>
          <button onclick="toggleCoreView()" id="btn-core-view" style="padding:2px 8px;font-size:0.72rem;" data-i18n="btn_core_view">🔲 Cards / Tabela</button>
        </div>
      </div>

      <!-- Visual Core Cards Grid -->
      <div class="cores-cards-grid mono" id="cores-cards"></div>

      <!-- Detailed Core Table (Toggled) -->
      <div class="table-scroll mono hidden-view" id="cores-table-wrap">
        <table>
          <thead><tr>
            <th data-i18n="th_core">Core</th>
            <th data-i18n="th_hash">Hashrate</th>
            <th data-i18n="th_rel">Relativo</th>
            <th data-i18n="th_cpu">CPU %</th>
            <th data-i18n="th_freq">Freq</th>
            <th data-i18n="th_status">Estado</th>
          </tr></thead>
          <tbody id="cores-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Deep Hardware & Process Inspector -->
    <div class="panel warn" id="pnl-sys">
      <div class="panel-head">
        <div class="panel-title" id="t-sys" data-i18n="t_sys">🖥 Telemetria de Hardware & Processo</div>
        <div class="panel-badges"><span class="tag mono" id="v-sys-load">Load: —</span></div>
      </div>

      <!-- 4 SVG Radial Gauges -->
      <div class="gauges-row mono">
        <div class="gauge-box">
          <svg class="gauge-svg" viewBox="0 0 80 80">
            <circle class="gauge-bg" cx="40" cy="40" r="32"></circle>
            <circle class="gauge-fg" id="g-cpu" cx="40" cy="40" r="32" stroke-dasharray="201" stroke-dashoffset="201"></circle>
          </svg>
          <div class="gauge-val" id="gv-cpu">0%</div>
          <div class="gauge-lbl" data-i18n="lbl_g_cpu">CPU Total</div>
        </div>
        <div class="gauge-box">
          <svg class="gauge-svg" viewBox="0 0 80 80">
            <circle class="gauge-bg" cx="40" cy="40" r="32"></circle>
            <circle class="gauge-fg" id="g-ram" cx="40" cy="40" r="32" stroke-dasharray="201" stroke-dashoffset="201"></circle>
          </svg>
          <div class="gauge-val" id="gv-ram">0%</div>
          <div class="gauge-lbl">RAM</div>
        </div>
        <div class="gauge-box">
          <svg class="gauge-svg" viewBox="0 0 80 80">
            <circle class="gauge-bg" cx="40" cy="40" r="32"></circle>
            <circle class="gauge-fg" id="g-swap" cx="40" cy="40" r="32" stroke-dasharray="201" stroke-dashoffset="201"></circle>
          </svg>
          <div class="gauge-val" id="gv-swap">0%</div>
          <div class="gauge-lbl">Swap</div>
        </div>
        <div class="gauge-box">
          <svg class="gauge-svg" viewBox="0 0 80 80">
            <circle class="gauge-bg" cx="40" cy="40" r="32"></circle>
            <circle class="gauge-fg" id="g-temp" cx="40" cy="40" r="32" stroke-dasharray="201" stroke-dashoffset="201"></circle>
          </svg>
          <div class="gauge-val" id="gv-temp">—</div>
          <div class="gauge-lbl" data-i18n="lbl_g_temp">Temp</div>
        </div>
      </div>

      <div class="kv-grid mono" style="margin-top:4px;">
        <div class="kv-item"><span data-i18n="kv_ram">Memória RAM:</span><span id="v-s-ram">—</span></div>
        <div class="kv-item"><span data-i18n="kv_swap">Memória Swap:</span><span id="v-s-swap">—</span></div>
        <div class="kv-item"><span data-i18n="kv_net_rate">Rede Taxa (↓/↑):</span><span id="v-s-net" style="color:var(--primary)">—</span></div>
        <div class="kv-item"><span data-i18n="kv_net_tot">Rede Total (RX/TX):</span><span id="v-s-nettot">—</span></div>
        <div class="kv-item"><span data-i18n="kv_bat">Bateria:</span><span id="v-s-bat">—</span></div>
        <div class="kv-item"><span data-i18n="kv_proc">Processo cpuminer:</span><span id="v-s-proc" style="color:var(--secondary)">—</span></div>
      </div>

      <div class="cmd-box mono" title="Linha de comando ativa do cpuminer" data-i18n-title="cmd_box_title">
        <span id="v-cmd-line">./cpuminer ...</span>
        <button onclick="copyCmdLine()" style="padding:3px 8px;font-size:0.72rem;flex-shrink:0;" data-i18n="btn_copy_cli">📋 Copiar CLI</button>
      </div>
    </div>

    <!-- Interactive Miner Event Console -->
    <div class="panel acc" id="pnl-log">
      <div class="panel-head">
        <div class="panel-title" id="t-log" data-i18n="t_log">📜 Console de Eventos do Minerador</div>
        <div class="panel-badges">
          <button onclick="exportLogs()" style="padding:2px 8px;font-size:0.72rem;" data-i18n="btn_export_log">⬇ Exportar .log</button>
          <button onclick="clearLogs()" style="padding:2px 8px;font-size:0.72rem;" data-i18n="btn_clear_log">🧹 Limpar</button>
        </div>
      </div>

      <div class="console-toolbar">
        <div class="filter-pills">
          <button class="filter-pill active" onclick="setLogFilter('all', this)" data-i18n="flt_all">Todos</button>
          <button class="filter-pill" onclick="setLogFilter('green', this)" data-i18n="flt_shares">✓ Shares</button>
          <button class="filter-pill" onclick="setLogFilter('yellow', this)" data-i18n="flt_jobs">⚡ Diff/Jobs</button>
          <button class="filter-pill" onclick="setLogFilter('red', this)" data-i18n="flt_err">✖ Erros</button>
        </div>
        <div style="display:flex;gap:5px;align-items:center;">
          <input id="log-search" placeholder="🔍 Filtrar texto..." data-i18n-ph="ph_log_search" oninput="renderLogs()" style="padding:3px 8px;font-size:0.75rem;width:135px;">
          <label style="font-size:0.73rem;color:var(--muted);display:flex;align-items:center;gap:4px;cursor:pointer;">
            <input type="checkbox" id="chk-autoscroll" checked> <span data-i18n="lbl_autoscroll">Auto-scroll</span>
          </label>
        </div>
      </div>

      <div class="log-box mono" id="log-box"></div>
    </div>

  </section>

</main>

<footer class="footer">
  <span data-i18n-html="footer_brand">CPUMiner Live Dashboard · Universal Multi-Algo Mission Control · Desenvolvido por <b>Luan Quaresma</b></span> ·
  BTC: <span class="mono" style="color:var(--warn);cursor:pointer" onclick="copyAddr('bc1qlk6dt8hj4tkf7wqgcfcsctuzgkwa0afzxpqku0')">bc1qlk6dt8hj4tkf7wqgcfcsctuzgkwa0afzxpqku0</span> ·
  DGB: <span class="mono" style="color:var(--primary);cursor:pointer" onclick="copyAddr('DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9')">DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9</span>
</footer>

<!-- MODAL 1: COMPARATIVE CONFIGURATION CENTER (PREVIOUS VS NEW) -->
<div class="modal-backdrop" id="modal-cfg">
  <div class="modal">
    <div class="modal-head">
      <h3 id="m-cfg-title" data-i18n="m_cfg_title">⚙️ Central Comparativa de Configuração (Anterior vs Nova)</h3>
      <button onclick="closeModal('modal-cfg')" data-i18n="btn_close">✖ Fechar</button>
    </div>

    <div style="margin-bottom:12px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <span style="font-size:0.8rem;color:var(--muted)" data-i18n="lbl_preset_pool">Presets Rápidos de Pool:</span>
      <select id="preset-pool" onchange="applyPoolPreset(this.value)" style="flex:1;min-width:220px;">
        <option value="" id="opt-sel-pool" data-i18n="opt_sel_pool">-- Selecionar Pool Conhecida (DGB & CPUMiner) --</option>
        <option value="stratum+tcp://m2pool.com:3333">M2Pool DGB (Global Multi-Algo - 3333)</option>
        <option value="stratum+tcp://europe.mining-dutch.nl:3437">Mining-Dutch DGB Scrypt (Europe NL - 3437)</option>
        <option value="stratum+tcp://americas.mining-dutch.nl:3437">Mining-Dutch Americas (Scrypt - 3437)</option>
        <option value="stratum+tcp://hub.mining-dutch.nl:3333">Mining-Dutch Multi-Coin Hub (Europe - 3333)</option>
        <option value="stratum+tcp://dgb.solopool.eu:3335">SoloPool DGB SHA-256 (Europe/Global - 3335)</option>
        <option value="stratum+tcp://dgb.solopool.eu:3349">SoloPool DGB Scrypt (Europe/Global - 3349)</option>
        <option value="stratum+tcp://dgb.solopool.org:3335">SoloPool Org DGB (Global Solo - 3335)</option>
        <option value="stratum+tcp://sha256.sa.mine.zpool.ca:3333">Zpool SHA256 (América do Sul BR - 3333)</option>
        <option value="stratum+tcp://sha256.na.mine.zpool.ca:3333">Zpool SHA256 (América do Norte US - 3333)</option>
        <option value="stratum+tcp://sha256.eu.mine.zpool.ca:3333">Zpool SHA256 (Europa EU - 3333)</option>
        <option value="stratum+tcp://yescrypt.eu.mine.zpool.ca:6233">Zpool Yescrypt CPU (Europa - 6233)</option>
        <option value="stratum+tcp://qubit.na.mine.zpool.ca:4733">Zpool Qubit CPU/ASIC (North America - 4733)</option>
        <option value="stratum+tcp://skein.na.mine.zpool.ca:4933">Zpool Skein (North America - 4933)</option>
        <option value="stratum+tcp://p2p-spb.xyz:5027">P2Pool Network DGB (SPB - 5027)</option>
        <option value="stratum+tcp://p2p-spb.xyz:5024">P2Pool Network Node Alt (5024)</option>
        <option value="stratum+tcp://eu.molepool.com:7451">MolePool DGB Solo SHA-256 (Europa - 7451)</option>
        <option value="stratum+tcp://eu.molepool.com:4601">MolePool Merged DGB+DOGE Scrypt (Europa - 4601)</option>
        <option value="stratum+tcp://digibyte.io:3333">DigiByte.io Seed/Node (Global - 3333)</option>
        <option value="stratum+tcp://thebeepool.com:3333">TheBeePool DGB (Global - 3333)</option>
        <option value="stratum+tcp://fenixpool.com:6666">FenixPool DGB SHA-256 (Global - 6666)</option>
        <option value="stratum+tcp://fenixpool.com:6668">FenixPool DGB Scrypt Solo (Global - 6668)</option>
        <option value="stratum+tcp://fenixpool.com:6660">FenixPool DGB Qubit CPU (Global - 6660)</option>
        <option value="stratum+tcp://fenixpool.com:6661">FenixPool DGB Skein (Global - 6661)</option>
        <option value="stratum+tcp://dgb.kryptex.network:7037">Kryptex DGB SHA-256 (Global - 7037)</option>
        <option value="stratum+tcp://mining-pool.io:4073">Mining-Pool.io Qubit CPU (Global - 4073)</option>
        <option value="stratum+tcp://mining-pool.io:4071">Mining-Pool.io Scrypt (Global - 4071)</option>
        <option value="stratum+tcp://huurrexpool.com:3333">HuurreXPool DGB SHA-256 (Europa - 3333)</option>
        <option value="stratum+tcp://stratum.kriptokyng.com:3312">KriptoKyng DGB SHA-256 (Global - 3312)</option>
        <option value="stratum+tcp://dgb.fusionpool.pro:3332">FusionPool DGB (Global - 3332)</option>
        <option value="stratum+tcp://dgb-sha256.2miners.com:3030">2Miners DGB (Global - 3030)</option>
        <option value="stratum+tcp://dgb.viabtc.io:3333">ViaBTC DGB (Global Smart - 3333)</option>
        <option value="stratum+tcp://prohashing.com:3335">Prohashing Multi-Algo (USA - 3335)</option>
        <option value="stratum+tcp://yespower.eu.mine.zergpool.com:6533">Zergpool Yespower CPU (Europa - 6533)</option>
        <option value="stratum+tcp://stratum-eu.rplant.xyz:7042">Rplant Pool CPU (Europa - 7042)</option>
        <option value="stratum+tcp://rx.unmineable.com:3333">Unmineable CPU RandomX (Global - 3333)</option>
      </select>
      <select id="preset-algo" onchange="if(this.value){document.getElementById('f-algo').value=this.value;updateCfgDiff();}">
        <option value="" id="opt-sel-algo" data-i18n="opt_sel_algo">-- Algoritmo --</option>
        <option value="sha256d">sha256d (Bitcoin / DigiByte)</option>
        <option value="scrypt">scrypt (Litecoin / Doge / DGB)</option>
        <option value="yescrypt">yescrypt</option>
        <option value="yespower">yespower</option>
        <option value="qubit">qubit</option>
        <option value="skein">skein</option>
      </select>
    </div>

    <table class="mono" style="margin-bottom:16px;">
      <thead>
        <tr>
          <th data-i18n="th_cfg_param">Parâmetro</th>
          <th data-i18n="th_cfg_old">⏪ Valor Anterior (Ativo)</th>
          <th data-i18n="th_cfg_new">🆕 Novo Valor (Editar)</th>
          <th data-i18n="th_cfg_status">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b data-i18n="fld_bin">Caminho do Binário</b></td>
          <td id="old-bin" style="color:var(--muted)">—</td>
          <td><input id="f-bin" oninput="updateCfgDiff()" style="width:100%"></td>
          <td id="st-bin"></td>
        </tr>
        <tr>
          <td><b data-i18n="fld_algo">Algoritmo (-a)</b></td>
          <td id="old-algo" style="color:var(--muted)">—</td>
          <td><input id="f-algo" oninput="updateCfgDiff()" style="width:100%"></td>
          <td id="st-algo"></td>
        </tr>
        <tr>
          <td><b data-i18n="fld_pool">URL da Pool (-o)</b></td>
          <td id="old-pool" style="color:var(--muted)">—</td>
          <td><input id="f-pool" oninput="updateCfgDiff()" style="width:100%"></td>
          <td id="st-pool"></td>
        </tr>
        <tr>
          <td><b data-i18n="fld_user">Carteira.Worker (-u)</b></td>
          <td id="old-user" style="color:var(--muted)">—</td>
          <td><input id="f-user" oninput="updateCfgDiff()" style="width:100%"></td>
          <td id="st-user"></td>
        </tr>
        <tr>
          <td><b data-i18n="fld_pass">Senha da Pool (-p)</b></td>
          <td id="old-pass" style="color:var(--muted)">—</td>
          <td><input id="f-pass" oninput="updateCfgDiff()" style="width:100%"></td>
          <td id="st-pass"></td>
        </tr>
        <tr>
          <td><b data-i18n="fld_threads">Threads CPU (-t, 0=Auto)</b></td>
          <td id="old-threads" style="color:var(--muted)">—</td>
          <td><input type="number" min="0" id="f-threads" oninput="updateCfgDiff()" style="width:100%"></td>
          <td id="st-threads"></td>
        </tr>
      </tbody>
    </table>

    <div style="display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;">
      <button class="btn-success" onclick="saveWebConfig(true)" data-i18n="btn_cfg_save_restart">✔ Salvar & Reiniciar Minerador Agora</button>
      <button class="btn-primary" onclick="saveWebConfig(false)" data-i18n="btn_cfg_save">💾 Salvar sem Reiniciar</button>
      <button onclick="closeModal('modal-cfg')" data-i18n="btn_cancel">✖ Cancelar</button>
    </div>
  </div>
</div>

<!-- MODAL 2: GLOBAL DNS & STRATUM PING RADAR -->
<div class="modal-backdrop" id="modal-dns">
  <div class="modal">
    <div class="modal-head">
      <h3 data-i18n="m_dns_title">🌍 Radar Global de DNS & Latência TCP Stratum</h3>
      <div style="display:flex;gap:8px;">
        <button class="btn-primary" onclick="openDnsModal(true)" data-i18n="btn_test_again">🔄 Testar Novamente</button>
        <button onclick="closeModal('modal-dns')" data-i18n="btn_close">✖ Fechar</button>
      </div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;background:rgba(0,0,0,0.28);border:1px solid var(--border);padding:10px;border-radius:8px;margin-bottom:10px;">
      <span style="font-size:0.78rem;color:var(--primary);font-weight:700;" data-i18n="lbl_new_dns_host">➕ Novo Host DNS:</span>
      <input id="dns-add-name" placeholder="Nome (ex: Minha Pool)" data-i18n-ph="ph_dns_name" style="width:150px;">
      <input id="dns-add-reg" placeholder="Região (ex: BR / Global)" data-i18n-ph="ph_dns_reg" style="width:140px;">
      <input id="dns-add-url" placeholder="Host/URL (ex: stratum+tcp://pool.com:3333)" data-i18n-ph="ph_dns_url" style="flex:1;min-width:220px;">
      <button class="btn-success" onclick="addDnsHost()" data-i18n="btn_add_dns_host">➕ Adicionar Host DNS</button>
    </div>
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap;">
      <input id="dns-search-filter" placeholder="🔍 Filtrar pool por nome, região ou host..." data-i18n-ph="ph_dns_filter" oninput="filterDnsList(this.value)" style="flex:1;min-width:220px;padding:7px 12px;background:rgba(0,0,0,0.32);border:1px solid var(--border);border-radius:6px;color:#fff;font-size:0.8rem;">
      <span id="dns-count-badge" style="font-size:0.75rem;color:var(--secondary);font-weight:700;"></span>
    </div>
    <div id="dns-best-banner" style="background:rgba(0,255,136,0.1);border:1px solid var(--secondary);padding:10px;border-radius:8px;margin-bottom:12px;font-size:0.86rem;text-align:center;">
      🌍 Sondando servidores DNS e portas TCP Stratum ao redor do mundo...
    </div>
    <div class="table-scroll mono" style="max-height:420px;">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th data-i18n="th_dns_pool">Pool</th>
            <th data-i18n="th_dns_reg">Região</th>
            <th data-i18n="th_dns_host">Host : Porta</th>
            <th data-i18n="th_dns_ip">IP Resolvido</th>
            <th>DNS</th>
            <th data-i18n="th_dns_ping">Ping TCP</th>
            <th data-i18n="th_dns_qual">Qualidade</th>
            <th data-i18n="th_dns_action">Ação</th>
          </tr>
        </thead>
        <tbody id="dns-tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- MODAL 3: DONATE & ABOUT -->
<div class="modal-backdrop" id="modal-donate">
  <div class="modal">
    <div class="modal-head">
      <h3 data-i18n="m_don_title">💝 Apoie o Projeto Open-Source · Luan Quaresma</h3>
      <button onclick="closeModal('modal-donate')" data-i18n="btn_close">✖ Fechar</button>
    </div>
    <p style="font-size:0.88rem;color:var(--muted);margin-bottom:14px;line-height:1.5;" data-i18n="don_desc">
      Este painel completo de telemetria (Terminal TUI & Mission Control Web) é 100% gratuito e open-source.
      Se a ferramenta ajuda na sua operação de mineração, considere apoiar o desenvolvimento com Bitcoin (BTC) ou DigiByte (DGB):
    </p>
    <div class="wallet-box">
      <div style="color:var(--warn);font-weight:800;margin-bottom:6px;" data-i18n="don_btc_hdr">₿ BITCOIN (BTC · Rede Nativa SegWit)</div>
      <div class="mono" style="font-size:0.96rem;margin-bottom:10px;color:#fff;">bc1qlk6dt8hj4tkf7wqgcfcsctuzgkwa0afzxpqku0</div>
      <button class="btn-warn" onclick="copyAddr('bc1qlk6dt8hj4tkf7wqgcfcsctuzgkwa0afzxpqku0')" data-i18n="btn_copy_btc">📋 Copiar Endereço BTC</button>
    </div>
    <div class="wallet-box" style="border-color:var(--primary)">
      <div style="color:var(--primary);font-weight:800;margin-bottom:6px;" data-i18n="don_dgb_hdr">💎 DIGIBYTE (DGB · Rede Principal)</div>
      <div class="mono" style="font-size:0.96rem;margin-bottom:10px;color:#fff;">DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9</div>
      <button class="btn-primary" onclick="copyAddr('DHHfRY2jQjYVmytPzrg2PkwqJ2Y1M587C9')" data-i18n="btn_copy_dgb">📋 Copiar Endereço DGB</button>
    </div>
    <div id="copy-msg" style="text-align:center;color:var(--secondary);font-weight:700;min-height:20px;"></div>
  </div>
</div>

<script>
const I18N_WEB = {
  pt: {
    dev_by: "Desenvolvido por Luan Quaresma",
    uptime_lbl: "Uptime:",
    algo_lbl: "Algo:",
    pool_lbl: "Pool:",
    btn_cfg: "⚙️ Config Center",
    btn_dns: "🌍 Radar DNS & Ping",
    btn_don: "💝 Doação",
    tab_all: "🎛️ Mission Control (Completo)",
    tab_hash: "📈 Hashrate & Núcleos CPU",
    tab_pool: "🌐 Pool, Shares & Blockchain",
    tab_sys: "🖥 Hardware & Processo",
    tab_log: "📜 Console Terminal",
    lbl_remote: "Controle Remoto:",
    btn_start: "▶ Iniciar / Retomar",
    btn_pause: "⏸ Pausar",
    btn_restart: "🔄 Reiniciar Miner",
    k1_title: "⚡ Hashrate Atual",
    pool_rep_lbl: "Reportado Pool:",
    k2_title: "🏆 Pico & Médias",
    lbl_overall: "Geral:",
    k3_title: "✅ Shares & Eficiência",
    k4_title: "🚀 Cadência de Shares",
    lbl_hour: "Hora:",
    lbl_est_day: "Est. Dia:",
    k5_title: "🌐 Latência Stratum",
    k6_title: "🖥 Carga de Hardware",
    lbl_cores: "Cores:",
    t_hash: "📈 Osciloscópio de Hashrate em Tempo Real",
    badge_cur: "━ Atual",
    badge_ma: "┅ Média Móvel",
    badge_peak: "┈ Pico",
    l_cur: "Atual",
    l_peak: "Pico Máx",
    l_min: "Mínimo",
    l_avg1: "Média 1m",
    l_avg5: "Média 5m",
    l_avgall: "Média Geral",
    t_pool: "🌐 Telemetria Stratum, Pool & Espectro de Ping",
    btn_pool_dns: "🌍 Testar / ➕ Add Host DNS",
    kv_pool_host: "Pool Host:",
    kv_algo: "Algoritmo:",
    kv_wallet: "Carteira:",
    kv_diff: "Diff Pool / Share:",
    kv_jobs: "Jobs / Blocos:",
    kv_accrej: "Aceitos / Rejeitados:",
    kv_err: "Erros / Reinícios:",
    t_chain: "⛓ Corrente de Blocos / Shares Minerados (Ao Vivo)",
    t_grid: "🟩 Matriz Cyber de Shares em Tempo Real",
    legend_shares: '<b style="color:#00ff88">★ Novo Share</b> · <b style="color:#00c853">■ Aceito</b> · <b style="color:#ff1744">✖ Rejeitado</b> · <b style="color:var(--warn)">❖ Minerando</b> · <b style="color:var(--primary)">▸ Scanner</b>',
    t_cores: "🧠 Desempenho por Núcleo (CPU Threads)",
    btn_core_view: "🔲 Cards / Tabela",
    th_core: "Core",
    th_hash: "Hashrate",
    th_rel: "Relativo",
    th_cpu: "CPU %",
    th_freq: "Freq",
    th_status: "Estado",
    t_sys: "🖥 Telemetria de Hardware & Processo",
    lbl_g_cpu: "CPU Total",
    lbl_g_temp: "Temp",
    kv_ram: "Memória RAM:",
    kv_swap: "Memória Swap:",
    kv_net_rate: "Rede Taxa (↓/↑):",
    kv_net_tot: "Rede Total (RX/TX):",
    kv_bat: "Bateria:",
    kv_proc: "Processo cpuminer:",
    btn_copy_cli: "📋 Copiar CLI",
    cmd_box_title: "Linha de comando ativa do cpuminer",
    click_copy: "Clique para copiar",
    t_log: "📜 Console de Eventos do Minerador",
    btn_export_log: "⬇ Exportar .log",
    btn_clear_log: "🧹 Limpar",
    flt_all: "Todos",
    flt_shares: "✓ Shares",
    flt_jobs: "⚡ Diff/Jobs",
    flt_err: "✖ Erros",
    ph_log_search: "🔍 Filtrar texto...",
    lbl_autoscroll: "Auto-scroll",
    footer_brand: "CPUMiner Live Dashboard · Universal Multi-Algo Mission Control · Desenvolvido por <b>Luan Quaresma</b>",
    m_cfg_title: "⚙️ Central Comparativa de Configuração (Anterior vs Nova)",
    btn_close: "✖ Fechar",
    lbl_preset_pool: "Presets Rápidos de Pool:",
    opt_sel_pool: "-- Selecionar Pool Conhecida (DGB & CPUMiner) --",
    opt_sel_algo: "-- Algoritmo --",
    th_cfg_param: "Parâmetro",
    th_cfg_old: "⏪ Valor Anterior (Ativo)",
    th_cfg_new: "🆕 Novo Valor (Editar)",
    th_cfg_status: "Status",
    fld_bin: "Caminho do Binário",
    fld_algo: "Algoritmo (-a)",
    fld_pool: "URL da Pool (-o)",
    fld_user: "Carteira.Worker (-u)",
    fld_pass: "Senha da Pool (-p)",
    fld_threads: "Threads CPU (-t, 0=Auto)",
    btn_cfg_save_restart: "✔ Salvar & Reiniciar Minerador Agora",
    btn_cfg_save: "💾 Salvar sem Reiniciar",
    btn_cancel: "✖ Cancelar",
    m_dns_title: "🌍 Radar Global de DNS & Latência TCP Stratum",
    btn_test_again: "🔄 Testar Novamente",
    lbl_new_dns_host: "➕ Novo Host DNS:",
    ph_dns_name: "Nome (ex: Minha Pool)",
    ph_dns_reg: "Região (ex: BR / Global)",
    ph_dns_url: "Host/URL (ex: stratum+tcp://pool.com:3333)",
    btn_add_dns_host: "➕ Adicionar Host DNS",
    ph_dns_filter: "🔍 Filtrar pool por nome, região ou host...",
    th_dns_pool: "Pool",
    th_dns_reg: "Região",
    th_dns_host: "Host : Porta",
    th_dns_ip: "IP Resolvido",
    th_dns_ping: "Ping TCP",
    th_dns_qual: "Qualidade",
    th_dns_action: "Ação",
    m_don_title: "💝 Apoie o Projeto Open-Source · Luan Quaresma",
    don_desc: "Este painel completo de telemetria (Terminal TUI & Mission Control Web) é 100% gratuito e open-source. Se a ferramenta ajuda na sua operação de mineração, considere apoiar o desenvolvimento com Bitcoin (BTC) ou DigiByte (DGB):",
    don_btc_hdr: "₿ BITCOIN (BTC · Rede Nativa SegWit)",
    btn_copy_btc: "📋 Copiar Endereço BTC",
    don_dgb_hdr: "💎 DIGIBYTE (DGB · Rede Principal)",
    btn_copy_dgb: "📋 Copiar Endereço DGB",
    prompt_token: "Digite o Web Token (--web-token) / Enter Web Token:",
    of_peak: "do Pico",
    stab: "Estab",
    total: "total",
    efficiency: "Eficiência",
    last: "Último",
    per_min: "/min",
    qual_exc: "EXCELENTE",
    qual_good: "BOM",
    qual_med: "MÉDIO",
    qual_high: "ALTO",
    temp_na: "Temp N/A",
    collecting_samples: "coletando amostras...",
    rej_reasons: "Motivos de rejeição",
    accepted: "Aceitos",
    rejected: "Rejeitados",
    since_last: "Desde último share",
    waiting_first_share: "Aguardando 1º share...",
    accepted_caps: "ACEITO",
    rejected_caps: "REJEITADO",
    at_time: "às",
    mining_next_share: "Minerando próximo share...",
    block_prefix: "Bloco",
    average: "Média",
    threads_word: "threads",
    estimated_short: "Est.",
    relative_hr: "Hashrate Relativo",
    charging: "⚡ Carregando",
    battery: "🔋 Bateria",
    ac_desktop: "AC / Desktop",
    stopped: "Parado",
    auto_threads: "Automático (0)",
    cfg_changed: "ALTERADO",
    cfg_kept: "mantido",
    dns_online: "online",
    dns_pools_total: "pools",
    dns_best_found: "Melhor Latência Detectada",
    dns_none_responded: "Nenhuma pool respondeu ao teste TCP no momento",
    dns_queried: "pools consultadas",
    dns_none_avail: "Nenhuma pool disponível no radar.",
    dns_none_found: "Nenhuma pool encontrada.",
    dns_del_tooltip: "Remover host customizado",
    btn_use_pool: "✔ Usar Pool",
    dns_probing_banner: "Sondando servidores DNS e latência Stratum das pools globais... Por favor, aguarde.",
    dns_probing_table: "Sondando resolução DNS e medindo latência TCP de todas as pools... Aguarde alguns instantes.",
    dns_err_title: "Erro ao obter pools",
    dns_comm_fail: "Falha de comunicação",
    btn_retry: "Tentar Novamente",
    dns_fail_api: 'Falha de conexão com a API de teste de DNS. Clique em "Tentar Novamente".',
    alert_enter_pool: "Informe o Host ou URL da Pool (ex: stratum+tcp://dgb.fusionpool.pro:3332)",
    copied_addr: "Endereço copiado para a área de transferência",
    st_mining: "MINERANDO",
    st_connecting: "CONECTANDO",
    st_starting: "INICIANDO",
    st_stopped: "PARADO",
    st_error: "ERRO",
    core_active: "Ativo",
    core_idle: "Inativo",
    core_est: "Ativo (Est.)"
  },
  en: {
    dev_by: "Developed by Luan Quaresma",
    uptime_lbl: "Uptime:",
    algo_lbl: "Algo:",
    pool_lbl: "Pool:",
    btn_cfg: "⚙️ Config Center",
    btn_dns: "🌍 DNS & Ping Radar",
    btn_don: "💝 Donation",
    tab_all: "🎛️ Mission Control (Full)",
    tab_hash: "📈 Hashrate & CPU Cores",
    tab_pool: "🌐 Pool, Shares & Blockchain",
    tab_sys: "🖥 Hardware & Process",
    tab_log: "📜 Terminal Console",
    lbl_remote: "Remote Control:",
    btn_start: "▶ Start / Resume",
    btn_pause: "⏸ Pause",
    btn_restart: "🔄 Restart Miner",
    k1_title: "⚡ Current Hashrate",
    pool_rep_lbl: "Pool Reported:",
    k2_title: "🏆 Peak & Averages",
    lbl_overall: "Overall:",
    k3_title: "✅ Shares & Efficiency",
    k4_title: "🚀 Share Cadence",
    lbl_hour: "Hour:",
    lbl_est_day: "Est. Day:",
    k5_title: "🌐 Stratum Latency",
    k6_title: "🖥 Hardware Load",
    lbl_cores: "Cores:",
    t_hash: "📈 Real-Time Hashrate Oscilloscope",
    badge_cur: "━ Current",
    badge_ma: "┅ Moving Average",
    badge_peak: "┈ Peak",
    l_cur: "Current",
    l_peak: "Peak Max",
    l_min: "Minimum",
    l_avg1: "1m Average",
    l_avg5: "5m Average",
    l_avgall: "Overall Avg",
    t_pool: "🌐 Stratum Telemetry, Pool & Ping Spectrum",
    btn_pool_dns: "🌍 Benchmark / ➕ Add DNS Host",
    kv_pool_host: "Pool Host:",
    kv_algo: "Algorithm:",
    kv_wallet: "Wallet:",
    kv_diff: "Diff Pool / Share:",
    kv_jobs: "Jobs / Blocks:",
    kv_accrej: "Accepted / Rejected:",
    kv_err: "Errors / Restarts:",
    t_chain: "⛓ Mined Blocks & Shares Chain (Live Stream)",
    t_grid: "🟩 Real-Time Cyber Share Matrix",
    legend_shares: '<b style="color:#00ff88">★ Fresh Share</b> · <b style="color:#00c853">■ Accepted</b> · <b style="color:#ff1744">✖ Rejected</b> · <b style="color:var(--warn)">❖ Mining</b> · <b style="color:var(--primary)">▸ Scanner</b>',
    t_cores: "🧠 Per-Core CPU Performance (Threads)",
    btn_core_view: "🔲 Cards / Table",
    th_core: "Core",
    th_hash: "Hashrate",
    th_rel: "Relative",
    th_cpu: "CPU %",
    th_freq: "Freq",
    th_status: "Status",
    t_sys: "🖥 Hardware & Process Telemetry",
    lbl_g_cpu: "Total CPU",
    lbl_g_temp: "Temp",
    kv_ram: "RAM Memory:",
    kv_swap: "Swap Memory:",
    kv_net_rate: "Net Rate (↓/↑):",
    kv_net_tot: "Net Total (RX/TX):",
    kv_bat: "Battery:",
    kv_proc: "cpuminer Process:",
    btn_copy_cli: "📋 Copy CLI",
    cmd_box_title: "Active cpuminer command line",
    click_copy: "Click to copy",
    t_log: "📜 Miner Event Console",
    btn_export_log: "⬇ Export .log",
    btn_clear_log: "🧹 Clear",
    flt_all: "All",
    flt_shares: "✓ Shares",
    flt_jobs: "⚡ Diff/Jobs",
    flt_err: "✖ Errors",
    ph_log_search: "🔍 Filter logs...",
    lbl_autoscroll: "Auto-scroll",
    footer_brand: "CPUMiner Live Dashboard · Universal Multi-Algo Mission Control · Developed by <b>Luan Quaresma</b>",
    m_cfg_title: "⚙️ Comparative Configuration Center (Previous vs New)",
    btn_close: "✖ Close",
    lbl_preset_pool: "Quick Pool Presets:",
    opt_sel_pool: "-- Select Known Pool (DGB & CPUMiner) --",
    opt_sel_algo: "-- Algorithm --",
    th_cfg_param: "Parameter",
    th_cfg_old: "⏪ Active Value (Current)",
    th_cfg_new: "🆕 New Value (Edit)",
    th_cfg_status: "Status",
    fld_bin: "Binary Path",
    fld_algo: "Algorithm (-a)",
    fld_pool: "Pool URL (-o)",
    fld_user: "Wallet.Worker (-u)",
    fld_pass: "Pool Password (-p)",
    fld_threads: "CPU Threads (-t, 0=Auto)",
    btn_cfg_save_restart: "✔ Save & Restart Miner Now",
    btn_cfg_save: "💾 Save without Restarting",
    btn_cancel: "✖ Cancel",
    m_dns_title: "🌍 Global DNS & Stratum TCP Latency Radar",
    btn_test_again: "🔄 Test Again",
    lbl_new_dns_host: "➕ New DNS Host:",
    ph_dns_name: "Name (e.g. My Pool)",
    ph_dns_reg: "Region (e.g. US / Global)",
    ph_dns_url: "Host/URL (e.g. stratum+tcp://pool.com:3333)",
    btn_add_dns_host: "➕ Add DNS Host",
    ph_dns_filter: "🔍 Filter pools by name, region or host...",
    th_dns_pool: "Pool",
    th_dns_reg: "Region",
    th_dns_host: "Host : Port",
    th_dns_ip: "Resolved IP",
    th_dns_ping: "TCP Ping",
    th_dns_qual: "Quality",
    th_dns_action: "Action",
    m_don_title: "💝 Support the Open-Source Project · Luan Quaresma",
    don_desc: "This comprehensive telemetry suite (Terminal TUI & Web Mission Control) is 100% free and open-source. If this tool aids your mining operations, please consider supporting development with Bitcoin (BTC) or DigiByte (DGB):",
    don_btc_hdr: "₿ BITCOIN (BTC · Native SegWit Network)",
    btn_copy_btc: "📋 Copy BTC Address",
    don_dgb_hdr: "💎 DIGIBYTE (DGB · Mainnet)",
    btn_copy_dgb: "📋 Copy DGB Address",
    prompt_token: "Enter Web Token (--web-token):",
    of_peak: "of Peak",
    stab: "Stab",
    total: "total",
    efficiency: "Efficiency",
    last: "Last",
    per_min: "/min",
    qual_exc: "EXCELLENT",
    qual_good: "GOOD",
    qual_med: "MEDIUM",
    qual_high: "HIGH",
    temp_na: "Temp N/A",
    collecting_samples: "collecting samples...",
    rej_reasons: "Rejection reasons",
    accepted: "Accepted",
    rejected: "Rejected",
    since_last: "Since last share",
    waiting_first_share: "Waiting for 1st share...",
    accepted_caps: "ACCEPTED",
    rejected_caps: "REJECTED",
    at_time: "at",
    mining_next_share: "Mining next share...",
    block_prefix: "Block",
    average: "Average",
    threads_word: "threads",
    estimated_short: "Est.",
    relative_hr: "Relative Hashrate",
    charging: "⚡ Charging",
    battery: "🔋 Battery",
    ac_desktop: "AC / Desktop",
    stopped: "Stopped",
    auto_threads: "Automatic (0)",
    cfg_changed: "CHANGED",
    cfg_kept: "kept",
    dns_online: "online",
    dns_pools_total: "pools",
    dns_best_found: "Lowest Latency Detected",
    dns_none_responded: "No pools responded to TCP benchmark at this time",
    dns_queried: "pools tested",
    dns_none_avail: "No pools available in radar.",
    dns_none_found: "No pools found.",
    dns_del_tooltip: "Remove custom host",
    btn_use_pool: "✔ Use Pool",
    dns_probing_banner: "Probing DNS servers and Stratum TCP latency globally... Please wait.",
    dns_probing_table: "Resolving DNS and benchmarking TCP latency for all pools... Please wait.",
    dns_err_title: "Error fetching pool benchmarks",
    dns_comm_fail: "Communication failure",
    btn_retry: "Retry",
    dns_fail_api: 'Connection failed with DNS benchmark API. Click "Retry".',
    alert_enter_pool: "Please enter Pool Host or URL (e.g. stratum+tcp://dgb.fusionpool.pro:3332)",
    copied_addr: "Address copied to clipboard",
    st_mining: "MINING",
    st_connecting: "CONNECTING",
    st_starting: "STARTING",
    st_stopped: "STOPPED",
    st_error: "ERROR",
    core_active: "Active",
    core_idle: "Inactive",
    core_est: "Active (Est.)"
  }
};

let currentLang = 'pt';

function t(key, fallback = '') {
  const dict = I18N_WEB[currentLang] || I18N_WEB['pt'];
  if (dict && dict[key] !== undefined) return dict[key];
  const defDict = I18N_WEB['pt'] || {};
  return defDict[key] !== undefined ? defDict[key] : (fallback || key);
}

function applyWebI18n(lang) {
  if (lang !== 'pt' && lang !== 'en') lang = 'pt';
  currentLang = lang;
  const sel = document.getElementById('sel-lang');
  if (sel && sel.value !== lang) sel.value = lang;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.getAttribute('data-i18n');
    const val = t(k);
    if (val) el.textContent = val;
  });

  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    const k = el.getAttribute('data-i18n-html');
    const val = t(k);
    if (val) el.innerHTML = val;
  });

  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const k = el.getAttribute('data-i18n-ph');
    const val = t(k);
    if (val) el.setAttribute('placeholder', val);
  });

  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const k = el.getAttribute('data-i18n-title');
    const val = t(k);
    if (val) el.setAttribute('title', val);
  });
}

const urlParams = new URLSearchParams(window.location.search);
let TOKEN = urlParams.get('token') || localStorage.getItem('miner_web_token') || '';
if (urlParams.get('token')) localStorage.setItem('miner_web_token', TOKEN);

let lastState = null;
let coreViewMode = 'cards'; // 'cards' | 'table'
let logFilter = 'all';
let cachedEvents = [];

function apiHeaders() {
  const h = {'Content-Type': 'application/json'};
  if (TOKEN) h['X-Auth-Token'] = TOKEN;
  return h;
}

async function apiFetch(path, opts={}) {
  opts.headers = Object.assign(apiHeaders(), opts.headers || {});
  const sep = path.includes('?') ? '&' : '?';
  const url = TOKEN ? `${path}${sep}token=${encodeURIComponent(TOKEN)}` : path;
  const r = await fetch(url, opts);
  if (r.status === 401) {
    const entered = prompt(t('prompt_token'));
    if (entered !== null) {
      TOKEN = entered;
      localStorage.setItem('miner_web_token', entered);
      return apiFetch(path, opts);
    }
  }
  return r.json();
}

function pingColorHex(ms) {
  if (!ms || ms <= 0) return '#ff3355';
  if (ms < 100) return '#00ff88';
  if (ms < 180) return '#22c55e';
  if (ms < 300) return '#fbbf24';
  return '#ff3355';
}

function pctColorHex(pct, warn=65, crit=85) {
  if (pct >= crit) return '#ff3355';
  if (pct >= warn) return '#fbbf24';
  return '#00ff88';
}

function switchView(mode, btn) {
  document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');

  const secCharts = document.getElementById('sec-charts');
  const secVis = document.getElementById('sec-visualizers');
  const secBot = document.getElementById('sec-bottom');
  const pnlHash = document.getElementById('pnl-hash');
  const pnlPool = document.getElementById('pnl-pool');
  const pnlCores = document.getElementById('pnl-cores');
  const pnlSys = document.getElementById('pnl-sys');
  const pnlLog = document.getElementById('pnl-log');

  [secCharts, secVis, secBot, pnlHash, pnlPool, pnlCores, pnlSys, pnlLog].forEach(el => el.classList.remove('hidden-view'));
  secCharts.style.gridTemplateColumns = '';
  secBot.style.gridTemplateColumns = '';

  if (mode === 'hash') {
    pnlPool.classList.add('hidden-view');
    secCharts.style.gridTemplateColumns = '1fr';
    secVis.classList.add('hidden-view');
    pnlSys.classList.add('hidden-view');
    pnlLog.classList.add('hidden-view');
    secBot.style.gridTemplateColumns = '1fr';
  } else if (mode === 'pool') {
    pnlHash.classList.add('hidden-view');
    secCharts.style.gridTemplateColumns = '1fr';
    secVis.classList.add('hidden-view');
    pnlCores.classList.add('hidden-view');
    pnlSys.classList.add('hidden-view');
    pnlLog.classList.add('hidden-view');
    secBot.style.gridTemplateColumns = '1fr';
  } else if (mode === 'sys') {
    secCharts.classList.add('hidden-view');
    secVis.classList.add('hidden-view');
    pnlLog.classList.add('hidden-view');
    secBot.style.gridTemplateColumns = '1fr 1fr';
  } else if (mode === 'log') {
    secCharts.classList.add('hidden-view');
    secVis.classList.add('hidden-view');
    pnlCores.classList.add('hidden-view');
    pnlSys.classList.add('hidden-view');
    secBot.style.gridTemplateColumns = '1fr';
    document.getElementById('log-box').style.height = '520px';
  } else {
    document.getElementById('log-box').style.height = '255px';
  }
}

function toggleCoreView() {
  coreViewMode = coreViewMode === 'cards' ? 'table' : 'cards';
  document.getElementById('cores-cards').classList.toggle('hidden-view', coreViewMode !== 'cards');
  document.getElementById('cores-table-wrap').classList.toggle('hidden-view', coreViewMode !== 'table');
}

function setRadialGauge(id, pct, color) {
  const el = document.getElementById(id);
  if (!el) return;
  const circum = 201;
  const clamped = Math.max(0, Math.min(100, pct || 0));
  el.style.strokeDashoffset = (circum - (clamped / 100) * circum).toFixed(1);
  if (color) el.style.stroke = color;
}

function renderHashrateSVG(history, peakVal) {
  const svg = document.getElementById('svg-hashrate');
  if (!svg) return;
  const W = 760, H = 195, padL = 54, padR = 14, padT = 14, padB = 24;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  const arr = (history && history.length) ? history : [0];
  const maxV = Math.max(...arr, peakVal || 0, 1);

  function fmtAxis(v) {
    if (v >= 1e9) return (v/1e9).toFixed(1) + 'G';
    if (v >= 1e6) return (v/1e6).toFixed(1) + 'M';
    if (v >= 1e3) return (v/1e3).toFixed(1) + 'k';
    return v.toFixed(0);
  }

  let html = `
    <defs>
      <linearGradient id="hrGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="var(--secondary)" stop-opacity="0.42"/>
        <stop offset="100%" stop-color="var(--secondary)" stop-opacity="0.0"/>
      </linearGradient>
    </defs>`;

  for (let i = 0; i <= 4; i++) {
    const y = padT + (plotH * i / 4);
    const val = maxV * (1 - i / 4);
    html += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="rgba(255,255,255,0.07)" stroke-dasharray="3,3"/>`;
    html += `<text x="${padL - 6}" y="${y + 4}" fill="#94a3b8" font-size="10" text-anchor="end" font-family="monospace">${fmtAxis(val)}</text>`;
  }

  if (peakVal > 0) {
    const py = padT + plotH * (1 - Math.min(1, peakVal / maxV));
    html += `<line x1="${padL}" y1="${py}" x2="${W - padR}" y2="${py}" stroke="var(--warn)" stroke-width="1" stroke-dasharray="5,4" opacity="0.75"/>`;
  }

  const pts = arr.map((v, idx) => {
    const x = padL + (arr.length === 1 ? plotW : (idx / (arr.length - 1)) * plotW);
    const y = padT + plotH * (1 - Math.min(1, Math.max(0, v) / maxV));
    return [x, y];
  });

  const maPts = arr.map((_, idx) => {
    const slice = arr.slice(Math.max(0, idx - 5), idx + 1);
    const mv = slice.reduce((a, b) => a + b, 0) / slice.length;
    const x = pts[idx][0];
    const y = padT + plotH * (1 - Math.min(1, Math.max(0, mv) / maxV));
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  if (pts.length > 1) {
    const polyPts = pts.map(p => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
    const areaPts = `${pts[0][0].toFixed(1)},${padT + plotH} ` + polyPts + ` ${pts[pts.length - 1][0].toFixed(1)},${padT + plotH}`;
    html += `<polygon points="${areaPts}" fill="url(#hrGrad)"/>`;
    html += `<polyline points="${maPts.join(' ')}" fill="none" stroke="var(--primary)" stroke-width="1.6" stroke-dasharray="4,3" opacity="0.85"/>`;
    html += `<polyline points="${polyPts}" fill="none" stroke="var(--secondary)" stroke-width="2.4"/>`;
    const last = pts[pts.length - 1];
    html += `<circle cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="4" fill="var(--secondary)"/>`;
  }

  svg.innerHTML = html;
}

function setLogFilter(flt, btn) {
  logFilter = flt;
  document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderLogs();
}

function renderLogs() {
  const lb = document.getElementById('log-box');
  if (!lb) return;
  const q = (document.getElementById('log-search').value || '').toLowerCase();
  const autoScroll = document.getElementById('chk-autoscroll').checked;
  lb.innerHTML = '';

  const filtered = cachedEvents.filter(ev => {
    if (logFilter !== 'all' && ev.style !== logFilter) return false;
    if (q && !ev.text.toLowerCase().includes(q) && !ev.ts.toLowerCase().includes(q)) return false;
    return true;
  });

  document.getElementById('v-log-cnt').textContent = filtered.length;

  filtered.forEach(ev => {
    const div = document.createElement('div');
    div.className = 'log-line ' + (ev.style || '');
    const col = ev.style === 'green' ? '#00ff88' : ev.style === 'red' ? '#ff3355' : ev.style === 'yellow' ? '#fbbf24' : '#cbd5e1';
    div.innerHTML = `<span style="color:#64748b">[${ev.ts}]</span> <span style="color:${col}">${ev.text}</span>`;
    lb.appendChild(div);
  });

  if (autoScroll) lb.scrollTop = lb.scrollHeight;
}

function exportLogs() {
  const txt = cachedEvents.map(e => `[${e.ts}] ${e.text}`).join('\n');
  const blob = new Blob([txt], {type: 'text/plain;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `cpuminer_session_${Date.now()}.log`;
  a.click();
}

async function clearLogs() {
  await apiFetch('/api/control', {method: 'POST', body: JSON.stringify({action: 'clear_logs'})});
  cachedEvents = [];
  renderLogs();
}

async function controlMiner(action) {
  await apiFetch('/api/control', {method: 'POST', body: JSON.stringify({action})});
  pollState();
}

async function pollState() {
  try {
    const s = await apiFetch('/api/state');
    if (!s || !s.config) return;
    lastState = s;

    // Theme CSS sync
    const th = s.theme_colors;
    if (th) {
      document.documentElement.style.setProperty('--bg', th.web_bg);
      document.documentElement.style.setProperty('--card', th.web_card);
      document.documentElement.style.setProperty('--primary', th.web_primary);
      document.documentElement.style.setProperty('--secondary', th.web_secondary);
      document.documentElement.style.setProperty('--accent', th.web_accent);
    }
    document.getElementById('sel-theme').value = s.config.theme;

    // Language sync
    if (s.config.lang && s.config.lang !== currentLang) {
      applyWebI18n(s.config.lang);
    } else {
      document.getElementById('sel-lang').value = currentLang;
    }

    // Top Header
    const stBadge = document.getElementById('st-badge');
    const stKey = 'st_' + (s.state || '').toLowerCase();
    document.getElementById('st-text').textContent = t(stKey, s.state_label);
    stBadge.className = 'status-pill ' + (s.state === 'mining' ? '' : (s.state === 'error' || s.state === 'stopped') ? 'err' : 'warn');
    document.getElementById('v-uptime').textContent = s.uptime;
    document.getElementById('v-top-algo').textContent = s.config.algo.toUpperCase();
    document.getElementById('v-top-pool').textContent = s.config.pool_host;
    document.getElementById('v-top-pid').textContent = s.pid || '—';
    document.getElementById('v-server-time').textContent = s.server_time || '';

    // 6-KPI Strip
    document.getElementById('k1-val').textContent = s.hashrate.current_fmt;
    document.getElementById('k1-rep').textContent = s.hashrate.reported_fmt;
    document.getElementById('k1-pct').textContent = `${s.hashrate.pct_of_peak}% ${t('of_peak')}`;
    document.getElementById('k1-stab').textContent = `${t('stab')}: ${s.hashrate.stability_pct}%`;
    document.getElementById('k1-bar').style.width = `${Math.min(100, s.hashrate.pct_of_peak)}%`;

    document.getElementById('k2-val').textContent = s.hashrate.peak_fmt;
    document.getElementById('k2-m1').textContent = s.hashrate.avg1_fmt;
    document.getElementById('k2-m5').textContent = s.hashrate.avg5_fmt;
    document.getElementById('k2-all').textContent = s.hashrate.avg_all_fmt;

    document.getElementById('k3-val').innerHTML =
      `<span style="color:#00ff88">${s.pool.accepted}</span> / <span style="color:#ff3355">${s.pool.rejected}</span>`;
    document.getElementById('k3-tot').textContent = `${s.pool.total} ${t('total')}`;
    document.getElementById('k3-rate').textContent = `${t('efficiency')}: ${s.pool.rate_pct}%`;
    document.getElementById('k3-last').textContent = `${t('last')}: ${s.pool.last_share_ago}`;
    document.getElementById('k3-bar').style.width = `${s.pool.rate_pct}%`;

    document.getElementById('k4-val').textContent = `${s.pool.spm} ${t('per_min')}`;
    document.getElementById('k4-sph').textContent = `${s.pool.sph}/h`;
    document.getElementById('k4-spd').textContent = `~${s.pool.spd}/d`;
    document.getElementById('k4-avg-t').textContent = `~${s.pool.avg_share_sec}s/sh`;
    document.getElementById('k4-bar').style.width = `${Math.min(100, s.pool.spm * 15)}%`;

    const pMs = s.pool.latency_ms;
    const pCol = pingColorHex(pMs);
    document.getElementById('k5-val').textContent = s.pool.online ? `${Math.round(pMs)} ms` : 'OFFLINE';
    document.getElementById('k5-val').style.color = pCol;
    document.getElementById('k5-qual').textContent = !s.pool.online ? 'OFFLINE' : (pMs < 100 ? t('qual_exc') : pMs < 180 ? t('qual_good') : pMs < 300 ? t('qual_med') : t('qual_high'));
    document.getElementById('k5-diff').textContent = s.pool.difficulty || '—';
    document.getElementById('k5-jobs').textContent = s.pool.jobs;
    document.getElementById('k5-jit').textContent = `${s.pool.ping_jitter || 0}ms`;
    document.getElementById('k5-bar').style.width = s.pool.online ? `${Math.max(10, 100 - Math.min(90, pMs / 4))}%` : '0%';
    document.getElementById('k5-bar').style.background = pCol;

    document.getElementById('k6-val').textContent = `CPU ${s.system.cpu_pct}%`;
    document.getElementById('k6-val').style.color = pctColorHex(s.system.cpu_pct);
    document.getElementById('k6-ram').textContent = `${s.system.ram_pct}%`;
    document.getElementById('k6-temp').textContent = s.system.temp_c ? `${s.system.temp_c} °C` : t('temp_na');
    document.getElementById('k6-cores').textContent = `${s.cores_active}/${s.cores_total}`;
    document.getElementById('k6-bar').style.width = `${s.system.cpu_pct}%`;

    // Hashrate Panel & SVG Oscilloscope
    document.getElementById('v-cur').textContent = s.hashrate.current_fmt;
    document.getElementById('v-peak').textContent = s.hashrate.peak_fmt;
    document.getElementById('v-min').textContent = s.hashrate.min_fmt;
    document.getElementById('v-avg1').textContent = s.hashrate.avg1_fmt;
    document.getElementById('v-avg5').textContent = s.hashrate.avg5_fmt;
    document.getElementById('v-avgall').textContent = s.hashrate.avg_all_fmt;
    renderHashrateSVG(s.hashrate.history, s.hashrate.peak);

    // Pool Panel & Ping Spectrum
    const stTag = document.getElementById('v-pool-status-tag');
    stTag.textContent = s.pool.online ? `ONLINE (${Math.round(pMs)}ms)` : 'OFFLINE';
    stTag.style.color = pCol;

    const pG = document.getElementById('ping-graph');
    pG.innerHTML = '';
    const pHist = s.pool.ping_history || [];
    const validP = pHist.filter(x => x !== null && x > 0);
    const pMax = Math.max(...validP, 300);
    pHist.slice(-48).forEach(ms => {
      const b = document.createElement('div');
      b.className = 'p-bar';
      const pct = (ms && ms > 0) ? Math.min(100, Math.max(14, Math.round((ms / pMax) * 100))) : 100;
      b.style.height = pct + '%';
      b.style.background = pingColorHex(ms);
      b.title = ms ? `${ms} ms` : 'Timeout / Offline';
      pG.appendChild(b);
    });
    document.getElementById('v-ping-stats').textContent =
      validP.length ? `min ${s.pool.ping_min}ms · avg ${s.pool.ping_avg}ms · max ${s.pool.ping_max}ms · jitter ${s.pool.ping_jitter}ms` : t('collecting_samples');

    document.getElementById('v-p-host').textContent = s.config.pool_host;
    document.getElementById('v-p-algo').textContent = s.config.algo;
    document.getElementById('v-p-wallet').textContent = s.config.wallet_short + ' 📋';
    document.getElementById('v-p-worker').textContent = s.config.worker;
    document.getElementById('v-p-diff').textContent = `${s.pool.difficulty || '—'} / ${s.pool.share_diff || '—'}`;
    document.getElementById('v-p-jobs').textContent = s.pool.jobs;
    document.getElementById('v-p-accrej').innerHTML =
      `<span style="color:#00ff88">${s.pool.accepted}</span> / <span style="color:#ff3355">${s.pool.rejected}</span> (${s.pool.rate_pct}%)`;
    document.getElementById('v-p-err').innerHTML =
      `<span style="color:${s.pool.errors ? '#ff3355' : '#00ff88'}">${s.pool.errors}</span> / ${s.pool.restarts}`;

    const rejBox = document.getElementById('v-rej-reasons');
    if (s.pool.reject_reasons && s.pool.reject_reasons.length) {
      rejBox.textContent = '⚠ ' + t('rej_reasons') + ': ' + s.pool.reject_reasons.map(r => `${r.reason} (×${r.count})`).join(', ');
    } else {
      rejBox.textContent = '';
    }

    // Dynamic 3-Row Cyber Share Matrix
    const sm = document.getElementById('share-map');
    sm.innerHTML = '';
    const boxW = Math.max(240, (sm.clientWidth || sm.parentElement.clientWidth || 720) - 20);
    const cols = Math.max(8, Math.floor(boxW / 26));
    const totalSlots = cols * 3;
    sm.style.gridTemplateColumns = `repeat(${cols}, minmax(0, 1fr))`;
    const recentShares = (s.shares_map || []).slice(-(totalSlots - 1));
    document.getElementById('v-grid-meta').textContent =
      `✓ ${s.pool.accepted} ${t('accepted')} | ✗ ${s.pool.rejected} ${t('rejected')} | ${t('efficiency')} ${s.pool.rate_pct}%`;
    document.getElementById('v-grid-timer').textContent =
      s.pool.since_last_sec !== null ? `${t('since_last')}: ${s.pool.since_last_sec}s` : t('waiting_first_share');

    recentShares.forEach((sh, idx) => {
      const c = document.createElement('div');
      c.className = 'sh-cell ' + (sh.ok ? (sh.fresh ? 'sh-fresh' : 'sh-ok') : 'sh-rej');
      c.textContent = sh.ok ? (sh.fresh ? '★' : '■') : '✖';
      c.title = `Share #${idx + 1} · ${sh.ok ? t('accepted_caps') : t('rejected_caps')} ${t('at_time')} ${sh.time}`;
      sm.appendChild(c);
    });
    const act = document.createElement('div');
    act.className = 'sh-cell sh-active';
    act.textContent = '❖';
    act.title = t('mining_next_share');
    sm.appendChild(act);

    const rem = Math.max(0, totalSlots - recentShares.length - 1);
    const scanIdx = Math.floor(Date.now() / 160) % Math.max(1, Math.min(cols, rem));
    for (let i = 0; i < rem; i++) {
      const e = document.createElement('div');
      e.className = 'sh-cell ' + (i === scanIdx ? 'sh-scan' : 'sh-empty');
      e.textContent = i === scanIdx ? '▸' : '·';
      sm.appendChild(e);
    }

    // Live Share Blockchain Stream
    const cr = document.getElementById('chain-row');
    cr.innerHTML = '';
    document.getElementById('v-chain-meta').textContent = `${t('block_prefix')} #${s.pool.total + 1}: ${s.next_block_pct}%`;
    document.getElementById('v-chain-avg').textContent = `${t('average')}: ~${s.pool.avg_share_sec}s / share`;

    const visBlocks = (s.blocks || []).slice(-8);
    visBlocks.forEach((b, idx) => {
      if (idx > 0) {
        const arr = document.createElement('span');
        arr.className = 'chain-arrow';
        arr.textContent = '═»';
        cr.appendChild(arr);
      }
      const d = document.createElement('div');
      d.className = 'blk-node ' + (b.ok ? '' : 'rej') + (b.fresh ? ' fresh' : '');
      d.innerHTML = `
        <div style="display:flex;justify-content:space-between;font-weight:800;color:${b.ok?'#00ff88':'#ff3355'}">
          <span>#${b.num}</span><span>${b.ok ? '✓' : '✗'}</span>
        </div>
        <div style="color:var(--muted);margin:2px 0;font-size:0.66rem;">${(b.digest || '').slice(0, 10)}</div>
        <div style="font-size:0.65rem;color:var(--text)">${b.time}</div>`;
      cr.appendChild(d);
    });

    if (visBlocks.length > 0) {
      const arr = document.createElement('span');
      arr.className = 'chain-arrow';
      arr.textContent = '═»';
      cr.appendChild(arr);
    }
    const hexScramble = Array.from({length: 10}, () => Math.floor(Math.random()*16).toString(16)).join('');
    const nextB = document.createElement('div');
    nextB.className = 'blk-node mining';
    nextB.innerHTML = `
      <div style="display:flex;justify-content:space-between;font-weight:800;color:var(--warn)">
        <span>⠋ #${s.pool.total + 1}</span><span>${s.next_block_pct}%</span>
      </div>
      <div style="color:var(--primary);margin:2px 0;font-size:0.66rem;">${hexScramble}</div>
      <div class="bar-bg" style="height:5px;"><div class="bar-fill" style="width:${s.next_block_pct}%;background:var(--warn)"></div></div>`;
    cr.appendChild(nextB);
    cr.scrollLeft = cr.scrollWidth;

    // Per-Core CPU Performance (Cards + Table)
    document.getElementById('v-cores-summary').textContent =
      `${s.cores_active}/${s.cores_total} ${t('threads_word')}` + (s.cores_estimated ? ` (${t('estimated_short')})` : '');
    const cc = document.getElementById('cores-cards');
    const ct = document.getElementById('cores-tbody');
    cc.innerHTML = '';
    ct.innerHTML = '';

    (s.cores || []).forEach(c => {
      const card = document.createElement('div');
      card.className = 'core-card' + (c.alive ? '' : ' inactive');
      const cpuCol = pctColorHex(c.cpu_pct);
      const stCore = c.alive ? (c.estimated ? t('core_est') : t('core_active')) : t('core_idle');
      card.innerHTML = `
        <div class="core-card-top">
          <b style="color:var(--warn)">CPU #${c.id}</b>
          <span style="font-size:0.68rem;color:${c.alive ? '#00ff88' : '#94a3b8'}">${stCore}</span>
        </div>
        <div class="core-hr">${c.hash_fmt}</div>
        <div class="bar-bg" title="${t('relative_hr')}: ${c.rel_pct}%"><div class="bar-fill" style="width:${c.rel_pct}%"></div></div>
        <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:var(--muted);margin-top:2px;">
          <span style="color:${cpuCol}">CPU ${c.cpu_pct}%</span>
          <span>${c.freq_mhz}</span>
        </div>`;
      cc.appendChild(card);

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="color:var(--warn);font-weight:700">#${c.id}</td>
        <td style="color:var(--secondary);font-weight:700">${c.hash_fmt}</td>
        <td style="width:95px"><div class="bar-bg"><div class="bar-fill" style="width:${c.rel_pct}%"></div></div></td>
        <td style="color:${cpuCol}">${c.cpu_pct}%</td>
        <td>${c.freq_mhz}</td>
        <td><span class="tag">${stCore}</span></td>`;
      ct.appendChild(tr);
    });

    // Hardware Radial Gauges & System Details
    document.getElementById('v-sys-load').textContent = `Load: ${s.system.load_avg}`;
    setRadialGauge('g-cpu', s.system.cpu_pct, pctColorHex(s.system.cpu_pct));
    document.getElementById('gv-cpu').textContent = `${s.system.cpu_pct}%`;

    setRadialGauge('g-ram', s.system.ram_pct, pctColorHex(s.system.ram_pct));
    document.getElementById('gv-ram').textContent = `${s.system.ram_pct}%`;

    setRadialGauge('g-swap', s.system.swap_pct, pctColorHex(s.system.swap_pct));
    document.getElementById('gv-swap').textContent = `${s.system.swap_pct}%`;

    const tVal = s.system.temp_c || 0;
    setRadialGauge('g-temp', Math.min(100, tVal), tVal >= 75 ? '#ff3355' : tVal >= 60 ? '#fbbf24' : '#00ff88');
    document.getElementById('gv-temp').textContent = s.system.temp_c ? `${s.system.temp_c}°C` : 'N/A';

    document.getElementById('v-s-ram').textContent = `${s.system.ram_used} / ${s.system.ram_total} (${s.system.ram_pct}%)`;
    document.getElementById('v-s-swap').textContent = `${s.system.swap_used} / ${s.system.swap_total} (${s.system.swap_pct}%)`;
    document.getElementById('v-s-net').textContent = `↓ ${s.system.net_down} · ↑ ${s.system.net_up}`;
    document.getElementById('v-s-nettot').textContent = `RX ${s.system.net_total_rx} · TX ${s.system.net_total_tx}`;
    document.getElementById('v-s-bat').textContent =
      s.system.bat_pct !== null ? `${s.system.bat_pct}% (${s.system.bat_plugged ? t('charging') : t('battery')})` : t('ac_desktop');
    document.getElementById('v-s-proc').textContent = s.system.proc_info || (s.pid ? `PID ${s.pid}` : t('stopped'));
    document.getElementById('v-cmd-line').textContent = s.config.cmd_line;

    // Events Console
    cachedEvents = s.events || [];
    renderLogs();
  } catch (e) {}
}

async function changeTheme(theme) {
  await apiFetch('/api/config', {method: 'POST', body: JSON.stringify({theme})});
  pollState();
}

async function changeLang(lang) {
  applyWebI18n(lang);
  localStorage.setItem('miner_web_lang', lang);
  await apiFetch('/api/config', {method: 'POST', body: JSON.stringify({lang})});
  pollState();
  if (window._allDnsPools && window._allDnsPools.length > 0) {
    renderDnsTable(window._allDnsPools);
  }
}

function openModal(id) {
  if (id === 'modal-cfg' && lastState && lastState.config) {
    const c = lastState.config;
    document.getElementById('old-bin').textContent = c.bin;
    document.getElementById('old-algo').textContent = c.algo;
    document.getElementById('old-pool').textContent = c.pool;
    document.getElementById('old-user').textContent = c.user;
    document.getElementById('old-pass').textContent = c.password;
    document.getElementById('old-threads').textContent = c.threads === 0 ? t('auto_threads') : c.threads;

    document.getElementById('f-bin').value = c.bin;
    document.getElementById('f-algo').value = c.algo;
    document.getElementById('f-pool').value = c.pool;
    document.getElementById('f-user').value = c.user;
    document.getElementById('f-pass').value = c.password;
    document.getElementById('f-threads').value = c.threads;
    updateCfgDiff();
  }
  document.getElementById(id).classList.add('active');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

function applyPoolPreset(url) {
  if (!url) return;
  document.getElementById('f-pool').value = url;
  updateCfgDiff();
}

function updateCfgDiff() {
  if (!lastState || !lastState.config) return;
  const c = lastState.config;
  const pairs = [
    ['bin', c.bin, document.getElementById('f-bin').value.trim()],
    ['algo', c.algo, document.getElementById('f-algo').value.trim()],
    ['pool', c.pool, document.getElementById('f-pool').value.trim()],
    ['user', c.user, document.getElementById('f-user').value.trim()],
    ['pass', c.password, document.getElementById('f-pass').value.trim()],
    ['threads', String(c.threads), String(parseInt(document.getElementById('f-threads').value || '0', 10))],
  ];
  pairs.forEach(([key, ov, nv]) => {
    const el = document.getElementById('st-' + key);
    if (!el) return;
    if (String(ov) !== String(nv)) {
      el.innerHTML = `<span class="cmp-badge-mod">● ${t('cfg_changed')}</span>`;
    } else {
      el.innerHTML = `<span class="cmp-badge-kept">${t('cfg_kept')}</span>`;
    }
  });
}

async function saveWebConfig(restartMiner) {
  const payload = {
    bin: document.getElementById('f-bin').value.trim(),
    algo: document.getElementById('f-algo').value.trim(),
    pool: document.getElementById('f-pool').value.trim(),
    user: document.getElementById('f-user').value.trim(),
    password: document.getElementById('f-pass').value.trim(),
    threads: parseInt(document.getElementById('f-threads').value || '0', 10),
    restart_miner: Boolean(restartMiner)
  };
  await apiFetch('/api/config', {method: 'POST', body: JSON.stringify(payload)});
  closeModal('modal-cfg');
  pollState();
}

let _dnsTesting = false;
window._allDnsPools = [];

function renderDnsTable(pools) {
  const banner = document.getElementById('dns-best-banner');
  const tb = document.getElementById('dns-tbody');
  const countBadge = document.getElementById('dns-count-badge');
  if (!tb) return;
  tb.innerHTML = '';

  const list = pools || [];
  const onlinePools = list.filter(p => p && p.ok);
  const best = onlinePools.length > 0 ? onlinePools[0] : null;

  if (countBadge) {
    countBadge.textContent = `${onlinePools.length} ${t('dns_online')} / ${list.length} ${t('dns_pools_total')}`;
  }

  if (best) {
    banner.innerHTML = `🏆 <b>${t('dns_best_found')}:</b> ${best.name} (${best.region}) — <b style="color:#00ff88">${Math.round(best.tcp_ms)} ms</b> (<span class="mono">${best.url}</span>)`;
  } else if (list.length > 0) {
    banner.innerHTML = `⚠ ${t('dns_none_responded')} (${list.length} ${t('dns_queried')}).`;
  } else {
    banner.innerHTML = `⚠ ${t('dns_none_avail')}`;
  }

  if (list.length === 0) {
    tb.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:20px;color:var(--muted)">${t('dns_none_found')}</td></tr>`;
    return;
  }

  list.forEach((r, idx) => {
    const tr = document.createElement('tr');
    const c = pingColorHex(r.tcp_ms);
    const qual = !r.ok ? '✖ OFFLINE' : (r.tcp_ms < 100 ? t('qual_exc') : r.tcp_ms < 180 ? t('qual_good') : r.tcp_ms < 300 ? t('qual_med') : t('qual_high'));
    const delBtn = r.custom
      ? ` <button class="btn-danger btn-del-host" data-url="${encodeURIComponent(r.url)}" title="${t('dns_del_tooltip')}" style="padding:3px 7px;font-size:0.74rem;">🗑</button>`
      : '';
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td><b>${r.name}</b>${r.custom ? ' <span class="tag" style="font-size:0.65rem;color:var(--primary)">Custom</span>' : ''}</td>
      <td>${r.region}</td>
      <td>${r.host}:${r.port}</td>
      <td style="color:var(--primary)">${r.ip || '—'}</td>
      <td>${r.dns_ms ? Math.round(r.dns_ms)+' ms' : '—'}</td>
      <td style="color:${c};font-weight:800">${r.ok ? Math.round(r.tcp_ms)+' ms' : 'OFFLINE'}</td>
      <td>
        <div style="display:flex;align-items:center;gap:6px;">
          <div style="width:70px;height:8px;background:#1e293b;border-radius:4px;overflow:hidden">
            <div style="width:${r.ok ? Math.min(100, Math.max(15, r.tcp_ms/4)) : 100}%;height:100%;background:${c}"></div>
          </div>
          <span style="color:${c};font-size:0.73rem">${qual}</span>
        </div>
      </td>
      <td style="white-space:nowrap;"><button class="btn-success btn-use-pool" data-url="${encodeURIComponent(r.url)}" style="padding:3px 9px;font-size:0.74rem;">${t('btn_use_pool')}</button>${delBtn}</td>`;
    tb.appendChild(tr);
  });

  tb.querySelectorAll('.btn-use-pool').forEach(btn => {
    btn.onclick = () => applyDnsPool(decodeURIComponent(btn.dataset.url));
  });
  tb.querySelectorAll('.btn-del-host').forEach(btn => {
    btn.onclick = () => removeDnsHost(decodeURIComponent(btn.dataset.url));
  });
}

function filterDnsList(q) {
  const query = (q || '').trim().toLowerCase();
  if (!query) {
    renderDnsTable(window._allDnsPools);
    return;
  }
  const filtered = (window._allDnsPools || []).filter(p =>
    (p.name && p.name.toLowerCase().includes(query)) ||
    (p.region && p.region.toLowerCase().includes(query)) ||
    (p.url && p.url.toLowerCase().includes(query)) ||
    (p.host && p.host.toLowerCase().includes(query))
  );
  renderDnsTable(filtered);
}

async function openDnsModal(forceFresh=false) {
  openModal('modal-dns');
  const banner = document.getElementById('dns-best-banner');
  const tb = document.getElementById('dns-tbody');

  if (window._allDnsPools && window._allDnsPools.length > 0 && !forceFresh) {
    renderDnsTable(window._allDnsPools);
    return;
  }

  if (_dnsTesting) return;
  _dnsTesting = true;

  banner.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite;margin-right:6px;">🔄</span> 🌍 ' + t('dns_probing_banner');

  if (!window._allDnsPools || window._allDnsPools.length === 0) {
    tb.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:26px;color:var(--primary);font-size:0.86rem;"><span style="display:inline-block;animation:spin 0.9s linear infinite;margin-right:8px;">🔄</span> ' + t('dns_probing_table') + '</td></tr>';
  }

  try {
    const res = await apiFetch('/api/dns_test' + (forceFresh ? '?refresh=1' : ''));
    if (!res || !res.pools || !Array.isArray(res.pools)) {
      throw new Error((res && res.error) || t('dns_comm_fail'));
    }
    window._allDnsPools = res.pools;
    const filterInput = document.getElementById('dns-search-filter');
    if (filterInput && filterInput.value.trim()) {
      filterDnsList(filterInput.value);
    } else {
      renderDnsTable(window._allDnsPools);
    }
  } catch (err) {
    console.error('Falha no radar DNS:', err);
    banner.innerHTML = `<span style="color:#ff3355">⚠ ${t('dns_err_title')}:</span> ${err.message || t('dns_comm_fail')}. <button class="btn-primary" onclick="openDnsModal(true)" style="padding:2px 8px;margin-left:8px;font-size:0.75rem;">🔄 ${t('btn_retry')}</button>`;
    if (!window._allDnsPools || window._allDnsPools.length === 0) {
      tb.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:24px;color:#ff3355">${t('dns_fail_api')}</td></tr>`;
    }
  } finally {
    _dnsTesting = false;
  }
}

async function addDnsHost() {
  const name = (document.getElementById('dns-add-name').value || '').trim() || 'Custom DNS';
  const region = (document.getElementById('dns-add-reg').value || '').trim() || 'Custom';
  const url = (document.getElementById('dns-add-url').value || '').trim();
  if (!url) {
    alert(t('alert_enter_pool'));
    return;
  }
  await apiFetch('/api/dns_hosts', {
    method: 'POST',
    body: JSON.stringify({action: 'add', name, region, url})
  });
  document.getElementById('dns-add-name').value = '';
  document.getElementById('dns-add-reg').value = '';
  document.getElementById('dns-add-url').value = '';
  openDnsModal(true);
}

async function removeDnsHost(url) {
  await apiFetch('/api/dns_hosts', {
    method: 'POST',
    body: JSON.stringify({action: 'remove', url})
  });
  openDnsModal(true);
}

async function applyDnsPool(poolUrl) {
  await apiFetch('/api/config', {method: 'POST', body: JSON.stringify({pool: poolUrl, restart_miner: true})});
  closeModal('modal-dns');
  pollState();
}

function copyCurrentWallet() {
  if (lastState && lastState.config && lastState.config.wallet) {
    navigator.clipboard.writeText(lastState.config.wallet);
  }
}

function copyCmdLine() {
  if (lastState && lastState.config && lastState.config.cmd_line) {
    navigator.clipboard.writeText(lastState.config.cmd_line);
  }
}

function copyAddr(addr) {
  navigator.clipboard.writeText(addr);
  const el = document.getElementById('copy-msg');
  if (el) el.textContent = '✔ ' + t('copied_addr') + ': ' + addr;
}

const savedLang = urlParams.get('lang') || localStorage.getItem('miner_web_lang') || 'pt';
applyWebI18n(savedLang);
setInterval(pollState, 1000);
pollState();
</script>
</body>
</html>
"""


def build_web_state_dict(stats, sysinfo, args, n_cores):
    now = time.time()
    theme = get_theme(args)
    with stats.lock:
        hist = list(stats.history)
        best = stats.best_hash
        acc, tot = stats.accepted, stats.total_shares
        last_ts = stats.last_share_ts
        last_ok = stats.last_share_ok
        share_times = list(stats.share_times)
        diff, jobs = stats.difficulty, stats.jobs
        sdiff = stats.share_diff
        errors, restarts = stats.errors, stats.restarts
        reject_reasons = dict(stats.reject_reasons)
        lat = stats.pool_latency
        online = stats.pool_online
        ping_hist = list(stats.ping_history)
        cores_raw = dict(stats.cores)
        reported = stats.reported_hash
        blocks_raw = list(stats.blocks)[-14:]
        share_log_raw = list(stats.share_log)[-115:]
        events_raw = list(stats.events)[-80:]

    cur = hist[-1] if hist else 0.0
    nz = [h for h in hist if h > 0]
    avg_all = (sum(nz) / len(nz)) if nz else 0.0
    min_hr = min(nz) if nz else 0.0
    avg1 = (sum(hist[-60:]) / len(hist[-60:])) if hist[-60:] else 0.0
    avg5 = (sum(hist[-300:]) / len(hist[-300:])) if hist[-300:] else 0.0
    pct_of_peak = round((cur / best * 100), 1) if best > 0 else 0.0
    if len(nz) >= 3 and avg_all > 0:
        mean_dev = sum(abs(x - avg_all) for x in nz[-30:]) / len(nz[-30:])
        stability_pct = round(max(0.0, min(100.0, 100.0 - (mean_dev / avg_all * 100.0))), 1)
    else:
        stability_pct = 100.0 if cur > 0 else 0.0

    rej = max(0, tot - acc)
    rate_pct = round((acc / tot * 100), 2) if tot else 0.0
    elapsed = max(now - stats.start_time, 1.0)
    spm = round(len([t for t in share_times if now - t < 600]) / min(elapsed, 600.0) * 60.0, 2)
    sph = round(tot / elapsed * 3600.0, 1)
    spd = int(round(sph * 24.0))

    valid_pings = [p for p in ping_hist if p is not None and p > 0]
    ping_min = round(min(valid_pings), 1) if valid_pings else None
    ping_avg = round(sum(valid_pings) / len(valid_pings), 1) if valid_pings else None
    ping_max = round(max(valid_pings), 1) if valid_pings else None
    if len(valid_pings) >= 2:
        diffs = [abs(valid_pings[i] - valid_pings[i - 1]) for i in range(1, len(valid_pings))]
        ping_jitter = round(sum(diffs) / len(diffs), 1)
    else:
        ping_jitter = 0.0

    estimated_cores = False
    if not any(now - ts < 120 for _, ts in cores_raw.values()) and reported and last_ts and now - last_ts < 180:
        estimated_cores = True
        per = reported / max(n_cores, 1)
        cores_raw = {i: (per, now) for i in range(n_cores)}
    count = max(n_cores, (max(cores_raw) + 1) if cores_raw else 0)
    peak_core = max([hr for hr, _ in cores_raw.values()] + [1.0])

    cores_list = []
    active_cores_count = 0
    for i in range(count):
        hr, ts = cores_raw.get(i, (None, 0))
        alive = hr is not None and now - ts < 120
        if alive:
            active_cores_count += 1
        rel = round((hr / peak_core * 100), 1) if alive else 0
        usage = round(sysinfo.cpu_percpu[i], 1) if i < len(sysinfo.cpu_percpu) else 0.0
        freq = f"{sysinfo.freqs[i]:,.0f} MHz" if i < len(sysinfo.freqs) and sysinfo.freqs[i] else "—"
        st_lbl = tr(args, "core_est") if (alive and estimated_cores) else (tr(args, "core_act") if alive else tr(args, "core_nodata"))
        cores_list.append({
            "id": i,
            "hash_raw": round(hr, 2) if alive and hr else 0.0,
            "hash_fmt": ("~" if estimated_cores and alive else "") + fmt_hash(hr) if alive else "—",
            "rel_pct": rel,
            "cpu_pct": usage,
            "freq_mhz": freq,
            "alive": alive,
            "estimated": estimated_cores,
            "state_label": st_lbl,
        })

    ram_pct, ram_used, ram_tot = 0.0, "—", "—"
    swap_pct, swap_used, swap_tot = 0.0, "—", "—"
    bat_pct, bat_plug = None, None
    load_str = "—"
    try:
        l1, l5, l15 = os.getloadavg()
        load_str = f"{l1:.2f} / {l5:.2f} / {l15:.2f}"
    except Exception:
        pass
    if psutil:
        try:
            vm = psutil.virtual_memory()
            ram_pct = round(vm.percent, 1)
            ram_used = fmt_bytes(vm.used)
            ram_tot = fmt_bytes(vm.total)
            sw = psutil.swap_memory()
            if sw.total:
                swap_pct = round(sw.percent, 1)
                swap_used = fmt_bytes(sw.used)
                swap_tot = fmt_bytes(sw.total)
        except Exception:
            pass
        try:
            bat = psutil.sensors_battery()
            if bat:
                bat_pct = round(bat.percent, 0)
                bat_plug = bool(bat.power_plugged)
        except Exception:
            pass

    temp = sysinfo.temperature()
    d_rate, u_rate = sysinfo.net_rate
    rx_tot, tx_tot = getattr(sysinfo, "net_totals", (0, 0))
    proc_info = ""
    proc_cpu, proc_rss, proc_threads = 0.0, "—", 0
    if sysinfo.proc:
        try:
            with sysinfo.proc.oneshot():
                proc_cpu = round(sysinfo.proc.cpu_percent(None), 1)
                proc_rss = fmt_bytes(sysinfo.proc.memory_info().rss)
                proc_threads = sysinfo.proc.num_threads()
            proc_info = f"CPU {proc_cpu:.0f}% · RAM {proc_rss} · {proc_threads} threads"
        except Exception:
            pass

    avg_blk = elapsed / tot if tot else 10.0
    since_blk = now - (last_ts or stats.start_time)
    next_blk_pct = min(99, int((since_blk / max(avg_blk, 0.5)) * 100))

    u_pool = urlparse(args.pool if "://" in args.pool else "tcp://" + args.pool)
    wallet_addr = args.user.split(".")[0]
    worker_name = args.user.split(".", 1)[1] if "." in args.user else "default"

    cmd_preview = f"{args.bin} -a {args.algo} -o {args.pool} -u {args.user} -p {args.password}"
    if args.threads > 0:
        cmd_preview += f" -t {args.threads}"

    state_map = {
        "mining": tr(args, "st_mining"),
        "connecting": tr(args, "st_connecting"),
        "starting": tr(args, "st_starting"),
        "stopped": tr(args, "st_stopped"),
        "error": tr(args, "st_error"),
    }

    return {
        "state": stats.state,
        "state_label": state_map.get(stats.state, stats.state),
        "uptime": fmt_dur(now - stats.start_time),
        "uptime_sec": int(elapsed),
        "server_time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "pid": stats.pid,
        "theme_colors": theme,
        "config": {
            "bin": args.bin,
            "algo": args.algo,
            "pool": args.pool,
            "pool_host": f"{u_pool.hostname}:{u_pool.port or 3333}",
            "user": args.user,
            "wallet": wallet_addr,
            "wallet_short": short_wallet(wallet_addr, 10),
            "worker": worker_name,
            "password": args.password,
            "threads": args.threads,
            "no_restart": bool(args.no_restart),
            "theme": getattr(args, "theme", DEFAULT_THEME),
            "theme_label": theme["label"],
            "lang": getattr(args, "lang", DEFAULT_LANG),
            "cmd_line": cmd_preview,
        },
        "hashrate": {
            "current": round(cur, 2),
            "current_fmt": fmt_hash(cur),
            "peak": round(best, 2),
            "peak_fmt": fmt_hash(best),
            "min_fmt": fmt_hash(min_hr),
            "avg_all_fmt": fmt_hash(avg_all),
            "avg1_fmt": fmt_hash(avg1),
            "avg5_fmt": fmt_hash(avg5),
            "reported_fmt": fmt_hash(reported),
            "pct_of_peak": pct_of_peak,
            "stability_pct": stability_pct,
            "history": [round(x, 2) for x in hist[-80:]],
        },
        "pool": {
            "online": bool(online),
            "latency_ms": round(lat, 1) if lat else None,
            "ping_min": ping_min,
            "ping_avg": ping_avg,
            "ping_max": ping_max,
            "ping_jitter": ping_jitter,
            "ping_history": ping_hist[-50:],
            "accepted": acc,
            "rejected": rej,
            "total": tot,
            "rate_pct": rate_pct,
            "spm": spm,
            "sph": sph,
            "spd": spd,
            "avg_share_sec": round(avg_blk, 1),
            "since_last_sec": round(now - last_ts, 1) if last_ts else None,
            "last_share_ago": fmt_ago(last_ts, args) if last_ts else "—",
            "last_share_ok": last_ok,
            "difficulty": diff,
            "share_diff": sdiff,
            "jobs": jobs,
            "errors": errors,
            "restarts": restarts,
            "reject_reasons": [{"reason": k, "count": v} for k, v in sorted(reject_reasons.items(), key=lambda x: -x[1])[:4]],
        },
        "system": {
            "cpu_pct": round(sysinfo.cpu_total, 1),
            "load_avg": load_str,
            "ram_pct": ram_pct,
            "ram_used": ram_used,
            "ram_total": ram_tot,
            "swap_pct": swap_pct,
            "swap_used": swap_used,
            "swap_total": swap_tot,
            "temp_c": round(temp, 1) if temp else None,
            "bat_pct": bat_pct,
            "bat_plugged": bat_plug,
            "net_down": fmt_bytes(d_rate) + "/s",
            "net_up": fmt_bytes(u_rate) + "/s",
            "net_total_rx": fmt_bytes(rx_tot),
            "net_total_tx": fmt_bytes(tx_tot),
            "proc_cpu": proc_cpu,
            "proc_rss": proc_rss,
            "proc_threads": proc_threads,
            "proc_info": proc_info,
        },
        "shares_map": [
            {
                "ok": ok,
                "fresh": (now - ts) < 2.2,
                "age_s": round(now - ts, 1),
                "time": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
            }
            for ok, ts in share_log_raw
        ],
        "blocks": [
            {
                "num": num,
                "ok": ok,
                "digest": digest,
                "fresh": (now - ts) < 2.5,
                "time": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
            }
            for num, ok, digest, ts in blocks_raw
        ],
        "next_block_pct": next_blk_pct,
        "cores_estimated": estimated_cores,
        "cores_active": active_cores_count,
        "cores_total": count,
        "cores": cores_list,
        "events": [
            {"ts": ts, "text": txt, "style": st}
            for ts, txt, st in events_raw
        ],
    }


def start_web_server(args, stats, sysinfo, miner_ref, n_cores_getter):
    """Inicia o servidor HTTP/JSON do painel Web em thread daemon."""

    class DashboardHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *a):
            pass  # Silencia logs HTTP no terminal para nao sujar o Rich Live

        def _check_auth(self):
            token = getattr(args, "web_token", "")
            if not token:
                return True
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            if qs.get("token", [""])[0] == token:
                return True
            if self.headers.get("X-Auth-Token", "") == token:
                return True
            return False

        def _send_json(self, obj, code=200):
            raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/" or parsed.path == "/index.html":
                raw = WEB_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return

            if not self._check_auth():
                self._send_json({"error": "Unauthorized (invalid web token)"}, 401)
                return

            if parsed.path == "/api/state":
                data = build_web_state_dict(stats, sysinfo, args, n_cores_getter())
                self._send_json(data)
            elif parsed.path == "/api/dns_test":
                try:
                    qs = parse_qs(parsed.query)
                    force = qs.get("refresh", [""])[0] in ("1", "true", "yes")
                    pools = run_all_pools_probe(args, force_refresh=force)
                    self._send_json({"ok": True, "pools": pools})
                except Exception as e:
                    self._send_json({"ok": False, "error": str(e), "pools": []})
            else:
                self._send_json({"error": "Not found"}, 404)

        def do_POST(self):
            if not self._check_auth():
                self._send_json({"error": "Unauthorized"}, 401)
                return
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else "{}"
            try:
                data = json.loads(body)
            except Exception:
                self._send_json({"error": "Invalid JSON"}, 400)
                return

            if parsed.path == "/api/config":
                if "theme" in data and data["theme"] in THEMES:
                    args.theme = data["theme"]
                if "lang" in data and data["lang"] in LANG_KEYS:
                    args.lang = data["lang"]
                if "algo" in data and data["algo"]:
                    args.algo = str(data["algo"]).strip()
                if "pool" in data and data["pool"]:
                    args.pool = str(data["pool"]).strip()
                if "user" in data and data["user"]:
                    args.user = str(data["user"]).strip()
                if "password" in data:
                    args.password = str(data["password"]).strip()
                if "threads" in data:
                    args.threads = max(0, int(data["threads"]))
                if "bin" in data and data["bin"]:
                    args.bin = str(data["bin"]).strip()
                if "no_restart" in data:
                    args.no_restart = bool(data["no_restart"])

                save_config(args)
                if data.get("restart_miner") and miner_ref():
                    miner_ref().trigger_restart()
                self._send_json({"ok": True})

            elif parsed.path == "/api/dns_hosts":
                action = data.get("action", "add")
                if not hasattr(args, "custom_pools") or not isinstance(args.custom_pools, list):
                    args.custom_pools = []
                if action == "add":
                    raw_url = normalize_pool_url(data.get("url", ""))
                    name = str(data.get("name", "") or "Custom DNS").strip()
                    region = str(data.get("region", "") or "Custom").strip()
                    if raw_url and not any(c[2].lower() == raw_url.lower() for c in args.custom_pools if len(c) >= 3):
                        args.custom_pools.insert(0, [name, region, raw_url])
                        save_config(args)
                elif action == "remove":
                    rem_url = str(data.get("url", "")).strip().lower()
                    args.custom_pools = [c for c in args.custom_pools if len(c) >= 3 and c[2].lower() != rem_url]
                    save_config(args)
                self._send_json({"ok": True, "custom_pools": args.custom_pools})

            elif parsed.path == "/api/control":
                action = data.get("action", "")
                m = miner_ref()
                if m:
                    if action == "pause":
                        m.pause()
                    elif action == "resume":
                        m.resume()
                    elif action == "restart":
                        m.trigger_restart()
                    elif action == "clear_logs":
                        with stats.lock:
                            stats.events.clear()
                self._send_json({"ok": True, "action": action})
            else:
                self._send_json({"error": "Not found"}, 404)

    server = ThreadingHTTPServer((args.web_host, args.web_port), DashboardHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# --------------------------------------------------------------------------
# Construcao dos paineis do Terminal em tempo real (Bilingue PT/EN)
# --------------------------------------------------------------------------
def panel_header(stats, args):
    theme = get_theme(args)
    state_map = {
        "mining": (tr(args, "st_mining"), "bright_green"),
        "connecting": (tr(args, "st_connecting"), "yellow"),
        "starting": (tr(args, "st_starting"), "yellow"),
        "stopped": (tr(args, "st_stopped"), "red"),
        "error": (tr(args, "st_error"), "red"),
    }
    st_label, color = state_map.get(stats.state, (stats.state, "yellow"))
    web_badge = (
        f" [bold bright_cyan]· 🌐 WEB :{args.web_port}[/]"
        if getattr(args, "web", False)
        else ""
    )
    grid = Table.grid(expand=True)
    grid.add_column(ratio=3)
    grid.add_column(justify="center", ratio=2)
    grid.add_column(justify="right", ratio=3)
    grid.add_row(
        Text.from_markup(
            f"[bold {theme['secondary']}]⛏  CPUMINER LIVE DASHBOARD[/] [dim]· {args.algo.upper()}[/]{web_badge}"
        ),
        Text.from_markup(f"[bold {color}]● {st_label.upper()}[/]"),
        Text.from_markup(
            f"[{theme['primary']}]{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/]  "
            f"[dim]uptime[/] [bold]{fmt_dur(time.time() - stats.start_time)}[/]"
        ),
    )
    return Panel(grid, border_style=theme["header_border"], box=box.ROUNDED, padding=(0, 1))


def panel_hashrate(stats, args, width):
    theme = get_theme(args)
    with stats.lock:
        hist = list(stats.history)
        best = stats.best_hash
    cur = hist[-1] if hist else 0.0
    nz = [h for h in hist if h > 0]
    avg = sum(nz) / len(nz) if nz else 0.0
    avg1 = (sum(hist[-60:]) / len(hist[-60:])) if hist[-60:] else 0.0
    avg5 = (sum(hist[-300:]) / len(hist[-300:])) if hist[-300:] else 0.0
    mn = min(nz) if nz else 0.0

    t = Table.grid(expand=True, padding=(0, 2))
    t.add_column(style=f"bold {theme['primary']}")
    t.add_column(style="white")
    t.add_column(style=f"bold {theme['primary']}")
    t.add_column(style="white")
    t.add_row(tr(args, "hr_cur"), f"[bold {theme['secondary']}]{fmt_hash(cur)}[/]", tr(args, "hr_avg1"), fmt_hash(avg1))
    t.add_row(tr(args, "hr_peak"), f"[yellow]{fmt_hash(best)}[/]", tr(args, "hr_avg5"), fmt_hash(avg5))
    t.add_row(tr(args, "hr_min"), fmt_hash(mn), tr(args, "hr_avg_all"), fmt_hash(avg))

    spark = Text(sparkline(hist, max(10, width)), style=theme["secondary"])
    body = Group(t, Text(""), Text(tr(args, "hr_spark_lbl"), style="dim"), spark)
    return Panel(body, title=f"[bold]{tr(args, 'hr_title')}[/]", border_style=theme["hash_border"], box=box.ROUNDED)


def panel_cores(stats, sysinfo, args, n_cores):
    theme = get_theme(args)
    now = time.time()
    with stats.lock:
        cores = dict(stats.cores)
        reported, last_ts = stats.reported_hash, stats.last_share_ts
    estimated = False
    if (
        not any(now - ts < 120 for _, ts in cores.values())
        and reported and last_ts and now - last_ts < 180
    ):
        estimated = True
        per = reported / max(n_cores, 1)
        cores = {i: (per, now) for i in range(n_cores)}
    count = max(n_cores, (max(cores) + 1) if cores else 0)
    peak = max([hr for hr, _ in cores.values()] + [1.0])

    tb = Table(box=box.SIMPLE_HEAD, expand=True, header_style=f"bold {theme['primary']}", pad_edge=False)
    tb.add_column(tr(args, "core_col_id"), justify="center", style="yellow", no_wrap=True)
    tb.add_column(tr(args, "core_col_hr"), justify="right", style=theme["secondary"], no_wrap=True)
    tb.add_column(tr(args, "core_col_rel"), no_wrap=True)
    tb.add_column(tr(args, "core_col_cpu"), justify="right", no_wrap=True)
    tb.add_column(tr(args, "core_col_freq"), justify="right", no_wrap=True)
    tb.add_column(tr(args, "core_col_st"), justify="center", no_wrap=True)

    for i in range(count):
        hr, ts = cores.get(i, (None, 0))
        alive = hr is not None and now - ts < 120
        rel = (hr / peak * 100) if alive else 0
        usage = sysinfo.cpu_percpu[i] if i < len(sysinfo.cpu_percpu) else None
        freq = sysinfo.freqs[i] if i < len(sysinfo.freqs) else None
        tb.add_row(
            f"#{i}",
            ("~" if estimated else "") + fmt_hash(hr) if alive else "—",
            Text(bar(rel, 14), style=theme["secondary"] if alive else "dim"),
            Text(f"{usage:5.1f}%", style=color_pct(usage)) if usage is not None else "—",
            f"{freq:,.0f} MHz" if freq else "—",
            (f"[yellow]{tr(args, 'core_est')}[/]" if estimated else f"[green]{tr(args, 'core_act')}[/]")
            if alive
            else f"[red]{tr(args, 'core_nodata')}[/]",
        )
    return Panel(
        tb,
        title=f"[bold]{tr(args, 'core_title')}[/]",
        subtitle=f"[dim]{tr(args, 'core_sub_est')}[/]" if estimated else None,
        border_style=theme["cores_border"],
        box=box.ROUNDED,
    )


def panel_pool(stats, args):
    theme = get_theme(args)
    with stats.lock:
        acc, tot = stats.accepted, stats.total_shares
        last_ts, last_ok = stats.last_share_ts, stats.last_share_ok
        times = list(stats.share_times)
        diff, jobs, errors, restarts = stats.difficulty, stats.jobs, stats.errors, stats.restarts
        best_report = stats.reported_hash
        sdiff = stats.share_diff
        reasons = dict(stats.reject_reasons)
        lat = stats.pool_latency
        online = stats.pool_online
        ping_hist = list(stats.ping_history)

    rej = max(0, tot - acc)
    rate = (acc / tot * 100) if tot else 0.0
    elapsed = max(time.time() - stats.start_time, 1)
    spm = len([t for t in times if time.time() - t < 600]) / min(elapsed, 600) * 60
    sph = tot / elapsed * 3600

    if online is None:
        net = Text(tr(args, "pool_testing"), style="yellow")
    elif online:
        net = ping_bar_meter(lat, args, width=10)
    else:
        net = Text(tr(args, "pool_offline"), style="bold red")

    valid_pings = [p for p in ping_hist if p is not None and p > 0]
    ping_stats_str = (
        f"min {min(valid_pings):.0f}ms · avg {sum(valid_pings)/len(valid_pings):.0f}ms · max {max(valid_pings):.0f}ms"
        if valid_pings
        else tr(args, "pool_collecting")
    )

    u = urlparse(args.pool if "://" in args.pool else "tcp://" + args.pool)
    t = Table.grid(expand=True, padding=(0, 1))
    t.add_column(style=f"bold {theme['primary']}", no_wrap=True)
    t.add_column(style="white", overflow="fold")
    t.add_row("Pool", f"{u.hostname}:{u.port}")
    t.add_row(tr(args, "pool_cur_ping"), net)
    t.add_row(tr(args, "pool_ping_graph"), colored_ping_sparkline(ping_hist, args, width=24))
    t.add_row(tr(args, "pool_latency"), f"[dim]{ping_stats_str}[/]")
    t.add_row(tr(args, "algorithm").rstrip(":"), args.algo)
    t.add_row(tr(args, "wallet").rstrip(":"), short_wallet(args.user.split('.')[0]))
    t.add_row("Worker", args.user.split(".", 1)[1] if "." in args.user else "—")
    t.add_row(
        tr(args, "pool_diff"),
        f"pool: {diff:g}" if diff is not None else "—" + (f" · share: {sdiff:g}" if sdiff else ""),
    )
    t.add_row(tr(args, "pool_jobs"), str(jobs))
    t.add_row(tr(args, "pool_acc_rej"), f"[bold green]{acc}[/] / [{'bold red' if rej else 'dim'}]{rej}[/] ({tot} total)")
    if reasons:
        top = sorted(reasons.items(), key=lambda kv: -kv[1])[:2]
        t.add_row(tr(args, "pool_rej_reasons"), ", ".join(f"{k} ×{v}" for k, v in top))
    t.add_row(tr(args, "pool_acc_rate"), Text(f"{rate:.2f}%", style=color_pct(100 - rate, 5, 15)) if tot else "—")
    t.add_row(tr(args, "pool_rate_sh"), f"{spm:.2f}/min · {sph:.1f}/h")
    t.add_row(
        tr(args, "pool_last_sh"),
        (f"[green]{tr(args, 'pool_acc_word')}[/] " if last_ok else f"[red]{tr(args, 'pool_rej_word')}[/] ")
        + fmt_ago(last_ts, args)
        if last_ts
        else "—",
    )
    t.add_row(tr(args, "pool_rep_hr"), fmt_hash(best_report))
    t.add_row(tr(args, "pool_err_rest"), f"[{'red' if errors else 'green'}]{errors}[/] / {restarts}")
    return Panel(t, title=f"[bold]{tr(args, 'pool_title')}[/]", border_style=theme["pool_border"], box=box.ROUNDED)


def panel_system(stats, sysinfo, args):
    theme = get_theme(args)
    t = Table.grid(expand=True, padding=(0, 1))
    t.add_column(style=f"bold {theme['primary']}", no_wrap=True)
    t.add_column(style="white", overflow="fold")

    if not psutil:
        t.add_row("psutil", f"[yellow]{tr(args, 'sys_no_psutil')}[/]")
        return Panel(t, title=f"[bold]{tr(args, 'sys_title')}[/]", border_style=theme["sys_border"], box=box.ROUNDED)

    cpu = sysinfo.cpu_total
    t.add_row(tr(args, "sys_cpu_tot"), Text.from_markup(f"[{color_pct(cpu)}]{bar(cpu)} {cpu:5.1f}%[/]"))
    try:
        l1, l5, l15 = os.getloadavg()
        t.add_row("Load (1/5/15)", f"{l1:.2f} / {l5:.2f} / {l15:.2f}")
    except Exception:
        pass
    try:
        vm = psutil.virtual_memory()
        t.add_row(
            "RAM",
            Text.from_markup(
                f"[{color_pct(vm.percent)}]{bar(vm.percent)} {vm.percent:4.1f}%[/] "
                f"[dim]{fmt_bytes(vm.used)}/{fmt_bytes(vm.total)}[/]"
            ),
        )
        sw = psutil.swap_memory()
        if sw.total:
            t.add_row("Swap", f"{sw.percent:.1f}% [dim]({fmt_bytes(sw.used)}/{fmt_bytes(sw.total)})[/]")
    except Exception:
        pass
    temp = sysinfo.temperature()
    if temp is not None:
        c = "green" if temp < 60 else "yellow" if temp < 75 else "red"
        t.add_row(tr(args, "sys_temp"), f"[{c}]{temp:.1f} °C[/]")
    try:
        bat = psutil.sensors_battery()
        if bat:
            c = "green" if bat.percent > 40 else "yellow" if bat.percent > 20 else "red"
            plug = tr(args, "sys_charging") if bat.power_plugged else tr(args, "sys_discharging")
            t.add_row(tr(args, "sys_bat"), f"[{c}]{bat.percent:.0f}%[/] [dim]({plug})[/]")
    except Exception:
        pass
    d, u = sysinfo.net_rate
    t.add_row(tr(args, "sys_net"), f"[cyan]↓ {fmt_bytes(d)}/s[/]  [magenta]↑ {fmt_bytes(u)}/s[/]")
    if sysinfo.proc:
        try:
            with sysinfo.proc.oneshot():
                pc = sysinfo.proc.cpu_percent(None)
                mem = sysinfo.proc.memory_info().rss
                th = sysinfo.proc.num_threads()
            t.add_row("cpuminer", f"CPU {pc:.0f}% · RAM {fmt_bytes(mem)} · {th} threads")
            t.add_row("PID", str(sysinfo.proc_pid))
        except Exception:
            t.add_row("cpuminer", f"[red]{tr(args, 'sys_proc_na')}[/]")
    return Panel(t, title=f"[bold]{tr(args, 'sys_title')}[/]", border_style=theme["sys_border"], box=box.ROUNDED)


BLOCK_W = 16
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
PULSE_FRAMES = ["◉", "◎", "●", "◈", "◆", "❖"]
WAVE_CHARS = ["·", "∙", "•", "∙"]


def panel_blocks(stats, args):
    theme = get_theme(args)
    now = time.time()
    width = max(40, console.size.width - 4)
    n_vis = max(2, width // (BLOCK_W + 4))
    with stats.lock:
        done = list(stats.blocks)[-(n_vis - 1):]
        total, last_ts = stats.total_shares, stats.last_share_ts
    elapsed = max(now - stats.start_time, 1)
    avg = elapsed / total if total else 10.0
    since = now - (last_ts or stats.start_time)
    prog = min(0.99, since / max(avg, 0.5))
    inner = BLOCK_W - 4

    def box_rows(style, title, l2, l3):
        return [
            (style, "┌" + "─" * (BLOCK_W - 2) + "┐"),
            (style, f"│ {title:<{inner}} │"),
            (style, f"│ {l2:<{inner}} │"),
            (style, f"│ {l3:<{inner}} │"),
            (style, "└" + "─" * (BLOCK_W - 2) + "┘"),
        ]

    chain = []
    for num, ok, digest, ts in done:
        fresh = now - ts < 2.0
        if ok:
            style = "bold bright_green" if fresh else "green"
            l3 = tr(args, "blk_new") if fresh else datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            chain.append(box_rows(style, f"#{num} ✓", digest, l3))
        else:
            style = "bold bright_red" if fresh else "red"
            chain.append(box_rows(style, f"#{num} ✗", digest, tr(args, "blk_rej")))

    spin = SPINNER[int(now * 10) % len(SPINNER)]
    scramble = "".join(random.choices("0123456789abcdef", k=inner))
    chain.append(box_rows("bold yellow", f"{spin} #{total + 1}", scramble, bar(prog * 100, inner)))

    lines = []
    for r in range(5):
        t = Text(no_wrap=True, overflow="crop")
        for i, rows in enumerate(chain):
            if i:
                t.append("══» " if r == 2 else "    ", style=theme["primary"])
            style, s = rows[r]
            t.append(s, style=style)
        lines.append(t)

    info_txt = tr(args, "blk_info").format(prog=prog * 100, avg=avg)
    info = Text.from_markup(f"[dim]{info_txt}[/]")
    return Panel(
        Group(*lines, info),
        title=f"[bold]{tr(args, 'blk_title')}[/]",
        border_style=theme["blocks_border"],
        box=box.ROUNDED,
    )


GRID_ROWS = 4


def panel_grid(stats, args):
    theme = get_theme(args)
    now = time.time()
    frame = int(now * 8)
    width = max(20, console.size.width - 4)
    cols = max(10, width // 2)
    cap = cols * GRID_ROWS
    with stats.lock:
        log = list(stats.share_log)[-(cap - 1):]
        acc, tot = stats.accepted, stats.total_shares
        last_ts = stats.last_share_ts
    rej = max(0, tot - acc)
    rate = (acc / tot * 100) if tot else 0.0

    cells = []
    for idx_s, (ok, ts) in enumerate(log):
        age = now - ts
        if ok:
            if age < 0.8:
                sym = "★ " if frame % 2 == 0 else "✦ "
                st = "bold bright_white on green"
            elif age < 2.5:
                sym = "◆ " if (frame + idx_s) % 2 == 0 else "■ "
                st = "bold bright_green"
            else:
                wave_hit = ((idx_s + frame) % 19) == 0
                sym = "▣ " if wave_hit else "■ "
                st = "bright_green" if wave_hit else "green"
        else:
            if age < 2.0:
                sym = "✖ " if frame % 2 == 0 else "■ "
                st = "bold bright_red"
            else:
                sym = "■ "
                st = "red"
        cells.append((sym, st))

    active_sym = PULSE_FRAMES[frame % len(PULSE_FRAMES)] + " "
    active_style = "bold bright_yellow" if frame % 2 == 0 else f"bold {theme['primary']}"
    cells.append((active_sym, active_style))

    scanner_pos = len(cells) + (frame % max(1, min(24, cap - len(cells) + 1)))

    lines = []
    for r in range(GRID_ROWS):
        t = Text(no_wrap=True, overflow="crop")
        for c in range(cols):
            i = r * cols + c
            if i < len(cells):
                sym, st = cells[i]
                t.append(sym, style=st)
            elif i == scanner_pos:
                t.append("▸ ", style=f"bold {theme['primary']}")
            else:
                wch = WAVE_CHARS[(i + frame // 2) % len(WAVE_CHARS)]
                t.append(f"{wch} ", style="grey35" if (i + frame) % 11 == 0 else "grey23")
        lines.append(t)

    spin = SPINNER[frame % len(SPINNER)]
    since_last = f"{now - last_ts:.1f}s" if last_ts else tr(args, "grid_waiting")
    legend = Text.from_markup(
        tr(args, "grid_legend").format(
            acc=acc,
            rej=rej,
            pulse=PULSE_FRAMES[frame % len(PULSE_FRAMES)],
            spin=spin,
            since=since_last,
            shown=len(log),
            tot=tot,
            rate=rate,
        )
    )
    return Panel(
        Group(*lines, legend),
        title=f"[bold]{tr(args, 'grid_title')} {spin}[/]",
        border_style="bright_green" if (last_ts and now - last_ts < 1.5) else theme["grid_border"],
        box=box.ROUNDED,
    )


def panel_log(stats, args, lines):
    theme = get_theme(args)
    with stats.lock:
        ev = list(stats.events)[-lines:]
    out = Group(*[
        Text.assemble((f"{ts} ", "dim"), (txt, style), no_wrap=True, overflow="ellipsis")
        for ts, txt, style in ev
    ]) if ev else Text(tr(args, "log_waiting"), style="dim")
    return Panel(out, title=f"[bold]{tr(args, 'log_title')}[/]", border_style=theme["log_border"], box=box.ROUNDED)


def build_layout():
    root = Layout()
    root.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="grid", size=GRID_ROWS + 3),
        Layout(name="blocks", size=9),
        Layout(name="log", size=9),
        Layout(name="footer", size=1),
    )
    root["main"].split_row(Layout(name="left", ratio=3), Layout(name="right", ratio=2))
    root["left"].split_column(Layout(name="hash", size=11), Layout(name="cores", ratio=1))
    root["right"].split_column(Layout(name="pool", ratio=3), Layout(name="sys", ratio=2))
    return root


def update_layout(root, stats, sysinfo, args, n_cores):
    width = max(20, console.size.width * 3 // 5 - 8)
    root["header"].update(panel_header(stats, args))
    root["hash"].update(panel_hashrate(stats, args, width))
    root["cores"].update(panel_cores(stats, sysinfo, args, n_cores))
    root["pool"].update(panel_pool(stats, args))
    root["sys"].update(panel_system(stats, sysinfo, args))
    h = console.size.height
    root["log"].visible = h >= 36
    root["blocks"].visible = h >= 30
    root["grid"].update(panel_grid(stats, args))
    root["blocks"].update(panel_blocks(stats, args))
    root["log"].update(panel_log(stats, args, 7))
    web_str = f"http://{args.web_host}:{args.web_port}" if getattr(args, "web", False) else "OFF"
    footer_txt = tr(args, "footer_live").format(
        web=web_str,
        theme=get_theme(args)["label"],
        btc=DONATE_BTC,
        dgb=DONATE_DGB,
    )
    root["footer"].update(Text.from_markup(f" [dim]{footer_txt}[/]"))


# --------------------------------------------------------------------------
# Main & CLI Arguments (Com suporte completo a --web, --web-host, --web-port, --web-token)
# --------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Universal Live Dashboard for cpuminer (Terminal TUI + Web Dashboard)")
    p.add_argument("--bin", default=DEFAULT_BIN, help="path to cpuminer binary")
    p.add_argument("-a", "--algo", default=DEFAULT_ALGO, help="mining algorithm (e.g. sha256d, scrypt, yescrypt)")
    p.add_argument("-o", "--pool", default=DEFAULT_POOL, help="Stratum pool URL")
    p.add_argument("-u", "--user", default=DEFAULT_USER, help="wallet.worker or username")
    p.add_argument("-p", "--password", default=DEFAULT_PASS, help="pool password")
    p.add_argument("-t", "--threads", type=int, default=0, help="CPU threads (0 = cpuminer default)")
    p.add_argument("--theme", default=DEFAULT_THEME, choices=THEME_KEYS, help="dashboard visual theme")
    p.add_argument("--lang", default=DEFAULT_LANG, choices=LANG_KEYS, help="interface language: pt or en")
    p.add_argument("--web", action="store_true", help="enable embedded Web Dashboard server")
    p.add_argument("--web-host", default=DEFAULT_WEB_HOST, help="Web Dashboard bind address (default: 0.0.0.0)")
    p.add_argument("--web-port", type=int, default=DEFAULT_WEB_PORT, help="Web Dashboard port (default: 8080)")
    p.add_argument("--web-token", default="", help="optional authentication token for Web Dashboard")
    p.add_argument("--no-restart", action="store_true", help="do not auto-restart cpuminer if it exits")
    p.add_argument("--auto-start", action="store_true", help="skip start menu and begin mining immediately")
    p.add_argument("--extra", nargs=argparse.REMAINDER, default=[], help="extra arguments passed to cpuminer")
    return p.parse_args()


def main():
    cli_argv = sys.argv[1:]
    args = parse_args()
    load_saved_config(args, cli_argv)

    passed_web_cli = any(flag in cli_argv for flag in ("--web", "--web-host", "--web-port", "--web-token"))
    if passed_web_cli:
        args.web = True

    stats = Stats()
    try:
        stats.logfile = open(LOG_FILE, "a", encoding="utf-8")
    except Exception:
        stats.logfile = None

    miner = Miner(args, stats)
    stop_evt = threading.Event()
    sysinfo = SysInfo(lambda: stats.pid)
    n_cores_getter = lambda: (args.threads if args.threads > 0 else (os.cpu_count() or 1))

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    web_srv = None
    if getattr(args, "web", False):
        try:
            web_srv = start_web_server(args, stats, sysinfo, lambda: miner, n_cores_getter)
            tok_info = f"?token={args.web_token}" if args.web_token else ""
            stats.event(f"Web Dashboard online: http://{args.web_host}:{args.web_port}/{tok_info}", "cyan")
        except Exception as e:
            stats.event(f"Falha ao iniciar servidor Web na porta {args.web_port}: {e}", "red")

    threading.Thread(target=pool_probe, args=(stats, args, stop_evt), daemon=True).start()

    first_cycle = True
    try:
        while True:
            # Sempre exibe o Menu Principal no terminal (exceto no 1º ciclo se --auto-start for usado)
            if not (first_cycle and args.auto_start):
                try:
                    show_start_menu(args)
                except KeyboardInterrupt:
                    console.print(f"\n[yellow]{tr(args, 'cancelled_msg')}[/yellow]")
                    break
            first_cycle = False

            # Caso o usuario tenha ativado o servidor Web dentro do menu de configuracoes
            if getattr(args, "web", False) and web_srv is None:
                try:
                    web_srv = start_web_server(args, stats, sysinfo, lambda: miner, n_cores_getter)
                    tok_info = f"?token={args.web_token}" if args.web_token else ""
                    stats.event(f"Web Dashboard online: http://{args.web_host}:{args.web_port}/{tok_info}", "cyan")
                except Exception as e:
                    stats.event(f"Falha ao iniciar servidor Web na porta {args.web_port}: {e}", "red")

            binary = args.bin
            if not os.path.exists(binary):
                found = shutil.which(os.path.basename(binary))
                if found:
                    args.bin = found
                elif not getattr(args, "web", False):
                    console.print(f"[red]{tr(args, 'bin_not_found')} {args.bin}[/red]")
                    time.sleep(2)
                    continue
                else:
                    stats.event(f"{tr(args, 'bin_not_found')} {args.bin}", "red")

            console.print(f"[yellow]{tr(args, 'starting_bg')}[/yellow]")
            stats.fatal = None
            miner.resume()

            layout = build_layout()
            return_to_menu = False
            posix_old_tty = None
            if os.name != "nt":
                try:
                    import termios
                    import tty
                    if sys.stdin.isatty():
                        fd = sys.stdin.fileno()
                        posix_old_tty = termios.tcgetattr(fd)
                        tty.setcbreak(fd)
                except Exception:
                    posix_old_tty = None

            try:
                with Live(layout, console=console, screen=True, refresh_per_second=8):
                    tick = 0
                    while True:
                        if stats.fatal and args.no_restart:
                            break
                        k_live = poll_key_nonblocking()
                        if k_live == "q":
                            return_to_menu = True
                            break
                        if tick % 5 == 0:
                            stats.sample()
                            sysinfo.update()
                        update_layout(layout, stats, sysinfo, args, n_cores_getter())
                        tick += 1
                        time.sleep(0.2)
            finally:
                if posix_old_tty is not None:
                    try:
                        import termios
                        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, posix_old_tty)
                    except Exception:
                        pass

            if return_to_menu:
                miner.pause()
                continue
            break
    except KeyboardInterrupt:
        pass
    finally:
        console.print(f"\n[red]{tr(args, 'stopping_miner')}[/red]")
        stop_evt.set()
        miner.stop()
        if web_srv:
            try:
                web_srv.shutdown()
            except Exception:
                pass
        if stats.logfile:
            stats.logfile.close()
        with stats.lock:
            acc, tot, best = stats.accepted, stats.total_shares, stats.best_hash
        console.print(
            Panel(
                f"{tr(args, 'sum_uptime')} [bold]{fmt_dur(time.time() - stats.start_time)}[/]\n"
                f"{tr(args, 'sum_shares')} [green]{acc}[/] {tr(args, 'sum_acc_of')} {tot} {tr(args, 'sum_sent')}\n"
                f"{tr(args, 'sum_peak')} [yellow]{fmt_hash(best)}[/]\n\n"
                f"[bold yellow]{tr(args, 'sum_support')}[/]\n"
                f"BTC: [white]{DONATE_BTC}[/]\n"
                f"DGB: [white]{DONATE_DGB}[/]",
                title=tr(args, "sum_title"),
                subtitle=f"[dim]{tr(args, 'dev_by')}[/]",
                border_style="green",
            )
        )
        if stats.fatal:
            console.print(f"[red]{stats.fatal}[/red]")
        console.print(f"[green]{tr(args, 'miner_safe_exit')}[/green]")


if __name__ == "__main__":
    main()
