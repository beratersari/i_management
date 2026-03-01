"""
PDF generation service for reports and exports.
"""
from datetime import date, time
from decimal import Decimal
from io import BytesIO
import logging
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF reports."""

    def generate_sales_report(
        self,
        sales_data: list[dict],
        start_date: date,
        end_date: date,
    ) -> BytesIO:
        """
        Generate a PDF sales report for the given date range.
        
        Args:
            sales_data: List of cart data with totals
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            BytesIO buffer containing the PDF
        """
        logger.info("Generating sales PDF report")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Title
        title = Paragraph("Sales Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Date range
        date_range = Paragraph(
            f"Period: {start_date} to {end_date}",
            subtitle_style
        )
        elements.append(date_range)
        elements.append(Spacer(1, 0.3 * inch))
        
        if not sales_data:
            # No data message
            no_data = Paragraph(
                "No completed sales found for the selected period.",
                normal_style
            )
            elements.append(no_data)
        else:
            total_subtotal = Decimal('0')
            total_discount = Decimal('0')
            total_tax = Decimal('0')
            total_sales = Decimal('0')
            total_items = 0

            for sale in sales_data:
                cart_header = Paragraph(
                    f"Cart #{sale['id']} (Desk: {sale['desk_number'] or '-'}) - {sale['created_at'][:10]}",
                    subtitle_style,
                )
                elements.append(cart_header)
                elements.append(Spacer(1, 0.1 * inch))

                cart_table_data = [
                    ['Item', 'SKU', 'Qty', 'Unit Price', 'Discount %', 'Tax %', 'Line Subtotal', 'Line Total']
                ]

                for item in sale.get('items', []):
                    line_subtotal = item['quantity'] * item['unit_price']
                    discount_amount = line_subtotal * (item['discount_rate'] / Decimal('100'))
                    taxable = line_subtotal - discount_amount
                    tax_amount = taxable * (item['tax_rate'] / Decimal('100'))
                    line_total = taxable + tax_amount

                    cart_table_data.append([
                        item['name'],
                        item['sku'] or '-',
                        f"{item['quantity']}",
                        f"${item['unit_price']:.2f}",
                        f"{item['discount_rate']:.2f}%",
                        f"{item['tax_rate']:.2f}%",
                        f"${line_subtotal:.2f}",
                        f"${line_total:.2f}",
                    ])

                cart_table_data.append([
                    'Cart Totals',
                    '',
                    str(sale['item_count']),
                    '',
                    '',
                    '',
                    f"${sale['subtotal']:.2f}",
                    f"${sale['total']:.2f}",
                ])

                cart_table = Table(cart_table_data, repeatRows=1, hAlign='LEFT')
                cart_table_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                    ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
                    ('ALIGN', (2, 1), (2, -2), 'CENTER'),
                    ('ALIGN', (3, 1), (-1, -2), 'RIGHT'),
                    ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -2), 8),
                    ('BOTTOMPADDING', (0, 1), (-1, -2), 6),

                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, -1), (-1, -1), 9),

                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ])

                for i in range(1, len(cart_table_data) - 1):
                    if i % 2 == 0:
                        cart_table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f7f9fb'))

                cart_table.setStyle(cart_table_style)
                elements.append(cart_table)
                elements.append(Spacer(1, 0.2 * inch))

                total_subtotal += sale['subtotal']
                total_discount += sale['discount_total']
                total_tax += sale['tax_total']
                total_sales += sale['total']
                total_items += sale['item_count']

            elements.append(Spacer(1, 0.2 * inch))
            summary_title = Paragraph("Summary", subtitle_style)
            elements.append(summary_title)
            elements.append(Spacer(1, 0.1 * inch))

            summary_data = [
                ['Metric', 'Value'],
                ['Total Carts', str(len(sales_data))],
                ['Total Items Sold', str(total_items)],
                ['Total Subtotal', f"${total_subtotal:.2f}"],
                ['Total Discounts', f"${total_discount:.2f}"],
                ['Total Tax', f"${total_tax:.2f}"],
                ['Total Sales', f"${total_sales:.2f}"],
            ]

            summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
            summary_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f6f3')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ])
            summary_table.setStyle(summary_style)
            elements.append(summary_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        logger.info("Sales PDF report generated successfully")
        return buffer

    def generate_working_time_report(
        self,
        time_entries: list[dict],
        start_date: date,
        end_date: date,
        employee_name: Optional[str] = None,
    ) -> BytesIO:
        """
        Generate a PDF working time report for the given date range.
        
        Args:
            time_entries: List of time entry data with employee info
            start_date: Report start date
            end_date: Report end date
            employee_name: Optional employee name for single-employee report
            
        Returns:
            BytesIO buffer containing the PDF
        """
        logger.info("Generating working time PDF report")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Title
        if employee_name:
            title = Paragraph(f"Working Time Report - {employee_name}", title_style)
        else:
            title = Paragraph("Working Time Report - All Employees", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Date range
        date_range = Paragraph(
            f"Period: {start_date} to {end_date}",
            subtitle_style
        )
        elements.append(date_range)
        elements.append(Spacer(1, 0.3 * inch))
        
        if not time_entries:
            # No data message
            no_data = Paragraph(
                "No accepted time entries found for the selected period.",
                normal_style
            )
            elements.append(no_data)
        else:
            # Group entries by employee if showing all employees
            if employee_name:
                # Single employee - show detailed table
                elements.extend(self._build_employee_time_table(
                    time_entries, employee_name, styles
                ))
            else:
                # All employees - group by employee
                employees_data = self._group_by_employee(time_entries)
                
                for emp_name, entries in employees_data.items():
                    emp_header = Paragraph(f"Employee: {emp_name}", subtitle_style)
                    elements.append(emp_header)
                    elements.append(Spacer(1, 0.1 * inch))
                    elements.extend(self._build_employee_time_table(entries, emp_name, styles))
                    elements.append(Spacer(1, 0.3 * inch))
            
            # Summary section
            elements.append(Spacer(1, 0.2 * inch))
            summary_title = Paragraph("Summary", subtitle_style)
            elements.append(summary_title)
            elements.append(Spacer(1, 0.1 * inch))
            
            total_hours = sum(
                float(entry['hours_worked']) for entry in time_entries
            )
            total_entries = len(time_entries)
            
            if employee_name:
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Entries', str(total_entries)],
                    ['Total Hours Worked', f"{total_hours:.2f}"],
                ]
            else:
                # Show per-employee summary
                employees_summary = self._group_by_employee(time_entries)
                summary_data = [['Employee', 'Entries', 'Total Hours']]
                for emp_name, entries in employees_summary.items():
                    emp_hours = sum(float(e['hours_worked']) for e in entries)
                    summary_data.append([
                        emp_name,
                        str(len(entries)),
                        f"{emp_hours:.2f}"
                    ])
                summary_data.append([
                    'TOTAL',
                    str(total_entries),
                    f"{total_hours:.2f}"
                ])
            
            summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch, 2 * inch])
            summary_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f6f3')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ])
            summary_table.setStyle(summary_style)
            elements.append(summary_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        logger.info("Working time PDF report generated successfully")
        return buffer

    def _build_employee_time_table(
        self,
        time_entries: list[dict],
        employee_name: str,
        styles,
    ) -> list:
        """Build a time entries table for an employee."""
        elements = []
        
        table_data = [
            ['Date', 'Start Time', 'End Time', 'Hours', 'Status', 'Notes']
        ]
        
        for entry in time_entries:
            table_data.append([
                str(entry['work_date']),
                str(entry['start_hour']),
                str(entry['end_hour']),
                f"{float(entry['hours_worked']):.2f}",
                entry['status'].value if hasattr(entry['status'], 'value') else entry['status'],
                entry.get('notes') or '-',
            ])
        
        # Calculate total hours for this employee
        total_hours = sum(float(entry['hours_worked']) for entry in time_entries)
        table_data.append([
            'TOTAL',
            '',
            '',
            f"{total_hours:.2f}",
            '',
            f"{len(time_entries)} entries"
        ])
        
        table = Table(table_data, repeatRows=1, hAlign='LEFT')
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),
            ('ALIGN', (1, 1), (3, -2), 'CENTER'),
            ('ALIGN', (4, 1), (4, -2), 'CENTER'),
            ('ALIGN', (5, 1), (5, -2), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 6),

            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),

            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])

        for i in range(1, len(table_data) - 1):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f7f9fb'))

        table.setStyle(table_style)
        elements.append(table)
        
        return elements

    def _group_by_employee(self, time_entries: list[dict]) -> dict:
        """Group time entries by employee name."""
        grouped = {}
        for entry in time_entries:
            emp_name = entry.get('employee_name', f"Employee {entry.get('employee_id', 'Unknown')}")
            if emp_name not in grouped:
                grouped[emp_name] = []
            grouped[emp_name].append(entry)
        return grouped

    def generate_sales_charts_report(
        self,
        category_sales: list[dict],
        daily_sales: list[dict],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> BytesIO:
        """
        Generate a PDF report with sales charts.
        
        Args:
            category_sales: List of category sales data [{'category': str, 'total_sales': float, 'item_count': int}]
            daily_sales: List of daily sales data [{'date': date, 'total_sales': float, 'transaction_count': int}]
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            BytesIO buffer containing the PDF
        """
        logger.info("Generating sales charts PDF report")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        
        elements = []
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Title
        title = Paragraph("Sales Analysis Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Date range
        if start_date and end_date:
            date_range = Paragraph(f"Period: {start_date} to {end_date}", subtitle_style)
        else:
            date_range = Paragraph("Period: All time", subtitle_style)
        elements.append(date_range)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Category Sales Bar Chart
        if category_sales:
            cat_header = Paragraph("Sales by Category", subtitle_style)
            elements.append(cat_header)
            elements.append(Spacer(1, 0.1 * inch))
            
            # Create bar chart for category sales
            chart_data = [['Category', 'Total Sales ($)', 'Items Sold']]
            for cat in category_sales:
                chart_data.append([
                    cat['category'],
                    f"${cat['total_sales']:.2f}",
                    str(cat['item_count'])
                ])
            
            # Add total row
            total_sales = sum(c['total_sales'] for c in category_sales)
            total_items = sum(c['item_count'] for c in category_sales)
            chart_data.append(['TOTAL', f"${total_sales:.2f}", str(total_items)])
            
            cat_table = Table(chart_data, colWidths=[3 * inch, 2 * inch, 2 * inch])
            cat_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
                ('ALIGN', (0, 1), (0, -2), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -2), 'RIGHT'),
                ('FONTNAME', (0, 1), (0, -2), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 8),

                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f6f3')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ])
            cat_table.setStyle(cat_style)
            elements.append(cat_table)
            elements.append(Spacer(1, 0.3 * inch))
            
            # Draw simple bar chart using Drawing
            from reportlab.graphics.shapes import Drawing, Rect, String
            from reportlab.graphics import renderPDF
            
            drawing = Drawing(700, 200)
            max_sales = max(c['total_sales'] for c in category_sales) if category_sales else 1
            bar_width = 60
            spacing = 20
            
            for i, cat in enumerate(category_sales):
                x = 50 + i * (bar_width + spacing)
                bar_height = (cat['total_sales'] / max_sales) * 150
                
                # Draw bar
                bar = Rect(x, 30, bar_width, bar_height)
                bar.fillColor = colors.HexColor('#3498db')
                bar.strokeColor = colors.HexColor('#2980b9')
                drawing.add(bar)
                
                # Draw category name (truncated if too long)
                cat_name = cat['category'][:10] + '...' if len(cat['category']) > 10 else cat['category']
                label = String(x + bar_width/2, 20, cat_name, textAnchor='middle', fontSize=8)
                drawing.add(label)
                
                # Draw value
                value_label = String(x + bar_width/2, 30 + bar_height + 5, f"${cat['total_sales']:.0f}", 
                                    textAnchor='middle', fontSize=8)
                drawing.add(value_label)
            
            elements.append(drawing)
            elements.append(Spacer(1, 0.3 * inch))
        
        # Daily Sales Line Chart
        if daily_sales:
            daily_header = Paragraph("Daily Sales Trend", subtitle_style)
            elements.append(daily_header)
            elements.append(Spacer(1, 0.1 * inch))
            
            # Create table for daily sales
            daily_data = [['Date', 'Total Sales ($)', 'Transactions']]
            for day in daily_sales:
                daily_data.append([
                    str(day['date']),
                    f"${day['total_sales']:.2f}",
                    str(day['transaction_count'])
                ])
            
            # Add total row
            total_daily_sales = sum(d['total_sales'] for d in daily_sales)
            total_transactions = sum(d['transaction_count'] for d in daily_sales)
            daily_data.append(['TOTAL', f"${total_daily_sales:.2f}", str(total_transactions)])
            
            daily_table = Table(daily_data, colWidths=[3 * inch, 2 * inch, 2 * inch])
            daily_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
                ('ALIGN', (0, 1), (0, -2), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -2), 'RIGHT'),
                ('FONTNAME', (0, 1), (0, -2), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 8),

                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f8f5')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ])
            daily_table.setStyle(daily_style)
            elements.append(daily_table)
            elements.append(Spacer(1, 0.3 * inch))
            
            # Draw simple line chart using Drawing
            from reportlab.graphics.shapes import Drawing, Line, String, Circle
            from reportlab.graphics import renderPDF
            
            drawing2 = Drawing(700, 200)
            max_daily = max(d['total_sales'] for d in daily_sales) if daily_sales else 1
            min_daily = min(d['total_sales'] for d in daily_sales) if daily_sales else 0
            
            chart_width = 600
            chart_height = 150
            x_offset = 50
            y_offset = 30
            
            # Draw axes
            x_axis = Line(x_offset, y_offset, x_offset + chart_width, y_offset)
            x_axis.strokeColor = colors.black
            drawing2.add(x_axis)
            
            y_axis = Line(x_offset, y_offset, x_offset, y_offset + chart_height)
            y_axis.strokeColor = colors.black
            drawing2.add(y_axis)
            
            # Plot points and connect with lines
            points = []
            for i, day in enumerate(daily_sales):
                x = x_offset + (i / max(len(daily_sales) - 1, 1)) * chart_width
                if max_daily > min_daily:
                    y = y_offset + ((day['total_sales'] - min_daily) / (max_daily - min_daily)) * chart_height
                else:
                    y = y_offset + chart_height / 2
                points.append((x, y, day))
                
                # Draw point
                point = Circle(x, y, 3)
                point.fillColor = colors.HexColor('#e74c3c')
                point.strokeColor = colors.HexColor('#c0392b')
                drawing2.add(point)
                
                # Draw date label (every 5th point or if less than 10 points)
                if len(daily_sales) <= 10 or i % 5 == 0:
                    date_label = String(x, y_offset - 15, str(day['date'])[5:], textAnchor='middle', fontSize=7)
                    drawing2.add(date_label)
            
            # Connect points with lines
            for i in range(len(points) - 1):
                line = Line(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
                line.strokeColor = colors.HexColor('#e74c3c')
                line.strokeWidth = 2
                drawing2.add(line)
            
            # Y-axis labels
            y_label_max = String(x_offset - 10, y_offset + chart_height, f"${max_daily:.0f}", 
                                textAnchor='end', fontSize=8)
            drawing2.add(y_label_max)
            
            y_label_min = String(x_offset - 10, y_offset, f"${min_daily:.0f}", 
                                textAnchor='end', fontSize=8)
            drawing2.add(y_label_min)
            
            elements.append(drawing2)
        
        if not category_sales and not daily_sales:
            no_data = Paragraph("No sales data found for the selected period.", normal_style)
            elements.append(no_data)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        logger.info("Sales charts PDF report generated successfully")
        return buffer
