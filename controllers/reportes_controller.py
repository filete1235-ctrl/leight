from flask import render_template, request, redirect, url_for, session, flash, send_file
from models.database import Database
from auth.auth import login_required, permiso_requerido
from auth.permissions import VER_REPORTES, GENERAR_REPORTES, EXPORTAR_REPORTES
import csv
import io
from datetime import datetime, timedelta
from utils.pdf_utils import generar_pdf_reporte

@login_required
@permiso_requerido(GENERAR_REPORTES)
def generar_reporte():
    """Generar reportes del sistema"""
    if request.method == 'POST':
        tipo_reporte = request.form['tipo']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form.get('fecha_fin', fecha_inicio)
        formato = request.form.get('formato', 'html')
        
        # Validar fechas
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            if tipo_reporte == 'mensual':
                fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
                if fecha_fin_dt < fecha_inicio_dt:
                    flash('La fecha fin no puede ser anterior a la fecha inicio', 'danger')
                    return redirect(url_for('generar_reporte'))
                
                # Validar que el rango no sea mayor a 31 días
                dias_diferencia = (fecha_fin_dt - fecha_inicio_dt).days
                if dias_diferencia > 31:
                    flash('El rango de fechas no puede ser mayor a 31 días', 'danger')
                    return redirect(url_for('generar_reporte'))
        except ValueError:
            flash('Formato de fecha inválido', 'danger')
            return redirect(url_for('generar_reporte'))
        
        # Guardar parámetros en sesión
        session['reporte_params'] = {
            'tipo': tipo_reporte,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'formato': formato
        }
        
        if formato == 'pdf':
            return redirect(url_for('exportar_reporte_pdf'))
        elif formato == 'csv':
            return redirect(url_for('exportar_reporte_csv'))
        else:
            return redirect(url_for('ver_reporte'))
    
    # Fechas por defecto
    hoy = datetime.now().strftime('%Y-%m-%d')
    primer_dia_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    return render_template('reportes/generar.html', 
                         hoy=hoy, 
                         primer_dia_mes=primer_dia_mes)

@login_required
@permiso_requerido(VER_REPORTES)
def ver_reporte():
    """Ver reporte en formato HTML"""
    if 'reporte_params' not in session:
        flash('No hay parámetros de reporte configurados', 'warning')
        return redirect(url_for('generar_reporte'))
    
    params = session['reporte_params']
    tipo = params['tipo']
    fecha_inicio = params['fecha_inicio']
    fecha_fin = params['fecha_fin']
    
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('generar_reporte'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if tipo == 'diario':
            # Reporte diario
            cursor.execute("""
                SELECT 
                    a.*, 
                    v.nombre as visitante, 
                    u.nombre as guardia,
                    v.empresa as empresa_visitante
                FROM accesos a 
                LEFT JOIN visitantes v ON a.visitante_id = v.id 
                LEFT JOIN usuarios u ON a.usuario_id = u.id 
                WHERE DATE(a.fecha_hora) = %s
                ORDER BY a.fecha_hora DESC
            """, (fecha_inicio,))
        else:
            # Reporte mensual
            cursor.execute("""
                SELECT 
                    a.*, 
                    v.nombre as visitante, 
                    u.nombre as guardia,
                    v.empresa as empresa_visitante
                FROM accesos a 
                LEFT JOIN visitantes v ON a.visitante_id = v.id 
                LEFT JOIN usuarios u ON a.usuario_id = u.id 
                WHERE DATE(a.fecha_hora) BETWEEN %s AND %s
                ORDER BY a.fecha_hora DESC
            """, (fecha_inicio, fecha_fin))
        
        accesos = cursor.fetchall()
        
        # Estadísticas detalladas
        if tipo == 'diario':
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_accesos,
                    SUM(CASE WHEN autorizado = 1 THEN 1 ELSE 0 END) as accesos_autorizados,
                    SUM(CASE WHEN autorizado = 0 THEN 1 ELSE 0 END) as accesos_denegados,
                    COUNT(DISTINCT visitante_id) as visitantes_unicos,
                    SUM(CASE WHEN tipo = 'entrada' THEN 1 ELSE 0 END) as total_entradas,
                    SUM(CASE WHEN tipo = 'salida' THEN 1 ELSE 0 END) as total_salidas
                FROM accesos 
                WHERE DATE(fecha_hora) = %s
            """, (fecha_inicio,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_accesos,
                    SUM(CASE WHEN autorizado = 1 THEN 1 ELSE 0 END) as accesos_autorizados,
                    SUM(CASE WHEN autorizado = 0 THEN 1 ELSE 0 END) as accesos_denegados,
                    COUNT(DISTINCT visitante_id) as visitantes_unicos,
                    SUM(CASE WHEN tipo = 'entrada' THEN 1 ELSE 0 END) as total_entradas,
                    SUM(CASE WHEN tipo = 'salida' THEN 1 ELSE 0 END) as total_salidas
                FROM accesos 
                WHERE DATE(fecha_hora) BETWEEN %s AND %s
            """, (fecha_inicio, fecha_fin))
        
        estadisticas = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('reportes/ver.html', 
                             accesos=accesos, 
                             estadisticas=estadisticas,
                             tipo=tipo,
                             fecha_inicio=fecha_inicio,
                             fecha_fin=fecha_fin,
                             now=datetime.now())
        
    except Exception as e:
        print(f"Error al generar reporte: {e}")
        flash('Error al generar el reporte', 'danger')
        return redirect(url_for('generar_reporte'))

