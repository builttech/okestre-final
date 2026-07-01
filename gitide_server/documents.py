import os
import json
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

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
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title_run = title_p.add_run(title)
    format_run(title_run, font_name="Arial", size_pt=20, color=COLOR_PRIMARY, bold=True)
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
    meta_run = meta_p.add_run(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nGerado via: Agente GitIDE")
    format_run(meta_run, font_name="Calibri", size_pt=8.5, color=COLOR_SECONDARY, italic=True)
    meta_p.paragraph_format.space_after = Pt(20)
    
    # --- SEÇÕES ---
    for sec in sections:
        heading_text = sec.get("heading", "").strip()
        body_text = sec.get("text", "").strip()
        sec_type = sec.get("type", "paragraph").strip().lower()

        if sec_type == "page_break":
            doc.add_page_break()
            continue
        
        # 1. Adiciona título da seção se houver
        if heading_text:
            h_p = doc.add_paragraph()
            h_run = h_p.add_run(heading_text)
            format_run(h_run, font_name="Arial", size_pt=13, color=COLOR_PRIMARY, bold=True)
            h_p.paragraph_format.space_before = Pt(14)
            h_p.paragraph_format.space_after = Pt(6)
            h_p.paragraph_format.keep_with_next = True
            
        # 2. Adiciona o conteúdo com base no tipo
        if not body_text:
            continue
            
        if sec_type == "paragraph":
            p = doc.add_paragraph()
            run = p.add_run(body_text)
            format_run(run, font_name="Calibri", size_pt=10, color=COLOR_TEXT)
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
                run = p.add_run(line)
                format_run(run, font_name="Calibri", size_pt=10, color=COLOR_TEXT)
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
            
            run = p.add_run(body_text)
            format_run(run, font_name="Calibri", size_pt=9.5, color=COLOR_SECONDARY, italic=True)
            
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
            # Tenta converter o texto JSON em tabela. Espera uma matriz de dados:
            # [["Coluna 1", "Coluna 2"], ["Dado A", "Dado B"]]
            try:
                data_matrix = json.loads(body_text)
                if not isinstance(data_matrix, list) or len(data_matrix) == 0:
                    raise ValueError("JSON não representa matriz válida")
                    
                rows_count = len(data_matrix)
                cols_count = max(len(row) for row in data_matrix if isinstance(row, list))
                
                tbl = doc.add_table(rows=rows_count, cols=cols_count)
                tbl.style = 'Table Grid'
                
                for r_idx, row_data in enumerate(data_matrix):
                    row = tbl.rows[r_idx]
                    is_header = (r_idx == 0)
                    
                    # Estilo da linha
                    if is_header:
                        row.height = Pt(20)
                    else:
                        row.height = Pt(18)
                        
                    for c_idx, cell_val in enumerate(row_data):
                        if c_idx >= cols_count:
                            continue
                        cell = row.cells[c_idx]
                        
                        # Alinhamento e espaçamento interno
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(3)
                        p.paragraph_format.space_after = Pt(3)
                        
                        run = p.add_run(str(cell_val))
                        
                        if is_header:
                            set_cell_background(cell, "374151") # Cabeçalho cinza escuro
                            format_run(run, font_name="Arial", size_pt=9.5, color=RGBColor(255, 255, 255), bold=True)
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        else:
                            # Linhas alternadas em cinza claro para legibilidade
                            if r_idx % 2 == 1:
                                set_cell_background(cell, COLOR_LIGHT_BG)
                            format_run(run, font_name="Calibri", size_pt=9.5, color=COLOR_TEXT)
                            
                # Espaço após a tabela
                space_p = doc.add_paragraph()
                space_p.paragraph_format.space_after = Pt(10)
                
            except Exception as e:
                # Fallback em caso de falha no parser do JSON
                p = doc.add_paragraph()
                run = p.add_run(f"[Tabela inválida: {body_text}]")
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
