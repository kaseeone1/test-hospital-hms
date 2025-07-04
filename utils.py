import logging
from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, User, Patient, PatientVisit, MedicineSale, ServiceCharge, Payment

def log_activity(activity_type, description=None):
    """Log user activity to the database."""
    try:
        from models import ActivityLog
        if current_user.is_authenticated:
            log_entry = ActivityLog(
                user_id=current_user.id,
                activity_type=activity_type,
                description=description,
                ip_address=request.remote_addr
            )
            db.session.add(log_entry)
            db.session.commit()
    except Exception as e:
        logging.error(f"Error logging activity: {str(e)}")

def require_role(*permissions):
    """Decorator to require specific role permissions for accessing routes."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page', 'danger')
                return redirect(url_for('login'))
            
            if not any(getattr(current_user.role, permission) for permission in permissions):
                flash('You do not have permission to access this page', 'danger')
                log_activity('Permission Denied', f'Attempted to access {request.path} without required permission')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_report_pdf(report_type, data):
    """Generate PDF report using WeasyPrint or ReportLab as fallback."""
    try:
        # Try to import WeasyPrint first
        try:
            from weasyprint import HTML, CSS
            use_weasyprint = True
        except ImportError:
            use_weasyprint = False
            logging.warning("WeasyPrint not available, using ReportLab fallback")
        
        # Generate HTML content based on report type
        if report_type == 'sales':
            html_content = generate_sales_report_html(data)
        elif report_type == 'patients':
            html_content = generate_patients_report_html(data)
        elif report_type == 'inventory':
            html_content = generate_inventory_report_html(data)
        else:
            raise ValueError(f"Invalid report type: {report_type}")
        
        if use_weasyprint:
            # Use WeasyPrint for better HTML to PDF conversion
            css_content = '''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            tfoot th {
                background-color: #e9ecef;
            }
            .summary {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                font-size: 0.9em;
                color: #666;
            }
            '''
            
            html = HTML(string=html_content)
            css = CSS(string=css_content)
            
            # Generate PDF in memory
            from io import BytesIO
            pdf_bytes = BytesIO()
            html.write_pdf(pdf_bytes, stylesheets=[css])
            pdf_bytes.seek(0)
            
            return pdf_bytes
        else:
            # Fallback to ReportLab for basic PDF generation
            return generate_reportlab_pdf(report_type, data)
        
    except Exception as e:
        logging.error(f"Error generating PDF report: {str(e)}")
        return None

def generate_reportlab_pdf(report_type, data):
    """Generate PDF using ReportLab as fallback."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        
        # Add title
        elements.append(Paragraph(data['title'], title_style))
        elements.append(Spacer(1, 12))
        
        # Add content based on report type
        if report_type == 'sales':
            # Sales report content
            elements.append(Paragraph(f"Period: {data['period']}", styles['Normal']))
            elements.append(Paragraph(f"Date Range: {data['date_from']} to {data['date_to']}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Summary table
            summary_data = [
                ['Metric', 'Amount'],
                ['Pharmacy Sales', f"${data['total_pharmacy']:.2f}"],
                ['Service Revenue', f"${data['total_services']:.2f}"],
                ['Total Revenue', f"${data['total_revenue']:.2f}"]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
            
        elif report_type == 'patients':
            # Patient report content
            elements.append(Paragraph(f"Period: {data['period']}", styles['Normal']))
            elements.append(Paragraph(f"Date Range: {data['date_from']} to {data['date_to']}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            summary_data = [
                ['Metric', 'Count'],
                ['New Patients', str(data['total_new_patients'])],
                ['Patient Visits', str(data['total_visits'])]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
            
        elif report_type == 'inventory':
            # Inventory report content
            elements.append(Paragraph(f"Period: {data['period']}", styles['Normal']))
            elements.append(Paragraph(f"Date Range: {data['date_from']} to {data['date_to']}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Sold', str(data['total_sold'])],
                ['Total Revenue', f"${data['total_revenue']:.2f}"],
                ['Total Cost', f"${data['total_cost']:.2f}"],
                ['Total Profit', f"${data['total_profit']:.2f}"]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logging.error(f"Error generating ReportLab PDF: {str(e)}")
        return None

def generate_sales_report_html(data):
    """Generate HTML content for sales report."""
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sales Report</title>
    </head>
    <body>
        <h1>{data['title']}</h1>
        <p>Period: {data['period']}</p>
        <p>Date Range: {data['date_from'].strftime('%Y-%m-%d')} to {data['date_to'].strftime('%Y-%m-%d')}</p>
        
        <h2>Pharmacy Sales</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Total Amount</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for sale in data['pharmacy_sales']:
        html += f'''
                <tr>
                    <td>{sale.sale_date.strftime('%Y-%m-%d')}</td>
                    <td>${sale.total:.2f}</td>
                </tr>
        '''
    
    html += f'''
            </tbody>
            <tfoot>
                <tr>
                    <th>Total</th>
                    <th>${data['total_pharmacy']:.2f}</th>
                </tr>
            </tfoot>
        </table>
        
        <h2>Service Revenue</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Total Amount</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for service in data['service_revenue']:
        html += f'''
                <tr>
                    <td>{service.date.strftime('%Y-%m-%d')}</td>
                    <td>${service.total:.2f}</td>
                </tr>
        '''
    
    html += f'''
            </tbody>
            <tfoot>
                <tr>
                    <th>Total</th>
                    <th>${data['total_services']:.2f}</th>
                </tr>
            </tfoot>
        </table>
        
        <div class="summary">
            <h3>Summary</h3>
            <p><strong>Total Pharmacy Sales:</strong> ${data['total_pharmacy']:.2f}</p>
            <p><strong>Total Service Revenue:</strong> ${data['total_services']:.2f}</p>
            <p><strong>Total Revenue:</strong> ${data['total_revenue']:.2f}</p>
        </div>
        
        <div class="footer">
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Bluwik HMS - Test Hospital</p>
        </div>
    </body>
    </html>
    '''
    return html

def generate_patients_report_html(data):
    """Generate HTML content for patients report."""
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Patients Report</title>
    </head>
    <body>
        <h1>{data['title']}</h1>
        <p>Period: {data['period']}</p>
        <p>Date Range: {data['date_from'].strftime('%Y-%m-%d')} to {data['date_to'].strftime('%Y-%m-%d')}</p>
        
        <h2>New Patients</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Patient Name</th>
                    <th>Gender</th>
                    <th>Age</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for patient in data['new_patients']:
        html += f'''
                <tr>
                    <td>{patient.created_at.strftime('%Y-%m-%d')}</td>
                    <td>{patient.get_full_name()}</td>
                    <td>{patient.gender}</td>
                    <td>{patient.get_age() or 'N/A'}</td>
                </tr>
        '''
    
    html += f'''
            </tbody>
            <tfoot>
                <tr>
                    <th colspan="3">Total New Patients</th>
                    <th>{data['total_new_patients']}</th>
                </tr>
            </tfoot>
        </table>
        
        <h2>Patient Visits</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Patient Name</th>
                    <th>Doctor</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for visit in data['visits']:
        html += f'''
                <tr>
                    <td>{visit.visit_date.strftime('%Y-%m-%d')}</td>
                    <td>{visit.patient.get_full_name()}</td>
                    <td>{visit.doctor.get_full_name()}</td>
                    <td>{'Completed' if visit.is_completed else 'Pending'}</td>
                </tr>
        '''
    
    html += f'''
            </tbody>
            <tfoot>
                <tr>
                    <th colspan="3">Total Visits</th>
                    <th>{data['total_visits']}</th>
                </tr>
            </tfoot>
        </table>
        
        <div class="summary">
            <h3>Summary</h3>
            <p><strong>New Patients:</strong> {data['total_new_patients']}</p>
            <p><strong>Total Visits:</strong> {data['total_visits']}</p>
        </div>
        
        <div class="footer">
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Bluwik HMS - Test Hospital</p>
        </div>
    </body>
    </html>
    '''
    return html

def generate_inventory_report_html(data):
    """Generate HTML content for inventory report."""
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Inventory Report</title>
    </head>
    <body>
        <h1>{data['title']}</h1>
        <p>Period: {data['period']}</p>
        <p>Date Range: {data['date_from'].strftime('%Y-%m-%d')} to {data['date_to'].strftime('%Y-%m-%d')}</p>
        
        <h2>Medicine Sales</h2>
        <table>
            <thead>
                <tr>
                    <th>Medicine</th>
                    <th>Quantity Sold</th>
                    <th>Revenue</th>
                    <th>Cost</th>
                    <th>Profit</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for sale in data['sales']:
        html += f'''
                <tr>
                    <td>{sale.medicine.name}</td>
                    <td>{sale.quantity}</td>
                    <td>${sale.total_amount:.2f}</td>
                    <td>${sale.quantity * sale.medicine.purchase_price:.2f}</td>
                    <td>${sale.total_amount - (sale.quantity * sale.medicine.purchase_price):.2f}</td>
                </tr>
        '''
    
    html += f'''
            </tbody>
            <tfoot>
                <tr>
                    <th>Total</th>
                    <th>{data['total_sold']}</th>
                    <th>${data['total_revenue']:.2f}</th>
                    <th>${data['total_cost']:.2f}</th>
                    <th>${data['total_profit']:.2f}</th>
                </tr>
            </tfoot>
        </table>
        
        <div class="summary">
            <h3>Summary</h3>
            <p><strong>Total Items Sold:</strong> {data['total_sold']}</p>
            <p><strong>Total Revenue:</strong> ${data['total_revenue']:.2f}</p>
            <p><strong>Total Cost:</strong> ${data['total_cost']:.2f}</p>
            <p><strong>Total Profit:</strong> ${data['total_profit']:.2f}</p>
        </div>
        
        <div class="footer">
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Bluwik HMS - Test Hospital</p>
        </div>
    </body>
    </html>
    '''
    return html 