from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
import threading
import logging

app = Flask(__name__)
CORS(app)

# קובץ בסיס הנתונים
DB_FILE = 'queue_system.db'
LOG_FILE = 'queue_system.log'

# הגדרת logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

# Lock לשמירה מפני Race Condition
db_lock = threading.Lock()

def log_action(action, details='', level='INFO'):
    """תעדוד פעולה בלוג"""
    message = f"{action}"
    if details:
        message += f" | {details}"
    
    if level == 'ERROR':
        logging.error(message)
    elif level == 'WARNING':
        logging.warning(message)
    else:
        logging.info(message)
    
    print(f"[{level}] {message}")

def init_db():
    """יצירת בסיס הנתונים בפעם הראשונה"""
    if not os.path.exists(DB_FILE):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # טבלת התחנות
            cursor.execute('''
                CREATE TABLE stations (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    current_number INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # טבלת הלקוחות בתור
            cursor.execute('''
                CREATE TABLE queue_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id INTEGER NOT NULL,
                    customer_number INTEGER NOT NULL,
                    status TEXT DEFAULT 'waiting',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    called_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    FOREIGN KEY (station_id) REFERENCES stations(id)
                )
            ''')
            
            # טבלת המפעילים
            cursor.execute('''
                CREATE TABLE operators (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    station_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (station_id) REFERENCES stations(id)
                )
            ''')
            
            # הוספת התחנות מה-JSON
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                for station in config['stations']:
                    cursor.execute('''
                        INSERT INTO stations (id, name, description, current_number)
                        VALUES (?, ?, ?, ?)
                    ''', (station['id'], station['name'], station['description'], 0))
                
                for operator in config['operators']:
                    cursor.execute('''
                        INSERT INTO operators (id, code, station_id, name)
                        VALUES (?, ?, ?, ?)
                    ''', (operator['id'], operator['code'], operator['station_id'], operator['name']))
            
            conn.commit()
            conn.close()
            log_action('DATABASE INITIALIZED', 'בסיס הנתונים נוצר בהצלחה')
        except Exception as e:
            log_action('DATABASE INIT FAILED', str(e), 'ERROR')
            raise

def get_db_connection():
    """חיבור לבסיס הנתונים"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ========== מסכים ==========
@app.route('/')
def center():
    log_action('VIEW ACCESSED', 'מסך מרכזי')
    return render_template('center.html')

@app.route('/add/<int:kiosk_id>')
def add_customer_kiosk(kiosk_id):
    if kiosk_id not in [1, 2, 3]:
        log_action('INVALID KIOSK', f'ניסיון גישה לעמדה {kiosk_id}')
        return "עמדה לא חוקית", 404
    log_action('VIEW ACCESSED', f'עמדה הוספה {kiosk_id}')
    return render_template('add_customer.html', kiosk_id=kiosk_id)

@app.route('/operator')
def operator():
    log_action('VIEW ACCESSED', 'מסך עובד')
    return render_template('operator.html')

@app.route('/finish')
def finish_station():
    log_action('VIEW ACCESSED', 'עמדת סיום')
    return render_template('finish_station.html')

@app.route('/admin')
def admin():
    log_action('VIEW ACCESSED', 'מסך admin')
    return render_template('admin.html')

# ========== API - נתונים בזמן אמת ==========
@app.route('/api/center-data')
def center_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stations ORDER BY id')
        stations = cursor.fetchall()
        
        result = []
        for station in stations:
            cursor.execute('''
                SELECT COUNT(*) as count FROM queue_entries 
                WHERE station_id = ? AND status = 'waiting'
            ''', (station['id'],))
            waiting = cursor.fetchone()['count']
            
            result.append({
                'id': station['id'],
                'name': station['name'],
                'current_number': station['current_number'],
                'waiting_count': waiting
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        log_action('API ERROR', f'center_data: {str(e)}', 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stations-list')
def stations_list():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stations ORDER BY id')
        stations = cursor.fetchall()
        
        result = []
        for station in stations:
            cursor.execute('''
                SELECT COUNT(*) as count FROM queue_entries 
                WHERE station_id = ? AND status = 'waiting'
            ''', (station['id'],))
            waiting = cursor.fetchone()['count']
            
            result.append({
                'id': station['id'],
                'name': station['name'],
                'waiting_count': waiting
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        log_action('API ERROR', f'stations_list: {str(e)}', 'ERROR')
        return jsonify({'error': str(e)}), 500

# ========== API - הוספה ==========
@app.route('/api/add-entry', methods=['POST'])
def add_entry():
    data = request.json
    station_id = data.get('station_id')
    customer_number = data.get('customer_number')
    
    if not station_id or not customer_number:
        log_action('ADD ENTRY FAILED', 'נתונים חסרים', 'WARNING')
        return jsonify({'error': 'נתונים חסרים'}), 400
    
    try:
        customer_number = int(customer_number)
    except ValueError:
        log_action('ADD ENTRY FAILED', 'מספר לא חוקי', 'WARNING')
        return jsonify({'error': 'מספר לקוח חייב להיות מספר'}), 400
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('SELECT id, name FROM stations WHERE id = ?', (station_id,))
            station = cursor.fetchone()
            if not station:
                conn.rollback()
                conn.close()
                log_action('ADD ENTRY FAILED', f'תחנה {station_id} לא קיימת', 'WARNING')
                return jsonify({'error': 'התחנה לא קיימת'}), 404
            
            cursor.execute('''
                SELECT id FROM queue_entries 
                WHERE station_id = ? AND customer_number = ? AND status IN ('waiting', 'called')
            ''', (station_id, customer_number))
            
            if cursor.fetchone():
                conn.rollback()
                conn.close()
                log_action('ADD ENTRY FAILED', f'לקוח {customer_number} כבר בתור תחנה {station_id}', 'WARNING')
                return jsonify({'error': 'הלקוח כבר בתור לתחנה זו'}), 400
            
            cursor.execute('''
                INSERT INTO queue_entries (station_id, customer_number, status)
                VALUES (?, ?, 'waiting')
            ''', (station_id, customer_number))
            
            conn.commit()
            log_action('CUSTOMER ADDED', f'לקוח {customer_number} לתחנה {station["name"]}')
            
            return jsonify({
                'success': True,
                'message': f'לקוח {customer_number} נוסף לתור בהצלחה'
            }), 201
        
        except Exception as e:
            conn.rollback()
            log_action('ADD ENTRY ERROR', str(e), 'ERROR')
            return jsonify({'error': f'שגיאה: {str(e)}'}), 500
        finally:
            conn.close()

# ========== API - עובד ==========
@app.route('/api/operator/login', methods=['POST'])
def operator_login():
    data = request.json
    code = data.get('code')
    
    if not code:
        log_action('OPERATOR LOGIN FAILED', 'קוד חסר', 'WARNING')
        return jsonify({'error': 'קוד חסר'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM operators WHERE code = ?', (code,))
        operator = cursor.fetchone()
        
        if not operator:
            conn.close()
            log_action('OPERATOR LOGIN FAILED', f'קוד לא נכון: {code}', 'WARNING')
            return jsonify({'error': 'קוד לא נכון'}), 401
        
        conn.close()
        log_action('OPERATOR LOGIN SUCCESS', f'עובד {operator["name"]} בתחנה {operator["station_id"]}')
        
        return jsonify({
            'success': True,
            'operator_id': operator['id'],
            'station_id': operator['station_id'],
            'operator_name': operator['name']
        })
    except Exception as e:
        log_action('OPERATOR LOGIN ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/station/<int:station_id>')
def get_station(station_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stations WHERE id = ?', (station_id,))
        station = cursor.fetchone()
        
        if not station:
            conn.close()
            return jsonify({'error': 'התחנה לא קיימת'}), 404
        
        cursor.execute('''
            SELECT id, customer_number, status, created_at, called_at, completed_at
            FROM queue_entries
            WHERE station_id = ?
            ORDER BY created_at ASC
        ''', (station_id,))
        entries = cursor.fetchall()
        
        result = {
            'id': station['id'],
            'name': station['name'],
            'current_number': station['current_number'],
            'entries': [dict(entry) for entry in entries]
        }
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        log_action('GET STATION ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/call-next/<int:station_id>', methods=['POST'])
def call_next_customer(station_id):
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('''
                SELECT id, customer_number FROM queue_entries
                WHERE station_id = ? AND status = 'waiting'
                ORDER BY created_at ASC
                LIMIT 1
            ''', (station_id,))
            entry = cursor.fetchone()
            
            if not entry:
                conn.rollback()
                conn.close()
                return jsonify({'error': 'אין לקוחות בתור'}), 404
            
            cursor.execute('''
                UPDATE queue_entries
                SET status = 'called', called_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (entry['id'],))
            
            cursor.execute('''
                UPDATE stations
                SET current_number = ?
                WHERE id = ?
            ''', (entry['customer_number'], station_id))
            
            conn.commit()
            log_action('CUSTOMER CALLED', f'לקוח {entry["customer_number"]} בתחנה {station_id}')
            
            return jsonify({
                'success': True,
                'customer_number': entry['customer_number'],
                'message': f'לקוח {entry["customer_number"]} נקרא לשירות'
            })
        
        except Exception as e:
            conn.rollback()
            log_action('CALL NEXT ERROR', str(e), 'ERROR')
            return jsonify({'error': f'שגיאה: {str(e)}'}), 500
        finally:
            conn.close()

