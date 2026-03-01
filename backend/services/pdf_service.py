"""
PDF generation service for reports and exports.
"""
from datetime import date
from decimal import Decimal
from io import BytesIO
import logging

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
