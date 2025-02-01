from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, 
    QFormLayout, QMessageBox, QLabel, QDateEdit,
    QDialog, QComboBox, QSpinBox, QGridLayout, QMenu
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from reportlab.pdfgen import canvas
import tempfile
import os
import sqlite3

# ------------------------- Sipariş Yönetimi -------------------------
class SiparisYonetimi(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.siparis_arayuzu_olustur()
        self.tabloyu_guncelle()
        
    def siparis_arayuzu_olustur(self):
        # Ana düzen
        ana_duzen = QVBoxLayout()
        
        # Üst kısım - Butonlar
        ust_duzen = QHBoxLayout()
        
        self.yeni_siparis_butonu = QPushButton("Yeni Sipariş")
        self.duzenle_butonu = QPushButton("Düzenle")
        self.sil_butonu = QPushButton("Sil")
        
        self.yeni_siparis_butonu.clicked.connect(self.yeni_siparis_formu)
        self.duzenle_butonu.clicked.connect(self.siparis_duzenle)
        self.sil_butonu.clicked.connect(self.siparis_sil)
        
        ust_duzen.addWidget(self.yeni_siparis_butonu)
        ust_duzen.addWidget(self.duzenle_butonu)
        ust_duzen.addWidget(self.sil_butonu)
        
        # Sipariş tablosu
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(5)
        self.tablo.setHorizontalHeaderLabels([
            "Sipariş No", "Tarih", "Müşteri Adı", 
            "Toplam Tutar", "Teslim Tarihi"
        ])
        self.tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        ana_duzen.addLayout(ust_duzen)
        ana_duzen.addWidget(self.tablo)
        
        self.setLayout(ana_duzen)
    
    def tabloyu_guncelle(self):
        """Tüm siparişleri veritabanından çekip tabloya ekler"""
        self.tablo.setRowCount(0)
        siparisler = self.db.tum_siparisleri_getir()
        
        for siparis in siparisler:
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            
            self.tablo.setItem(satir, 0, QTableWidgetItem(siparis['siparis_no']))
            self.tablo.setItem(satir, 1, QTableWidgetItem(siparis['siparis_tarihi']))
            self.tablo.setItem(satir, 2, QTableWidgetItem(siparis['musteri_adi']))
            self.tablo.setItem(satir, 3, QTableWidgetItem(f"{float(siparis['toplam_tutar']):.2f} ₺"))
            self.tablo.setItem(satir, 4, QTableWidgetItem(siparis['teslim_tarihi']))
        
        self.tablo.resizeColumnsToContents()
    
    def yeni_siparis_formu(self):
        dialog = SiparisFormu(parent=self)
        dialog.exec()
    
    def siparis_duzenle(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            siparis_no = self.tablo.item(secili_satir, 0).text()
            dialog = SiparisFormu(parent=self, siparis_no=siparis_no)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek siparişi seçin!")
    
    def siparis_sil(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            siparis_no = self.tablo.item(secili_satir, 0).text()
            cevap = QMessageBox.question(
                self, "Onay", 
                "Bu siparişi silmek istediğinizden emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if cevap == QMessageBox.StandardButton.Yes:
                try:
                    self.db.siparis_sil(siparis_no)
                    self.tabloyu_guncelle()
                    QMessageBox.information(self, "Başarılı", "Sipariş başarıyla silindi.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Sipariş silinirken bir hata oluştu:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek siparişi seçin!")

# ------------------------- Sipariş Formu -------------------------
class SiparisFormu(QDialog):
    def __init__(self, parent=None, siparis_no=None):
        super().__init__(parent)
        self.parent = parent
        self.siparis_no = siparis_no
        self.db = self.parent.db
        self.kdv_orani = 20
        self._updating = False  # Programatik güncelleme sırasında sinyali yoksaymak için
        self.form_olustur()
        self.musteri_listesini_yukle()
        # Hücre değişikliği sinyalini yakalıyoruz:
        self.urun_tablosu.cellChanged.connect(self.hucre_degisti)
        
    def form_olustur(self):
        self.setWindowTitle("Sipariş Formu")
        self.setGeometry(100, 100, 800, 600)
        
        ana_duzen = QVBoxLayout()
        
        # Üst kısım – Sipariş bilgileri
        ust_form = QFormLayout()
        
        # Sipariş No (sadece okunabilir)
        self.siparis_no_input = QLineEdit()
        self.siparis_no_input.setReadOnly(True)
        if not self.siparis_no:
            self.siparis_no_input.setText(self.yeni_siparis_no_olustur())
        else:
            self.siparis_no_input.setText(self.siparis_no)
            
        # Tarihler
        self.siparis_tarihi = QDateEdit()
        self.siparis_tarihi.setDate(QDate.currentDate())
        self.teslim_tarihi = QDateEdit()
        self.teslim_tarihi.setDate(QDate.currentDate().addDays(7))
        
        # Müşteri seçimi
        self.musteri_combo = QComboBox()
        self.musteri_combo.currentIndexChanged.connect(self.musteri_secildi)
        
        # Müşteri bilgileri
        self.musteri_bilgileri = QLabel()
        
        ust_form.addRow("Sipariş No:", self.siparis_no_input)
        ust_form.addRow("Sipariş Tarihi:", self.siparis_tarihi)
        ust_form.addRow("Teslim Tarihi:", self.teslim_tarihi)
        ust_form.addRow("Müşteri:", self.musteri_combo)
        ust_form.addRow("Müşteri Bilgileri:", self.musteri_bilgileri)
        
        # Ürün ekleme butonu
        self.urun_ekle_butonu = QPushButton("Ürün Ekle")
        self.urun_ekle_butonu.clicked.connect(self.urun_ekle_dialog)
        ust_form.addRow(self.urun_ekle_butonu)
        
        # Ürün tablosu
        self.urun_tablosu = QTableWidget()
        self.urun_tablosu.setColumnCount(6)
        self.urun_tablosu.setHorizontalHeaderLabels([
            "Ürün Kodu", "Özellikler", "İsk.", "Adet", "Br.Fiyat", "Toplam"
        ])
        # Sağ tıklama menüsü ekleniyor
        self.urun_tablosu.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.urun_tablosu.customContextMenuRequested.connect(self.urun_menu_goster)
        
        # Alt kısım – Toplam, iskonto, KDV ve genel toplam bilgileri
        alt_duzen = QVBoxLayout()
        ozet_duzen = QGridLayout()
        
        self.ara_toplam_label = QLabel("Ara Toplam: 0.00 ₺")
        self.iskonto_label = QLabel("Genel İskonto: 0.00 ₺")
        self.kdv_label = QLabel("KDV: 0.00 ₺")
        self.toplam_label = QLabel("Genel Toplam: 0.00 ₺")
        
        # Genel iskonto ve KDV oranı için SpinBox’lar
        self.genel_iskonto_spin = QSpinBox()
        self.genel_iskonto_spin.setRange(0, 100)
        self.genel_iskonto_spin.setSuffix("%")
        self.genel_iskonto_spin.valueChanged.connect(self.genel_toplam_guncelle)
        
        self.kdv_spin = QSpinBox()
        self.kdv_spin.setRange(0, 100)
        self.kdv_spin.setValue(20)
        self.kdv_spin.setSuffix("%")
        self.kdv_spin.valueChanged.connect(self.genel_toplam_guncelle)
        
        ozet_duzen.addWidget(QLabel("Genel İskonto:"), 0, 0)
        ozet_duzen.addWidget(self.genel_iskonto_spin, 0, 1)
        ozet_duzen.addWidget(QLabel("KDV Oranı:"), 1, 0)
        ozet_duzen.addWidget(self.kdv_spin, 1, 1)
        ozet_duzen.addWidget(self.ara_toplam_label, 2, 0, 1, 2)
        ozet_duzen.addWidget(self.iskonto_label, 3, 0, 1, 2)
        ozet_duzen.addWidget(self.kdv_label, 4, 0, 1, 2)
        ozet_duzen.addWidget(self.toplam_label, 5, 0, 1, 2)
        
        alt_duzen.addLayout(ozet_duzen)
        
        buton_duzen = QHBoxLayout()
        self.kaydet_butonu = QPushButton("Siparişi Kaydet")
        self.yazdir_butonu = QPushButton("PDF Yazdır")
        
        self.kaydet_butonu.clicked.connect(self.siparis_kaydet)
        self.yazdir_butonu.clicked.connect(self.pdf_yazdir)
        
        buton_duzen.addWidget(self.kaydet_butonu)
        buton_duzen.addWidget(self.yazdir_butonu)
        alt_duzen.addLayout(buton_duzen)
        
        ana_duzen.addLayout(ust_form)
        ana_duzen.addWidget(self.urun_tablosu)
        ana_duzen.addLayout(alt_duzen)
        
        self.setLayout(ana_duzen)
    
    def musteri_listesini_yukle(self):
        """Müşteri listesini veritabanından çekip combo box'a ekler"""
        musteriler = self.db.musterileri_getir()
        self.musteri_combo.clear()
        self.musteri_combo.addItem("Müşteri Seçin", None)
        for musteri in musteriler:
            musteri_text = f"{musteri['ad']} {musteri['soyad']} - {musteri['telefon']}"
            self.musteri_combo.addItem(musteri_text, musteri['id'])
    
    def musteri_secildi(self, index):
        """Müşteri seçildiğinde bilgileri göster ve sipariş tablosundaki ürün fiyatlarını güncelle"""
        if index <= 0:
            self.musteri_bilgileri.clear()
            return
            
        musteri_id = self.musteri_combo.currentData()
        musteriler = self.db.musterileri_getir()
        musteri = next((m for m in musteriler if m['id'] == musteri_id), None)
        if musteri:
            bilgi_text = (f"Adres: {musteri['adres']}\n"
                          f"Telefon: {musteri['telefon']}\n")
            self.musteri_bilgileri.setText(bilgi_text)
            # Müşteri değiştiğinde, ürünlerin birim fiyatlarını da güncelleyelim:
            self.guncelle_urun_fiyatlari()
    
    def guncelle_urun_fiyatlari(self):
        """Müşteri değişikliğinde, sipariş tablosundaki her ürün için yeni birim fiyat ve satır toplamı hesaplanır."""
        musteri_id = self.musteri_combo.currentData()
        if not musteri_id:
            return
        for row in range(self.urun_tablosu.rowCount()):
            urun_id = self.urun_tablosu.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if not urun_id:
                continue
            new_price = self.db.musteri_urun_fiyati_getir(musteri_id, urun_id)
            # Eğer kullanıcı tarafından el ile değiştirilmemişse
            current_price_text = self.urun_tablosu.item(row, 4).text()
            try:
                current_price = float(current_price_text.replace("₺", "").strip())
            except Exception:
                current_price = new_price
            if abs(current_price - new_price) < 0.01:
                self.urun_tablosu.item(row, 4).setText(f"{new_price:.2f} ₺")
                try:
                    adet = int(self.urun_tablosu.item(row, 3).text())
                    iskonto = int(self.urun_tablosu.item(row, 2).text())
                    row_total = (new_price * adet) * (1 - iskonto/100)
                    self.urun_tablosu.item(row, 5).setText(f"{row_total:.2f} ₺")
                except Exception:
                    continue
        self.genel_toplam_guncelle()
    
    def yeni_siparis_no_olustur(self):
        """Son sipariş numarasına göre yeni numara oluşturur"""
        try:
            son_no = self.db.son_siparis_no_getir()
            yeni_no = str(int(son_no) + 1).zfill(6)
            return yeni_no
        except:
            return "000001"
    
    def siparis_kaydet(self):
        """Sipariş ve sipariş detaylarını veritabanına kaydeder"""
        if self.musteri_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen müşteri seçin!")
            return
        if self.urun_tablosu.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir ürün ekleyin!")
            return
        try:
            siparis_bilgileri = {
                'siparis_no': self.siparis_no_input.text(),
                'musteri_id': self.musteri_combo.currentData(),
                'siparis_tarihi': self.siparis_tarihi.date().toString("yyyy-MM-dd"),
                'teslim_tarihi': self.teslim_tarihi.date().toString("yyyy-MM-dd"),
                'toplam_tutar': float(self.toplam_label.text().split(":")[1].strip().replace("₺", "").strip())
            }
            siparis_detaylari = []
            for row in range(self.urun_tablosu.rowCount()):
                detay = {
                    'urun_id': int(self.urun_tablosu.item(row, 0).data(Qt.ItemDataRole.UserRole)),
                    'adet': int(self.urun_tablosu.item(row, 3).text()),
                    'birim_fiyat': float(self.urun_tablosu.item(row, 4).text().replace("₺", "").strip()),
                    'iskonto': int(self.urun_tablosu.item(row, 2).text()),
                    'toplam_fiyat': float(self.urun_tablosu.item(row, 5).text().replace("₺", "").strip())
                }
                siparis_detaylari.append(detay)
            
            self.db.siparis_ekle(siparis_bilgileri, siparis_detaylari)
            QMessageBox.information(self, "Başarılı", "Sipariş başarıyla kaydedildi.")
            self.parent.tabloyu_guncelle()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sipariş kaydedilirken bir hata oluştu:\n{str(e)}")
    
    def urun_ekle_dialog(self):
        dialog = UrunSecimDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.secilen_urun:
            self.urun_tabloya_ekle(dialog.secilen_urun)
    
    def urun_tabloya_ekle(self, urun, adet=1, iskonto=0):
        satir = self.urun_tablosu.rowCount()
        self.urun_tablosu.insertRow(satir)
        
        musteri_id = self.musteri_combo.currentData()
        birim_fiyat = self.db.musteri_urun_fiyati_getir(musteri_id, urun['id'])
        
        # Ürün kodu ve adı düzenlenemez olarak ayarlanabilir
        item0 = QTableWidgetItem(urun['kod'])
        item0.setFlags(item0.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.urun_tablosu.setItem(satir, 0, item0)
        
        item1 = QTableWidgetItem(urun['ad'])
        item1.setFlags(item1.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.urun_tablosu.setItem(satir, 1, item1)
        
        # İskonto ve adet hücreleri (değişiklik yapılmayacak)
        item2 = QTableWidgetItem(str(iskonto))
        item2.setFlags(item2.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.urun_tablosu.setItem(satir, 2, item2)
        
        item3 = QTableWidgetItem(str(adet))
        item3.setFlags(item3.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.urun_tablosu.setItem(satir, 3, item3)
        
        # Birim fiyat hücresini düzenlenebilir bırakıyoruz:
        item4 = QTableWidgetItem(f"{birim_fiyat:.2f} ₺")
        self.urun_tablosu.setItem(satir, 4, item4)
        
        # Satır toplamı hesapla
        toplam = (birim_fiyat * adet) * (1 - iskonto/100)
        item5 = QTableWidgetItem(f"{toplam:.2f} ₺")
        item5.setFlags(item5.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.urun_tablosu.setItem(satir, 5, item5)
        
        # Ürün verisini saklamak için (ürün id'si)
        self.urun_tablosu.item(satir, 0).setData(Qt.ItemDataRole.UserRole, urun['id'])
        self.genel_toplam_guncelle()
    
    def hucre_degisti(self, row, column):
        """
        Kullanıcı tarafından düzenlenen hücrede değişiklik olduğunda (özellikle Birim Fiyat sütununda)
        o satırın toplamı ve genel toplam yeniden hesaplanır.
        """
        if self._updating:
            return

        if column == 4:
            try:
                unit_price_text = self.urun_tablosu.item(row, 4).text()
                yeni_birim_fiyat = float(unit_price_text.replace("₺", "").strip())
            except Exception:
                return

            try:
                adet = int(self.urun_tablosu.item(row, 3).text())
            except Exception:
                adet = 1

            try:
                iskonto = int(self.urun_tablosu.item(row, 2).text())
            except Exception:
                iskonto = 0

            yeni_toplam = (yeni_birim_fiyat * adet) * (1 - iskonto/100)
            self._updating = True

            # Eğer sütun 5'teki hücre oluşturulmamışsa, yeni bir hücre oluştur
            total_item = self.urun_tablosu.item(row, 5)
            if total_item is None:
                total_item = QTableWidgetItem()
                self.urun_tablosu.setItem(row, 5, total_item)
            total_item.setText(f"{yeni_toplam:.2f} ₺")

            self._updating = False

            self.genel_toplam_guncelle()
        
    def genel_toplam_guncelle(self):
        ara_toplam = 0
        for row in range(self.urun_tablosu.rowCount()):
            try:
                ara_toplam += float(self.urun_tablosu.item(row, 5).text().replace("₺", "").strip())
            except Exception:
                continue
        
        genel_iskonto_orani = self.genel_iskonto_spin.value() / 100
        iskonto_tutari = ara_toplam * genel_iskonto_orani
        iskonto_sonrasi = ara_toplam - iskonto_tutari
        kdv_orani = self.kdv_spin.value()
        kdv_tutari = iskonto_sonrasi * (kdv_orani / 100)
        genel_toplam = iskonto_sonrasi + kdv_tutari
        
        self.ara_toplam_label.setText(f"Ara Toplam: {ara_toplam:.2f} ₺")
        self.iskonto_label.setText(f"Genel İskonto: {iskonto_tutari:.2f} ₺")
        self.kdv_label.setText(f"KDV (%{kdv_orani}): {kdv_tutari:.2f} ₺")
        self.toplam_label.setText(f"Genel Toplam: {genel_toplam:.2f} ₺")
    
    def urun_menu_goster(self, position):
        secili_satir = self.urun_tablosu.currentRow()
        if secili_satir >= 0:
            menu = QMenu()
            sil_action = menu.addAction("Ürünü Sil")
            duzenle_action = menu.addAction("Ürünü Düzenle")
            
            action = menu.exec(self.urun_tablosu.mapToGlobal(position))
            
            if action == sil_action:
                cevap = QMessageBox.question(
                    self, 
                    "Onay", 
                    "Bu ürünü silmek istediğinizden emin misiniz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if cevap == QMessageBox.StandardButton.Yes:
                    self.urun_tablosu.removeRow(secili_satir)
                    self.genel_toplam_guncelle()
            elif action == duzenle_action:
                self.urunu_duzenle(secili_satir)
    
    def urunu_duzenle(self, satir):
        adet = int(self.urun_tablosu.item(satir, 3).text())
        iskonto = int(self.urun_tablosu.item(satir, 2).text())
        
        dialog = UrunDuzenleDialog(self, adet=adet, iskonto=iskonto)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.urun_tablosu.item(satir, 2).setText(str(dialog.iskonto))
            self.urun_tablosu.item(satir, 3).setText(str(dialog.adet))
            
            try:
                birim_fiyat = float(self.urun_tablosu.item(satir, 4).text().replace("₺", "").strip())
            except Exception:
                birim_fiyat = 0
            toplam = (birim_fiyat * dialog.adet) * (1 - dialog.iskonto/100)
            self.urun_tablosu.item(satir, 5).setText(f"{toplam:.2f} ₺")
            self.genel_toplam_guncelle()
    
    def pdf_olustur(self):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                pdf = canvas.Canvas(tmp.name)
                pdf.setFont("Helvetica-Bold", 16)
                pdf.drawString(50, 800, "SİPARİŞ FORMU")
                pdf.setFont("Helvetica", 12)
                pdf.drawString(50, 750, f"Sipariş No: {self.siparis_no_input.text()}")
                pdf.drawString(50, 730, f"Tarih: {self.siparis_tarihi.date().toString()}")
                
                musteri_id = self.musteri_combo.currentData()
                musteri = next((m for m in self.db.musterileri_getir() if m['id'] == musteri_id), None)
                if musteri:
                    pdf.drawString(50, 700, f"Müşteri: {musteri['ad']} {musteri['soyad']}")
                    pdf.drawString(50, 680, f"Adres: {musteri['adres']}")
                    pdf.drawString(50, 660, f"Telefon: {musteri['telefon']}")
                
                y = 600
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(50, y, "Ürün Kodu")
                pdf.drawString(150, y, "Özellikler")
                pdf.drawString(300, y, "İsk.")
                pdf.drawString(350, y, "Adet")
                pdf.drawString(400, y, "Br.Fiyat")
                pdf.drawString(480, y, "Toplam")
                
                pdf.setFont("Helvetica", 10)
                y -= 20
                for row in range(self.urun_tablosu.rowCount()):
                    pdf.drawString(50, y, self.urun_tablosu.item(row, 0).text())
                    pdf.drawString(150, y, self.urun_tablosu.item(row, 1).text())
                    pdf.drawString(300, y, self.urun_tablosu.item(row, 2).text())
                    pdf.drawString(350, y, self.urun_tablosu.item(row, 3).text())
                    pdf.drawString(400, y, self.urun_tablosu.item(row, 4).text())
                    pdf.drawString(480, y, self.urun_tablosu.item(row, 5).text())
                    y -= 20
                
                y -= 40
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawRightString(400, y, self.ara_toplam_label.text())
                y -= 20
                pdf.drawRightString(400, y, self.iskonto_label.text())
                y -= 20
                pdf.drawRightString(400, y, self.kdv_label.text())
                y -= 20
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawRightString(400, y, self.toplam_label.text())
                
                pdf.save()
                return tmp.name
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturulurken bir hata oluştu:\n{str(e)}")
            return None
    
    def pdf_yazdir(self):
        pdf_dosyasi = self.pdf_olustur()
        if pdf_dosyasi:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                os.startfile(pdf_dosyasi, 'print')

# ------------------------- Ürün Seçim Dialogu -------------------------
class UrunSecimDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.db = self.parent.db
        self.secilen_urun = None
        self.dialog_olustur()
        
    def dialog_olustur(self):
        self.setWindowTitle("Ürün Seç")
        self.setGeometry(200, 200, 600, 400)
        
        duzen = QVBoxLayout()
        self.arama_kutusu = QLineEdit()
        self.arama_kutusu.setPlaceholderText("Ürün Ara (Kod veya İsim)")
        self.arama_kutusu.textChanged.connect(self.urun_ara)
        duzen.addWidget(self.arama_kutusu)
        
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(3)
        self.tablo.setHorizontalHeaderLabels(["Ürün Kodu", "Ürün Adı", "Fiyat"])
        self.tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tablo.doubleClicked.connect(self.urun_sec)
        duzen.addWidget(self.tablo)
        
        buton_duzen = QHBoxLayout()
        self.sec_butonu = QPushButton("Seç")
        self.iptal_butonu = QPushButton("İptal")
        self.sec_butonu.clicked.connect(self.urun_sec)
        self.iptal_butonu.clicked.connect(self.reject)
        buton_duzen.addWidget(self.sec_butonu)
        buton_duzen.addWidget(self.iptal_butonu)
        duzen.addLayout(buton_duzen)
        
        self.setLayout(duzen)
        self.urunleri_yukle()
        
    def urunleri_yukle(self):
        self.tablo.setRowCount(0)
        urunler = self.db.urunleri_getir()
        for urun in urunler:
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            self.tablo.setItem(satir, 0, QTableWidgetItem(urun['kod']))
            self.tablo.setItem(satir, 1, QTableWidgetItem(urun['ad']))
            self.tablo.setItem(satir, 2, QTableWidgetItem(f"{urun['fiyat']:.2f} ₺"))
            self.tablo.item(satir, 0).setData(Qt.ItemDataRole.UserRole, urun)
    
    def urun_ara(self, arama_metni):
        for i in range(self.tablo.rowCount()):
            satir_gizle = True
            for j in range(2):  # Ürün kodu ve adı
                item = self.tablo.item(i, j)
                if item and arama_metni.lower() in item.text().lower():
                    satir_gizle = False
                    break
            self.tablo.setRowHidden(i, satir_gizle)
    
    def urun_sec(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            self.secilen_urun = self.tablo.item(secili_satir, 0).data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ürün seçin!")

# ------------------------- Ürün Düzenleme Dialogu -------------------------
class UrunDuzenleDialog(QDialog):
    def __init__(self, parent=None, adet=1, iskonto=0):
        super().__init__(parent)
        self.adet = adet
        self.iskonto = iskonto
        self.dialog_olustur()
        
    def dialog_olustur(self):
        self.setWindowTitle("Ürün Düzenle")
        self.setGeometry(300, 300, 300, 150)
        
        duzen = QFormLayout()
        self.adet_spin = QSpinBox()
        self.adet_spin.setMinimum(1)
        self.adet_spin.setMaximum(9999)
        self.adet_spin.setValue(self.adet)
        duzen.addRow("Adet:", self.adet_spin)
        
        self.iskonto_spin = QSpinBox()
        self.iskonto_spin.setMinimum(0)
        self.iskonto_spin.setMaximum(100)
        self.iskonto_spin.setValue(self.iskonto)
        self.iskonto_spin.setSuffix("%")
        duzen.addRow("İskonto:", self.iskonto_spin)
        
        butonlar = QHBoxLayout()
        self.kaydet_butonu = QPushButton("Kaydet")
        self.iptal_butonu = QPushButton("İptal")
        self.kaydet_butonu.clicked.connect(self.kaydet)
        self.iptal_butonu.clicked.connect(self.reject)
        butonlar.addWidget(self.kaydet_butonu)
        butonlar.addWidget(self.iptal_butonu)
        duzen.addRow(butonlar)
        
        self.setLayout(duzen)
    
    def kaydet(self):
        self.adet = self.adet_spin.value()
        self.iskonto = self.iskonto_spin.value()
        self.accept() 

# ------------------------- Sipariş Geçmişi Dialogu -------------------------
class SiparisGecmisiDialog(QDialog):
    def __init__(self, parent=None, musteri_id=None):
        super().__init__(parent)
        self.parent = parent
        self.db = self.parent.db
        self.musteri_id = musteri_id
        self.dialog_olustur()
        self.siparisleri_yukle()
        
    def dialog_olustur(self):
        self.setWindowTitle("Sipariş Geçmişi")
        self.setGeometry(100, 100, 900, 600)
        
        ana_duzen = QVBoxLayout()
        self.musteri_bilgi_label = QLabel()
        self.musteri_bilgi_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        ana_duzen.addWidget(self.musteri_bilgi_label)
        
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(6)
        self.tablo.setHorizontalHeaderLabels([
            "Sipariş No", "Sipariş Tarihi", "Teslim Tarihi", 
            "Toplam Tutar", "Durum", "Ürünler"
        ])
        self.tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tablo.setColumnWidth(5, 300)
        ana_duzen.addWidget(self.tablo)
        
        self.istatistik_label = QLabel()
        self.istatistik_label.setStyleSheet("font-weight: bold;")
        ana_duzen.addWidget(self.istatistik_label)
        
        self.kapat_butonu = QPushButton("Kapat")
        self.kapat_butonu.clicked.connect(self.close)
        ana_duzen.addWidget(self.kapat_butonu)
        
        self.setLayout(ana_duzen)
    
    def siparisleri_yukle(self):
        if not self.musteri_id:
            return
            
        siparisler = self.db.musteri_siparisleri_getir(self.musteri_id)
        if not siparisler:
            self.musteri_bilgi_label.setText("Bu müşteriye ait sipariş bulunamadı.")
            return
            
        ilk_siparis = siparisler[0]
        self.musteri_bilgi_label.setText(
            f"Müşteri: {ilk_siparis['ad']} {ilk_siparis['soyad']}\n"
            f"Telefon: {ilk_siparis['telefon']}\n"
            f"Adres: {ilk_siparis['adres']}"
        )
        
        self.tablo.setRowCount(0)
        toplam_tutar = 0
        for siparis in siparisler:
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            
            self.tablo.setItem(satir, 0, QTableWidgetItem(siparis['siparis_no']))
            self.tablo.setItem(satir, 1, QTableWidgetItem(siparis['siparis_tarihi']))
            self.tablo.setItem(satir, 2, QTableWidgetItem(siparis['teslim_tarihi']))
            self.tablo.setItem(satir, 3, QTableWidgetItem(f"{siparis['toplam_tutar']:.2f} ₺"))
            self.tablo.setItem(satir, 4, QTableWidgetItem(siparis['durum']))
            
            urunler_item = QTableWidgetItem(siparis['urunler'].replace(',', '\n'))
            urunler_item.setToolTip(siparis['urunler'].replace(',', '\n'))
            self.tablo.setItem(satir, 5, urunler_item)
            
            toplam_tutar += float(siparis['toplam_tutar'])
        
        self.istatistik_label.setText(
            f"Toplam Sipariş Sayısı: {len(siparisler)}\n"
            f"Toplam Harcama: {toplam_tutar:.2f} ₺"
        )