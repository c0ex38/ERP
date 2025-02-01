from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QCheckBox, QWidget)
from PyQt6.QtPdf import QPdfDocument           # Doğru modül
from PyQt6.QtPdfWidgets import QPdfView         # Doğru modül
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, black, white, gray
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from datetime import datetime
import tempfile
import os


class SiparisGecmisiDialog(QDialog):
    def __init__(self, parent=None, musteri_id=None):
        super().__init__(parent)
        self.parent = parent
        self.db = self.parent.db
        self.musteri_id = musteri_id
        self.siparisler = []  # Siparişleri sınıf değişkeni olarak sakla
        self.dialog_olustur()
        self.siparisleri_yukle()
        
    def dialog_olustur(self):
        self.setWindowTitle("Sipariş Geçmişi")
        self.setGeometry(100, 100, 900, 600)
        
        ana_duzen = QVBoxLayout()
        
        # Müşteri bilgileri
        self.musteri_bilgi_label = QLabel()
        self.musteri_bilgi_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        ana_duzen.addWidget(self.musteri_bilgi_label)
        
        # Sipariş tablosu
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(6)  # Checkbox için +1
        self.tablo.setHorizontalHeaderLabels([
            "Seç", "Sipariş No", "Sipariş Tarihi", "Teslim Tarihi", 
            "Toplam Tutar", "Ürünler"
        ])
        self.tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Sütun genişliklerini ayarla
        self.tablo.setColumnWidth(0, 50)  # Checkbox sütunu
        self.tablo.setColumnWidth(5, 300)  # Ürünler sütunu
        ana_duzen.addWidget(self.tablo)
        
        # İstatistik label'ı ekle
        self.istatistik_label = QLabel()
        self.istatistik_label.setStyleSheet("font-weight: bold;")
        ana_duzen.addWidget(self.istatistik_label)
        
        # Butonlar için yatay düzen
        buton_duzen = QHBoxLayout()
        
        # Tümünü Seç/Kaldır butonu
        self.tumunu_sec_butonu = QPushButton("Tümünü Seç")
        self.tumunu_sec_butonu.setCheckable(True)
        self.tumunu_sec_butonu.clicked.connect(self.tumunu_sec_kaldir)
        buton_duzen.addWidget(self.tumunu_sec_butonu)
        
        # PDF butonu ekle
        self.pdf_butonu = QPushButton("Seçilenleri PDF'e Aktar")
        self.pdf_butonu.clicked.connect(self.pdf_olustur)
        buton_duzen.addWidget(self.pdf_butonu)
        
        # Kapat butonu
        self.kapat_butonu = QPushButton("Kapat")
        self.kapat_butonu.clicked.connect(self.close)
        buton_duzen.addWidget(self.kapat_butonu)
        
        ana_duzen.addLayout(buton_duzen)
        self.setLayout(ana_duzen)
    
    def siparisleri_yukle(self):
        if not self.musteri_id:
            return
            
        self.siparisler = self.db.musteri_siparisleri_getir(self.musteri_id)
        if not self.siparisler:
            self.musteri_bilgi_label.setText("Bu müşteriye ait sipariş bulunamadı.")
            return
        
        # Müşteri bilgilerini göster (ilk siparişten alıyoruz)
        ilk_siparis = self.siparisler[0]
        self.musteri_bilgi_label.setText(
            f"Müşteri: {ilk_siparis['ad']} {ilk_siparis['soyad']}\n"
            f"Telefon: {ilk_siparis['telefon']}\n"
            f"Adres: {ilk_siparis['adres']}"
        )
        
        # Siparişleri tabloya ekle
        self.tablo.setRowCount(0)
        toplam_tutar = 0
        
        for siparis in self.siparisler:
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            
            # Checkbox ekle
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.tablo.setCellWidget(satir, 0, checkbox_widget)
            
            self.tablo.setItem(satir, 1, QTableWidgetItem(siparis['siparis_no']))
            self.tablo.setItem(satir, 2, QTableWidgetItem(siparis['siparis_tarihi']))
            self.tablo.setItem(satir, 3, QTableWidgetItem(siparis['teslim_tarihi']))
            self.tablo.setItem(satir, 4, QTableWidgetItem(f"{siparis['toplam_tutar']:.2f} ₺"))
            
            # Ürünleri daha iyi göstermek için:
            # Siparişte yer alan ürünler, virgülle ayrılmış stringden elde ediliyor.
            # Her bir ürünün başına tire eklenip, parantez içinde teslim tarihi bilgisi ekleniyor.
            urunler_list = []
            for urun in siparis['urunler'].split(','):
                urun = urun.strip()
                if urun:
                    urunler_list.append(f"- {urun} (Teslim: {siparis['teslim_tarihi']})")
            urunler_str = "\n".join(urunler_list)
            
            urunler_item = QTableWidgetItem(urunler_str)
            urunler_item.setToolTip(urunler_str)
            self.tablo.setItem(satir, 5, urunler_item)
            
            toplam_tutar += float(siparis['toplam_tutar'])
        
        # İstatistikleri göster
        self.istatistik_label.setText(
            f"Toplam Sipariş Sayısı: {len(self.siparisler)}\n"
            f"Toplam Harcama: {toplam_tutar:.2f} ₺"
        )
    
    def tumunu_sec_kaldir(self):
        secili = self.tumunu_sec_butonu.isChecked()
        self.tumunu_sec_butonu.setText("Tümünü Kaldır" if secili else "Tümünü Seç")
        
        for satir in range(self.tablo.rowCount()):
            checkbox_widget = self.tablo.cellWidget(satir, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            checkbox.setChecked(secili)
    
    def secili_siparisleri_getir(self):
        secili_siparisler = []
        for satir in range(self.tablo.rowCount()):
            checkbox_widget = self.tablo.cellWidget(satir, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox.isChecked():
                siparis_no = self.tablo.item(satir, 1).text()
                secili_siparisler.append(next(s for s in self.siparisler if s['siparis_no'] == siparis_no))
        return secili_siparisler
    
    def pdf_olustur(self):
        secili_siparisler = self.secili_siparisleri_getir()
        if not secili_siparisler:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir sipariş seçin!")
            return

        try:
            onizleme_dialog = PDFOnizlemeDialog(secili_siparisler, self)
            onizleme_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturulurken bir hata oluştu:\n{str(e)}")

class PDFOnizlemeDialog(QDialog):
    def __init__(self, siparisler, parent=None):
        super().__init__(parent)
        self.siparisler = siparisler
        self.temp_pdf_path = None
        self.setup_ui()
        self.pdf_olustur()

    def setup_ui(self):
        self.setWindowTitle("PDF Önizleme")
        self.setModal(True)
        self.resize(800, 1000)

        layout = QVBoxLayout(self)

        # PDF görüntüleyici
        self.pdf_view = QPdfView(self)
        self.pdf_view.setMinimumSize(QSize(750, 900))
        layout.addWidget(self.pdf_view)

        # Butonlar için horizontal layout
        button_layout = QHBoxLayout()
        self.kaydet_button = QPushButton("PDF Kaydet", self)
        self.kaydet_button.clicked.connect(self.pdf_kaydet)
        button_layout.addWidget(self.kaydet_button)

        self.kapat_button = QPushButton("Kapat", self)
        self.kapat_button.clicked.connect(self.close)
        button_layout.addWidget(self.kapat_button)
        layout.addLayout(button_layout)

    def pdf_olustur(self):
        try:
            # Font dosyalarının bulunduğu dizin ayarlanıyor.
            base_dir = os.path.dirname(os.path.abspath(__file__))
            roboto_bold_path = os.path.join(base_dir, "Roboto-Bold.ttf")
            roboto_regular_path = os.path.join(base_dir, "Roboto-Regular.ttf")

            # Font dosyalarını kontrol et
            if not os.path.exists(roboto_bold_path):
                raise Exception(f"Font file not found: {roboto_bold_path}")
            if not os.path.exists(roboto_regular_path):
                raise Exception(f"Font file not found: {roboto_regular_path}")

            pdfmetrics.registerFont(TTFont('Roboto-Bold', roboto_bold_path))
            pdfmetrics.registerFont(TTFont('Roboto', roboto_regular_path))
            
            # Geçici PDF dosyası oluşturuluyor.
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            self.temp_pdf_path = temp_pdf.name
            pdf = canvas.Canvas(self.temp_pdf_path, pagesize=A4)
            width, height = A4

            # Arka plan
            pdf.setFillColor(Color(0.98, 0.98, 1.0))
            pdf.rect(0, 0, width, height, fill=True)

            # Üst Banner
            banner_height = 4.5 * cm
            pdf.setFillColor(Color(0.85, 0.92, 1.0))
            pdf.rect(0, height - banner_height, width, banner_height, fill=True)
            # Banner altı için gradient benzeri efekt
            pdf.setFillColor(Color(0.7, 0.7, 0.7, 0.3))
            pdf.rect(0, height - banner_height - 0.2 * cm, width, 0.2 * cm, fill=True)

            # Logo (varsa)
            logo_path = "black.png"
            if os.path.exists(logo_path):
                pdf.drawImage(logo_path, 1 * cm, height - 4 * cm, width=3 * cm, height=3 * cm, mask='auto')

            # Başlık
            pdf.setFillColor(Color(0.1, 0.2, 0.4))
            pdf.setFont("Roboto-Bold", 26)
            baslik_metni = "DUA&MİSS SİPARİŞ FORMU"
            text_width = pdf.stringWidth(baslik_metni, "Roboto-Bold", 26)
            pdf.drawString((width - text_width) / 2, height - 2.5 * cm, baslik_metni)

            # Tarih
            pdf.setFillColor(Color(0.3, 0.3, 0.3))
            pdf.setFont("Roboto", 12)
            tarih_metni = f"Tarih: {datetime.now().strftime('%d.%m.%Y')}"
            pdf.drawRightString(width - 1.5 * cm, height - 3.7 * cm, tarih_metni)

            # Müşteri Bilgileri Kartı
            card_x = 1.5 * cm
            card_y = height - 8 * cm
            card_width = width - 3 * cm
            card_height = 3 * cm
            pdf.setFillColor(Color(0.95, 0.98, 1.0))
            pdf.roundRect(card_x, card_y, card_width, card_height, 10, fill=True)

            pdf.setFillColor(Color(0.1, 0.2, 0.4))
            pdf.setFont("Roboto-Bold", 14)
            pdf.drawString(card_x + 0.5 * cm, card_y + card_height - 1 * cm, "MÜŞTERİ BİLGİLERİ")
            pdf.setStrokeColor(Color(0.7, 0.7, 0.7))
            pdf.setLineWidth(0.5)
            pdf.line(card_x + 0.5 * cm, card_y + card_height - 1.2 * cm, card_x + card_width - 0.5 * cm, card_y + card_height - 1.2 * cm)

            musteri = self.siparisler[0]
            detaylar = [
                ("Ad Soyad:", f"{musteri['ad']} {musteri['soyad']}"),
                ("Telefon:", musteri['telefon']),
                ("Adres:", musteri['adres'])
            ]
            y_pos = card_y + card_height - 1.5 * cm
            for etiket, deger in detaylar:
                pdf.setFont("Roboto-Bold", 11)
                pdf.setFillColor(Color(0.3, 0.3, 0.3))
                pdf.drawString(card_x + 0.5 * cm, y_pos, etiket)
                pdf.setFont("Roboto", 11)
                pdf.setFillColor(Color(0.2, 0.2, 0.2))
                pdf.drawString(card_x + 3 * cm, y_pos, deger)
                y_pos -= 0.7 * cm

            # Sipariş Detayları Başlığı
            y_pos = height - 9 * cm
            pdf.setFillColor(Color(0.2, 0.3, 0.4))
            pdf.setFont("Roboto-Bold", 16)
            pdf.drawString(1.5 * cm, y_pos, "SİPARİŞ DETAYLARI")

            # Modern Tablo Tasarımı
            # Her satır: [Kalem, Sipariş Tarihi, Teslim Tarihi, Adet, Birim Fiyat, Toplam]
            basliklar = ["Kalem", "Sipariş Tarihi", "Teslim Tarihi", "Adet", "Birim Fiyat", "Toplam"]
            veriler = [basliklar]
            for siparis in self.siparisler:
                siparis_tarihi = siparis["siparis_tarihi"]
                teslim_tarihi = siparis["teslim_tarihi"]
                # Örnekte miktar "1" olarak alınıyor; eğer detaylı bilgi varsa güncellenmeli.
                fiyat = float(siparis["toplam_tutar"])
                for kalem in siparis["urunler"].split(","):
                    kalem = kalem.strip()
                    if kalem:
                        veriler.append([
                            kalem,
                            siparis_tarihi,
                            teslim_tarihi,
                            "1",
                            f"{fiyat:.2f} ₺",
                            f"{fiyat:.2f} ₺",
                        ])

            # Tabloyu sola hizalayarak, sağdan da daraltıyoruz.
            tablo = Table(veriler, colWidths=[6 * cm, 3 * cm, 3 * cm, 2 * cm, 3 * cm, 3 * cm])
            tablo_stil = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), Color(0.2, 0.3, 0.4)),
                ("TEXTCOLOR", (0, 0), (-1, 0), Color(1, 1, 1)),
                ("FONTNAME", (0, 0), (-1, 0), "Roboto-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("FONTNAME", (0, 1), (-1, -1), "Roboto"),
                ("FONTSIZE", (0, 1), (-1, -1), 11),
                ("TEXTCOLOR", (0, 1), (-1, -1), Color(0.2, 0.3, 0.4)),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, Color(0.8, 0.8, 0.8)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [Color(1, 1, 1), Color(0.97, 0.98, 1.0)]),
                ("RIGHTPADDING", (5, 0), (5, -1), 5),  # Sağ kenar boşluğu
                ("LEFTPADDING", (0, 0), (-1, -1), 5),  # Sol kenar boşluğu ekledik
            ])
            tablo.setStyle(tablo_stil)

            y_pos -= 1.5 * cm
            # Tablonun çizileceği genişliği daraltıp sola hizalıyoruz.
            tablo.wrapOn(pdf, width - 3 * cm, height)
            tablo.drawOn(pdf, 1.0 * cm, y_pos - len(veriler) * 1.2 * cm)

            pdf.setFont("Roboto", 9)
            pdf.setFillColor(Color(0.5, 0.5, 0.5))
            pdf.setStrokeColor(Color(0.8, 0.8, 0.8))
            pdf.line(1.5 * cm, 1.5 * cm, width - 1.5 * cm, 1.5 * cm)
            pdf.drawRightString(width - 1.5 * cm, 1 * cm, f"Sayfa 1/1 • Belge No: {musteri['siparis_no']}")

            pdf.save()

            doc = QPdfDocument(self)
            doc.load(self.temp_pdf_path)
            self.pdf_view.setDocument(doc)

        except Exception as e:
            print(f"PDF oluşturma hatası: {str(e)}")

    def pdf_kaydet(self):
        try:
            if self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
                from PyQt6.QtWidgets import QFileDialog
                dosya_adi, _ = QFileDialog.getSaveFileName(self, "PDF Kaydet", "", "PDF Dosyaları (*.pdf)")
                if dosya_adi:
                    import shutil
                    shutil.copy2(self.temp_pdf_path, dosya_adi)
        except Exception as e:
            print(f"PDF kaydetme hatası: {str(e)}")

    def closeEvent(self, event):
        try:
            self.pdf_view.setDocument(None)
            import time
            time.sleep(0.1)
            if self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
                try:
                    os.unlink(self.temp_pdf_path)
                except PermissionError:
                    try:
                        import tempfile
                        tempfile._get_default_tempdir()
                    except:
                        pass
        except Exception as e:
            print(f"Geçici dosya temizleme hatası: {str(e)}")
        super().closeEvent(event)