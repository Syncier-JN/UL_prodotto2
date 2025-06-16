from fpdf import FPDF

class BasePDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Confronto delle prestazioni (profilo MiFID)", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")
