from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os
from datetime import datetime
import threading
import logging

app = Flask(__name__)

# CORS configuration
cors_config = {
    "origins": ["https://queue-system-qw88.onrender.com", "http://localhost:5000", "http://127.0.0.1:5000"],
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["Content-Type"]
}
CORS(app, resources={r"/api/*": cors_config})

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Database configuration
DB_FILE = 'queue_system.db'
LOG_FILE = 'queue_system.log'

# Logging setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

# Lock for thread safety
db_lock = threading.Lock()

def log_action(action, details='', level='INFO'):
    """Log an action to file and console"""
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

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        log_action('INIT DB', 'Checking if tables exist')
        
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if len(tables) > 0:
            log_action('INIT DB', f'Tables already exist: {len(tables)} tables')
            conn.close()
            return
        
        log_action('INIT DB', 'Creating new tables')
        
        # Create stations table
        cursor.execute('''
            CREATE TABLE stations (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                current_number INTEGER DEFAULT 0,
                queue_group_id TEXT DEFAULT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create queue entries table
        cursor.execute('''
            CREATE TABLE queue_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id INTEGER NOT NULL,
                customer_number INTEGER NOT NULL,
                status TEXT DEFAULT 'waiting',
                position INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                called_at TIMESTAMP,
                completed_at TIMESTAMP,
                finished_at TIMESTAMP,
                FOREIGN KEY (station_id) REFERENCES stations(id)
            )
        ''')
        
        # Create operators table
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
        
        log_action('INIT DB', 'Tables created successfully')
        
        # Load data from config
        log_action('INIT DB', 'Loading data from config.json')
        
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Add stations
                for station in config.get('stations', []):
                    cursor.execute('''
                        INSERT INTO stations (id, name, description, current_number, queue_group_id, is_active)
                        VALUES (?, ?, ?, ?, ?, 1)
                    ''', (station['id'], station['name'], station['description'], 0, station.get('queue_group_id')))
                
                # Add operators
                for operator in config.get('operators', []):
                    cursor.execute('''
                        INSERT INTO operators (id, code, station_id, name)
                        VALUES (?, ?, ?, ?)
                    ''', (operator['id'], operator['code'], operator['station_id'], operator['name']))
            
            log_action('INIT DB', f'Added {len(config.get("stations", []))} stations and {len(config.get("operators", []))} operators')
        else:
            log_action('INIT DB', 'config.json not found!', 'WARNING')
        
        conn.commit()
        conn.close()
        log_action('INIT DB', 'Database ready!')
        
    except Exception as e:
        log_action('INIT DB ERROR', f'{str(e)}', 'ERROR')
        raise

# =====================
# ROUTES - Web Pages
# =====================

@app.route('/')
def center():
    """Central display screen"""
    log_action('VIEW ACCESSED', 'Center screen')
    return render_template('center.html')

@app.route('/stations')
def stations():
    """Paginated stations view"""
    log_action('VIEW ACCESSED', 'Stations screen')
    return render_template('stations.html')

@app.route('/add/<int:station_id>')
def add_customer(station_id):
    """Add customer station"""
    log_action('VIEW ACCESSED', f'Add customer - Station {station_id}')
    return render_template('add_customer.html')

@app.route('/operator/<int:station_id>')
def operator(station_id):
    """Operator screen"""
    log_action('VIEW ACCESSED', f'Operator screen - Station {station_id}')
    return render_template('operator.html', station_id=station_id)




@app.route('/finish')
def finish():
    """Finish station screen"""
    log_action('VIEW ACCESSED', 'Finish station')
    return render_template('finish_station.html')

@app.route('/admin')
def admin():
    """Admin management screen"""
    log_action('VIEW ACCESSED', 'Admin screen')
    return render_template('admin.html')

# =====================
# API ENDPOINTS
# =====================

@app.route('/api/center-data')
def center_data():
    """Get center display data - grouped by queue_group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stations ORDER BY id')
        stations = cursor.fetchall()
        
        result = []
        for station in stations:
            # Get the actual station to get queue data from
            if station['queue_group_id']:
                # Get first station in queue group
                cursor.execute('''
                    SELECT id FROM stations 
                    WHERE queue_group_id = ?
                    LIMIT 1
                ''', (station['queue_group_id'],))
                first_station_row = cursor.fetchone()
                queue_station_id = first_station_row['id']
            else:
                queue_station_id = station['id']
            
            # Get current customer
            cursor.execute('''
                SELECT customer_number FROM queue_entries 
                WHERE station_id = ? AND status = 'called'
                LIMIT 1
            ''', (queue_station_id,))
            current = cursor.fetchone()
            current_number = current['customer_number'] if current else None
            
            # Get waiting customers
            cursor.execute('''
                SELECT customer_number FROM queue_entries 
                WHERE station_id = ? AND status = 'waiting'
                ORDER BY position ASC, created_at ASC
                LIMIT 10
            ''', (queue_station_id,))
            waiting = cursor.fetchall()
            waiting_list = [row['customer_number'] for row in waiting]
            
            result.append({
                'id': station['id'],
                'name': station['name'],
                'description': station['description'],
                'queue_group_id': station['queue_group_id'],
                'current_number': current_number,
                'waiting_list': waiting_list,
                'is_active': station['is_active']
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        log_action('API ERROR', f'center_data: {str(e)}', 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stations-list')
def stations_list():
    """Get list of stations with waiting count"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stations ORDER BY id')
        stations = cursor.fetchall()
        
        result = []
        for station in stations:
            # Get the actual station to get queue data from
            if station['queue_group_id']:
                # Get first station in queue group
                cursor.execute('''
                    SELECT id FROM stations 
                    WHERE queue_group_id = ?
                    LIMIT 1
                ''', (station['queue_group_id'],))
                first_station_row = cursor.fetchone()
                queue_station_id = first_station_row['id']
            else:
                queue_station_id = station['id']
            
            cursor.execute('''
                SELECT COUNT(*) as count FROM queue_entries 
                WHERE station_id = ? AND status = 'waiting'
            ''', (queue_station_id,))
            waiting_count = cursor.fetchone()['count']
            
            result.append({
                'id': station['id'],
                'name': station['name'],
                'description': station['description'],
                'queue_group_id': station['queue_group_id'],
                'waiting_count': waiting_count
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        log_action('API ERROR', f'stations_list: {str(e)}', 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-operator-station', methods=['POST'])
def get_operator_station():
    """Get station_id for operator code"""
    data = request.json
    operator_code = data.get('operator_code')
    
    if not operator_code:
        return jsonify({'error': 'Operator code missing'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT station_id FROM operators WHERE code = ?', (operator_code,))
        operator = cursor.fetchone()
        
        conn.close()
        
        if not operator:
            log_action('GET OPERATOR STATION ERROR', f'Operator {operator_code} not found', 'WARNING')
            return jsonify({'error': 'Operator not found'}), 404
        
        log_action('GET OPERATOR STATION', f'Operator {operator_code} → Station {operator["station_id"]}')
        
        return jsonify({
            'success': True,
            'station_id': operator['station_id']
        })
    except Exception as e:
        log_action('GET OPERATOR STATION ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500








@app.route('/api/add-entry', methods=['POST'])
def add_entry():
    """Add customer to queue - supports queue groups"""
    data = request.json
    station_id = data.get('station_id')
    customer_number = data.get('customer_number')
    transfer = data.get('transfer', False)
    
    if not station_id or not customer_number:
        log_action('ADD ENTRY FAILED', 'Missing data', 'WARNING')
        return jsonify({'error': 'Missing data'}), 400
    
    try:
        customer_number = int(customer_number)
    except ValueError:
        log_action('ADD ENTRY FAILED', 'Invalid number', 'WARNING')
        return jsonify({'error': 'Customer number must be a number'}), 400
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('SELECT id, name, queue_group_id FROM stations WHERE id = ?', (station_id,))
            station = cursor.fetchone()
            if not station:
                conn.rollback()
                conn.close()
                log_action('ADD ENTRY FAILED', f'Station {station_id} not found', 'WARNING')
                return jsonify({'error': 'Station not found'}), 404
            
            # Get the actual station to add to
            if station['queue_group_id']:
                cursor.execute('''
                    SELECT id FROM stations 
                    WHERE queue_group_id = ?
                    LIMIT 1
                ''', (station['queue_group_id'],))
                first_station_row = cursor.fetchone()
                queue_station_id = first_station_row['id']
            else:
                queue_station_id = station['id']
            
            # Check if customer already in queue
            cursor.execute('''
                SELECT id FROM queue_entries 
                WHERE station_id = ? AND customer_number = ? AND status IN ('waiting', 'called')
            ''', (queue_station_id, customer_number))
            
            if cursor.fetchone():
                conn.rollback()
                conn.close()
                log_action('ADD ENTRY FAILED', f'Customer {customer_number} already in queue', 'WARNING')
                return jsonify({'error': 'Customer already in queue'}), 400
            
            # Check if customer in another queue
            cursor.execute('''
                SELECT station_id FROM queue_entries 
                WHERE customer_number = ? AND status IN ('waiting', 'called')
                LIMIT 1
            ''', (customer_number,))
            
            existing = cursor.fetchone()
            
            if existing:
                other_station_id = existing['station_id']
                cursor.execute('SELECT name FROM stations WHERE id = ?', (other_station_id,))
                other_station = cursor.fetchone()
                
                if not transfer:
                    conn.rollback()
                    conn.close()
                    return jsonify({
                        'error': f'Customer {customer_number} is already in queue',
                        'conflict': True,
                        'customer_number': customer_number,
                        'existing_station': other_station["name"],
                        'new_station': station["name"]
                    }), 409
                
                if transfer:
                    cursor.execute('''
                        DELETE FROM queue_entries 
                        WHERE customer_number = ? AND station_id = ? AND status != 'completed'
                    ''', (customer_number, other_station_id))
                    log_action('CUSTOMER TRANSFERRED', f'Customer {customer_number} transferred')
            
            # Add to queue station
            cursor.execute('''
                INSERT INTO queue_entries (station_id, customer_number, status)
                VALUES (?, ?, 'waiting')
            ''', (queue_station_id, customer_number))
            
            log_action('CUSTOMER ADDED', f'Customer {customer_number} to {station["name"]}')
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Customer {customer_number} added to queue'
            }), 201
        
        except Exception as e:
            conn.rollback()
            log_action('ADD ENTRY ERROR', str(e), 'ERROR')
            return jsonify({'error': f'Error: {str(e)}'}), 500
        finally:
            conn.close()

@app.route('/api/call-next/<int:station_id>', methods=['POST'])
def call_next_customer(station_id):
    """Call next customer from queue group"""
    data = request.json
    operator_code = data.get('operator_code')
    
    if not operator_code:
        log_action('CALL NEXT ERROR', 'Operator code missing', 'WARNING')
        return jsonify({'error': 'Operator code missing'}), 400
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name FROM operators 
                WHERE code = ? AND station_id = ?
            ''', (operator_code, station_id))
            
            operator = cursor.fetchone()
            if not operator:
                conn.close()
                log_action('CALL NEXT ERROR', f'Operator {operator_code} not authorized', 'WARNING')
                return jsonify({'error': 'Operator not assigned to this station'}), 401
            
            # Get station info
            cursor.execute('SELECT queue_group_id FROM stations WHERE id = ?', (station_id,))
            station = cursor.fetchone()
            
            # Get the actual station to get queue from
            if station['queue_group_id']:
                cursor.execute('''
                    SELECT id FROM stations 
                    WHERE queue_group_id = ?
                    LIMIT 1
                ''', (station['queue_group_id'],))
                first_station_row = cursor.fetchone()
                queue_station_id = first_station_row['id']
            else:
                queue_station_id = station_id
            
            # Get next customer
            cursor.execute('''
                SELECT id, customer_number FROM queue_entries 
                WHERE station_id = ? AND status = 'waiting'
                ORDER BY position ASC, created_at ASC
                LIMIT 1
            ''', (queue_station_id,))
            
            entry = cursor.fetchone()
            
            if not entry:
                conn.close()
                log_action('CALL NEXT', f'No customers waiting', 'WARNING')
                return jsonify({'error': 'No customers waiting'}), 404
            
            cursor.execute('''
                UPDATE queue_entries 
                SET status = 'called', called_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (entry['id'],))
            
            conn.commit()
            log_action('CUSTOMER CALLED', f'Customer {entry["customer_number"]} called')
            
            return jsonify({
                'success': True,
                'customer_number': entry['customer_number'],
                'message': f'Customer {entry["customer_number"]} called'
            }), 200
        
        except Exception as e:
            conn.rollback()
            log_action('CALL NEXT ERROR', str(e), 'ERROR')
            return jsonify({'error': f'Error: {str(e)}'}), 500
        finally:
            conn.close()

@app.route('/api/finish-customer', methods=['POST'])
def finish_customer():
    """Finish customer for the day"""
    data = request.json
    customer_number = data.get('customer_number')
    
    if not customer_number:
        log_action('FINISH CUSTOMER FAILED', 'Customer number missing', 'WARNING')
        return jsonify({'error': 'Customer number missing'}), 400
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('''
                UPDATE queue_entries 
                SET status = 'finished', finished_at = CURRENT_TIMESTAMP
                WHERE customer_number = ? AND status IN ('waiting', 'called')
            ''', (customer_number,))
            
            conn.commit()
            log_action('CUSTOMER FINISHED DAY', f'Customer {customer_number} finished')
            
            return jsonify({
                'success': True,
                'message': f'Customer {customer_number} finished successfully!'
            }), 200
        
        except Exception as e:
            conn.rollback()
            log_action('FINISH CUSTOMER ERROR', str(e), 'ERROR')
            return jsonify({'error': f'Error: {str(e)}'}), 500
        finally:
            conn.close()

@app.route('/api/toggle-station-status/<int:station_id>', methods=['POST'])
def toggle_station_status(station_id):
    """Toggle station status - active/inactive"""
    data = request.json
    operator_code = data.get('operator_code')
    
    if not operator_code:
        return jsonify({'error': 'Operator code missing'}), 400
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM operators 
                WHERE code = ? AND station_id = ?
            ''', (operator_code, station_id))
            
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Not authorized'}), 401
            
            cursor.execute('SELECT is_active FROM stations WHERE id = ?', (station_id,))
            station = cursor.fetchone()
            
            if not station:
                conn.close()
                return jsonify({'error': 'Station not found'}), 404
            
            new_status = 1 - station['is_active']
            cursor.execute('''
                UPDATE stations 
                SET is_active = ?
                WHERE id = ?
            ''', (new_status, station_id))
            
            conn.commit()
            status_text = 'Active' if new_status else 'Inactive'
            log_action('STATION STATUS CHANGED', f'Station {station_id} → {status_text}')
            
            return jsonify({
                'success': True,
                'is_active': new_status,
                'message': f'Station is now {status_text}'
            }), 200
        
        except Exception as e:
            conn.rollback()
            log_action('TOGGLE STATUS ERROR', str(e), 'ERROR')
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

