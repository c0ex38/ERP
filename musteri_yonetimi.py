from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTableWidget, QTableWidgetItem, QLineEdit, 
                           QFormLayout, QMessageBox, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt
from siparis_gecmisi import SiparisGecmisiDialog

class MusteriYonetimi(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.musteri_arayuzu_olustur()
        self.tabloyu_guncelle()
        
    def musteri_arayuzu_olustur(self):
        # Ana düzen
        ana_duzen = QVBoxLayout()
        
        # Üst kısım - Arama ve butonlar
        ust_duzen = QHBoxLayout()
        
        # Arama kutusu
        self.arama_kutusu = QLineEdit()
        self.arama_kutusu.setPlaceholderText("Müşteri Ara...")
        self.arama_kutusu.textChanged.connect(self.musteri_ara)
        ust_duzen.addWidget(self.arama_kutusu)
        
        # Butonlar
        self.ekle_butonu = QPushButton("Yeni Müşteri")
        self.duzenle_butonu = QPushButton("Düzenle")
        self.sil_butonu = QPushButton("Sil")
        
        self.ekle_butonu.clicked.connect(self.yeni_musteri_formu)
        self.duzenle_butonu.clicked.connect(self.musteri_duzenle)
        self.sil_butonu.clicked.connect(self.musteri_sil)
        
        ust_duzen.addWidget(self.ekle_butonu)
        ust_duzen.addWidget(self.duzenle_butonu)
        ust_duzen.addWidget(self.sil_butonu)
        
        # Sipariş geçmişi butonu ekle
        self.siparis_gecmisi_butonu = QPushButton("Sipariş Geçmişi")
        self.siparis_gecmisi_butonu.clicked.connect(self.siparis_gecmisini_goster)
        ust_duzen.addWidget(self.siparis_gecmisi_butonu)
        
        # Müşteri tablosu
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(5)
        self.tablo.setHorizontalHeaderLabels(["ID", "Ad", "Soyad", "Telefon", "Adres"])
        self.tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Düzeni yerleştir
        ana_duzen.addLayout(ust_duzen)
        ana_duzen.addWidget(self.tablo)
        
        self.setLayout(ana_duzen)
    
    def tabloyu_guncelle(self):
        self.tablo.setRowCount(0)
        musteriler = self.db.musterileri_getir()
        for musteri in musteriler:
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            self.tablo.setItem(satir, 0, QTableWidgetItem(str(musteri['id'])))
            self.tablo.setItem(satir, 1, QTableWidgetItem(musteri['ad']))
            self.tablo.setItem(satir, 2, QTableWidgetItem(musteri['soyad']))
            self.tablo.setItem(satir, 3, QTableWidgetItem(musteri['telefon']))
            self.tablo.setItem(satir, 4, QTableWidgetItem(musteri['adres']))
    
    def yeni_musteri_formu(self):
        self.musteri_form = MusteriFormu(parent=self)
        self.musteri_form.show()
    
    def musteri_duzenle(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            musteri_id = int(self.tablo.item(secili_satir, 0).text())
            musteri = next((m for m in self.db.musterileri_getir() if m['id'] == musteri_id), None)
            if musteri:
                self.musteri_form = MusteriFormu(parent=self, musteri=musteri)
                self.musteri_form.show()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek müşteriyi seçin!")
    
    def musteri_sil(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            musteri_id = int(self.tablo.item(secili_satir, 0).text())
            cevap = QMessageBox.question(self, "Onay", 
                                       "Bu müşteriyi silmek istediğinizden emin misiniz?",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            
            if cevap == QMessageBox.StandardButton.Yes:
                self.db.musteri_sil(musteri_id)
                self.tabloyu_guncelle()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek müşteriyi seçin!")
    
    def musteri_ara(self, arama_metni):
        for i in range(self.tablo.rowCount()):
            satir_gizle = True
            for j in range(self.tablo.columnCount()):
                item = self.tablo.item(i, j)
                if item and arama_metni.lower() in item.text().lower():
                    satir_gizle = False
                    break
            self.tablo.setRowHidden(i, satir_gizle)
    
    def siparis_gecmisini_goster(self):
        secili_satir = self.tablo.currentRow()
        if secili_satir >= 0:
            musteri_id = int(self.tablo.item(secili_satir, 0).text())
            dialog = SiparisGecmisiDialog(self, musteri_id)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir müşteri seçin!")

class MusteriFormu(QWidget):
    def __init__(self, parent=None, musteri=None):
        super().__init__()
        self.parent = parent
        self.musteri = musteri
        self.form_olustur()
        
    def form_olustur(self):
        self.setWindowTitle("Müşteri Formu")
        self.setGeometry(200, 200, 400, 300)
        
        duzen = QFormLayout()
        
        # Form alanları
        self.ad_input = QLineEdit()
        self.soyad_input = QLineEdit()
        self.telefon_input = QLineEdit()
        self.adres_input = QTextEdit()
        self.email_input = QLineEdit()
        self.grup_input = QComboBox()
        self.grup_input.addItems(["Standart", "VIP", "Potansiyel"])
        self.notlar_input = QTextEdit()
        
        duzen.addRow("Ad *:", self.ad_input)
        duzen.addRow("Soyad *:", self.soyad_input)
        duzen.addRow("Telefon *:", self.telefon_input)
        duzen.addRow("Adres *:", self.adres_input)
        duzen.addRow("E-posta:", self.email_input)
        duzen.addRow("Grup *:", self.grup_input)
        duzen.addRow("Notlar:", self.notlar_input)
        
        if self.musteri:
            self.ad_input.setText(self.musteri['ad'])
            self.soyad_input.setText(self.musteri['soyad'])
            self.telefon_input.setText(self.musteri['telefon'])
            self.adres_input.setText(self.musteri['adres'])
            if 'email' in self.musteri:
                self.email_input.setText(self.musteri['email'])
            if 'grup' in self.musteri:
                index = self.grup_input.findText(self.musteri['grup'])
                if index >= 0:
                    self.grup_input.setCurrentIndex(index)
            if 'notlar' in self.musteri:
                self.notlar_input.setText(self.musteri['notlar'])
        
        self.kaydet_butonu = QPushButton("Kaydet")
        self.kaydet_butonu.clicked.connect(self.kaydet)
        duzen.addRow(self.kaydet_butonu)
        
        self.setLayout(duzen)
    
    def kaydet(self):
        musteri_bilgileri = {
            'ad': self.ad_input.text().strip(),
            'soyad': self.soyad_input.text().strip(),
            'telefon': self.telefon_input.text().strip(),
            'adres': self.adres_input.toPlainText().strip(),
            'email': self.email_input.text().strip(),
            'grup': self.grup_input.currentText(),
            'notlar': self.notlar_input.toPlainText().strip()
        }
        
        if self.musteri:  # Düzenleme modu
            self.parent.db.musteri_guncelle(self.musteri['id'], musteri_bilgileri)
        else:  # Yeni müşteri modu
            self.parent.db.musteri_ekle(musteri_bilgileri)
        
        self.parent.tabloyu_guncelle()
        self.close() 