@app.route('/api/complete/<int:entry_id>', methods=['POST'])
def complete_customer(entry_id):
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('''
                UPDATE queue_entries
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (entry_id,))
            
            conn.commit()
            log_action('SERVICE COMPLETED', f'רשומה {entry_id}')
            return jsonify({'success': True, 'message': 'שירות הושלם'})
        
        except Exception as e:
            conn.rollback()
            log_action('COMPLETE ERROR', str(e), 'ERROR')
            return jsonify({'error': f'שגיאה: {str(e)}'}), 500
        finally:
            conn.close()

@app.route('/api/remove/<int:entry_id>', methods=['DELETE'])
def remove_entry(entry_id):
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('DELETE FROM queue_entries WHERE id = ?', (entry_id,))
            
            conn.commit()
            log_action('ENTRY REMOVED', f'רשומה {entry_id}')
            return jsonify({'success': True, 'message': 'לקוח הוסר מהתור'})
        
        except Exception as e:
            conn.rollback()
            log_action('REMOVE ERROR', str(e), 'ERROR')
            return jsonify({'error': f'שגיאה: {str(e)}'}), 500
        finally:
            conn.close()

# ========== API - עמדת סיום ==========
@app.route('/api/finish-customer', methods=['POST'])
def finish_customer():
    """סיום של לקוח לכל היום"""
    data = request.json
    customer_number = data.get('customer_number')
    
    if not customer_number:
        log_action('FINISH FAILED', 'מס\' סידורי חסר', 'WARNING')
        return jsonify({'error': 'מס\' סידורי חסר'}), 400
    
    try:
        customer_number = int(customer_number)
    except ValueError:
        log_action('FINISH FAILED', 'מספר לא חוקי', 'WARNING')
        return jsonify({'error': 'מספר חייב להיות מספר'}), 400
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('''
                SELECT id FROM queue_entries
                WHERE customer_number = ? AND status != 'finished'
            ''', (customer_number,))
            entries = cursor.fetchall()
            
            if not entries:
                conn.rollback()
                conn.close()
                log_action('FINISH FAILED', f'לקוח {customer_number} לא נמצא בתור', 'WARNING')
                return jsonify({'error': 'לקוח לא נמצא בתור'}), 404
            
            for entry in entries:
                cursor.execute('''
                    UPDATE queue_entries
                    SET status = 'finished', finished_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (entry['id'],))
            
            conn.commit()
            log_action('CUSTOMER FINISHED DAY', f'לקוח {customer_number} סיים ליום')
            
            return jsonify({
                'success': True,
                'message': f'לקוח {customer_number} סיים את היום בהצלחה!'
            }), 200
        
        except Exception as e:
            conn.rollback()
            log_action('FINISH ERROR', str(e), 'ERROR')
            return jsonify({'error': f'שגיאה: {str(e)}'}), 500
        finally:
            conn.close()

