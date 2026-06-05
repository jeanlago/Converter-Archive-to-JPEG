#!/usr/bin/env python3
"""Converte arquivos de imagem (com ou sem extensão) para JPEG."""

from __future__ import annotations

import hashlib
import os
import re
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, UnidentifiedImageError

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic", ".heif"}
EXTENSOES_JPEG = {".jpg", ".jpeg"}
CREDITOS = "Jean, irmã de Thalyta Marins backoffice"
EMAIL_CONTATO = "jeanlago203@gmail.com"
TEXTO_CREDITOS = f"Feito por {CREDITOS}"
TEXTO_CONTATO = f"Contato: {EMAIL_CONTATO}"

COR_FUNDO = "#eef2ff"
COR_CARTAO = "#ffffff"
COR_BORDA = "#c7d2fe"
COR_DESTAQUE = "#4f46e5"
COR_DESTAQUE_ESCURO = "#4338ca"
COR_CABECALHO = "#312e81"
COR_CABECALHO_CLARO = "#4338ca"
COR_TEXTO = "#1e1b4b"
COR_TEXTO_SUAVE = "#64748b"
COR_RODAPE = "#e0e7ff"
COR_SUCESSO = "#059669"
COR_ERRO = "#dc2626"
COR_AVISO = "#d97706"
ARQUIVOS_IGNORADOS = {
    "converter_para_jpeg.py",
    "converter_para_jpeg.bat",
    "instalar.bat",
    "requirements.txt",
    "LEIA-ME.txt",
}

INSTRUCOES = """Como usar:

1. Baixe os arquivos do sistema (geralmente vêm só como "arquivo", sem extensão).
2. Escolha uma opção:
   - Pasta inteira: converte só arquivos "arquivo" ou sem extensão.
   - Arquivos escolhidos: selecione um ou vários arquivos (Ctrl+clique).
3. Clique em "Converter arquivos".
4. Clique em "Abrir pasta convertidos" para ver os JPEGs prontos.

Proteções:
- Na pasta, arquivos comuns (PDF, ZIP, fotos .png etc.) são ignorados.
- Se a imagem já foi convertida antes, ela não é convertida de novo.

Os JPEGs ficam na subpasta "convertidos", dentro da pasta escolhida."""

PADRAO_NOME_BAIXADO = re.compile(r"^arquivo(\s*\(\d+\))?$", re.IGNORECASE)


def explicar_erro_conversao(caminho: Path, erro: Exception | str) -> str:
    texto = str(erro).lower()

    if isinstance(erro, UnidentifiedImageError) or "cannot identify image" in texto:
        return (
            "Motivo: o conteúdo deste arquivo não é uma imagem válida. "
            "Ele pode ter sido corrompido no download, estar incompleto ou não ser uma foto."
        )
    if isinstance(erro, PermissionError) or "permission denied" in texto or "acesso negado" in texto:
        return (
            "Motivo: o Windows bloqueou a leitura ou gravação deste arquivo. "
            "Feche programas que possam estar usando o arquivo e tente novamente."
        )
    if "no space left" in texto or "disk full" in texto or "espaco insuficiente" in texto:
        return (
            "Motivo: não há espaço livre suficiente no disco. "
            "Apague arquivos desnecessários e tente novamente."
        )
    if isinstance(erro, FileNotFoundError) or "no such file" in texto:
        return (
            "Motivo: o arquivo não foi encontrado. "
            "Ele pode ter sido movido, renomeado ou excluído antes da conversão."
        )
    if "truncated" in texto or "broken" in texto:
        return (
            "Motivo: a imagem parece estar incompleta ou danificada. "
            "Tente baixar o arquivo novamente no sistema."
        )

    return (
        f"Motivo: não foi possível converter este arquivo. "
        f"Detalhe técnico: {erro}"
    )


def explicar_ja_convertido(caminho: Path, destino: Path) -> str:
    return (
        f"Motivo: este arquivo já foi convertido antes. "
        f"O JPEG correspondente já existe em convertidos ({destino.name}). "
        "Nada foi alterado para evitar duplicar a mesma imagem."
    )


def mensagem_pasta_nao_encontrada(pasta: Path) -> list[str]:
    return [
        "Erro: pasta não encontrada.",
        "",
        f"Caminho informado: {pasta}",
        "",
        "O que fazer:",
        "- Clique em \"Escolher pasta\" e selecione novamente a pasta correta.",
        "- Verifique se a pasta não foi movida ou excluída.",
    ]


