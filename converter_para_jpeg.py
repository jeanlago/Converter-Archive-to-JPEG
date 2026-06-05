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

from i18n import I18n, _i18n

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic", ".heif"}
EXTENSOES_JPEG = {".jpg", ".jpeg"}
CREDITOS = "Jean, irmã de Thalyta Marins backoffice"
EMAIL_CONTATO = "jeanlago203@gmail.com"

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
    "i18n.py",
}

PADRAO_NOME_BAIXADO = re.compile(r"^arquivo(\s*\(\d+\))?$", re.IGNORECASE)


def explicar_erro_conversao(caminho: Path, erro: Exception | str, i18n: I18n | None = None) -> str:
    tr = i18n or _i18n
    texto = str(erro).lower()

    if isinstance(erro, UnidentifiedImageError) or "cannot identify image" in texto:
        return tr.t("err_invalid_image")
    if isinstance(erro, PermissionError) or "permission denied" in texto or "acesso negado" in texto:
        return tr.t("err_permission")
    if "no space left" in texto or "disk full" in texto or "espaco insuficiente" in texto:
        return tr.t("err_disk_full")
    if isinstance(erro, FileNotFoundError) or "no such file" in texto:
        return tr.t("err_not_found")
    if "truncated" in texto or "broken" in texto:
        return tr.t("err_corrupt")

    return tr.t("err_generic", detail=erro)


def explicar_ja_convertido(caminho: Path, destino: Path, i18n: I18n | None = None) -> str:
    tr = i18n or _i18n
    return tr.t("err_already_converted", name=destino.name)


def mensagem_pasta_nao_encontrada(pasta: Path, i18n: I18n | None = None) -> list[str]:
    tr = i18n or _i18n
    return [
        tr.t("err_folder_not_found"),
        "",
        tr.t("folder_path", path=pasta),
        "",
        tr.t("what_to_do"),
        tr.t("pick_folder_again"),
        tr.t("check_folder_moved"),
    ]


def mensagem_pasta_sem_elegiveis(pasta: Path, i18n: I18n | None = None) -> list[str]:
    tr = i18n or _i18n
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
        tr.t("no_eligible_title"),
        "",
        tr.t("folder_mode_rules"),
        tr.t("rule_no_ext"),
        tr.t("rule_arquivo_name"),
        "",
        tr.t("found_summary"),
    ]

    if nome_invalido:
        mensagens.append(tr.t("ignored_by_name", n=nome_invalido, examples=", ".join(exemplos_nome)))
        mensagens.append(tr.t("ignored_by_name_hint"))
    if ja_jpeg:
        mensagens.append(tr.t("already_jpeg", n=ja_jpeg))
    if nao_imagem:
        mensagens.append(
            tr.t("not_image_content", n=nao_imagem, examples=", ".join(exemplos_nao_imagem))
        )
        mensagens.append(tr.t("not_image_hint"))
    if ignorados:
        mensagens.append(tr.t("ignored_internal", n=ignorados))
    if not any([nome_invalido, ja_jpeg, nao_imagem, ignorados]):
        mensagens.append(tr.t("folder_empty"))

    mensagens.extend([
        "",
        tr.t("what_to_do"),
        tr.t("confirm_downloads_here"),
        tr.t("use_file_mode"),
        tr.t("redownload"),
    ])
    return mensagens


def mensagem_selecao_sem_validos(caminhos: list[Path], i18n: I18n | None = None) -> list[str]:
    tr = i18n or _i18n
    motivos: list[str] = []

    for caminho in caminhos:
        if not caminho.is_file():
            motivos.append(tr.t("invalid_or_missing", name=caminho.name))
            continue
        if caminho.name in ARQUIVOS_IGNORADOS:
            motivos.append(tr.t("internal_ignored", name=caminho.name))
            continue
        if caminho.suffix.lower() in EXTENSOES_JPEG:
            motivos.append(tr.t("already_jpeg_file", name=caminho.name))
            continue
        if caminho.suffix and caminho.suffix.lower() not in EXTENSOES_IMAGEM:
            motivos.append(tr.t("unsupported_ext", name=caminho.name, ext=caminho.suffix))
            continue
        motivos.append(tr.t("not_accepted", name=caminho.name))

    return [
        tr.t("none_selected_valid_title"),
        "",
        tr.t("each_file_reason"),
        *motivos,
        "",
        tr.t("what_to_do"),
        tr.t("select_downloads_or_images"),
        tr.t("jpeg_skip"),
        tr.t("try_redownload"),
    ]