@app.route('/api/insert-customer-at-position', methods=['POST'])
def insert_customer_at_position():
    """Insert customer at specific position in queue"""
    data = request.json
    station_id = data.get('station_id')
    customer_number = data.get('customer_number')
    position = data.get('position', 1)
    
    if not station_id or not customer_number:
        return jsonify({'error': 'Missing data'}), 400
    
    try:
        customer_number = int(customer_number)
        position = int(position)
    except ValueError:
        return jsonify({'error': 'Invalid data'}), 400
    
    if position < 1:
        return jsonify({'error': 'Position must be >= 1'}), 400
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('SELECT id, name, queue_group_id FROM stations WHERE id = ?', (station_id,))
            station = cursor.fetchone()
            if not station:
                conn.rollback()
                conn.close()
                return jsonify({'error': 'Station not found'}), 404
            
            # Get the actual station to add to
            if station['queue_group_id']:
                cursor.execute('''
                    SELECT id FROM stations 
                    WHERE queue_group_id = ?
                    LIMIT 1
                ''', (station['queue_group_id'],))
                first_station_row = cursor.fetchone()
                queue_station_id = first_station_row['id']
            else:
                queue_station_id = station['id']
            
            cursor.execute('''
                SELECT id, station_id FROM queue_entries 
                WHERE customer_number = ? AND status IN ('waiting', 'called')
                LIMIT 1
            ''', (customer_number,))
            
            existing = cursor.fetchone()
            if existing:
                cursor.execute('''
                    DELETE FROM queue_entries 
                    WHERE customer_number = ? AND station_id = ? AND status != 'completed'
                ''', (customer_number, existing['station_id']))
            
            cursor.execute('''
                SELECT id, position FROM queue_entries 
                WHERE station_id = ? AND status = 'waiting'
                ORDER BY position ASC, created_at ASC
            ''', (queue_station_id,))
            
            queue = cursor.fetchall()
            
            for i, entry in enumerate(queue):
                new_position = i + 2 if i >= position - 1 else i + 1
                cursor.execute('''
                    UPDATE queue_entries 
                    SET position = ?
                    WHERE id = ?
                ''', (new_position, entry['id']))
            
            cursor.execute('''
                INSERT INTO queue_entries (station_id, customer_number, status, position)
                VALUES (?, ?, 'waiting', ?)
            ''', (queue_station_id, customer_number, position))
            
            conn.commit()
            log_action('CUSTOMER INSERTED', f'Customer {customer_number} at position {position}')
            
            return jsonify({
                'success': True,
                'message': f'Customer {customer_number} added at position {position}'
            }), 201
        
        except Exception as e:
            conn.rollback()
            log_action('INSERT CUSTOMER ERROR', str(e), 'ERROR')
            return jsonify({'error': f'Error: {str(e)}'}), 500
        finally:
            conn.close()

