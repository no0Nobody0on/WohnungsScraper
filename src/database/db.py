"""
WohnungsScraper - Database Module
SQLite Datenbank-Handler
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict
from pathlib import Path


class Database:
    def __init__(self, db_path: Path):
        # Pfad als String speichern (nicht Path-Objekt) fuer pywebview Kompatibilitaet
        self._db_path_str = str(db_path)
        self.conn = sqlite3.connect(self._db_path_str, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_db()
    
    def init_db(self):
        cursor = self.conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS addresses (
                id TEXT PRIMARY KEY,
                street TEXT NOT NULL,
                house_number TEXT NOT NULL,
                postal_code TEXT,
                city TEXT NOT NULL,
                notes TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                started_at TEXT,
                completed_at TEXT,
                addresses_checked INTEGER,
                websites_checked TEXT,
                matches_found INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                search_mode TEXT
            );
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                report_id TEXT,
                address_id TEXT,
                address_display TEXT,
                website TEXT,
                website_name TEXT,
                listing_url TEXT,
                listing_title TEXT,
                match_type TEXT,
                found_at TEXT,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );
        ''')
        self.conn.commit()
    
    def generate_id(self) -> str:
        return str(uuid.uuid4())[:8]
    
    def add_address(self, street: str, house_number: str, postal_code: str, city: str, notes: str = "") -> Dict:
        cursor = self.conn.cursor()
        id = self.generate_id()
        now = datetime.now().isoformat()
        cursor.execute(
            'INSERT INTO addresses (id, street, house_number, postal_code, city, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (id, street, house_number, postal_code, city, notes, now)
        )
        self.conn.commit()
        return {"id": id, "street": street, "house_number": house_number, "postal_code": postal_code, "city": city, "notes": notes}
    
    def update_address(self, id: str, street: str, house_number: str, postal_code: str, city: str, notes: str = "") -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE addresses SET street=?, house_number=?, postal_code=?, city=?, notes=? WHERE id=?',
            (street, house_number, postal_code, city, notes, id)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_addresses(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM addresses ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_address(self, id: str) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM addresses WHERE id=?', (id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_address(self, id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM addresses WHERE id=?', (id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def create_report(self, addresses_checked: int, websites: List[str], search_mode: str) -> str:
        cursor = self.conn.cursor()
        id = self.generate_id()
        now = datetime.now().isoformat()
        cursor.execute(
            'INSERT INTO reports (id, started_at, addresses_checked, websites_checked, status, search_mode) VALUES (?, ?, ?, ?, ?, ?)',
            (id, now, addresses_checked, json.dumps(websites), 'running', search_mode)
        )
        self.conn.commit()
        return id
    
    def complete_report(self, id: str, matches_found: int, status: str = "completed"):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            'UPDATE reports SET completed_at=?, matches_found=?, status=? WHERE id=?',
            (now, matches_found, status, id)
        )
        self.conn.commit()
    
    def get_reports(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM reports ORDER BY started_at DESC')
        reports = []
        for row in cursor.fetchall():
            report = dict(row)
            report['websites_checked'] = json.loads(report['websites_checked'])
            cursor.execute('SELECT * FROM matches WHERE report_id=?', (report['id'],))
            report['matches'] = [dict(m) for m in cursor.fetchall()]
            reports.append(report)
        return reports
    
    def delete_report(self, id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM matches WHERE report_id=?', (id,))
        cursor.execute('DELETE FROM reports WHERE id=?', (id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def add_match(self, report_id: str, address_id: str, address_display: str, website: str, 
                  website_name: str, listing_url: str, listing_title: str, match_type: str):
        cursor = self.conn.cursor()
        id = self.generate_id()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO matches (id, report_id, address_id, address_display, website, website_name, listing_url, listing_title, match_type, found_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id, report_id, address_id, address_display, website, website_name, listing_url, listing_title, match_type, now))
        self.conn.commit()
    
    def get_stats(self) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM addresses')
        addresses = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM reports')
        reports = cursor.fetchone()['count']
        cursor.execute('SELECT COALESCE(SUM(matches_found), 0) as total FROM reports')
        matches = cursor.fetchone()['total']
        cursor.execute('SELECT COUNT(*) as count FROM reports WHERE status="running"')
        running = cursor.fetchone()['count']
        return {"addresses": addresses, "reports": reports, "matches": matches, "running": running}