def mensagem_pasta_sem_elegiveis(pasta: Path) -> list[str]:
    ja_jpeg = 0
    nome_invalido = 0
    nao_imagem = 0
    ignorados = 0
    exemplos_nome: list[str] = []
    exemplos_nao_imagem: list[str] = []

    for caminho in sorted(pasta.iterdir()):
        if not caminho.is_file():
            continue
        if caminho.name in ARQUIVOS_IGNORADOS or caminho.parent.name == "convertidos":
            ignorados += 1
            continue
        if caminho.suffix.lower() in EXTENSOES_JPEG:
            ja_jpeg += 1
            continue
        if not parece_arquivo_baixado(caminho):
            nome_invalido += 1
            if len(exemplos_nome) < 3:
                exemplos_nome.append(caminho.name)
            continue
        if not eh_imagem_valida(caminho):
            nao_imagem += 1
            if len(exemplos_nao_imagem) < 3:
                exemplos_nao_imagem.append(caminho.name)
            continue

    mensagens = [
        "Nenhum arquivo elegível foi encontrado nesta pasta.",
        "",
        "Na opção \"Pasta inteira\", só convertemos arquivos:",
        '- sem extensão (ex.: "arquivo")',
        '- ou com nome "arquivo", "arquivo (1)" etc.',
        "",
        "Resumo do que foi encontrado:",
    ]

    if nome_invalido:
        mensagens.append(
            f"- {nome_invalido} arquivo(s) ignorado(s) por nome ou extensão "
            f"(ex.: {', '.join(exemplos_nome)})"
        )
        mensagens.append(
            "  Esses arquivos não parecem ser downloads do sistema no formato esperado."
        )
    if ja_jpeg:
        mensagens.append(
            f"- {ja_jpeg} arquivo(s) já estão em JPEG e não precisam ser convertidos."
        )
    if nao_imagem:
        mensagens.append(
            f"- {nao_imagem} arquivo(s) sem extensão/nome válido, mas com conteúdo que "
            f"não é imagem (ex.: {', '.join(exemplos_nao_imagem)})"
        )
        mensagens.append(
            "  Isso pode indicar download incompleto ou arquivo corrompido."
        )
    if ignorados:
        mensagens.append(
            f"- {ignorados} item(ns) ignorado(s) por serem arquivos do próprio conversor "
            "ou da pasta convertidos."
        )
    if not any([nome_invalido, ja_jpeg, nao_imagem, ignorados]):
        mensagens.append("- A pasta está vazia ou não contém arquivos comuns de download.")

    mensagens.extend([
        "",
        "O que fazer:",
        "- Confirme se os arquivos baixados realmente estão nesta pasta.",
        "- Se forem outros tipos de arquivo, use \"Arquivos escolhidos\".",
        "- Se o download veio corrompido, baixe novamente no sistema.",
    ])
    return mensagens


def mensagem_selecao_sem_validos(caminhos: list[Path]) -> list[str]:
    motivos: list[str] = []

    for caminho in caminhos:
        if not caminho.is_file():
            motivos.append(
                f"- {caminho.name}: não é um arquivo válido ou não foi encontrado."
            )
            continue
        if caminho.name in ARQUIVOS_IGNORADOS:
            motivos.append(
                f"- {caminho.name}: é um arquivo interno do conversor e foi ignorado."
            )
            continue
        if caminho.suffix.lower() in EXTENSOES_JPEG:
            motivos.append(
                f"- {caminho.name}: já é JPEG. Não é necessário converter novamente."
            )
            continue
        if caminho.suffix and caminho.suffix.lower() not in EXTENSOES_IMAGEM:
            motivos.append(
                f"- {caminho.name}: extensão \"{caminho.suffix}\" não é de imagem suportada."
            )
            continue
        motivos.append(
            f"- {caminho.name}: não pôde ser aceito para conversão."
        )

    mensagens = [
        "Nenhum dos arquivos selecionados pôde ser convertido.",
        "",
        "Motivo de cada arquivo:",
        *motivos,
        "",
        "O que fazer:",
        "- Selecione arquivos baixados do sistema ou imagens (.png, .webp etc.).",
        "- Arquivos que já são .jpeg não precisam ser convertidos.",
        "- Se o arquivo veio sem extensão, tente baixá-lo novamente.",
    ]
    return mensagens


def resumo_final_vazio(mensagens: list[str]) -> str:
    return (
        "Nenhum arquivo novo foi convertido.\n\n"
        "Veja o campo \"Resultado\" abaixo para entender o motivo de cada item."
    )


def hash_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(65536), b""):
            digest.update(bloco)
    return digest.hexdigest()[:12]


def eh_imagem_valida(caminho: Path) -> bool:
    try:
        with Image.open(caminho) as imagem:
            imagem.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def parece_arquivo_baixado(caminho: Path) -> bool:
    if caminho.suffix == "":
        return True
    return bool(PADRAO_NOME_BAIXADO.match(caminho.stem))


def nome_base_saida(caminho: Path) -> str:
    if parece_arquivo_baixado(caminho):
        return f"arquivo_{hash_arquivo(caminho)}"
    return caminho.stem


