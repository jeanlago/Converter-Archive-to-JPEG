"""Traduções PT/EN do conversor."""

from __future__ import annotations

import locale

TRADUCOES: dict[str, dict[str, str]] = {
    "pt": {
        "app_title": "Conversor para JPEG",
        "header_title": "🖼️  Conversor para JPEG",
        "header_subtitle": "Transforme arquivos baixados em imagens prontas para abrir",
        "credits": "Feito por Jean, irmã de Thalyta Marins backoffice",
        "contact": "Contato: jeanlago203@gmail.com",
        "status_ready": "Pronto para converter",
        "status_converting": "Convertendo arquivos...",
        "status_success": "Conversão finalizada com sucesso!",
        "status_none": "Nenhum arquivo foi convertido.",
        "status_files_ready": "{n} arquivo(s) prontos para converter",
        "status_folder_ready": "Pasta selecionada. Clique em converter.",
        "badge_files": "  {n} arquivo(s) selecionado(s)  ",
        "badge_folder": "  Pasta selecionada  ",
        "section_instructions": "Instruções",
        "section_mode": "O que converter?",
        "section_selection": "Seleção",
        "section_actions": "Ações",
        "section_result": "Resultado",
        "instructions": """Como usar:

1. Baixe os arquivos do sistema (geralmente vêm só como "arquivo", sem extensão).
2. Escolha uma opção:
   - Pasta inteira: converte só arquivos "arquivo" ou sem extensão.
   - Arquivos escolhidos: selecione um ou vários arquivos (Ctrl+clique).
3. Clique em "Converter arquivos".
4. Clique em "Abrir pasta convertidos" para ver os JPEGs prontos.

Proteções:
- Na pasta, arquivos comuns (PDF, ZIP, fotos .png etc.) são ignorados.
- Se a imagem já foi convertida antes, ela não é convertida de novo.

Os JPEGs ficam na subpasta "convertidos", dentro da pasta escolhida.""",
        "hide_instructions": "▼  Ocultar instruções",
        "show_instructions": "▶  Mostrar instruções",
        "mode_folder": "📁  Pasta inteira",
        "mode_files": "📄  Arquivos escolhidos (um ou vários)",
        "select_folder_hint": "Escolha a pasta com os arquivos baixados",
        "select_files_hint": "Escolha um ou vários arquivos (Ctrl+clique para marcar vários)",
        "no_file_selected": "Nenhum arquivo selecionado",
        "files_summary": "({n} arquivos) {names}",
        "btn_choose_folder": "Escolher pasta",
        "btn_choose_files": "Escolher arquivos...",
        "btn_convert": "✨  Converter arquivos",
        "btn_open_output": "📂  Abrir pasta convertidos",
        "log_waiting": "Aguardando conversão...",
        "dialog_choose_folder": "Escolha a pasta com os arquivos",
        "dialog_choose_files": "Escolha os arquivos para converter (Ctrl+clique para vários)",
        "filetype_all": "Todos os arquivos",
        "filetype_images": "Imagens",
        "err_no_files_title": "Nenhum arquivo selecionado",
        "err_no_files_body": (
            "Você marcou \"Arquivos escolhidos\", mas nenhum arquivo foi selecionado.\n\n"
            "O que fazer:\n"
            "1. Clique em \"Escolher arquivos...\"\n"
            "2. Selecione um ou vários arquivos (Ctrl+clique para marcar vários)\n"
            "3. Clique em \"Converter arquivos\""
        ),
        "err_no_folder_title": "Nenhuma pasta selecionada",
        "err_no_folder_body": (
            "Você marcou \"Pasta inteira\", mas ainda não escolheu uma pasta.\n\n"
            "O que fazer:\n"
            "1. Clique em \"Escolher pasta\"\n"
            "2. Selecione onde estão os arquivos baixados\n"
            "3. Clique em \"Converter arquivos\""
        ),
        "err_folder_missing_title": "Pasta não encontrada",
        "err_folder_missing_body": (
            "A pasta informada não existe:\n{path}\n\n"
            "Motivo: o caminho pode estar errado ou a pasta foi movida/excluída.\n\n"
            "O que fazer:\n"
            "- Clique em \"Escolher pasta\" e selecione novamente."
        ),
        "err_not_folder_title": "Caminho inválido",
        "err_not_folder_body": (
            "O caminho informado não é uma pasta:\n{path}\n\n"
            "Motivo: você pode ter selecionado um arquivo em vez de uma pasta.\n\n"
            "O que fazer:\n"
            "- Use \"Escolher pasta\" para selecionar a pasta correta,\n"
            "  ou mude para \"Arquivos escolhidos\"."
        ),
        "info_nothing_open_title": "Nada para abrir",
        "info_nothing_open_body": (
            "Ainda não existe pasta convertidos para abrir.\n\n"
            "Motivo: nenhuma conversão foi concluída com sucesso até agora.\n"
            "Converta pelo menos um arquivo e tente novamente."
        ),
        "warn_nothing_converted_title": "Nada foi convertido",
        "warn_nothing_converted_body": (
            "Nenhum arquivo novo foi convertido.\n\n"
            "Veja o campo \"Resultado\" abaixo para entender o motivo de cada item."
        ),
        "err_folder_not_found": "Erro: pasta não encontrada.",
        "converting_eligible": "Convertendo {n} arquivo(s) elegível(is)...",
        "converting_selected": "Convertendo {n} arquivo(s) selecionado(s)...",
        "processing": "⏳ Processando {i}/{total}: {name}",
        "summary": "Resumo: {ok} convertido(s), {skip} já existente(s), {err} com erro.",
        "saved_to": "Salvos em:",
        "converted_folders": "Pastas convertidos:",
        "none_converted_all_failed": "Nenhum arquivo foi convertido porque todos falharam ou foram rejeitados.",
        "reason_prefix": "Motivo:",
        "err_invalid_image": (
            "Motivo: o conteúdo deste arquivo não é uma imagem válida. "
            "Ele pode ter sido corrompido no download, estar incompleto ou não ser uma foto."
        ),
        "err_permission": (
            "Motivo: o Windows bloqueou a leitura ou gravação deste arquivo. "
            "Feche programas que possam estar usando o arquivo e tente novamente."
        ),
        "err_disk_full": (
            "Motivo: não há espaço livre suficiente no disco. "
            "Apague arquivos desnecessários e tente novamente."
        ),
        "err_not_found": (
            "Motivo: o arquivo não foi encontrado. "
            "Ele pode ter sido movido, renomeado ou excluído antes da conversão."
        ),
        "err_corrupt": (
            "Motivo: a imagem parece estar incompleta ou danificada. "
            "Tente baixar o arquivo novamente no sistema."
        ),
        "err_generic": "Motivo: não foi possível converter este arquivo. Detalhe técnico: {detail}",
        "err_already_converted": (
            "Motivo: este arquivo já foi convertido antes. "
            "O JPEG correspondente já existe em convertidos ({name}). "
            "Nada foi alterado para evitar duplicar a mesma imagem."
        ),
        "folder_path": "Caminho informado: {path}",
        "what_to_do": "O que fazer:",
        "pick_folder_again": "- Clique em \"Escolher pasta\" e selecione novamente a pasta correta.",
        "check_folder_moved": "- Verifique se a pasta não foi movida ou excluída.",
        "no_eligible_title": "Nenhum arquivo elegível foi encontrado nesta pasta.",
        "folder_mode_rules": "Na opção \"Pasta inteira\", só convertemos arquivos:",
        "rule_no_ext": '- sem extensão (ex.: "arquivo")',
        "rule_arquivo_name": '- ou com nome "arquivo", "arquivo (1)" etc.',
        "found_summary": "Resumo do que foi encontrado:",
        "ignored_by_name": "- {n} arquivo(s) ignorado(s) por nome ou extensão (ex.: {examples})",
        "ignored_by_name_hint": "  Esses arquivos não parecem ser downloads do sistema no formato esperado.",
        "already_jpeg": "- {n} arquivo(s) já estão em JPEG e não precisam ser convertidos.",
        "not_image_content": "- {n} arquivo(s) sem extensão/nome válido, mas com conteúdo que não é imagem (ex.: {examples})",
        "not_image_hint": "  Isso pode indicar download incompleto ou arquivo corrompido.",
        "ignored_internal": "- {n} item(ns) ignorado(s) por serem arquivos do próprio conversor ou da pasta convertidos.",
        "folder_empty": "- A pasta está vazia ou não contém arquivos comuns de download.",
        "confirm_downloads_here": "- Confirme se os arquivos baixados realmente estão nesta pasta.",
        "use_file_mode": "- Se forem outros tipos de arquivo, use \"Arquivos escolhidos\".",
        "redownload": "- Se o download veio corrompido, baixe novamente no sistema.",
        "none_selected_valid_title": "Nenhum dos arquivos selecionados pôde ser convertido.",
        "each_file_reason": "Motivo de cada arquivo:",
        "invalid_or_missing": "- {name}: não é um arquivo válido ou não foi encontrado.",
        "internal_ignored": "- {name}: é um arquivo interno do conversor e foi ignorado.",
        "already_jpeg_file": "- {name}: já é JPEG. Não é necessário converter novamente.",
        "unsupported_ext": "- {name}: extensão \"{ext}\" não é de imagem suportada.",
        "not_accepted": "- {name}: não pôde ser aceito para conversão.",
        "select_downloads_or_images": "- Selecione arquivos baixados do sistema ou imagens (.png, .webp etc.).",
        "jpeg_skip": "- Arquivos que já são .jpeg não precisam ser convertidos.",
        "try_redownload": "- Se o arquivo veio sem extensão, tente baixá-lo novamente.",
        "lang_pt": "PT",
        "lang_en": "EN",
    },
    "en": {
        "app_title": "JPEG Converter",
        "header_title": "🖼️  JPEG Converter",
        "header_subtitle": "Turn downloaded files into images ready to open",
        "credits": "Made by Jean, Thalyta Marins backoffice's sister",
        "contact": "Contact: jeanlago203@gmail.com",
        "status_ready": "Ready to convert",
        "status_converting": "Converting files...",
        "status_success": "Conversion completed successfully!",
        "status_none": "No files were converted.",
        "status_files_ready": "{n} file(s) ready to convert",
        "status_folder_ready": "Folder selected. Click convert.",
        "badge_files": "  {n} file(s) selected  ",
        "badge_folder": "  Folder selected  ",
        "section_instructions": "Instructions",
        "section_mode": "What to convert?",
        "section_selection": "Selection",
        "section_actions": "Actions",
        "section_result": "Result",
        "instructions": """How to use:

1. Download files from the system (they usually come as "arquivo" with no extension).
2. Choose an option:
   - Entire folder: converts only "arquivo" files or files without extension.
   - Selected files: pick one or more files manually (Ctrl+click).
3. Click "Convert files".
4. Click "Open convertidos folder" to see the JPEGs.

Protections:
- In folder mode, common files (PDF, ZIP, .png photos, etc.) are ignored.
- If an image was already converted, it will not be converted again.

JPEGs are saved in the "convertidos" subfolder inside the chosen folder.""",
        "hide_instructions": "▼  Hide instructions",
        "show_instructions": "▶  Show instructions",
        "mode_folder": "📁  Entire folder",
        "mode_files": "📄  Selected files (one or more)",
        "select_folder_hint": "Choose the folder with downloaded files",
        "select_files_hint": "Choose one or more files (Ctrl+click to select multiple)",
        "no_file_selected": "No file selected",
        "files_summary": "({n} files) {names}",
        "btn_choose_folder": "Choose folder",
        "btn_choose_files": "Choose files...",
        "btn_convert": "✨  Convert files",
        "btn_open_output": "📂  Open convertidos folder",
        "log_waiting": "Waiting for conversion...",
        "dialog_choose_folder": "Choose the folder with files",
        "dialog_choose_files": "Choose files to convert (Ctrl+click for multiple)",
        "filetype_all": "All files",
        "filetype_images": "Images",
        "err_no_files_title": "No file selected",
        "err_no_files_body": (
            "You chose \"Selected files\", but no file was selected.\n\n"
            "What to do:\n"
            "1. Click \"Choose files...\"\n"
            "2. Select one or more files (Ctrl+click for multiple)\n"
            "3. Click \"Convert files\""
        ),
        "err_no_folder_title": "No folder selected",
        "err_no_folder_body": (
            "You chose \"Entire folder\", but no folder was selected yet.\n\n"
            "What to do:\n"
            "1. Click \"Choose folder\"\n"
            "2. Select where the downloaded files are\n"
            "3. Click \"Convert files\""
        ),
        "err_folder_missing_title": "Folder not found",
        "err_folder_missing_body": (
            "The specified folder does not exist:\n{path}\n\n"
            "Reason: the path may be wrong or the folder was moved/deleted.\n\n"
            "What to do:\n"
            "- Click \"Choose folder\" and select again."
        ),
        "err_not_folder_title": "Invalid path",
        "err_not_folder_body": (
            "The specified path is not a folder:\n{path}\n\n"
            "Reason: you may have selected a file instead of a folder.\n\n"
            "What to do:\n"
            "- Use \"Choose folder\" to pick the correct folder,\n"
            "  or switch to \"Selected files\"."
        ),
        "info_nothing_open_title": "Nothing to open",
        "info_nothing_open_body": (
            "There is no convertidos folder to open yet.\n\n"
            "Reason: no conversion has completed successfully so far.\n"
            "Convert at least one file and try again."
        ),
        "warn_nothing_converted_title": "Nothing converted",
        "warn_nothing_converted_body": (
            "No new files were converted.\n\n"
            "See the \"Result\" section below to understand why."
        ),
        "err_folder_not_found": "Error: folder not found.",
        "converting_eligible": "Converting {n} eligible file(s)...",
        "converting_selected": "Converting {n} selected file(s)...",
        "processing": "⏳ Processing {i}/{total}: {name}",
        "summary": "Summary: {ok} converted, {skip} already exist, {err} with errors.",
        "saved_to": "Saved to:",
        "converted_folders": "Convertidos folders:",
        "none_converted_all_failed": "No files were converted because all failed or were rejected.",
        "reason_prefix": "Reason:",
        "err_invalid_image": (
            "Reason: this file content is not a valid image. "
            "It may be corrupted, incomplete, or not a photo."
        ),
        "err_permission": (
            "Reason: Windows blocked reading or writing this file. "
            "Close programs that may be using it and try again."
        ),
        "err_disk_full": (
            "Reason: not enough free disk space. "
            "Delete unnecessary files and try again."
        ),
        "err_not_found": (
            "Reason: file not found. "
            "It may have been moved, renamed, or deleted before conversion."
        ),
        "err_corrupt": (
            "Reason: the image appears incomplete or damaged. "
            "Try downloading the file again from the system."
        ),
        "err_generic": "Reason: could not convert this file. Technical detail: {detail}",
        "err_already_converted": (
            "Reason: this file was already converted before. "
            "The matching JPEG already exists in convertidos ({name}). "
            "Nothing was changed to avoid duplicating the same image."
        ),
        "folder_path": "Specified path: {path}",
        "what_to_do": "What to do:",
        "pick_folder_again": "- Click \"Choose folder\" and select the correct folder again.",
        "check_folder_moved": "- Check whether the folder was moved or deleted.",
        "no_eligible_title": "No eligible files were found in this folder.",
        "folder_mode_rules": "In \"Entire folder\" mode, we only convert files:",
        "rule_no_ext": '- with no extension (e.g. "arquivo")',
        "rule_arquivo_name": '- or named "arquivo", "arquivo (1)", etc.',
        "found_summary": "Summary of what was found:",
        "ignored_by_name": "- {n} file(s) ignored by name or extension (e.g. {examples})",
        "ignored_by_name_hint": "  These files do not look like expected system downloads.",
        "already_jpeg": "- {n} file(s) are already JPEG and do not need conversion.",
        "not_image_content": "- {n} file(s) with valid name/no extension but non-image content (e.g. {examples})",
        "not_image_hint": "  This may indicate an incomplete download or corrupted file.",
        "ignored_internal": "- {n} item(s) ignored because they belong to the converter or convertidos folder.",
        "folder_empty": "- The folder is empty or has no common download files.",
        "confirm_downloads_here": "- Confirm the downloaded files are really in this folder.",
        "use_file_mode": "- For other file types, use \"Selected files\".",
        "redownload": "- If the download was corrupted, download again from the system.",
        "none_selected_valid_title": "None of the selected files could be converted.",
        "each_file_reason": "Reason for each file:",
        "invalid_or_missing": "- {name}: not a valid file or not found.",
        "internal_ignored": "- {name}: internal converter file, ignored.",
        "already_jpeg_file": "- {name}: already JPEG. No need to convert again.",
        "unsupported_ext": "- {name}: extension \"{ext}\" is not a supported image type.",
        "not_accepted": "- {name}: could not be accepted for conversion.",
        "select_downloads_or_images": "- Select system downloads or images (.png, .webp, etc.).",
        "jpeg_skip": "- Files that are already .jpeg do not need conversion.",
        "try_redownload": "- If the file has no extension, try downloading it again.",
        "lang_pt": "PT",
        "lang_en": "EN",
    },
}


def detectar_idioma() -> str:
    try:
        codigo = locale.getdefaultlocale()[0] or ""
        if codigo.lower().startswith("en"):
            return "en"
    except (AttributeError, ValueError, TypeError):
        pass
    return "pt"


class I18n:
    def __init__(self, idioma: str | None = None) -> None:
        self.idioma = idioma if idioma in TRADUCOES else detectar_idioma()

    def t(self, chave: str, **kwargs: object) -> str:
        texto = TRADUCOES[self.idioma].get(chave, TRADUCOES["pt"].get(chave, chave))
        return texto.format(**kwargs) if kwargs else texto

    def set_idioma(self, idioma: str) -> None:
        if idioma in TRADUCOES:
            self.idioma = idioma

    def reason_prefix(self) -> str:
        return self.t("reason_prefix")

    def is_title_line(self, linha: str) -> bool:
        return linha.startswith(("Resumo:", "Summary:", "Convertendo", "Converting"))

    def is_detail_line(self, linha: str) -> bool:
        return (
            linha.startswith(self.reason_prefix())
            or linha.startswith("Motivo:")
            or linha.startswith("Reason:")
            or linha.startswith("    ")
            or linha.startswith("- ")
        )


_i18n = I18n()
