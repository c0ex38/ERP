from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTableWidget, QTableWidgetItem, QLineEdit, 
                           QFormLayout, QMessageBox, QComboBox, QLabel,
                           QDoubleSpinBox, QSpinBox, QDialog)
from PyQt6.QtCore import Qt
import sqlite3

class UrunYonetimi(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.urun_arayuzu_olustur()
        self.tabloyu_guncelle()
        
    def urun_arayuzu_olustur(self):
        # Ana düzen
        ana_duzen = QVBoxLayout()
        
        # Üst kısım - Arama ve butonlar
        ust_duzen = QHBoxLayout()
        
        # Arama kutusu
        self.arama_kutusu = QLineEdit()
        self.arama_kutusu.setPlaceholderText("Ürün Ara...")
        self.arama_kutusu.textChanged.connect(self.urun_ara)
        ust_duzen.addWidget(self.arama_kutusu)
        
        # Butonlar
        self.ekle_butonu = QPushButton("Yeni Ürün")
        self.duzenle_butonu = QPushButton("Düzenle")
        self.sil_butonu = QPushButton("Sil")
        
        self.ekle_butonu.clicked.connect(self.yeni_urun_formu)
        self.duzenle_butonu.clicked.connect(self.urun_duzenle)
        self.sil_butonu.clicked.connect(self.urun_sil)
        
        ust_duzen.addWidget(self.ekle_butonu)
        ust_duzen.addWidget(self.duzenle_butonu)
        ust_duzen.addWidget(self.sil_butonu)
        
        # Ürün tablosu
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(3)
        self.tablo.setHorizontalHeaderLabels([
            "Ürün Kodu", "Ürün Adı", "Fiyat"
        ])
        self.tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Düzeni yerleştir
        ana_duzen.addLayout(ust_duzen)
        ana_duzen.addWidget(self.tablo)
        
        self.setLayout(ana_duzen)
    
    def tabloyu_guncelle(self):
        self.tablo.setRowCount(0)
        urunler = self.db.urunleri_getir()
        
        for urun in urunler:
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            
            self.tablo.setItem(satir, 0, QTableWidgetItem(urun['kod']))
            self.tablo.setItem(satir, 1, QTableWidgetItem(urun['ad']))
            self.tablo.setItem(satir, 2, QTableWidgetItem(f"{urun['fiyat']:.2f} ₺"))
            
            # Ürün verisini satırda sakla
            self.tablo.item(satir, 0).setData(Qt.ItemDataRole.UserRole, urun)
    
    def yeni_urun_formu(self):
        self.urun_form = UrunFormu(parent=self)
        self.urun_form.show()
    
    def urun_duzenle(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            urun_id = int(self.tablo.item(secili_satir, 0).text())
            urun = next((u for u in self.db.urunleri_getir() if u['id'] == urun_id), None)
            if urun:
                self.urun_form = UrunFormu(parent=self, urun=urun)
                self.urun_form.show()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek ürünü seçin!")
    
    def urun_sil(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            try:
                # UserRole'den ürün verisini al
                urun_verisi = self.tablo.item(secili_satir, 0).data(Qt.ItemDataRole.UserRole)
                if not urun_verisi or 'id' not in urun_verisi:
                    raise ValueError("Ürün verisi bulunamadı")
                
                urun_id = urun_verisi['id']  # Ürün ID'sini al
                
                cevap = QMessageBox.question(
                    self,
                    "Onay",
                    "Bu ürünü silmek istediğinizden emin misiniz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if cevap == QMessageBox.StandardButton.Yes:
                    self.db.urun_sil(urun_id)
                    self.tabloyu_guncelle()
                    QMessageBox.information(self, "Başarılı", "Ürün başarıyla silindi.")
                    
            except ValueError as e:
                QMessageBox.warning(self, "Uyarı", f"Ürün silinemedi: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün silinirken bir hata oluştu:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek ürünü seçin!")

    def urun_ara(self, arama_metni):
        for i in range(self.tablo.rowCount()):
            satir_gizle = True
            for j in range(self.tablo.columnCount()):
                item = self.tablo.item(i, j)
                if item and arama_metni.lower() in item.text().lower():
                    satir_gizle = False
                    break
            self.tablo.setRowHidden(i, satir_gizle)

class UrunFormu(QDialog):
    def __init__(self, parent=None, urun=None):
        super().__init__(parent)
        self.parent = parent
        self.urun = urun
        self.form_olustur()
        
    def form_olustur(self):
        self.setWindowTitle("Ürün Formu")
        duzen = QFormLayout()
        
        # Form alanları
        self.kod_input = QLineEdit()
        self.ad_input = QLineEdit()
        self.fiyat_input = QDoubleSpinBox()
        self.fiyat_input.setMaximum(999999.99)
        self.fiyat_input.setDecimals(2)
        self.fiyat_input.setSuffix(" ₺")
        
        duzen.addRow("Ürün Kodu:", self.kod_input)
        duzen.addRow("Ürün Adı:", self.ad_input)
        duzen.addRow("Fiyat:", self.fiyat_input)
        
        # Eğer düzenleme modundaysa mevcut bilgileri doldur
        if self.urun:
            self.kod_input.setText(self.urun['kod'])
            self.ad_input.setText(self.urun['ad'])
            self.fiyat_input.setValue(float(self.urun['fiyat']))
        
        # Kaydet butonu
        self.kaydet_butonu = QPushButton("Kaydet")
        self.kaydet_butonu.clicked.connect(self.kaydet)
        duzen.addRow(self.kaydet_butonu)
        
        self.setLayout(duzen)
    
    def kaydet(self):
        # Form verilerini topla
        urun_bilgileri = {
            'kod': self.kod_input.text().strip(),
            'ad': self.ad_input.text().strip(),
            'fiyat': self.fiyat_input.value()
        }
        
        # Zorunlu alanları kontrol et
        if not all([urun_bilgileri['kod'], urun_bilgileri['ad']]):
            QMessageBox.warning(self, "Uyarı", "Lütfen tüm alanları doldurun!")
            return
        
        try:
            if self.urun:  # Düzenleme modu
                self.parent.db.urun_guncelle(self.urun['id'], urun_bilgileri)
            else:  # Yeni ürün modu
                self.parent.db.urun_ekle(urun_bilgileri)
            
            self.parent.tabloyu_guncelle()
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Hata", "Bu ürün kodu zaten kullanılıyor!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Bir hata oluştu:\n{str(e)}") 