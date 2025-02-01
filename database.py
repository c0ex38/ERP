import sqlite3
from datetime import datetime
from typing import Any, Dict, List

class Database:
    def __init__(self, db_file: str = "siparis_sistemi.db") -> None:
        """
        Veritabanı bağlantısı kurar ve tabloları oluşturur.
        """
        self.db_file = db_file
        self.create_tables()

    def create_tables(self) -> None:
        """
        Gerekli tabloları veritabanında oluşturur.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Müşteriler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS musteriler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    telefon TEXT NOT NULL,
                    adres TEXT NOT NULL,
                    email TEXT,
                    grup TEXT NOT NULL,
                    notlar TEXT,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Ürünler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urunler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kod TEXT UNIQUE NOT NULL,
                    ad TEXT NOT NULL,
                    fiyat DECIMAL(10,2) NOT NULL,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Siparişler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS siparisler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    siparis_no TEXT NOT NULL UNIQUE,
                    musteri_id INTEGER NOT NULL,
                    siparis_tarihi DATE NOT NULL,
                    teslim_tarihi DATE NOT NULL,
                    toplam_tutar DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (id)
                )
            ''')
            
            # Sipariş detayları tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS siparis_detaylari (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    siparis_id INTEGER NOT NULL,
                    urun_id INTEGER NOT NULL,
                    adet INTEGER NOT NULL,
                    birim_fiyat DECIMAL(10,2) NOT NULL,
                    iskonto INTEGER NOT NULL DEFAULT 0,
                    toplam_fiyat DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (siparis_id) REFERENCES siparisler (id),
                    FOREIGN KEY (urun_id) REFERENCES urunler (id)
                )
            ''')
            
            # Müşteri özel fiyat tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS musteri_fiyatlari (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    musteri_id INTEGER NOT NULL,
                    urun_id INTEGER NOT NULL,
                    ozel_fiyat DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (id),
                    FOREIGN KEY (urun_id) REFERENCES urunler (id),
                    UNIQUE(musteri_id, urun_id)
                )
            ''')
            
            conn.commit()

    # Müşteri işlemleri

    def musteri_ekle(self, musteri_bilgileri: Dict[str, Any]) -> int:
        """
        Yeni müşteri ekler ve eklenen kaydın ID'sini döndürür.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO musteriler (ad, soyad, telefon, adres, email, grup, notlar)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                musteri_bilgileri['ad'],
                musteri_bilgileri['soyad'],
                musteri_bilgileri['telefon'],
                musteri_bilgileri['adres'],
                musteri_bilgileri.get('email'),
                musteri_bilgileri['grup'],
                musteri_bilgileri.get('notlar')
            ))
            return cursor.lastrowid

    def musteri_guncelle(self, musteri_id: int, musteri_bilgileri: Dict[str, Any]) -> None:
        """
        Belirtilen ID'li müşteriyi günceller.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE musteriler 
                SET ad = ?, soyad = ?, telefon = ?, adres = ?, email = ?, grup = ?, notlar = ?
                WHERE id = ?
            ''', (
                musteri_bilgileri['ad'],
                musteri_bilgileri['soyad'],
                musteri_bilgileri['telefon'],
                musteri_bilgileri['adres'],
                musteri_bilgileri.get('email'),
                musteri_bilgileri['grup'],
                musteri_bilgileri.get('notlar'),
                musteri_id
            ))
            conn.commit()

    def musteri_sil(self, musteri_id: int) -> None:
        """
        Belirtilen ID'li müşteriyi siler.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM musteriler WHERE id = ?', (musteri_id,))
            conn.commit()

    def musterileri_getir(self) -> List[Dict[str, Any]]:
        """
        Tüm müşterileri getirir.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM musteriler ORDER BY ad, soyad')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Ürün işlemleri

    def urun_ekle(self, urun_bilgileri: Dict[str, Any]) -> int:
        """
        Yeni ürün ekler ve eklenen kaydın ID'sini döndürür.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO urunler (kod, ad, fiyat)
                VALUES (?, ?, ?)
            ''', (
                urun_bilgileri['kod'],
                urun_bilgileri['ad'],
                urun_bilgileri['fiyat']
            ))
            return cursor.lastrowid

    def urun_guncelle(self, urun_id: int, urun_bilgileri: Dict[str, Any]) -> None:
        """
        Belirtilen ID'li ürünü günceller.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE urunler 
                SET kod = ?, ad = ?, fiyat = ?
                WHERE id = ?
            ''', (
                urun_bilgileri['kod'],
                urun_bilgileri['ad'],
                urun_bilgileri['fiyat'],
                urun_id
            ))
            conn.commit()

    def urun_sil(self, urun_id: int) -> None:
        """
        Belirtilen ID'li ürünü siler.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM urunler WHERE id = ?', (urun_id,))
            conn.commit()

    def urunleri_getir(self) -> List[Dict[str, Any]]:
        """
        Tüm ürünleri getirir.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM urunler ORDER BY kod')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Sipariş işlemleri

    def siparis_ekle(self, siparis_bilgileri: Dict[str, Any], siparis_detaylari: List[Dict[str, Any]]) -> int:
        """
        Yeni sipariş ve sipariş detaylarını ekler, sipariş ID'sini döndürür.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO siparisler (
                    siparis_no, musteri_id, siparis_tarihi, 
                    teslim_tarihi, toplam_tutar
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (
                siparis_bilgileri['siparis_no'],
                siparis_bilgileri['musteri_id'],
                siparis_bilgileri['siparis_tarihi'],
                siparis_bilgileri['teslim_tarihi'],
                siparis_bilgileri['toplam_tutar']
            ))
            siparis_id = cursor.lastrowid

            for detay in siparis_detaylari:
                cursor.execute('''
                    INSERT INTO siparis_detaylari (
                        siparis_id, urun_id, adet, 
                        birim_fiyat, iskonto, toplam_fiyat
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    siparis_id,
                    detay['urun_id'],
                    detay['adet'],
                    detay['birim_fiyat'],
                    detay['iskonto'],
                    detay['toplam_fiyat']
                ))
            conn.commit()
            return siparis_id

    def musteri_siparisleri_getir(self, musteri_id: int) -> List[Dict[str, Any]]:
        """
        Belirtilen müşteriye ait siparişleri detaylarıyla birlikte getirir.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, m.ad, m.soyad, m.telefon, m.adres,
                       GROUP_CONCAT(
                           u.kod || ' - ' || u.ad || ' (' || sd.adet || ' adet)' 
                           || ' Fiyat: ' || sd.toplam_fiyat || ' ₺'
                       ) AS urunler
                FROM siparisler s
                JOIN musteriler m ON s.musteri_id = m.id
                JOIN siparis_detaylari sd ON s.id = sd.siparis_id
                JOIN urunler u ON sd.urun_id = u.id
                WHERE s.musteri_id = ?
                GROUP BY s.id
                ORDER BY s.siparis_tarihi DESC
            ''', (musteri_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def son_siparis_no_getir(self) -> str:
        """
        Veritabanından son sipariş numarasını getirir.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT siparis_no FROM siparisler ORDER BY CAST(siparis_no AS INTEGER) DESC LIMIT 1")
            son_no = cursor.fetchone()
            if son_no:
                return str(int(son_no[0]))
            return "0"  # Hiç sipariş yoksa 0 döndür

    def tum_siparisleri_getir(self) -> List[Dict[str, Any]]:
        """
        Tüm siparişleri müşteri bilgileriyle birlikte getirir.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    s.siparis_no,
                    s.siparis_tarihi,
                    m.ad || ' ' || m.soyad AS musteri_adi,
                    s.toplam_tutar,
                    s.teslim_tarihi
                FROM siparisler s
                JOIN musteriler m ON s.musteri_id = m.id
                ORDER BY s.siparis_tarihi DESC
            ''')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def siparis_sil(self, siparis_no: str) -> None:
        """
        Belirtilen sipariş numarasına ait siparişi ve detaylarını siler.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM siparis_detaylari 
                WHERE siparis_id IN (
                    SELECT id FROM siparisler WHERE siparis_no = ?
                )
            ''', (siparis_no,))
            cursor.execute('DELETE FROM siparisler WHERE siparis_no = ?', (siparis_no,))
            conn.commit()

    def musteri_urun_fiyati_getir(self, musteri_id: int, urun_id: int) -> float:
        """
        Müşteriye özel fiyatı; yoksa ürünün varsayılan fiyatını getirir.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ozel_fiyat 
                FROM musteri_fiyatlari 
                WHERE musteri_id = ? AND urun_id = ?
            ''', (musteri_id, urun_id))
            ozel_fiyat = cursor.fetchone()
            if ozel_fiyat:
                return float(ozel_fiyat[0])
            
            # Özel fiyat yoksa, ürünün normal fiyatını getir
            cursor.execute('SELECT fiyat FROM urunler WHERE id = ?', (urun_id,))
            normal_fiyat = cursor.fetchone()
            return float(normal_fiyat[0]) if normal_fiyat else 0.0