# ========== API - Admin ==========
@app.route('/api/admin/verify', methods=['POST'])
def admin_verify():
    data = request.json
    password = data.get('password')
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            admin_password = config.get('admin_password')
        
        if password == admin_password:
            log_action('ADMIN LOGIN SUCCESS', 'כניסה למערכת ניהול')
            return jsonify({'success': True})
        else:
            log_action('ADMIN LOGIN FAILED', 'סיסמה שגויה', 'WARNING')
            return jsonify({'error': 'סיסמה שגויה'}), 401
    except Exception as e:
        log_action('ADMIN VERIFY ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/entries', methods=['GET', 'PUT', 'DELETE'])
def admin_entries():
    try:
        if request.method == 'GET':
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT qe.id, qe.customer_number, qe.station_id, s.name as station_name,
                       qe.status, qe.created_at, qe.called_at, qe.completed_at, qe.finished_at
                FROM queue_entries qe
                JOIN stations s ON qe.station_id = s.id
                ORDER BY qe.created_at DESC
            ''')
            entries = cursor.fetchall()
            conn.close()
            
            return jsonify([dict(e) for e in entries])
        
        elif request.method == 'PUT':
            data = request.json
            entry_id = data.get('id')
            customer_number = data.get('customer_number')
            status = data.get('status')
            
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('BEGIN IMMEDIATE')
                
                cursor.execute('''
                    UPDATE queue_entries
                    SET customer_number = ?, status = ?
                    WHERE id = ?
                ''', (customer_number, status, entry_id))
                
                conn.commit()
                conn.close()
                log_action('ENTRY EDITED', f'רשומה {entry_id}: מס\' {customer_number}, סטטוס {status}')
                
                return jsonify({'success': True})
        
        elif request.method == 'DELETE':
            data = request.json
            entry_id = data.get('id')
            
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('BEGIN IMMEDIATE')
                
                cursor.execute('DELETE FROM queue_entries WHERE id = ?', (entry_id,))
                
                conn.commit()
                conn.close()
                log_action('ENTRY DELETED', f'רשומה {entry_id}')
                
                return jsonify({'success': True})
    except Exception as e:
        log_action('ADMIN ENTRIES ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/report')
def admin_report():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stations ORDER BY id')
        stations = cursor.fetchall()
        
        report = []
        for station in stations:
            cursor.execute('''
                SELECT COUNT(*) as total FROM queue_entries
                WHERE station_id = ?
            ''', (station['id'],))
            total = cursor.fetchone()['total']
            
            cursor.execute('''
                SELECT COUNT(*) as completed FROM queue_entries
                WHERE station_id = ? AND status = 'completed'
            ''', (station['id'],))
            completed = cursor.fetchone()['completed']
            
            cursor.execute('''
                SELECT COUNT(*) as waiting FROM queue_entries
                WHERE station_id = ? AND status = 'waiting'
            ''', (station['id'],))
            waiting = cursor.fetchone()['waiting']
            
            cursor.execute('''
                SELECT COUNT(*) as finished FROM queue_entries
                WHERE station_id = ? AND status = 'finished'
            ''', (station['id'],))
            finished = cursor.fetchone()['finished']
            
            report.append({
                'station_name': station['name'],
                'total': total,
                'completed': completed,
                'waiting': waiting,
                'finished': finished,
                'current_number': station['current_number']
            })
        
        conn.close()
        return jsonify(report)
    except Exception as e:
        log_action('REPORT ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            return jsonify({'logs': logs[-100:]})
        else:
            return jsonify({'logs': ['No logs yet']})
    except Exception as e:
        log_action('GET LOGS ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    log_action('SYSTEM STARTUP', 'מערכת מתחילה')
    try:
        init_db()
        log_action('DATABASE READY', 'בסיס נתונים מוכן')
    except Exception as e:
        log_action('DATABASE ERROR', str(e), 'ERROR')
    
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')