@login_required
@permiso_requerido(EXPORTAR_REPORTES)
def exportar_reporte_csv():
    """Exportar reporte a CSV"""
    if 'reporte_params' not in session:
        flash('No hay parámetros de reporte configurados', 'warning')
        return redirect(url_for('generar_reporte'))
    
    params = session['reporte_params']
    tipo = params['tipo']
    fecha_inicio = params['fecha_inicio']
    fecha_fin = params['fecha_fin']
    
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('generar_reporte'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if tipo == 'diario':
            cursor.execute("""
                SELECT 
                    a.fecha_hora,
                    v.nombre as visitante,
                    v.identificacion,
                    v.empresa,
                    a.tipo,
                    CASE WHEN a.autorizado THEN 'Sí' ELSE 'No' END as autorizado,
                    u.nombre as guardia 
                FROM accesos a 
                LEFT JOIN visitantes v ON a.visitante_id = v.id 
                LEFT JOIN usuarios u ON a.usuario_id = u.id 
                WHERE DATE(a.fecha_hora) = %s
                ORDER BY a.fecha_hora DESC
            """, (fecha_inicio,))
        else:
            cursor.execute("""
                SELECT 
                    a.fecha_hora,
                    v.nombre as visitante,
                    v.identificacion,
                    v.empresa,
                    a.tipo,
                    CASE WHEN a.autorizado THEN 'Sí' ELSE 'No' END as autorizado,
                    u.nombre as guardia 
                FROM accesos a 
                LEFT JOIN visitantes v ON a.visitante_id = v.id 
                LEFT JOIN usuarios u ON a.usuario_id = u.id 
                WHERE DATE(a.fecha_hora) BETWEEN %s AND %s
                ORDER BY a.fecha_hora DESC
            """, (fecha_inicio, fecha_fin))
        
        accesos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow([
            'Fecha/Hora', 'Visitante', 'Identificación', 'Empresa', 
            'Tipo', 'Autorizado', 'Guardia'
        ])
        
        # Escribir datos
        for acceso in accesos:
            writer.writerow([
                acceso['fecha_hora'].strftime('%Y-%m-%d %H:%M'),
                acceso['visitante'] or 'N/A',
                acceso['identificacion'] or 'N/A',
                acceso['empresa'] or 'N/A',
                acceso['tipo'].capitalize(),
                acceso['autorizado'],
                acceso['guardia'] or 'Sistema'
            ])
        
        output.seek(0)
        
        # Crear nombre de archivo
        nombre_archivo = f"reporte_accesos_{tipo}_{fecha_inicio}"
        if tipo == 'mensual':
            nombre_archivo += f"_{fecha_fin}"
        nombre_archivo += ".csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            download_name=nombre_archivo,
            as_attachment=True,
            mimetype='text/csv'
        )
        
    except Exception as e:
        print(f"Error al exportar CSV: {e}")
        flash('Error al exportar el reporte', 'danger')
        return redirect(url_for('generar_reporte'))

