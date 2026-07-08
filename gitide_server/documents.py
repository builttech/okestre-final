import os
import json
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import re

# Cores do Tema Corporate (Clean Black & White / Gray)
COLOR_PRIMARY = RGBColor(0, 0, 0)        # Preto puro para títulos
COLOR_SECONDARY = RGBColor(75, 85, 99)  # Cinza escuro para metadados/legendas (#4B5563)
COLOR_TEXT = RGBColor(17, 24, 39)        # Quase preto para o texto principal (#111827)
COLOR_LIGHT_BG = "F9FAFB"                # Cinza muito claro (#F9FAFB)
COLOR_BORDER = "D1D5DB"                  # Cinza claro para bordas (#D1D5DB)

def set_cell_background(cell, color_hex):
    """Define a cor de fundo de uma célula da tabela usando XML do Word."""
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_callout_borders(cell, border_color_hex):
    """Define borda esquerda mais fina e remove as outras bordas (estilo Callout)."""
    borders_xml = f'''
    <w:tcBorders {nsdecls("w")}>
        <w:top w:val="none"/>
        <w:left w:val="single" w:sz="12" w:space="0" w:color="{border_color_hex}"/>
        <w:bottom w:val="none"/>
        <w:right w:val="none"/>
    </w:tcBorders>
    '''
    cell._tc.get_or_add_tcPr().append(parse_xml(borders_xml))

def format_run(run, font_name="Calibri", size_pt=11, color=COLOR_TEXT, bold=False, italic=False):
    """Auxiliar para aplicar fontes e formatações a um run de texto."""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.color.rgb = color
    run.bold = bold
    run.italic = italic

def add_markdown_runs(paragraph, text, font_name="Calibri", size_pt=10, color=COLOR_TEXT, bold=False, italic=False):
    """Analisa marcações markdown simples em um texto e insere múltiplos runs no parágrafo."""
    # Pattern: ***bolditalic***, **bold**, *italic*, `code`
    pattern = re.compile(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|`.*?`)')
    parts = pattern.split(text)
    
    for part in parts:
        if not part:
            continue
        
        is_bold = bold
        is_italic = italic
        run_font = font_name
        run_color = color
        
        if part.startswith('***') and part.endswith('***') and len(part) >= 6:
            txt = part[3:-3]
            is_bold = True
            is_italic = True
        elif part.startswith('**') and part.endswith('**') and len(part) >= 4:
            txt = part[2:-2]
            is_bold = True
        elif part.startswith('*') and part.endswith('*') and len(part) >= 2:
            txt = part[1:-1]
            is_italic = True
        elif part.startswith('`') and part.endswith('`') and len(part) >= 2:
            txt = part[1:-1]
            run_font = "Consolas"
            run_color = RGBColor(55, 65, 81)
        else:
            txt = part
            
        run = paragraph.add_run(txt)
        format_run(run, font_name=run_font, size_pt=size_pt, color=run_color, bold=is_bold, italic=is_italic)

def parse_markdown_table(md_str):
    """Tenta converter uma string de tabela Markdown em uma matriz (lista de listas)."""
    lines = md_str.strip().split('\n')
    data = []
    for line in lines:
        line = line.strip()
        # Ignora linhas de separador de cabeçalho
        if not line or line.startswith('|-') or '-|-' in line:
            continue
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        if line:
            row = [cell.strip() for cell in line.split('|')]
            data.append(row)
    return data

def generate_docx(project_path: str, title: str, sections: list, filename: str = None) -> dict:
    """
    Gera um arquivo Word (.docx) estruturado e com design premium.
    Retorna um dicionário contendo informações do arquivo criado.
    """
    # Garante a existência do diretório .documents
    docs_dir = os.path.join(project_path, ".documents")
    os.makedirs(docs_dir, exist_ok=True)
    
    # Cria o Documento
    doc = Document()
    
    # Configura margens (2.5 cm / 1 polegada)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    # --- CABEÇALHO DO DOCUMENTO (CAPA / TÍTULO PRINCIPAL) ---
    title_p = doc.add_heading(title, level=0)
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in title_p.runs:
        format_run(r, font_name="Arial", size_pt=20, color=COLOR_PRIMARY, bold=True)
    title_p.paragraph_format.space_after = Pt(4)
    
    # Linha divisória colorida abaixo do título
    divider_table = doc.add_table(rows=1, cols=1)
    divider_cell = divider_table.rows[0].cells[0]
    set_cell_background(divider_cell, "000000")
    # Reduz altura da linha
    divider_table.rows[0].height = Pt(1.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(16) # Espaço
    
    # --- METADADOS ---
    meta_p = doc.add_paragraph()
    meta_run = meta_p.add_run(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nGerado via: Agente Act IA software engineer")
    format_run(meta_run, font_name="Calibri", size_pt=8.5, color=COLOR_SECONDARY, italic=True)
    meta_p.paragraph_format.space_after = Pt(20)
    
    # --- SEÇÕES ---
    processed_sections = []
    for sec in sections:
        sec_type = sec.get("type", "paragraph").strip().lower()
        if sec_type == "paragraph":
            heading = sec.get("heading", "").strip()
            if heading:
                processed_sections.append({"type": "paragraph", "heading": heading, "text": ""})
            
            body = sec.get("text", "").strip()
            if not body:
                continue
                
            lines = body.split('\n')
            current_block = []
            block_type = "text"
            
            def flush_block():
                if not current_block: return
                text = "\n".join(current_block).strip()
                if text:
                    if block_type == "table":
                        processed_sections.append({"type": "table", "text": text})
                    elif block_type == "quote":
                        clean = "\n".join(l.lstrip('> ').strip() for l in current_block)
                        processed_sections.append({"type": "highlight", "text": clean})
                    elif block_type == "hr":
                        processed_sections.append({"type": "hr", "text": ""})
                    else:
                        processed_sections.append({"type": "paragraph", "text": text})
                current_block.clear()
                
            for line in lines:
                sline = line.strip()
                if sline.startswith('---') and len(sline) >= 3 and sline.count('-') == len(sline):
                    flush_block()
                    block_type = "hr"
                    current_block.append(sline)
                    flush_block()
                    block_type = "text"
                elif sline.startswith('|') and sline.endswith('|'):
                    if block_type != "table": 
                        flush_block()
                        block_type = "table"
                    current_block.append(sline)
                elif sline.startswith('>'):
                    if block_type != "quote": 
                        flush_block()
                        block_type = "quote"
                    current_block.append(sline)
                elif sline.startswith('#'):
                    flush_block()
                    block_type = "heading"
                    current_block.append(sline)
                    flush_block()
                    block_type = "text"
                elif sline == "":
                    flush_block()
                    block_type = "text"
                else:
                    if block_type != "text": 
                        flush_block()
                        block_type = "text"
                    current_block.append(sline)
            flush_block()
        else:
            processed_sections.append(sec)

    for sec in processed_sections:
        heading_text = sec.get("heading", "").strip()
        body_text = sec.get("text", "").strip()
        sec_type = sec.get("type", "paragraph").strip().lower()

        if sec_type == "page_break":
            doc.add_page_break()
            continue
            
        elif sec_type == "hr":
            doc.add_paragraph().paragraph_format.space_after = Pt(16)
            continue
        
        # 1. Adiciona título da seção se houver
        if heading_text:
            h_p = doc.add_heading(heading_text, level=1)
            for r in h_p.runs:
                format_run(r, font_name="Arial", size_pt=14, color=COLOR_PRIMARY, bold=True)
            h_p.paragraph_format.space_before = Pt(14)
            h_p.paragraph_format.space_after = Pt(6)
            h_p.paragraph_format.keep_with_next = True
            
        # 2. Adiciona o conteúdo com base no tipo
        if not body_text:
            continue
            
        if sec_type == "paragraph":
            if body_text.startswith('#'):
                level = 0
                while level < len(body_text) and body_text[level] == '#':
                    level += 1
                level = min(level, 4)
                txt = body_text[level:].strip()
                p = doc.add_heading(txt, level=level)
                for r in p.runs:
                    format_run(r, font_name="Arial", size_pt=15-level, color=COLOR_PRIMARY, bold=True)
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.keep_with_next = True
            else:
                p = doc.add_paragraph()
                add_markdown_runs(p, body_text, font_name="Calibri", size_pt=10, color=COLOR_TEXT)
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(8)
            
        elif sec_type == "bullet":
            # Suporta múltiplas linhas separadas por quebra de linha como múltiplos itens de lista
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]
            for line in lines:
                # Remove marcador existente do markdown se colado acidentalmente
                if line.startswith("- ") or line.startswith("* "):
                    line = line[2:]
                p = doc.add_paragraph(style='List Bullet')
                add_markdown_runs(p, line, font_name="Calibri", size_pt=10, color=COLOR_TEXT)
                p.paragraph_format.space_after = Pt(3)
                
        elif sec_type == "highlight":
            # Caixa de destaque (Callout box): tabela de 1 célula com borda esquerda
            tbl = doc.add_table(rows=1, cols=1)
            tbl.autofit = False
            tbl.columns[0].width = Inches(6.5)
            
            cell = tbl.rows[0].cells[0]
            set_cell_background(cell, COLOR_LIGHT_BG)
            set_callout_borders(cell, "9CA3AF") # Borda cinza neutro
            
            # Espaçamento interno da célula
            p = cell.paragraphs[0]
            p.paragraph_format.left_indent = Inches(0.15)
            p.paragraph_format.right_indent = Inches(0.15)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            
            add_markdown_runs(p, body_text, font_name="Calibri", size_pt=9.5, color=COLOR_SECONDARY, italic=True)
            
            # Espaço após a tabela
            space_p = doc.add_paragraph()
            space_p.paragraph_format.space_before = Pt(4)
            space_p.paragraph_format.space_after = Pt(4)
            
        elif sec_type == "code":
            # Bloco de código: caixa cinza claro com fonte monoespaçada e bordas finas cinzas
            tbl = doc.add_table(rows=1, cols=1)
            tbl.autofit = False
            tbl.columns[0].width = Inches(6.5)
            
            cell = tbl.rows[0].cells[0]
            set_cell_background(cell, "F9FAFB") # gray-50
            
            borders_xml = f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>
                <w:left w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>
            </w:tcBorders>
            '''
            cell._tc.get_or_add_tcPr().append(parse_xml(borders_xml))
            
            p = cell.paragraphs[0]
            p.paragraph_format.left_indent = Inches(0.1)
            p.paragraph_format.right_indent = Inches(0.1)
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(5)
            
            run = p.add_run(body_text)
            format_run(run, font_name="Consolas", size_pt=9, color=RGBColor(55, 65, 81))
            
            # Espaço após a tabela
            space_p = doc.add_paragraph()
            space_p.paragraph_format.space_before = Pt(4)
            space_p.paragraph_format.space_after = Pt(4)
            
        elif sec_type == "table":
            try:
                # Tenta como JSON primeiro
                if body_text.startswith('[') or body_text.startswith('{'):
                    try:
                        data_matrix = json.loads(body_text)
                    except json.JSONDecodeError:
                        data_matrix = parse_markdown_table(body_text)
                else:
                    data_matrix = parse_markdown_table(body_text)
                    
                if not isinstance(data_matrix, list) or len(data_matrix) == 0:
                    raise ValueError("Tabela vazia ou inválida")
                    
                rows_count = len(data_matrix)
                cols_count = max(len(row) for row in data_matrix if isinstance(row, list))
                
                tbl = doc.add_table(rows=rows_count, cols=cols_count)
                tbl.style = 'Table Grid'
                
                for r_idx, row_data in enumerate(data_matrix):
                    row = tbl.rows[r_idx]
                    is_header = (r_idx == 0)
                    
                    if is_header:
                        row.height = Pt(20)
                    else:
                        row.height = Pt(18)
                        
                    for c_idx, cell_val in enumerate(row_data):
                        if c_idx >= cols_count:
                            continue
                        cell = row.cells[c_idx]
                        
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(3)
                        p.paragraph_format.space_after = Pt(3)
                        
                        if is_header:
                            set_cell_background(cell, "374151")
                            add_markdown_runs(p, str(cell_val), font_name="Arial", size_pt=9.5, color=RGBColor(255, 255, 255), bold=True)
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        else:
                            if r_idx % 2 == 1:
                                set_cell_background(cell, COLOR_LIGHT_BG)
                            add_markdown_runs(p, str(cell_val), font_name="Calibri", size_pt=9.5, color=COLOR_TEXT)
                            
                space_p = doc.add_paragraph()
                space_p.paragraph_format.space_after = Pt(10)
                
            except Exception as e:
                p = doc.add_paragraph()
                run = p.add_run(f"[Tabela inválida: não foi possível extrair os dados]")
                format_run(run, font_name="Calibri", size_pt=10, color=RGBColor(239, 68, 68), italic=True)
                p.paragraph_format.space_after = Pt(8)
                
    # --- SALVAMENTO ---
    # Normaliza o título para o nome do arquivo
    if filename:
        filename = os.path.basename(filename)
        if not filename.lower().endswith(".docx"):
            filename = f"{filename}.docx"
    else:
        safe_title = "".join([c if c.isalnum() else "_" for c in title]).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.docx"
    filepath = os.path.join(docs_dir, filename)
    
    doc.save(filepath)
    
    return {
        "status": "success",
        "filename": filename,
        "filepath": filepath,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "size_bytes": os.path.getsize(filepath)
    }

def parse_docx_to_json(filepath: str) -> dict:
    """
    Analisa um arquivo .docx e reconstrói sua estrutura em um JSON
    compatível com a criação (para prévia em tempo real).
    """
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    doc = Document(filepath)
    sections = []
    title = "Documento"
    
    body_element = doc.element.body
    is_first_paragraph = True
    
    for child in body_element.iterchildren():
        if child.tag.endswith('p'):
            # É um parágrafo
            p = Paragraph(child, doc)
            text = p.text.strip()
            if not text:
                continue
                
            # Verifica se é o título do documento (heurística do primeiro parágrafo)
            if is_first_paragraph:
                is_first_paragraph = False
                if p.style.name == 'Title' or (p.runs and p.runs[0].font.size and p.runs[0].font.size.pt > 20):
                    title = text
                    continue
            
            # Subtítulos / Títulos de seção
            if p.style.name.startswith('Heading') or (p.runs and p.runs[0].bold and p.runs[0].font.size and p.runs[0].font.size.pt >= 14):
                sections.append({
                    "heading": text,
                    "text": "",
                    "type": "paragraph"
                })
                continue
            
            # Se for um item de lista
            sec_type = "paragraph"
            if p.style.name.startswith('List Bullet') or p.style.name.startswith('List'):
                sec_type = "bullet"
                
            # Adiciona ao texto da última seção se ela não tiver conteúdo, ou cria nova
            if sections and sections[-1]["text"] == "" and sections[-1]["type"] == "paragraph" and sec_type == "paragraph":
                sections[-1]["text"] = text
            else:
                sections.append({
                    "heading": "",
                    "text": text,
                    "type": sec_type
                })
                
        elif child.tag.endswith('tbl'):
            # É uma tabela
            t = Table(child, doc)
            if len(t.rows) == 1 and len(t.columns) == 1:
                # Callout ou Code
                cell = t.rows[0].cells[0]
                text = cell.text.strip()
                
                sec_type = "highlight"
                # Heurística para detectar bloco de código pelo background ou fonte Consolas
                tcPr = cell._tc.get_or_add_tcPr()
                shd = tcPr.find(qn('w:shd'))
                if shd is not None:
                    fill = shd.get(qn('w:fill'))
                    if fill == "F1F5F9": # slate-100 (código)
                        sec_type = "code"
                
                # Se houver runs, verifica fonte Consolas
                if cell.paragraphs and cell.paragraphs[0].runs:
                    font_name = cell.paragraphs[0].runs[0].font.name
                    if font_name == "Consolas":
                        sec_type = "code"
                        
                sections.append({
                    "heading": "",
                    "text": text,
                    "type": sec_type
                })
            else:
                # Tabela de dados normal
                table_data = []
                for row in t.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    # Ignora linhas totalmente vazias de preenchimento do Word
                    if any(row_data):
                        table_data.append(row_data)
                
                sections.append({
                    "heading": "",
                    "text": json.dumps(table_data),
                    "type": "table"
                })
                
    return {
        "title": title,
        "sections": sections
    }