def resumo_final_vazio(i18n: I18n | None = None) -> str:
    return (i18n or _i18n).t("warn_nothing_converted_body")


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


def converter_arquivo(caminho: Path, i18n: I18n | None = None) -> tuple[Path | None, str | None, bool]:
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
        return None, explicar_erro_conversao(caminho, erro, i18n), False


def converter_pasta(
    pasta: Path,
    ao_linha: Callable[[str], None] | None = None,
    i18n: I18n | None = None,
) -> tuple[int, list[str], Path | None]:
    tr = i18n or _i18n

    def emitir(linha: str) -> None:
        mensagens.append(linha)
        if ao_linha:
            ao_linha(linha)

    mensagens: list[str] = []
    if not pasta.is_dir():
        emitir(tr.t("err_folder_not_found"))
        for linha in mensagem_pasta_nao_encontrada(pasta, tr)[1:]:
            emitir(linha)
        return 0, mensagens, None

    arquivos = sorted(p for p in pasta.iterdir() if deve_processar_pasta(p))
    if not arquivos:
        for linha in mensagem_pasta_sem_elegiveis(pasta, tr):
            emitir(linha)
        return 0, mensagens, None

    emitir(tr.t("converting_eligible", n=len(arquivos)))
    emitir("")
    convertidos = 0
    ignorados = 0
    erros = 0
    pasta_saida = pasta / "convertidos"

    for indice, caminho in enumerate(arquivos, start=1):
        if ao_linha:
            ao_linha(tr.t("processing", i=indice, total=len(arquivos), name=caminho.name))

        destino, erro, ja_existia = converter_arquivo(caminho, tr)
        if ja_existia and destino:
            ignorados += 1
            emitir(f"[==] {caminho.name}")
            emitir(f"    {explicar_ja_convertido(caminho, destino, tr)}")
        elif destino:
            convertidos += 1
            emitir(f"[OK] {caminho.name}  ->  {destino.name}")
        else:
            erros += 1
            emitir(f"[ERRO] {caminho.name}")
            emitir(f"    {erro}")

    emitir("")
    emitir(tr.t("summary", ok=convertidos, skip=ignorados, err=erros))
    emitir(tr.t("saved_to"))
    emitir(str(pasta_saida))
    return convertidos + ignorados, mensagens, pasta_saida if convertidos or ignorados else None


def converter_lista(
    caminhos: list[Path],
    ao_linha: Callable[[str], None] | None = None,
    i18n: I18n | None = None,
) -> tuple[int, list[str], Path | None]:
    tr = i18n or _i18n

    def emitir(linha: str) -> None:
        mensagens.append(linha)
        if ao_linha:
            ao_linha(linha)

    mensagens: list[str] = []
    arquivos = sorted({p.resolve() for p in caminhos if deve_processar_selecionado(p)})
    if not arquivos:
        for linha in mensagem_selecao_sem_validos(caminhos, tr):
            emitir(linha)
        return 0, mensagens, None

    emitir(tr.t("converting_selected", n=len(arquivos)))
    emitir("")
    convertidos = 0
    ignorados = 0
    erros = 0
    pastas_saida: set[Path] = set()

    for indice, caminho in enumerate(arquivos, start=1):
        if ao_linha:
            ao_linha(tr.t("processing", i=indice, total=len(arquivos), name=caminho.name))

        destino, erro, ja_existia = converter_arquivo(caminho, tr)
        if ja_existia and destino:
            ignorados += 1
            pastas_saida.add(destino.parent)
            emitir(f"[==] {caminho.name}")
            emitir(f"    {explicar_ja_convertido(caminho, destino, tr)}")
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
        emitir(tr.t("none_converted_all_failed"))
        return 0, mensagens, None

    emitir("")
    emitir(tr.t("summary", ok=convertidos, skip=ignorados, err=erros))
    if len(pastas_saida) == 1:
        pasta_saida = pastas_saida.pop()
        emitir(tr.t("saved_to"))
        emitir(str(pasta_saida))
    else:
        pasta_saida = next(iter(pastas_saida))
        emitir(tr.t("converted_folders"))
        for pasta in sorted(pastas_saida):
            emitir(f"- {pasta}")

    return convertidos + ignorados, mensagens, pasta_saida


class ConversorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.i18n = _i18n
        self.idioma_var = tk.StringVar(value=self.i18n.idioma)
        self._secao_titulos: dict[str, tk.Label] = {}

        self.title(self.i18n.t("app_title"))
        self.minsize(540, 440)

        self.pasta_var = tk.StringVar(value="")
        self.modo_var = tk.StringVar(value="pasta")
        self.arquivos_selecionados: list[Path] = []
        self.ultima_pasta_saida: Path | None = None
        self.instrucoes_abertas = True

        self._configurar_tema()
        self._montar_interface()
        self._aplicar_idioma()
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
            self.badge_selecao.configure(text=self.i18n.t("badge_files", n=total))
            self.badge_selecao.pack(anchor="w", pady=(0, 10))
            self._atualizar_status(self.i18n.t("status_files_ready", n=total), COR_DESTAQUE)
            return

        if self.modo_var.get() == "pasta":
            pasta = self.pasta_var.get().strip()
            if pasta and not pasta.startswith("(") and Path(pasta).is_dir():
                self.badge_selecao.configure(text=self.i18n.t("badge_folder"))
                self.badge_selecao.pack(anchor="w", pady=(0, 10))
                self._atualizar_status(self.i18n.t("status_folder_ready"), COR_DESTAQUE)
                return

        self.badge_selecao.pack_forget()
        self._atualizar_status(self.i18n.t("status_ready"))

    def _alternar_instrucoes(self) -> None:
        if self.instrucoes_abertas:
            self.frame_instrucoes_conteudo.pack_forget()
            self.btn_toggle_instrucoes.configure(text=self.i18n.t("show_instructions"))
            self.instrucoes_abertas = False
        else:
            self.frame_instrucoes_conteudo.pack(fill="x")
            self.btn_toggle_instrucoes.configure(text=self.i18n.t("hide_instructions"))
            self.instrucoes_abertas = True

    def _iniciar_progresso(self) -> None:
        self.progress.pack(fill="x", pady=(12, 0))
        self.progress.start(10)
        self._atualizar_status(self.i18n.t("status_converting"), COR_DESTAQUE)

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

    def _criar_secao(self, parent: tk.Misc, titulo_key: str, emoji: str = "") -> tk.Frame:
        bloco = tk.Frame(parent, bg=COR_FUNDO)
        bloco.pack(fill="x", pady=(0, 14))

        titulo_label = tk.Label(
            bloco,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_DESTAQUE,
        )
        titulo_label.pack(anchor="w", pady=(0, 6))
        self._secao_titulos[titulo_key] = titulo_label
        self._secao_emojis = getattr(self, "_secao_emojis", {})
        self._secao_emojis[titulo_key] = emoji

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

        cabecalho_top = tk.Frame(cabecalho, bg=COR_CABECALHO)
        cabecalho_top.pack(fill="x")

        titulo_col = tk.Frame(cabecalho_top, bg=COR_CABECALHO)
        titulo_col.pack(side="left", fill="x", expand=True)

        self.lbl_titulo_cabecalho = tk.Label(
            titulo_col,
            text="",
            font=("Segoe UI", 20, "bold"),
            bg=COR_CABECALHO,
            fg="white",
        )
        self.lbl_titulo_cabecalho.pack(anchor="w")

        self.lbl_subtitulo_cabecalho = tk.Label(
            titulo_col,
            text="",
            font=("Segoe UI", 10),
            bg=COR_CABECALHO,
            fg="#c7d2fe",
        )
        self.lbl_subtitulo_cabecalho.pack(anchor="w", pady=(4, 0))

        lang_frame = tk.Frame(cabecalho_top, bg=COR_CABECALHO)
        lang_frame.pack(side="right", anchor="ne")

        self.btn_lang_pt = tk.Button(
            lang_frame,
            text="PT",
            command=lambda: self._trocar_idioma("pt"),
            font=("Segoe UI", 9, "bold"),
            bg="#4338ca",
            fg="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.btn_lang_pt.pack(side="left", padx=(0, 4))

        self.btn_lang_en = tk.Button(
            lang_frame,
            text="EN",
            command=lambda: self._trocar_idioma("en"),
            font=("Segoe UI", 9, "bold"),
            bg="#6366f1",
            fg="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.btn_lang_en.pack(side="left")

        tk.Frame(self, bg=COR_DESTAQUE, height=3).pack(side="top", fill="x")

        status_bar = tk.Frame(self, bg=COR_CARTAO, padx=16, pady=8, highlightbackground=COR_BORDA, highlightthickness=1)
        status_bar.pack(side="bottom", fill="x")

        status_inner = tk.Frame(status_bar, bg=COR_CARTAO)
        status_inner.pack(fill="x")

        self.status_dot = tk.Label(status_inner, text="●", font=("Segoe UI", 11), bg=COR_CARTAO, fg=COR_SUCESSO)
        self.status_dot.pack(side="left")

        self.status_var = tk.StringVar(value="")
        tk.Label(
            status_inner,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg=COR_CARTAO,
            fg=COR_TEXTO,
        ).pack(side="left", padx=(6, 0))

        rodape = tk.Frame(self, bg=COR_RODAPE, padx=16, pady=10)
        rodape.pack(side="bottom", fill="x")

        self.lbl_creditos = tk.Label(
            rodape,
            text="",
            font=("Segoe UI", 9),
            bg=COR_RODAPE,
            fg=COR_TEXTO_SUAVE,
        )
        self.lbl_creditos.pack(anchor="center")

        self.lbl_contato = tk.Label(
            rodape,
            text="",
            font=("Segoe UI", 9, "underline"),
            bg=COR_RODAPE,
            fg=COR_DESTAQUE,
            cursor="hand2",
        )
        self.lbl_contato.pack(anchor="center", pady=(2, 0))
        self.lbl_contato.bind("<Button-1>", lambda _e: os.startfile(f"mailto:{EMAIL_CONTATO}"))

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

        secao_instrucoes = self._criar_secao(container, "section_instructions", "📋")
        self.btn_toggle_instrucoes = tk.Button(
            secao_instrucoes,
            text="",
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

        self.lbl_instrucoes = tk.Label(
            self.frame_instrucoes_conteudo,
            text="",
            font=("Segoe UI", 10),
            bg=COR_CARTAO,
            fg=COR_TEXTO_SUAVE,
            justify="left",
            anchor="w",
        )
        self.lbl_instrucoes.pack(anchor="w")

        secao_modo = self._criar_secao(container, "section_mode", "🎯")
        opcoes = tk.Frame(secao_modo, bg=COR_CARTAO)
        opcoes.pack(anchor="w", fill="x")

        self.radio_pasta = ttk.Radiobutton(
            opcoes,
            text="",
            value="pasta",
            variable=self.modo_var,
            command=self.atualizar_modo,
            style="Card.TRadiobutton",
        )
        self.radio_pasta.pack(side="left", padx=(0, 24))

        self.radio_arquivos = ttk.Radiobutton(
            opcoes,
            text="",
            value="arquivos",
            variable=self.modo_var,
            command=self.atualizar_modo,
            style="Card.TRadiobutton",
        )
        self.radio_arquivos.pack(side="left")

        secao_selecao = self._criar_secao(container, "section_selection", "📂")
        self.selecao_label = tk.Label(
            secao_selecao,
            text="",
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

        self.btn_pasta = self._criar_botao_secundario(pasta_frame, "", self.escolher_pasta)
        self.btn_pasta.pack(side="left", padx=(10, 0))

        self.btn_arquivos = self._criar_botao_secundario(
            pasta_frame, "", self.escolher_arquivos
        )
        self.btn_arquivos.configure(state="disabled")
        self.btn_arquivos.pack(side="left", padx=(10, 0))

        secao_acoes = self._criar_secao(container, "section_actions", "⚡")
        botoes = tk.Frame(secao_acoes, bg=COR_CARTAO)
        botoes.pack(fill="x")

        self.btn_converter = self._criar_botao_primario(
            botoes, "", self.iniciar_conversao
        )
        self.btn_converter.pack(side="left")

        self.btn_abrir = self._criar_botao_secundario(
            botoes, "", self.abrir_pasta_convertidos
        )
        self.btn_abrir.configure(state="disabled")
        self.btn_abrir.pack(side="left", padx=(12, 0))

        self.progress = ttk.Progressbar(
            secao_acoes,
            mode="indeterminate",
            style="Accent.Horizontal.TProgressbar",
        )

        secao_resultado = self._criar_secao(container, "section_result", "📊")
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

        self.log.insert("1.0", "\n", "detalhe")
        self.log.configure(state="disabled")

        self.log.bind(
            "<MouseWheel>",
            lambda event: self.log.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )
        self._bind_scroll_pagina(container, canvas, ignorar={log_frame, self.log, log_scroll})

    def _trocar_idioma(self, idioma: str) -> None:
        if idioma == self.i18n.idioma:
            return
        self.i18n.set_idioma(idioma)
        _i18n.set_idioma(idioma)
        self.idioma_var.set(idioma)
        self._aplicar_idioma()

    def _aplicar_idioma(self) -> None:
        tr = self.i18n
        self.title(tr.t("app_title"))
        self.lbl_titulo_cabecalho.configure(text=tr.t("header_title"))
        self.lbl_subtitulo_cabecalho.configure(text=tr.t("header_subtitle"))
        self.lbl_creditos.configure(text=tr.t("credits"))
        self.lbl_contato.configure(text=tr.t("contact"))

        ativo = "#4338ca"
        inativo = "#6366f1"
        if tr.idioma == "pt":
            self.btn_lang_pt.configure(bg=ativo)
            self.btn_lang_en.configure(bg=inativo)
        else:
            self.btn_lang_pt.configure(bg=inativo)
            self.btn_lang_en.configure(bg=ativo)

        for chave, label in self._secao_titulos.items():
            emoji = getattr(self, "_secao_emojis", {}).get(chave, "")
            titulo = tr.t(chave)
            label.configure(text=f"{emoji}  {titulo}" if emoji else titulo)

        self.lbl_instrucoes.configure(text=tr.t("instructions"))
        self.btn_toggle_instrucoes.configure(
            text=tr.t("hide_instructions") if self.instrucoes_abertas else tr.t("show_instructions")
        )
        self.radio_pasta.configure(text=tr.t("mode_folder"))
        self.radio_arquivos.configure(text=tr.t("mode_files"))
        self.btn_pasta.configure(text=tr.t("btn_choose_folder"))
        self.btn_arquivos.configure(text=tr.t("btn_choose_files"))
        self.btn_converter.configure(text=tr.t("btn_convert"))
        self.btn_abrir.configure(text=tr.t("btn_open_output"))

        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("1.0", tr.t("log_waiting") + "\n", "detalhe")
        self.log.configure(state="disabled")

        self.atualizar_modo()

    def atualizar_modo(self) -> None:
        if self.modo_var.get() == "pasta":
            self.selecao_label.configure(text=self.i18n.t("select_folder_hint"))
            self.btn_pasta.configure(state="normal")
            self.btn_arquivos.configure(state="disabled")
            if not self.pasta_var.get().startswith("("):
                self._atualizar_badge()
                return
            self.pasta_var.set("")
            self.arquivos_selecionados.clear()
        else:
            self.selecao_label.configure(text=self.i18n.t("select_files_hint"))
            self.btn_pasta.configure(state="disabled")
            self.btn_arquivos.configure(state="normal")
            self.resumir_arquivos_selecionados()

        self._atualizar_badge()

    def resumir_arquivos_selecionados(self) -> None:
        if not self.arquivos_selecionados:
            self.pasta_var.set(self.i18n.t("no_file_selected"))
            self._atualizar_badge()
            return

        if len(self.arquivos_selecionados) == 1:
            self.pasta_var.set(str(self.arquivos_selecionados[0]))
            self._atualizar_badge()
            return

        nomes = ", ".join(arquivo.name for arquivo in self.arquivos_selecionados[:3])
        if len(self.arquivos_selecionados) > 3:
            nomes += ", ..."
        self.pasta_var.set(
            self.i18n.t("files_summary", n=len(self.arquivos_selecionados), names=nomes)
        )
        self._atualizar_badge()

    def escolher_pasta(self) -> None:
        pasta = filedialog.askdirectory(title=self.i18n.t("dialog_choose_folder"))
        if pasta:
            self.pasta_var.set(pasta)
            self.arquivos_selecionados.clear()
            self._atualizar_badge()

    def escolher_arquivos(self) -> None:
        selecionados = filedialog.askopenfilenames(
            title=self.i18n.t("dialog_choose_files"),
            filetypes=[
                (self.i18n.t("filetype_all"), "*.*"),
                (self.i18n.t("filetype_images"), "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif;*.tif;*.tiff"),
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
        if self.i18n.is_title_line(linha):
            return "titulo"
        if self.i18n.is_detail_line(linha):
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
                self.i18n.t("info_nothing_open_title"),
                self.i18n.t("info_nothing_open_body"),
            )

    def iniciar_conversao(self) -> None:
        if self.modo_var.get() == "arquivos":
            if not self.arquivos_selecionados:
                messagebox.showerror(
                    self.i18n.t("err_no_files_title"),
                    self.i18n.t("err_no_files_body"),
                )
                return
        else:
            texto_pasta = self.pasta_var.get().strip()
            if not texto_pasta:
                messagebox.showerror(
                    self.i18n.t("err_no_folder_title"),
                    self.i18n.t("err_no_folder_body"),
                )
                return

            pasta = Path(texto_pasta)
            if not pasta.exists():
                messagebox.showerror(
                    self.i18n.t("err_folder_missing_title"),
                    self.i18n.t("err_folder_missing_body", path=texto_pasta),
                )
                return
            if not pasta.is_dir():
                messagebox.showerror(
                    self.i18n.t("err_not_folder_title"),
                    self.i18n.t("err_not_folder_body", path=texto_pasta),
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
            self._atualizar_status(self.i18n.t("status_success"), COR_SUCESSO)
        elif convertidos == 0:
            self._atualizar_status(self.i18n.t("status_none"), COR_ERRO)
            messagebox.showwarning(
                self.i18n.t("warn_nothing_converted_title"),
                resumo_final_vazio(self.i18n),
            )

    def _executar_conversao_pasta(self, pasta: Path) -> None:
        convertidos, mensagens, pasta_saida = converter_pasta(
            pasta, ao_linha=self._ao_linha_log_thread, i18n=self.i18n
        )
        self.after(0, lambda: self._finalizar_conversao(convertidos, mensagens, pasta_saida))

    def _executar_conversao_arquivos(self, arquivos: list[Path]) -> None:
        convertidos, mensagens, pasta_saida = converter_lista(
            arquivos, ao_linha=self._ao_linha_log_thread, i18n=self.i18n
        )
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