def nome_saida(caminho: Path) -> Path:
    pasta_saida = caminho.parent / "convertidos"
    pasta_saida.mkdir(exist_ok=True)
    return pasta_saida / f"{nome_base_saida(caminho)}.jpeg"


def deve_ignorar(caminho: Path) -> bool:
    if not caminho.is_file():
        return True
    if caminho.name in ARQUIVOS_IGNORADOS:
        return True
    if caminho.parent.name == "convertidos":
        return True
    return False


def deve_processar_pasta(caminho: Path) -> bool:
    if deve_ignorar(caminho):
        return False
    if caminho.suffix.lower() in EXTENSOES_JPEG:
        return False
    if not parece_arquivo_baixado(caminho):
        return False
    return eh_imagem_valida(caminho)


def deve_processar_selecionado(caminho: Path) -> bool:
    if deve_ignorar(caminho):
        return False
    if caminho.suffix.lower() in EXTENSOES_JPEG:
        return False
    return caminho.suffix.lower() in EXTENSOES_IMAGEM or caminho.suffix == ""


def converter_arquivo(caminho: Path) -> tuple[Path | None, str | None, bool]:
    destino = nome_saida(caminho)
    if destino.exists():
        return destino, None, True

    try:
        with Image.open(caminho) as imagem:
            if imagem.mode in ("RGBA", "LA", "P"):
                imagem = imagem.convert("RGB")
            elif imagem.mode != "RGB":
                imagem = imagem.convert("RGB")

            imagem.save(destino, format="JPEG", quality=92, optimize=True)
            return destino, None, False
    except (UnidentifiedImageError, OSError, PermissionError, ValueError) as erro:
        return None, explicar_erro_conversao(caminho, erro), False


def converter_pasta(
    pasta: Path,
    ao_linha: Callable[[str], None] | None = None,
) -> tuple[int, list[str], Path | None]:
    def emitir(linha: str) -> None:
        mensagens.append(linha)
        if ao_linha:
            ao_linha(linha)

    mensagens: list[str] = []
    if not pasta.is_dir():
        emitir("Erro: pasta não encontrada.")
        for linha in mensagem_pasta_nao_encontrada(pasta)[1:]:
            emitir(linha)
        return 0, mensagens, None

    arquivos = sorted(p for p in pasta.iterdir() if deve_processar_pasta(p))
    if not arquivos:
        for linha in mensagem_pasta_sem_elegiveis(pasta):
            emitir(linha)
        return 0, mensagens, None

    emitir(f"Convertendo {len(arquivos)} arquivo(s) elegível(is)...")
    emitir("")
    convertidos = 0
    ignorados = 0
    erros = 0
    pasta_saida = pasta / "convertidos"

    for indice, caminho in enumerate(arquivos, start=1):
        if ao_linha:
            ao_linha(f"⏳ Processando {indice}/{len(arquivos)}: {caminho.name}")

        destino, erro, ja_existia = converter_arquivo(caminho)
        if ja_existia and destino:
            ignorados += 1
            emitir(f"[==] {caminho.name}")
            emitir(f"    {explicar_ja_convertido(caminho, destino)}")
        elif destino:
            convertidos += 1
            emitir(f"[OK] {caminho.name}  ->  {destino.name}")
        else:
            erros += 1
            emitir(f"[ERRO] {caminho.name}")
            emitir(f"    {erro}")

    emitir("")
    emitir(f"Resumo: {convertidos} convertido(s), {ignorados} já existente(s), {erros} com erro.")
    emitir(f"Salvos em:")
    emitir(str(pasta_saida))
    return convertidos + ignorados, mensagens, pasta_saida if convertidos or ignorados else None