@app.route('/api/admin/verify', methods=['POST'])
def admin_verify():
    """Verify admin password"""
    data = request.json
    password = data.get('password')
    
    if not password:
        log_action('ADMIN LOGIN FAILED', 'Password missing', 'WARNING')
        return jsonify({'error': 'Password missing'}), 400
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            admin_password = config.get('admin_password')
        
        if password == admin_password:
            log_action('ADMIN LOGIN SUCCESS', 'Admin logged in')
            return jsonify({'success': True})
        else:
            log_action('ADMIN LOGIN FAILED', 'Wrong password', 'WARNING')
            return jsonify({'error': 'Wrong password'}), 401
    except Exception as e:
        log_action('ADMIN VERIFY ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/entries', methods=['GET'])
def get_entries():
    """Get all queue entries"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT qe.*, s.name as station_name, s.queue_group_id
            FROM queue_entries qe
            JOIN stations s ON qe.station_id = s.id
            ORDER BY qe.created_at DESC
        ''')
        
        entries = cursor.fetchall()
        result = [dict(entry) for entry in entries]
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        log_action('GET ENTRIES ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/entries', methods=['PUT'])
def update_entry():
    """Update queue entry"""
    data = request.json
    entry_id = data.get('id')
    customer_number = data.get('customer_number')
    status = data.get('status')
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE queue_entries 
                SET customer_number = ?, status = ?
                WHERE id = ?
            ''', (customer_number, status, entry_id))
            
            conn.commit()
            log_action('ENTRY EDITED', f'Entry {entry_id} updated')
            
            return jsonify({'success': True})
        except Exception as e:
            conn.rollback()
            log_action('UPDATE ENTRY ERROR', str(e), 'ERROR')
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

@app.route('/api/admin/entries', methods=['DELETE'])
def delete_entry():
    """Delete queue entry"""
    data = request.json
    entry_id = data.get('id')
    
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM queue_entries WHERE id = ?', (entry_id,))
            
            conn.commit()
            log_action('ENTRY DELETED', f'Entry {entry_id} deleted')
            
            return jsonify({'success': True})
        except Exception as e:
            conn.rollback()
            log_action('DELETE ENTRY ERROR', str(e), 'ERROR')
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

@app.route('/api/admin/report')
def admin_report():
    """Get daily report"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stations ORDER BY id')
        stations = cursor.fetchall()
        
        result = []
        for station in stations:
            # Get the actual station to get queue data from
            if station['queue_group_id']:
                cursor.execute('''
                    SELECT id FROM stations 
                    WHERE queue_group_id = ?
                    LIMIT 1
                ''', (station['queue_group_id'],))
                first_station_row = cursor.fetchone()
                queue_station_id = first_station_row['id']
            else:
                queue_station_id = station['id']
            
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN status = 'waiting' THEN 1 ELSE 0 END) as waiting,
                    SUM(CASE WHEN status = 'called' THEN 1 ELSE 0 END) as called,
                    SUM(CASE WHEN status = 'finished' THEN 1 ELSE 0 END) as finished
                FROM queue_entries
                WHERE station_id = ?
            ''', (queue_station_id,))
            
            counts = cursor.fetchone()
            
            cursor.execute('''
                SELECT customer_number FROM queue_entries
                WHERE station_id = ? AND status = 'called'
                LIMIT 1
            ''', (queue_station_id,))
            
            current = cursor.fetchone()
            current_number = current['customer_number'] if current else None
            
            waiting = counts['waiting'] or 0
            called = counts['called'] or 0
            finished = counts['finished'] or 0
            total = waiting + called + finished
            
            result.append({
                'station_name': station['name'],
                'waiting': waiting,
                'called': called,
                'finished': finished,
                'total': total,
                'current_number': current_number
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        log_action('ADMIN REPORT ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get logs"""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            logs = [line.strip() for line in lines[-100:]]
        
        return jsonify({'logs': logs})
    except Exception as e:
        log_action('GET LOGS ERROR', str(e), 'ERROR')
        return jsonify({'error': str(e)}), 500


# =====================
# INITIALIZATION
# =====================

try:
    init_db()
    log_action('DATABASE READY', 'Database initialized')
except Exception as e:
    log_action('DATABASE ERROR', str(e), 'ERROR')

if __name__ == '__main__':
    log_action('SYSTEM STARTUP', 'System starting')
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
