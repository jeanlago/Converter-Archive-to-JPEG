#!/usr/bin/env python3
"""Converte arquivos de imagem (com ou sem extensão) para JPEG."""

from __future__ import annotations

import hashlib
import os
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, UnidentifiedImageError

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic", ".heif"}
EXTENSOES_JPEG = {".jpg", ".jpeg"}
CREDITOS = "Jean, irmã de Thalyta Marins backoffice"
EMAIL_CONTATO = "jeanlago203@gmail.com"
TEXTO_CREDITOS = f"Feito por {CREDITOS}"
TEXTO_CONTATO = f"Contato: {EMAIL_CONTATO}"
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


def converter_pasta(pasta: Path) -> tuple[int, list[str], Path | None]:
    if not pasta.is_dir():
        return 0, mensagem_pasta_nao_encontrada(pasta), None

    arquivos = sorted(p for p in pasta.iterdir() if deve_processar_pasta(p))
    if not arquivos:
        return 0, mensagem_pasta_sem_elegiveis(pasta), None

    mensagens: list[str] = [f"Convertendo {len(arquivos)} arquivo(s) elegível(is)...\n"]
    convertidos = 0
    ignorados = 0
    erros = 0
    pasta_saida = pasta / "convertidos"

    for caminho in arquivos:
        destino, erro, ja_existia = converter_arquivo(caminho)
        if ja_existia and destino:
            ignorados += 1
            mensagens.append(f"[==] {caminho.name}\n    {explicar_ja_convertido(caminho, destino)}")
        elif destino:
            convertidos += 1
            mensagens.append(f"[OK] {caminho.name}  ->  {destino.name}")
        else:
            erros += 1
            mensagens.append(f"[ERRO] {caminho.name}\n    {erro}")

    mensagens.append(
        f"\nResumo: {convertidos} convertido(s), {ignorados} já existente(s), {erros} com erro."
    )
    mensagens.append(f"Salvos em:\n{pasta_saida}")
    return convertidos + ignorados, mensagens, pasta_saida if convertidos or ignorados else None


def converter_lista(caminhos: list[Path]) -> tuple[int, list[str], Path | None]:
    arquivos = sorted({p.resolve() for p in caminhos if deve_processar_selecionado(p)})
    if not arquivos:
        return 0, mensagem_selecao_sem_validos(caminhos), None

    mensagens: list[str] = [f"Convertendo {len(arquivos)} arquivo(s) selecionado(s)...\n"]
    convertidos = 0
    ignorados = 0
    erros = 0
    pastas_saida: set[Path] = set()

    for caminho in arquivos:
        destino, erro, ja_existia = converter_arquivo(caminho)
        if ja_existia and destino:
            ignorados += 1
            pastas_saida.add(destino.parent)
            mensagens.append(f"[==] {caminho.name}\n    {explicar_ja_convertido(caminho, destino)}")
        elif destino:
            convertidos += 1
            pastas_saida.add(destino.parent)
            mensagens.append(f"[OK] {caminho.name}  ->  {destino.name}")
        else:
            erros += 1
            mensagens.append(f"[ERRO] {caminho.name}\n    {erro}")

    if convertidos == 0 and ignorados == 0:
        mensagens.append(
            "\nNenhum arquivo foi convertido porque todos falharam ou foram rejeitados."
        )
        return 0, mensagens, None

    if len(pastas_saida) == 1:
        pasta_saida = pastas_saida.pop()
        mensagens.append(
            f"\nResumo: {convertidos} convertido(s), {ignorados} já existente(s), {erros} com erro."
        )
        mensagens.append(f"Salvos em:\n{pasta_saida}")
    else:
        pasta_saida = next(iter(pastas_saida))
        destinos = "\n".join(f"- {pasta}" for pasta in sorted(pastas_saida))
        mensagens.append(
            f"\nResumo: {convertidos} convertido(s), {ignorados} já existente(s), {erros} com erro."
        )
        mensagens.append(f"Pastas convertidos:\n{destinos}")

    return convertidos + ignorados, mensagens, pasta_saida


class ConversorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Conversor para JPEG")
        self.geometry("680x640")
        self.minsize(520, 420)
        self.configure(bg="#f5f5f5")

        self.pasta_var = tk.StringVar(value="")
        self.modo_var = tk.StringVar(value="pasta")
        self.arquivos_selecionados: list[Path] = []
        self.ultima_pasta_saida: Path | None = None

        self._montar_interface()

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
        rodape = tk.Frame(self, bg="#e8e8e8", padx=16, pady=8)
        rodape.pack(side="bottom", fill="x")

        tk.Label(
            rodape,
            text=TEXTO_CREDITOS,
            font=("Segoe UI", 9),
            bg="#e8e8e8",
            fg="#555555",
        ).pack(anchor="center")

        tk.Label(
            rodape,
            text=TEXTO_CONTATO,
            font=("Segoe UI", 9),
            bg="#e8e8e8",
            fg="#555555",
        ).pack(anchor="center", pady=(2, 0))

        scroll_outer = tk.Frame(self, bg="#f5f5f5")
        scroll_outer.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(scroll_outer, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(
            scroll_outer,
            bg="#f5f5f5",
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        container = tk.Frame(canvas, bg="#f5f5f5", padx=24, pady=20)
        self._configurar_scroll(canvas, container)

        titulo = tk.Label(
            container,
            text="Conversor para JPEG",
            font=("Segoe UI", 18, "bold"),
            bg="#f5f5f5",
            fg="#222222",
        )
        titulo.pack(anchor="w")

        instrucoes_frame = tk.LabelFrame(
            container,
            text=" Instruções ",
            font=("Segoe UI", 10, "bold"),
            bg="#f5f5f5",
            fg="#333333",
            padx=12,
            pady=10,
        )
        instrucoes_frame.pack(fill="x", pady=(8, 16))

        instrucoes = tk.Label(
            instrucoes_frame,
            text=INSTRUCOES,
            font=("Segoe UI", 10),
            bg="#f5f5f5",
            fg="#444444",
            justify="left",
            anchor="w",
        )
        instrucoes.pack(anchor="w")

        modo_frame = tk.LabelFrame(
            container,
            text=" O que converter? ",
            font=("Segoe UI", 10, "bold"),
            bg="#f5f5f5",
            fg="#333333",
            padx=12,
            pady=10,
        )
        modo_frame.pack(fill="x", pady=(0, 12))

        opcoes = tk.Frame(modo_frame, bg="#f5f5f5")
        opcoes.pack(anchor="w", fill="x")

        ttk.Radiobutton(
            opcoes,
            text="Pasta inteira",
            value="pasta",
            variable=self.modo_var,
            command=self.atualizar_modo,
        ).pack(side="left", padx=(0, 20))

        ttk.Radiobutton(
            opcoes,
            text="Arquivos escolhidos (um ou vários)",
            value="arquivos",
            variable=self.modo_var,
            command=self.atualizar_modo,
        ).pack(side="left")

        self.selecao_label = tk.Label(
            container,
            text="Passo 2: escolha a pasta com os arquivos baixados",
            font=("Segoe UI", 10, "bold"),
            bg="#f5f5f5",
            fg="#333333",
        )
        self.selecao_label.pack(anchor="w", pady=(0, 8))

        pasta_frame = tk.Frame(container, bg="#f5f5f5")
        pasta_frame.pack(fill="x", pady=(0, 12))

        entrada = tk.Entry(
            pasta_frame,
            textvariable=self.pasta_var,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
        )
        entrada.pack(side="left", fill="x", expand=True, ipady=6)

        self.btn_pasta = ttk.Button(pasta_frame, text="Escolher pasta", command=self.escolher_pasta)
        self.btn_pasta.pack(side="left", padx=(10, 0))

        self.btn_arquivos = ttk.Button(
            pasta_frame,
            text="Escolher arquivos...",
            command=self.escolher_arquivos,
            state="disabled",
        )
        self.btn_arquivos.pack(side="left", padx=(10, 0))

        botoes = tk.Frame(container, bg="#f5f5f5")
        botoes.pack(fill="x", pady=(0, 16))

        self.btn_converter = ttk.Button(
            botoes,
            text="Converter arquivos",
            command=self.iniciar_conversao,
        )
        self.btn_converter.pack(side="left")

        self.btn_abrir = ttk.Button(
            botoes,
            text="Abrir pasta convertidos",
            command=self.abrir_pasta_convertidos,
            state="disabled",
        )
        self.btn_abrir.pack(side="left", padx=(10, 0))

        log_label = tk.Label(
            container,
            text="Resultado",
            font=("Segoe UI", 10, "bold"),
            bg="#f5f5f5",
            fg="#333333",
        )
        log_label.pack(anchor="w")

        log_frame = tk.Frame(container, bg="#f5f5f5")
        log_frame.pack(fill="both", expand=True, pady=(6, 0))

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical")
        log_scroll.pack(side="right", fill="y")

        self.log = tk.Text(
            log_frame,
            height=10,
            font=("Consolas", 10),
            relief="solid",
            bd=1,
            wrap="word",
            bg="#ffffff",
            fg="#222222",
            yscrollcommand=log_scroll.set,
        )
        self.log.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log.yview)
        self.log.insert("1.0", "Aguardando conversão...\n")
        self.log.configure(state="disabled")

        self.log.bind(
            "<MouseWheel>",
            lambda event: self.log.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )
        self._bind_scroll_pagina(container, canvas, ignorar={log_frame, self.log, log_scroll})

    def atualizar_modo(self) -> None:
        if self.modo_var.get() == "pasta":
            self.selecao_label.configure(text="Passo 2: escolha a pasta com os arquivos baixados")
            self.btn_pasta.configure(state="normal")
            self.btn_arquivos.configure(state="disabled")
            if not self.pasta_var.get().startswith("("):
                return
            self.pasta_var.set("")
            self.arquivos_selecionados.clear()
        else:
            self.selecao_label.configure(
                text="Passo 2: escolha um ou vários arquivos (use Ctrl+clique para marcar vários)"
            )
            self.btn_pasta.configure(state="disabled")
            self.btn_arquivos.configure(state="normal")
            self.resumir_arquivos_selecionados()

    def resumir_arquivos_selecionados(self) -> None:
        if not self.arquivos_selecionados:
            self.pasta_var.set("Nenhum arquivo selecionado")
            return

        if len(self.arquivos_selecionados) == 1:
            self.pasta_var.set(str(self.arquivos_selecionados[0]))
            return

        nomes = ", ".join(arquivo.name for arquivo in self.arquivos_selecionados[:3])
        if len(self.arquivos_selecionados) > 3:
            nomes += ", ..."
        self.pasta_var.set(f"({len(self.arquivos_selecionados)} arquivos) {nomes}")

    def escolher_pasta(self) -> None:
        pasta = filedialog.askdirectory(title="Escolha a pasta com os arquivos")
        if pasta:
            self.pasta_var.set(pasta)
            self.arquivos_selecionados.clear()

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

    def escrever_log(self, texto: str) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("1.0", texto)
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

        self.btn_converter.configure(state="disabled")
        self.btn_abrir.configure(state="disabled")
        self.escrever_log("Convertendo, aguarde...\n")

        if self.modo_var.get() == "arquivos":
            arquivos = list(self.arquivos_selecionados)
            threading.Thread(target=self._executar_conversao_arquivos, args=(arquivos,), daemon=True).start()
        else:
            pasta = Path(self.pasta_var.get().strip())
            threading.Thread(target=self._executar_conversao_pasta, args=(pasta,), daemon=True).start()

    def _finalizar_conversao(self, convertidos: int, mensagens: list[str], pasta_saida: Path | None) -> None:
        texto = "\n".join(mensagens)
        self.escrever_log(texto)
        self.btn_converter.configure(state="normal")
        if convertidos > 0 and pasta_saida:
            self.ultima_pasta_saida = pasta_saida
            self.btn_abrir.configure(state="normal")
            messagebox.showinfo(
                "Conversão finalizada",
                "A conversão terminou.\n\n"
                "Veja o campo \"Resultado\" abaixo para saber o que foi convertido, "
                "o que já existia e o que deu erro.",
            )
        elif convertidos == 0:
            messagebox.showwarning("Nada foi convertido", resumo_final_vazio(mensagens))

    def _executar_conversao_pasta(self, pasta: Path) -> None:
        convertidos, mensagens, pasta_saida = converter_pasta(pasta)
        self.after(0, lambda: self._finalizar_conversao(convertidos, mensagens, pasta_saida))

    def _executar_conversao_arquivos(self, arquivos: list[Path]) -> None:
        convertidos, mensagens, pasta_saida = converter_lista(arquivos)
        self.after(0, lambda: self._finalizar_conversao(convertidos, mensagens, pasta_saida))


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