@login_required
@permiso_requerido(EXPORTAR_REPORTES)
def exportar_reporte_pdf():
    """Exportar reporte a PDF"""
    if 'reporte_params' not in session:
        flash('No hay parámetros de reporte configurados', 'warning')
        return redirect(url_for('generar_reporte'))
    
    params = session['reporte_params']
    tipo = params['tipo']
    fecha_inicio = params['fecha_inicio']
    fecha_fin = params['fecha_fin']
    
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('generar_reporte'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if tipo == 'diario':
            cursor.execute("""
                SELECT 
                    a.fecha_hora,
                    v.nombre as visitante,
                    a.tipo,
                    a.autorizado,
                    u.nombre as guardia 
                FROM accesos a 
                LEFT JOIN visitantes v ON a.visitante_id = v.id 
                LEFT JOIN usuarios u ON a.usuario_id = u.id 
                WHERE DATE(a.fecha_hora) = %s
                ORDER BY a.fecha_hora DESC
            """, (fecha_inicio,))
        else:
            cursor.execute("""
                SELECT 
                    a.fecha_hora,
                    v.nombre as visitante,
                    a.tipo,
                    a.autorizado,
                    u.nombre as guardia 
                FROM accesos a 
                LEFT JOIN visitantes v ON a.visitante_id = v.id 
                LEFT JOIN usuarios u ON a.usuario_id = u.id 
                WHERE DATE(a.fecha_hora) BETWEEN %s AND %s
                ORDER BY a.fecha_hora DESC
            """, (fecha_inicio, fecha_fin))
        
        accesos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Generar PDF
        titulo = f"Reporte de Accesos - {tipo.capitalize()}"
        pdf_content = generar_pdf_reporte(
            accesos, 
            tipo, 
            fecha_inicio, 
            fecha_fin, 
            titulo
        )
        
        # Crear nombre de archivo
        nombre_archivo = f"reporte_accesos_{tipo}_{fecha_inicio}"
        if tipo == 'mensual':
            nombre_archivo += f"_{fecha_fin}"
        nombre_archivo += ".pdf"
        
        return send_file(
            io.BytesIO(pdf_content),
            download_name=nombre_archivo,
            as_attachment=True,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error al exportar PDF: {e}")
        flash('Error al exportar el reporte PDF', 'danger')
        return redirect(url_for('generar_reporte'))

@login_required
@permiso_requerido(VER_REPORTES)
def reporte_estadisticas():
    """Reporte de estadísticas generales"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return render_template('reportes/estadisticas.html', estadisticas={})
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM visitantes WHERE estado = 'activo') as visitantes_activos,
                (SELECT COUNT(*) FROM usuarios WHERE estado = 'activo') as usuarios_activos,
                (SELECT COUNT(*) FROM accesos WHERE DATE(fecha_hora) = CURDATE()) as accesos_hoy,
                (SELECT COUNT(*) FROM alertas WHERE DATE(fecha) = CURDATE()) as alertas_hoy,
                (SELECT COUNT(*) FROM credenciales WHERE estado = 'activa') as credenciales_activas
        """)
        estadisticas = cursor.fetchone()
        
        # Accesos por día (últimos 7 días)
        cursor.execute("""
            SELECT 
                DATE(fecha_hora) as fecha,
                COUNT(*) as total,
                SUM(CASE WHEN tipo = 'entrada' THEN 1 ELSE 0 END) as entradas,
                SUM(CASE WHEN tipo = 'salida' THEN 1 ELSE 0 END) as salidas,
                SUM(CASE WHEN autorizado = 0 THEN 1 ELSE 0 END) as denegados
            FROM accesos 
            WHERE fecha_hora >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(fecha_hora)
            ORDER BY fecha DESC
        """)
        accesos_7_dias = cursor.fetchall()
        
        # Visitantes más frecuentes
        cursor.execute("""
            SELECT 
                v.nombre,
                v.empresa,
                COUNT(*) as total_visitas
            FROM accesos a
            JOIN visitantes v ON a.visitante_id = v.id
            WHERE a.tipo = 'entrada'
            GROUP BY v.id, v.nombre, v.empresa
            ORDER BY total_visitas DESC
            LIMIT 10
        """)
        visitantes_frecuentes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('reportes/estadisticas.html',
                             estadisticas=estadisticas,
                             accesos_7_dias=accesos_7_dias,
                             visitantes_frecuentes=visitantes_frecuentes)
        
    except Exception as e:
        print(f"Error al generar reporte de estadísticas: {e}")
        flash('Error al generar el reporte de estadísticas', 'danger')
        return render_template('reportes/estadisticas.html', estadisticas={})