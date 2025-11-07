from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

def generar_pdf_reporte(accesos, tipo_reporte, fecha_inicio, fecha_fin, titulo="Reporte de Accesos"):
    """Generar PDF del reporte de accesos"""
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30)
    
    # Lista de elementos del PDF
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Título
    title = Paragraph(titulo, title_style)
    elements.append(title)
    
    # Información del reporte
    info_text = f"""
    <b>Tipo de Reporte:</b> {tipo_reporte.capitalize()}<br/>
    <b>Período:</b> {fecha_inicio} {f' al {fecha_fin}' if tipo_reporte == 'mensual' else ''}<br/>
    <b>Generado el:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>
    <b>Total de registros:</b> {len(accesos)}
    """
    
    info_paragraph = Paragraph(info_text, styles['Normal'])
    elements.append(info_paragraph)
    elements.append(Spacer(1, 20))
    
    # Tabla de datos
    if accesos:
        # Encabezados de la tabla
        data = [['Fecha/Hora', 'Visitante', 'Tipo', 'Autorizado', 'Guardia']]
        
        # Datos
        for acceso in accesos:
            fecha_str = acceso['fecha_hora'].strftime('%Y-%m-%d %H:%M')
            visitante = acceso.get('visitante', 'N/A')
            tipo = acceso['tipo'].capitalize()
            autorizado = 'Sí' if acceso['autorizado'] else 'No'
            guardia = acceso.get('guardia', 'Sistema')
            
            data.append([fecha_str, visitante, tipo, autorizado, guardia])
        
        # Crear tabla
        table = Table(data, colWidths=[1.5*inch, 2*inch, 0.8*inch, 0.8*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
    else:
        no_data = Paragraph("<b>No hay registros para el período seleccionado</b>", styles['Normal'])
        elements.append(no_data)
    
    # Generar PDF
    doc.build(elements)
    
    # Obtener contenido del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def generar_pdf_credencial(visitante, codigo):
    """Generar PDF de credencial para visitante"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(300, 400), topMargin=20)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CredencialTitle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1
    )
    
    # Título
    title = Paragraph("CREDENCIAL DE ACCESO", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Información del visitante
    info_text = f"""
    <b>Nombre:</b> {visitante['nombre']}<br/>
    <b>Identificación:</b> {visitante['identificacion']}<br/>
    <b>Empresa:</b> {visitante.get('empresa', 'N/A')}<br/>
    <b>Motivo:</b> {visitante.get('motivo', 'N/A')}<br/>
    <b>Fecha de registro:</b> {visitante['fecha_registro'].strftime('%Y-%m-%d')}
    """
    
    info_paragraph = Paragraph(info_text, styles['Normal'])
    elements.append(info_paragraph)
    elements.append(Spacer(1, 30))
    
    # Código de acceso (grande y destacado)
    codigo_style = ParagraphStyle(
        'CodigoStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.red,
        alignment=1
    )
    
    codigo_paragraph = Paragraph(f"<b>{codigo}</b>", codigo_style)
    elements.append(codigo_paragraph)
    
    # Instrucciones
    elements.append(Spacer(1, 20))
    instrucciones = Paragraph(
        "<i>Presentar esta credencial al guardia de seguridad para ingresar a las instalaciones</i>",
        styles['Italic']
    )
    elements.append(instrucciones)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def generar_pdf_estadisticas(estadisticas, accesos_7_dias, visitantes_frecuentes):
    """Generar PDF de reporte de estadísticas"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1
    )
    
    # Título
    title = Paragraph("Reporte de Estadísticas - Sistema de Control de Acceso", title_style)
    elements.append(title)
    
    # Información del reporte
    info_text = f"""
    <b>Generado el:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>
    <b>Período analizado:</b> Últimos 7 días
    """
    
    info_paragraph = Paragraph(info_text, styles['Normal'])
    elements.append(info_paragraph)
    elements.append(Spacer(1, 20))
    
    # Estadísticas generales
    stats_title = Paragraph("<b>Estadísticas Generales</b>", styles['Heading2'])
    elements.append(stats_title)
    
    stats_data = [
        ['Visitantes Activos', estadisticas.get('visitantes_activos', 0)],
        ['Usuarios Activos', estadisticas.get('usuarios_activos', 0)],
        ['Accesos Hoy', estadisticas.get('accesos_hoy', 0)],
        ['Alertas Hoy', estadisticas.get('alertas_hoy', 0)],
        ['Credenciales Activas', estadisticas.get('credenciales_activas', 0)]
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # Accesos últimos 7 días
    if accesos_7_dias:
        accesos_title = Paragraph("<b>Accesos - Últimos 7 Días</b>", styles['Heading2'])
        elements.append(accesos_title)
        
        accesos_data = [['Fecha', 'Total', 'Entradas', 'Salidas', 'Denegados']]
        for acceso in accesos_7_dias:
            accesos_data.append([
                acceso['fecha'].strftime('%Y-%m-%d'),
                acceso['total'],
                acceso['entradas'],
                acceso['salidas'],
                acceso['denegados']
            ])
        
        accesos_table = Table(accesos_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        accesos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(accesos_table)
        elements.append(Spacer(1, 20))
    
    # Visitantes más frecuentes
    if visitantes_frecuentes:
        visitantes_title = Paragraph("<b>Visitantes Más Frecuentes</b>", styles['Heading2'])
        elements.append(visitantes_title)
        
        visitantes_data = [['Visitante', 'Empresa', 'Total Visitas']]
        for visitante in visitantes_frecuentes:
            visitantes_data.append([
                visitante['nombre'],
                visitante.get('empresa', 'N/A'),
                visitante['total_visitas']
            ])
        
        visitantes_table = Table(visitantes_data, colWidths=[2*inch, 2*inch, 1*inch])
        visitantes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(visitantes_table)
    
    # Generar PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf