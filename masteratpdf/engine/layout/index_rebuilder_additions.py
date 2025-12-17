    def _convert_paragraph_to_hyperlink_preserve_format(self, para, bookmark_name):
        """
        Convierte párrafo en hyperlink PRESERVANDO tab stops y formato.
        
        Esto es crítico para mantener los puntos guía.
        """
        from docx.oxml import OxmlElement
        from docx.oxml.shared import qn
        
        # Extraer el texto antes del tab
        full_text = para.text
        parts = full_text.split('\t')
        if len(parts) < 2:
            return  # No hay tab, no hacer nada
        
        title_text = parts[0].strip()
        page_text = parts[1].strip()
        
        # Guardar formato del tab stop
        tab_stops = list(para.paragraph_format.tab_stops)
        indent = para.paragraph_format.left_indent
        
        # Limpiar párrafo
        p = para._p
        for run in list(para.runs):
            run._element.getparent().remove(run._element)
        
        # Recrear con hyperlink
        hyperlink = OxmlElement('w:hyperlink')
        hyperlink.set(qn('w:anchor'), bookmark_name)
        
        # Run con título (dentro del hyperlink)
        run1 = OxmlElement('w:r')
        rPr1 = OxmlElement('w:rPr')
        
        # Color azul + underline para hyperlink
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        color = OxmlElement('w:color')
        color.set(qn('w:val'), '0000FF')
        
        rPr1.append(u)
        rPr1.append(color)
        run1.append(rPr1)
        
        t1 = OxmlElement('w:t')
        t1.set(qn('xml:space'), 'preserve')
        t1.text = title_text
        run1.append(t1)
        
        hyperlink.append(run1)
        p.append(hyperlink)
        
        # Tab (FUERA del hyperlink)
        run_tab = OxmlElement('w:r')
        tab = OxmlElement('w:tab')
        run_tab.append(tab)
        p.append(run_tab)
        
        # Número de página (FUERA del hyperlink)
        run2 = OxmlElement('w:r')
        t2 = OxmlElement('w:t')
        t2.text = page_text
        run2.append(t2)
        p.append(run2)
        
        # Restaurar tab stops
        para.paragraph_format.left_indent = indent
        for tab_stop in tab_stops:
            para.paragraph_format.tab_stops.add_tab_stop(
                tab_stop.position,
                tab_stop.alignment,
                tab_stop.leader
            )
