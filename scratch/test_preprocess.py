def preprocess_sections(sections):
    processed = []
    for sec in sections:
        sec_type = sec.get("type", "paragraph").strip().lower()
        if sec_type == "paragraph":
            heading = sec.get("heading", "").strip()
            if heading:
                processed.append({"type": "paragraph", "heading": heading, "text": ""})
            
            body = sec.get("text", "").strip()
            if not body:
                continue
                
            lines = body.split('\n')
            current_block = []
            block_type = "text"
            
            def flush():
                nonlocal current_block, block_type
                if not current_block: return
                text = "\n".join(current_block).strip()
                if text:
                    if block_type == "table":
                        processed.append({"type": "table", "text": text})
                    elif block_type == "quote":
                        clean = "\n".join(l.lstrip('> ').strip() for l in current_block)
                        processed.append({"type": "highlight", "text": clean})
                    elif block_type == "hr":
                        processed.append({"type": "hr", "text": ""})
                    else:
                        processed.append({"type": "paragraph", "text": text})
                current_block = []
                block_type = "text"
                
            for line in lines:
                sline = line.strip()
                if sline.startswith('---') and len(sline) >= 3 and sline.count('-') == len(sline):
                    flush()
                    block_type = "hr"
                    current_block = [sline]
                    flush()
                elif sline.startswith('|') and sline.endswith('|'):
                    if block_type != "table": flush(); block_type = "table"
                    current_block.append(sline)
                elif sline.startswith('>'):
                    if block_type != "quote": flush(); block_type = "quote"
                    current_block.append(sline)
                elif sline.startswith('#'):
                    flush()
                    block_type = "heading"
                    current_block = [sline]
                    flush()
                elif sline == "":
                    flush()
                else:
                    if block_type != "text": flush(); block_type = "text"
                    current_block.append(sline)
            flush()
        else:
            processed.append(sec)
    return processed

sections = [
    {"type": "paragraph", "heading": "Test", "text": "> This is a quote\n> Second line\n\nSome text\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n---\n\n# Heading inside\nText"}
]
print(preprocess_sections(sections))