def converter_lista(
    caminhos: list[Path],
    ao_linha: Callable[[str], None] | None = None,
) -> tuple[int, list[str], Path | None]:
    def emitir(linha: str) -> None:
        mensagens.append(linha)
        if ao_linha:
            ao_linha(linha)

    mensagens: list[str] = []
    arquivos = sorted({p.resolve() for p in caminhos if deve_processar_selecionado(p)})
    if not arquivos:
        for linha in mensagem_selecao_sem_validos(caminhos):
            emitir(linha)
        return 0, mensagens, None

    emitir(f"Convertendo {len(arquivos)} arquivo(s) selecionado(s)...")
    emitir("")
    convertidos = 0
    ignorados = 0
    erros = 0
    pastas_saida: set[Path] = set()

    for indice, caminho in enumerate(arquivos, start=1):
        if ao_linha:
            ao_linha(f"⏳ Processando {indice}/{len(arquivos)}: {caminho.name}")

        destino, erro, ja_existia = converter_arquivo(caminho)
        if ja_existia and destino:
            ignorados += 1
            pastas_saida.add(destino.parent)
            emitir(f"[==] {caminho.name}")
            emitir(f"    {explicar_ja_convertido(caminho, destino)}")
        elif destino:
            convertidos += 1
            pastas_saida.add(destino.parent)
            emitir(f"[OK] {caminho.name}  ->  {destino.name}")
        else:
            erros += 1
            emitir(f"[ERRO] {caminho.name}")
            emitir(f"    {erro}")

    if convertidos == 0 and ignorados == 0:
        emitir("")
        emitir("Nenhum arquivo foi convertido porque todos falharam ou foram rejeitados.")
        return 0, mensagens, None

    emitir("")
    emitir(f"Resumo: {convertidos} convertido(s), {ignorados} já existente(s), {erros} com erro.")
    if len(pastas_saida) == 1:
        pasta_saida = pastas_saida.pop()
        emitir("Salvos em:")
        emitir(str(pasta_saida))
    else:
        pasta_saida = next(iter(pastas_saida))
        emitir("Pastas convertidos:")
        for pasta in sorted(pastas_saida):
            emitir(f"- {pasta}")

    return convertidos + ignorados, mensagens, pasta_saida


class ConversorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Conversor para JPEG")
        self.minsize(540, 440)

        self.pasta_var = tk.StringVar(value="")
        self.modo_var = tk.StringVar(value="pasta")
        self.arquivos_selecionados: list[Path] = []
        self.ultima_pasta_saida: Path | None = None
        self.instrucoes_abertas = True

        self._configurar_tema()
        self._montar_interface()
        self._centralizar_janela()
        self.bind("<Return>", lambda _e: self.iniciar_conversao())

    def _configurar_tema(self) -> None:
        self.configure(bg=COR_FUNDO)
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(
            "Card.TButton",
            font=("Segoe UI", 10),
            padding=(12, 7),
            background=COR_CARTAO,
            foreground=COR_TEXTO,
            borderwidth=1,
        )
        estilo.map(
            "Card.TButton",
            background=[("active", COR_FUNDO), ("disabled", "#f1f5f9")],
            foreground=[("disabled", "#94a3b8")],
        )
        estilo.configure(
            "Card.TRadiobutton",
            font=("Segoe UI", 10),
            background=COR_CARTAO,
            foreground=COR_TEXTO,
        )
        estilo.map(
            "Card.TRadiobutton",
            background=[("active", COR_CARTAO), ("selected", COR_CARTAO)],
        )
        estilo.configure("Vertical.TScrollbar", background=COR_BORDA, troughcolor=COR_FUNDO)
        estilo.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor="#e0e7ff",
            background=COR_DESTAQUE,
            thickness=8,
        )

    def _centralizar_janela(self) -> None:
        self.update_idletasks()
        largura = 720
        altura = 720
        pos_x = max(0, (self.winfo_screenwidth() - largura) // 2)
        pos_y = max(0, (self.winfo_screenheight() - altura) // 2)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

    def _atualizar_status(self, texto: str, cor: str = COR_TEXTO_SUAVE) -> None:
        self.status_var.set(texto)
        self.status_dot.configure(fg=cor)

    def _atualizar_badge(self) -> None:
        if self.modo_var.get() == "arquivos" and self.arquivos_selecionados:
            total = len(self.arquivos_selecionados)
            texto = f"  {total} arquivo(s) selecionado(s)  "
            self.badge_selecao.configure(text=texto)
            self.badge_selecao.pack(anchor="w", pady=(0, 10))
            self._atualizar_status(f"{total} arquivo(s) prontos para converter", COR_DESTAQUE)
            return

        if self.modo_var.get() == "pasta":
            pasta = self.pasta_var.get().strip()
            if pasta and not pasta.startswith("(") and Path(pasta).is_dir():
                self.badge_selecao.configure(text="  Pasta selecionada  ")
                self.badge_selecao.pack(anchor="w", pady=(0, 10))
                self._atualizar_status("Pasta selecionada. Clique em converter.", COR_DESTAQUE)
                return

        self.badge_selecao.pack_forget()
        self._atualizar_status("Pronto para converter")

    def _alternar_instrucoes(self) -> None:
        if self.instrucoes_abertas:
            self.frame_instrucoes_conteudo.pack_forget()
            self.btn_toggle_instrucoes.configure(text="▶  Mostrar instruções")
            self.instrucoes_abertas = False
        else:
            self.frame_instrucoes_conteudo.pack(fill="x")
            self.btn_toggle_instrucoes.configure(text="▼  Ocultar instruções")
            self.instrucoes_abertas = True

    def _iniciar_progresso(self) -> None:
        self.progress.pack(fill="x", pady=(12, 0))
        self.progress.start(10)
        self._atualizar_status("Convertendo arquivos...", COR_DESTAQUE)

    def _parar_progresso(self) -> None:
        self.progress.stop()
        self.progress.pack_forget()

    def _set_busy(self, ocupado: bool) -> None:
        if ocupado:
            self.btn_converter.configure(state="disabled", bg="#a5b4fc")
            self.btn_abrir.configure(state="disabled")
            self.btn_pasta.configure(state="disabled")
            self.btn_arquivos.configure(state="disabled")
            return

        self.btn_converter.configure(state="normal", bg=COR_DESTAQUE)
        self.btn_pasta.configure(state="normal" if self.modo_var.get() == "pasta" else "disabled")
        self.btn_arquivos.configure(state="normal" if self.modo_var.get() == "arquivos" else "disabled")

    def _limpar_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _append_log_linha(self, linha: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", linha + "\n", self._tag_log_linha(linha))
        self.log.see("end")
        self.log.configure(state="disabled")

    def _criar_secao(self, parent: tk.Misc, titulo: str, emoji: str = "") -> tk.Frame:
        bloco = tk.Frame(parent, bg=COR_FUNDO)
        bloco.pack(fill="x", pady=(0, 14))

        rotulo = f"{emoji}  {titulo}" if emoji else titulo
        tk.Label(
            bloco,
            text=rotulo,
            font=("Segoe UI", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_DESTAQUE,
        ).pack(anchor="w", pady=(0, 6))

        cartao = tk.Frame(
            bloco,
            bg=COR_CARTAO,
            highlightbackground=COR_BORDA,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        cartao.pack(fill="x")
        return cartao

    def _criar_botao_primario(self, parent: tk.Misc, texto: str, comando) -> tk.Button:
        botao = tk.Button(
            parent,
            text=texto,
            command=comando,
            font=("Segoe UI", 11, "bold"),
            bg=COR_DESTAQUE,
            fg="white",
            activebackground=COR_DESTAQUE_ESCURO,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
        )
        botao.bind("<Enter>", lambda _e: botao.configure(bg=COR_DESTAQUE_ESCURO))
        botao.bind(
            "<Leave>",
            lambda _e: botao.configure(bg="#a5b4fc" if str(botao["state"]) == "disabled" else COR_DESTAQUE),
        )
        return botao

    def _criar_botao_secundario(self, parent: tk.Misc, texto: str, comando) -> ttk.Button:
        return ttk.Button(parent, text=texto, command=comando, style="Card.TButton")

    def _configurar_scroll(self, canvas: tk.Canvas, container: tk.Frame) -> None:
        janela = canvas.create_window((0, 0), window=container, anchor="nw")

        def atualizar_scroll(_event: tk.Event | None = None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def ajustar_largura(event: tk.Event) -> None:
            canvas.itemconfig(janela, width=event.width)

        container.bind("<Configure>", atualizar_scroll)
        canvas.bind("<Configure>", ajustar_largura)

    def _bind_scroll_pagina(self, widget: tk.Misc, canvas: tk.Canvas, ignorar: set[tk.Misc]) -> None:
        if widget in ignorar:
            return

        def rolar(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        widget.bind("<MouseWheel>", rolar)
        for filho in widget.winfo_children():
            self._bind_scroll_pagina(filho, canvas, ignorar)

    def _montar_interface(self) -> None:
        cabecalho = tk.Frame(self, bg=COR_CABECALHO, padx=24, pady=20)
        cabecalho.pack(side="top", fill="x")

        tk.Label(
            cabecalho,
            text="🖼️  Conversor para JPEG",
            font=("Segoe UI", 20, "bold"),
            bg=COR_CABECALHO,
            fg="white",
        ).pack(anchor="w")

        tk.Label(
            cabecalho,
            text="Transforme arquivos baixados em imagens prontas para abrir",
            font=("Segoe UI", 10),
            bg=COR_CABECALHO,
            fg="#c7d2fe",
        ).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=COR_DESTAQUE, height=3).pack(side="top", fill="x")

        status_bar = tk.Frame(self, bg=COR_CARTAO, padx=16, pady=8, highlightbackground=COR_BORDA, highlightthickness=1)
        status_bar.pack(side="bottom", fill="x")

        status_inner = tk.Frame(status_bar, bg=COR_CARTAO)
        status_inner.pack(fill="x")

        self.status_dot = tk.Label(status_inner, text="●", font=("Segoe UI", 11), bg=COR_CARTAO, fg=COR_SUCESSO)
        self.status_dot.pack(side="left")

        self.status_var = tk.StringVar(value="Pronto para converter")
        tk.Label(
            status_inner,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg=COR_CARTAO,
            fg=COR_TEXTO,
        ).pack(side="left", padx=(6, 0))

        rodape = tk.Frame(self, bg=COR_RODAPE, padx=16, pady=10)
        rodape.pack(side="bottom", fill="x")

        tk.Label(
            rodape,
            text=TEXTO_CREDITOS,
            font=("Segoe UI", 9),
            bg=COR_RODAPE,
            fg=COR_TEXTO_SUAVE,
        ).pack(anchor="center")

        email_label = tk.Label(
            rodape,
            text=TEXTO_CONTATO,
            font=("Segoe UI", 9, "underline"),
            bg=COR_RODAPE,
            fg=COR_DESTAQUE,
            cursor="hand2",
        )
        email_label.pack(anchor="center", pady=(2, 0))
        email_label.bind("<Button-1>", lambda _e: os.startfile(f"mailto:{EMAIL_CONTATO}"))

        scroll_outer = tk.Frame(self, bg=COR_FUNDO)
        scroll_outer.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(scroll_outer, orient="vertical", style="Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(
            scroll_outer,
            bg=COR_FUNDO,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        container = tk.Frame(canvas, bg=COR_FUNDO, padx=24, pady=16)
        self._configurar_scroll(canvas, container)

        secao_instrucoes = self._criar_secao(container, "Instruções", "📋")
        self.btn_toggle_instrucoes = tk.Button(
            secao_instrucoes,
            text="▼  Ocultar instruções",
            command=self._alternar_instrucoes,
            font=("Segoe UI", 9),
            bg="#ede9fe",
            fg=COR_DESTAQUE,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.btn_toggle_instrucoes.pack(anchor="w", pady=(0, 8))

        self.frame_instrucoes_conteudo = tk.Frame(secao_instrucoes, bg=COR_CARTAO)
        self.frame_instrucoes_conteudo.pack(fill="x")

        tk.Label(
            self.frame_instrucoes_conteudo,
            text=INSTRUCOES,
            font=("Segoe UI", 10),
            bg=COR_CARTAO,
            fg=COR_TEXTO_SUAVE,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        secao_modo = self._criar_secao(container, "O que converter?", "🎯")
        opcoes = tk.Frame(secao_modo, bg=COR_CARTAO)
        opcoes.pack(anchor="w", fill="x")

        ttk.Radiobutton(
            opcoes,
            text="📁  Pasta inteira",
            value="pasta",
            variable=self.modo_var,
            command=self.atualizar_modo,
            style="Card.TRadiobutton",
        ).pack(side="left", padx=(0, 24))

        ttk.Radiobutton(
            opcoes,
            text="📄  Arquivos escolhidos (um ou vários)",
            value="arquivos",
            variable=self.modo_var,
            command=self.atualizar_modo,
            style="Card.TRadiobutton",
        ).pack(side="left")

        secao_selecao = self._criar_secao(container, "Seleção", "📂")
        self.selecao_label = tk.Label(
            secao_selecao,
            text="Escolha a pasta com os arquivos baixados",
            font=("Segoe UI", 10),
            bg=COR_CARTAO,
            fg=COR_TEXTO_SUAVE,
        )
        self.selecao_label.pack(anchor="w", pady=(0, 6))

        self.badge_selecao = tk.Label(
            secao_selecao,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#ede9fe",
            fg=COR_DESTAQUE,
            padx=10,
            pady=4,
        )

        pasta_frame = tk.Frame(secao_selecao, bg=COR_CARTAO)
        pasta_frame.pack(fill="x")

        entrada = tk.Entry(
            pasta_frame,
            textvariable=self.pasta_var,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            bg="#f8fafc",
            fg=COR_TEXTO,
            highlightthickness=1,
            highlightbackground=COR_BORDA,
            highlightcolor=COR_DESTAQUE,
        )
        entrada.pack(side="left", fill="x", expand=True, ipady=7)

        self.btn_pasta = self._criar_botao_secundario(pasta_frame, "Escolher pasta", self.escolher_pasta)
        self.btn_pasta.pack(side="left", padx=(10, 0))

        self.btn_arquivos = self._criar_botao_secundario(
            pasta_frame, "Escolher arquivos...", self.escolher_arquivos
        )
        self.btn_arquivos.configure(state="disabled")
        self.btn_arquivos.pack(side="left", padx=(10, 0))

        secao_acoes = self._criar_secao(container, "Ações", "⚡")
        botoes = tk.Frame(secao_acoes, bg=COR_CARTAO)
        botoes.pack(fill="x")

        self.btn_converter = self._criar_botao_primario(
            botoes, "✨  Converter arquivos", self.iniciar_conversao
        )
        self.btn_converter.pack(side="left")

        self.btn_abrir = self._criar_botao_secundario(
            botoes, "📂  Abrir pasta convertidos", self.abrir_pasta_convertidos
        )
        self.btn_abrir.configure(state="disabled")
        self.btn_abrir.pack(side="left", padx=(12, 0))

        self.progress = ttk.Progressbar(
            secao_acoes,
            mode="indeterminate",
            style="Accent.Horizontal.TProgressbar",
        )

        secao_resultado = self._criar_secao(container, "Resultado", "📊")
        log_frame = tk.Frame(secao_resultado, bg=COR_CARTAO)
        log_frame.pack(fill="both", expand=True)

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", style="Vertical.TScrollbar")
        log_scroll.pack(side="right", fill="y")

        self.log = tk.Text(
            log_frame,
            height=10,
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            wrap="word",
            bg="#f8fafc",
            fg=COR_TEXTO,
            yscrollcommand=log_scroll.set,
            padx=8,
            pady=8,
        )
        self.log.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log.yview)

        self.log.tag_configure("ok", foreground=COR_SUCESSO)
        self.log.tag_configure("erro", foreground=COR_ERRO)
        self.log.tag_configure("dup", foreground=COR_AVISO)
        self.log.tag_configure("detalhe", foreground=COR_TEXTO_SUAVE)
        self.log.tag_configure("titulo", foreground=COR_DESTAQUE, font=("Consolas", 10, "bold"))
        self.log.tag_configure("progresso", foreground=COR_DESTAQUE, font=("Consolas", 10, "italic"))

        self.log.insert("1.0", "Aguardando conversão...\n", "detalhe")
        self.log.configure(state="disabled")

        self.log.bind(
            "<MouseWheel>",
            lambda event: self.log.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )
        self._bind_scroll_pagina(container, canvas, ignorar={log_frame, self.log, log_scroll})

    def atualizar_modo(self) -> None:
        if self.modo_var.get() == "pasta":
            self.selecao_label.configure(text="Escolha a pasta com os arquivos baixados")
            self.btn_pasta.configure(state="normal")
            self.btn_arquivos.configure(state="disabled")
            if not self.pasta_var.get().startswith("("):
                self._atualizar_badge()
                return
            self.pasta_var.set("")
            self.arquivos_selecionados.clear()
        else:
            self.selecao_label.configure(
                text="Escolha um ou vários arquivos (Ctrl+clique para marcar vários)"
            )
            self.btn_pasta.configure(state="disabled")
            self.btn_arquivos.configure(state="normal")
            self.resumir_arquivos_selecionados()

        self._atualizar_badge()

    def resumir_arquivos_selecionados(self) -> None:
        if not self.arquivos_selecionados:
            self.pasta_var.set("Nenhum arquivo selecionado")
            self._atualizar_badge()
            return

        if len(self.arquivos_selecionados) == 1:
            self.pasta_var.set(str(self.arquivos_selecionados[0]))
            self._atualizar_badge()
            return

        nomes = ", ".join(arquivo.name for arquivo in self.arquivos_selecionados[:3])
        if len(self.arquivos_selecionados) > 3:
            nomes += ", ..."
        self.pasta_var.set(f"({len(self.arquivos_selecionados)} arquivos) {nomes}")
        self._atualizar_badge()

    def escolher_pasta(self) -> None:
        pasta = filedialog.askdirectory(title="Escolha a pasta com os arquivos")
        if pasta:
            self.pasta_var.set(pasta)
            self.arquivos_selecionados.clear()
            self._atualizar_badge()

    def escolher_arquivos(self) -> None:
        selecionados = filedialog.askopenfilenames(
            title="Escolha os arquivos para converter (Ctrl+clique para vários)",
            filetypes=[
                ("Todos os arquivos", "*.*"),
                ("Imagens", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif;*.tif;*.tiff"),
            ],
        )
        if selecionados:
            self.arquivos_selecionados = [Path(caminho) for caminho in selecionados]
            self.resumir_arquivos_selecionados()

    def _tag_log_linha(self, linha: str) -> str:
        if linha.startswith("⏳"):
            return "progresso"
        if linha.startswith("[OK]"):
            return "ok"
        if linha.startswith("[ERRO]"):
            return "erro"
        if linha.startswith("[==]"):
            return "dup"
        if linha.startswith("Resumo:") or linha.startswith("Convertendo"):
            return "titulo"
        if linha.startswith("Motivo:") or linha.startswith("    ") or linha.startswith("- "):
            return "detalhe"
        return "normal"

    def escrever_log(self, texto: str) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        for linha in texto.splitlines():
            self.log.insert("end", linha + "\n", self._tag_log_linha(linha))
        self.log.configure(state="disabled")

    def abrir_pasta_convertidos(self) -> None:
        if self.ultima_pasta_saida and self.ultima_pasta_saida.exists():
            os.startfile(self.ultima_pasta_saida)
        else:
            messagebox.showinfo(
                "Nada para abrir",
                "Ainda não existe pasta convertidos para abrir.\n\n"
                "Motivo: nenhuma conversão foi concluída com sucesso até agora.\n"
                "Converta pelo menos um arquivo e tente novamente.",
            )

    def iniciar_conversao(self) -> None:
        if self.modo_var.get() == "arquivos":
            if not self.arquivos_selecionados:
                messagebox.showerror(
                    "Nenhum arquivo selecionado",
                    "Você marcou \"Arquivos escolhidos\", mas nenhum arquivo foi selecionado.\n\n"
                    "O que fazer:\n"
                    "1. Clique em \"Escolher arquivos...\"\n"
                    "2. Selecione um ou vários arquivos (Ctrl+clique para marcar vários)\n"
                    "3. Clique em \"Converter arquivos\"",
                )
                return
        else:
            texto_pasta = self.pasta_var.get().strip()
            if not texto_pasta:
                messagebox.showerror(
                    "Nenhuma pasta selecionada",
                    "Você marcou \"Pasta inteira\", mas ainda não escolheu uma pasta.\n\n"
                    "O que fazer:\n"
                    "1. Clique em \"Escolher pasta\"\n"
                    "2. Selecione onde estão os arquivos baixados\n"
                    "3. Clique em \"Converter arquivos\"",
                )
                return

            pasta = Path(texto_pasta)
            if not pasta.exists():
                messagebox.showerror(
                    "Pasta não encontrada",
                    f"A pasta informada não existe:\n{texto_pasta}\n\n"
                    "Motivo: o caminho pode estar errado ou a pasta foi movida/excluída.\n\n"
                    "O que fazer:\n"
                    "- Clique em \"Escolher pasta\" e selecione novamente.",
                )
                return
            if not pasta.is_dir():
                messagebox.showerror(
                    "Caminho inválido",
                    f"O caminho informado não é uma pasta:\n{texto_pasta}\n\n"
                    "Motivo: você pode ter selecionado um arquivo em vez de uma pasta.\n\n"
                    "O que fazer:\n"
                    "- Use \"Escolher pasta\" para selecionar a pasta correta,\n"
                    "  ou mude para \"Arquivos escolhidos\".",
                )
                return

        self._set_busy(True)
        self._limpar_log()
        self._iniciar_progresso()

        if self.modo_var.get() == "arquivos":
            arquivos = list(self.arquivos_selecionados)
            threading.Thread(target=self._executar_conversao_arquivos, args=(arquivos,), daemon=True).start()
        else:
            pasta = Path(self.pasta_var.get().strip())
            threading.Thread(target=self._executar_conversao_pasta, args=(pasta,), daemon=True).start()

    def _ao_linha_log(self, linha: str) -> None:
        if linha.startswith("⏳"):
            self._atualizar_status(linha, COR_DESTAQUE)
        self._append_log_linha(linha)

    def _finalizar_conversao(self, convertidos: int, mensagens: list[str], pasta_saida: Path | None) -> None:
        self._parar_progresso()
        self._set_busy(False)
        self.escrever_log("\n".join(mensagens))
        if convertidos > 0 and pasta_saida:
            self.ultima_pasta_saida = pasta_saida
            self.btn_abrir.configure(state="normal")
            self._atualizar_status("Conversão finalizada com sucesso!", COR_SUCESSO)
        elif convertidos == 0:
            self._atualizar_status("Nenhum arquivo foi convertido.", COR_ERRO)
            messagebox.showwarning("Nada foi convertido", resumo_final_vazio(mensagens))

    def _executar_conversao_pasta(self, pasta: Path) -> None:
        convertidos, mensagens, pasta_saida = converter_pasta(pasta, ao_linha=self._ao_linha_log_thread)
        self.after(0, lambda: self._finalizar_conversao(convertidos, mensagens, pasta_saida))

    def _executar_conversao_arquivos(self, arquivos: list[Path]) -> None:
        convertidos, mensagens, pasta_saida = converter_lista(arquivos, ao_linha=self._ao_linha_log_thread)
        self.after(0, lambda: self._finalizar_conversao(convertidos, mensagens, pasta_saida))

    def _ao_linha_log_thread(self, linha: str) -> None:
        self.after(0, lambda l=linha: self._ao_linha_log(l))


def main_cli() -> int:
    if len(sys.argv) > 2 and sys.argv[1] == "--cli":
        pasta = Path(sys.argv[2]).resolve()
    elif len(sys.argv) > 1:
        pasta = Path(sys.argv[1]).resolve()
    else:
        pasta = Path(__file__).resolve().parent
    convertidos, mensagens, _ = converter_pasta(pasta)
    print("\n".join(mensagens))
    return 0 if convertidos >= 0 else 1


def main_gui() -> None:
    app = ConversorApp()
    app.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        raise SystemExit(main_cli())
    main_gui()
