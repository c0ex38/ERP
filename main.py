import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QTabWidget, QLabel, QHBoxLayout, QPushButton, QSpacerItem, 
                             QSizePolicy, QLineEdit, QDialog, QMessageBox, QFrame, QListWidget, QStackedWidget)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QIcon
import json
from pathlib import Path
from musteri_yonetimi import MusteriYonetimi
from urun_yonetimi import UrunYonetimi
from siparis_yonetimi import SiparisYonetimi
from database import Database

# Yardımcı fonksiyon: Paketlenmiş (frozen) ortamda kaynak dosyaların konumunu belirler.
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # Paketlenmişse bu dizin kullanılır.
    except AttributeError:
        base_path = os.path.abspath(".")  # Paketlenmemişse mevcut çalışma dizini.
    return os.path.join(base_path, relative_path)

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giriş Yap")
        # resource_path ile ikon dosyasını çağırıyoruz.
        self.setWindowIcon(QIcon(resource_path("white.png")))
        self.setGeometry(500, 300, 400, 400)
        
        # Tema ayarlarını yükle
        self.tema_ayarlarini_yukle()
        
        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Üst bar (logo ve tema butonu)
        ust_bar = QHBoxLayout()
        
        # Logo
        self.logo_label = QLabel()
        self.logo_guncelle()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ust_bar.addWidget(self.logo_label)
        
        # Spacer
        ust_bar.addStretch()
        
        # Tema değiştirme butonu
        self.tema_button = QPushButton()
        self.tema_button.setFixedSize(40, 40)
        self.tema_button.clicked.connect(self.tema_degistir)
        self.tema_button_guncelle()
        ust_bar.addWidget(self.tema_button)
        
        layout.addLayout(ust_bar)

        # Ayrım çizgisi
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Kullanıcı Adı Alanı
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        layout.addWidget(self.username_input)

        # Şifre Alanı
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Giriş Butonu
        self.login_button = QPushButton("Giriş Yap")
        self.login_button.clicked.connect(self.check_credentials)
        layout.addWidget(self.login_button)

        self.setLayout(layout)
        
        # Temayı uygula
        self.tema_uygula()

    def tema_ayarlarini_yukle(self):
        self.ayarlar_dosyasi = Path("ayarlar.json")
        if self.ayarlar_dosyasi.exists():
            with open(self.ayarlar_dosyasi, "r", encoding="utf-8") as f:
                ayarlar = json.load(f)
                self.tema = ayarlar.get("tema", "light")
        else:
            self.tema = "light"

    def tema_ayarlarini_kaydet(self):
        with open(self.ayarlar_dosyasi, "w", encoding="utf-8") as f:
            json.dump({"tema": self.tema}, f)

    def tema_degistir(self):
        if self.tema == "light":
            self.tema = "dark"
        else:
            self.tema = "light"
        self.tema_ayarlarini_kaydet()
        self.tema_uygula()
        self.logo_guncelle()
        self.tema_button_guncelle()

    def tema_uygula(self):
        if self.tema == "dark":
            self.setStyleSheet("""
                QDialog {
                    background-color: #2e2e2e;
                    color: #ffffff;
                }
                QLineEdit {
                    padding: 10px;
                    font-size: 14px;
                    border-radius: 5px;
                    background-color: #3e3e3e;
                    color: white;
                    border: 1px solid #4e4e4e;
                }
                QPushButton {
                    padding: 10px;
                    font-size: 16px;
                    border-radius: 5px;
                    background-color: #5a9;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #4a8;
                }
                QFrame {
                    color: #4e4e4e;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f4f4f4;
                    color: #000000;
                }
                QLineEdit {
                    padding: 10px;
                    font-size: 14px;
                    border-radius: 5px;
                    background-color: white;
                    color: black;
                    border: 1px solid #ddd;
                }
                QPushButton {
                    padding: 10px;
                    font-size: 16px;
                    border-radius: 5px;
                    background-color: #5a9;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #4a8;
                }
                QFrame {
                    color: #ddd;
                }
            """)

    def logo_guncelle(self):
        # Tema dark ise "white.png", light ise "black.png" kullanılıyor.
        logo_dosyasi = "white.png" if self.tema == "dark" else "black.png"
        # resource_path fonksiyonu ile dosya yolunu dinamik hale getiriyoruz.
        logo_pixmap = QPixmap(resource_path(logo_dosyasi))
        logo_pixmap = logo_pixmap.scaled(250, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
        self.logo_label.setPixmap(logo_pixmap)

    def tema_button_guncelle(self):
        # Tema butonunun ikonunu ve stilini güncelle
        if self.tema == "dark":
            self.tema_button.setStyleSheet("""
                QPushButton {
                    background-color: #3e3e3e;
                    border-radius: 20px;
                    border: 2px solid #5a9;
                }
                QPushButton:hover {
                    background-color: #4a8;
                }
            """)
            self.tema_button.setIcon(QIcon(resource_path("white.png")))
        else:
            self.tema_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border-radius: 20px;
                    border: 2px solid #5a9;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            self.tema_button.setIcon(QIcon(resource_path("black.png")))
        # İkon boyutunu, resource_path ile çağrılan QPixmap üzerinden ayarlıyoruz.
        self.tema_button.setIconSize(QPixmap(resource_path("black.png")).size().scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))

    def check_credentials(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if username == "admin" and password == "1234":
            self.accept()
        else:
            QMessageBox.warning(self, "Hatalı Giriş", "Kullanıcı adı veya şifre yanlış!")
            self.username_input.clear()
            self.password_input.clear()


class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("white.png")))
        self.db = Database()
        self.tema_ayarlarini_yukle()
        self.pencere_ayarlarini_yukle()

    def tema_ayarlarini_yukle(self):
        self.ayarlar_dosyasi = Path("ayarlar.json")
        if self.ayarlar_dosyasi.exists():
            with open(self.ayarlar_dosyasi, "r", encoding="utf-8") as f:
                ayarlar = json.load(f)
                self.tema = ayarlar.get("tema", "light")
        else:
            self.tema = "light"

    def tema_ayarlarini_kaydet(self):
        with open(self.ayarlar_dosyasi, "w", encoding="utf-8") as f:
            json.dump({"tema": self.tema}, f)

    def tema_degistir(self):
        if self.tema == "light":
            self.tema = "dark"
            self.setStyleSheet("background-color: #2e2e2e; color: #ffffff; font-size: 14px;")
            self.logo_guncelle("white.png")
        else:
            self.tema = "light"
            self.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 14px;")
            self.logo_guncelle("black.png")
        self.tema_ayarlarini_kaydet()

    def logo_guncelle(self, logo_dosyasi):
        logo_pixmap = QPixmap(resource_path(logo_dosyasi))
        logo_pixmap = logo_pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo_label.setPixmap(logo_pixmap)
        self.animasyon_baslat(self.logo_label)

    def pencere_ayarlarini_yukle(self):
        self.setWindowTitle("Dua Miss Yönetim Sistemi")
        self.setGeometry(100, 100, 1200, 800)
        ana_widget = QWidget()
        self.setCentralWidget(ana_widget)
        ana_duzen = QVBoxLayout()
        ana_widget.setLayout(ana_duzen)

        # Navbar
        navbar = QHBoxLayout()
        navbar.setContentsMargins(10, 10, 10, 10)
        navbar.setSpacing(10)
        navbar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("white.png")).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo_label.setPixmap(logo_pixmap)
        navbar.addWidget(self.logo_label)

        baslik = QLabel("Dua Miss Yönetim Sistemi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        navbar.addWidget(baslik)

        ana_duzen.addLayout(navbar)
        
        # Ana Layout
        ana_layout = QHBoxLayout()
        sidebar = QListWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #333; color: white; font-size: 18px; padding: 10px; border-radius: 5px;")
        sidebar.addItem("Müşteri Yönetimi")
        sidebar.addItem("Ürün Yönetimi")
        sidebar.addItem("Sipariş Yönetimi")
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.sekme_olustur(MusteriYonetimi(self.db)))
        self.pages.addWidget(self.sekme_olustur(UrunYonetimi(self.db)))
        self.pages.addWidget(self.sekme_olustur(SiparisYonetimi(self.db)))
        sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        
        ana_layout.addWidget(sidebar)
        ana_layout.addWidget(self.pages)
        ana_duzen.addLayout(ana_layout)
    
    def animasyon_baslat(self, widget):
        animasyon = QPropertyAnimation(widget, b"geometry")
        animasyon.setDuration(500)
        animasyon.setStartValue(widget.geometry())
        animasyon.setEndValue(widget.geometry().adjusted(0, -10, 0, -10))
        animasyon.setEasingCurve(QEasingCurve.Type.OutBounce)
        animasyon.start()

    def sekme_olustur(self, modül_widget):
        sekme = QWidget()
        sekme_duzen = QVBoxLayout()
        sekme.setLayout(sekme_duzen)
        sekme_duzen.addWidget(modül_widget)
        return sekme

def main():
    uygulama = QApplication(sys.argv)
    
    # Uygulamanın genel ikonunu ayarla
    app_icon = QIcon(resource_path("white.png"))
    uygulama.setWindowIcon(app_icon)  
    
    # Windows'a özgü görev çubuğu ayarı (sadece Windows ortamında çalıştır)
    if sys.platform == "win32":
        import ctypes
        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Login ekranı
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        pencere = AnaPencere()
        pencere.show()
        sys.exit(uygulama.exec())

if __name__ == "__main__":
    main()