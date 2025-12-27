/**
 * Servidor Express para Sistema CBR de Menús Gastronómicos
 * =========================================================
 * APIs:
 * - POST /api/users            : Crear/actualizar perfil de usuario
 * - GET  /api/users/:id        : Obtener perfil de usuario
 * - POST /api/cbr/search       : Ejecutar búsqueda CBR
 * - POST /api/cbr/evaluate     : Evaluar menú (utilidad)
 * - GET  /api/sessions/:userId : Obtener historial de sesiones
 */

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Rutas a bases de datos JSON
const DATA_DIR = path.join(__dirname, 'data');
const USERS_FILE = path.join(DATA_DIR, 'users.json');
const SESSIONS_FILE = path.join(DATA_DIR, 'sessions.json');
const UTILITY_FILE = path.join(DATA_DIR, 'menu_utility.json');

// Asegurar que existen los archivos de datos
function ensureDataFiles() {
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(USERS_FILE)) {
        fs.writeFileSync(USERS_FILE, JSON.stringify({ users: {} }, null, 2));
    }
    if (!fs.existsSync(SESSIONS_FILE)) {
        fs.writeFileSync(SESSIONS_FILE, JSON.stringify({ sessions: {} }, null, 2));
    }
    if (!fs.existsSync(UTILITY_FILE)) {
        fs.writeFileSync(UTILITY_FILE, JSON.stringify({ menus: {} }, null, 2));
    }
}

// Helpers para leer/escribir JSON
function readJSON(filepath) {
    return JSON.parse(fs.readFileSync(filepath, 'utf8'));
}

function writeJSON(filepath, data) {
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
}

// =============================================================================
// API: USUARIOS
// =============================================================================

// Crear o actualizar usuario
app.post('/api/users', (req, res) => {
    try {
        const users = readJSON(USERS_FILE);
        const userId = req.body.userId || uuidv4();
        
        users.users[userId] = {
            ...users.users[userId],
            ...req.body.preferences,
            userId,
            updatedAt: new Date().toISOString()
        };
        
        writeJSON(USERS_FILE, users);
        res.json({ success: true, userId, user: users.users[userId] });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Obtener usuario
app.get('/api/users/:userId', (req, res) => {
    try {
        const users = readJSON(USERS_FILE);
        const user = users.users[req.params.userId];
        
        if (user) {
            res.json({ success: true, user });
        } else {
            res.status(404).json({ success: false, error: 'Usuario no encontrado' });
        }
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// =============================================================================
// API: CBR - BÚSQUEDA
// =============================================================================

app.post('/api/cbr/search', async (req, res) => {
    try {
        const { userId, preferences, sessionId } = req.body;
        const currentSessionId = sessionId || uuidv4();
        
        // Guardar preferencias del usuario
        const users = readJSON(USERS_FILE);
        if (!users.users[userId]) {
            users.users[userId] = { userId, createdAt: new Date().toISOString() };
        }
        users.users[userId].lastPreferences = preferences;
        users.users[userId].updatedAt = new Date().toISOString();
        writeJSON(USERS_FILE, users);
        
        // Ejecutar CBR via Python
        const result = await runCBRPython(preferences);
        
        // Guardar sesión
        const sessions = readJSON(SESSIONS_FILE);
        if (!sessions.sessions[userId]) {
            sessions.sessions[userId] = [];
        }
        
        const searchRecord = {
            sessionId: currentSessionId,
            searchNumber: sessions.sessions[userId].filter(s => s.sessionId === currentSessionId).length + 1,
            timestamp: new Date().toISOString(),
            preferences,
            result: {
                menuId: result.menu?.menu_id,
                menuName: result.menu?.menu_name,
                similarity: result.similarity,
                isValid: result.is_valid
            }
        };
        
        sessions.sessions[userId].push(searchRecord);
        writeJSON(SESSIONS_FILE, sessions);
        
        res.json({
            success: true,
            sessionId: currentSessionId,
            searchNumber: searchRecord.searchNumber,
            result
        });
    } catch (error) {
        console.error('Error en CBR:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// =============================================================================
// API: EVALUACIÓN DE MENÚS
// =============================================================================

app.post('/api/cbr/evaluate', (req, res) => {
    try {
        const { userId, sessionId, menuId, rating, satisfaction, comments } = req.body;
        
        // Actualizar utilidad del menú
        const utility = readJSON(UTILITY_FILE);
        if (!utility.menus[menuId]) {
            utility.menus[menuId] = {
                totalRatings: 0,
                sumRatings: 0,
                avgRating: 0,
                evaluations: []
            };
        }
        
        const menu = utility.menus[menuId];
        menu.totalRatings++;
        menu.sumRatings += rating;
        menu.avgRating = menu.sumRatings / menu.totalRatings;
        menu.evaluations.push({
            userId,
            sessionId,
            rating,
            satisfaction,
            comments,
            timestamp: new Date().toISOString()
        });
        
        // Verificar si menú debe eliminarse (utilidad < 2 con al menos 5 evaluaciones)
        const shouldRemove = menu.avgRating < 2 && menu.totalRatings >= 5;
        menu.markedForRemoval = shouldRemove;
        
        writeJSON(UTILITY_FILE, utility);
        
        // Actualizar sesión con evaluación
        const sessions = readJSON(SESSIONS_FILE);
        if (sessions.sessions[userId]) {
            const session = sessions.sessions[userId].find(
                s => s.sessionId === sessionId && s.result?.menuId === menuId
            );
            if (session) {
                session.evaluation = { rating, satisfaction, comments };
            }
            writeJSON(SESSIONS_FILE, sessions);
        }
        
        res.json({
            success: true,
            menuUtility: menu.avgRating,
            totalRatings: menu.totalRatings,
            markedForRemoval: shouldRemove
        });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// =============================================================================
// API: HISTORIAL DE SESIONES
// =============================================================================

app.get('/api/sessions/:userId', (req, res) => {
    try {
        const sessions = readJSON(SESSIONS_FILE);
        const userSessions = sessions.sessions[req.params.userId] || [];
        
        res.json({ success: true, sessions: userSessions });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// =============================================================================
// PUENTE PYTHON - CBR
// =============================================================================

function runCBRPython(preferences) {
    return new Promise((resolve, reject) => {
        const pythonScript = path.join(__dirname, 'cbr_bridge.py');
        const cbrDir = path.join(__dirname, '..');
        
        const python = spawn('python', [pythonScript, JSON.stringify(preferences)], {
            cwd: cbrDir
        });
        
        let stdout = '';
        let stderr = '';
        
        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        python.on('close', (code) => {
            if (code !== 0) {
                console.error('Python stderr:', stderr);
                reject(new Error(`Python exited with code ${code}: ${stderr}`));
                return;
            }
            
            try {
                // Buscar JSON en la salida
                const jsonMatch = stdout.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    resolve(JSON.parse(jsonMatch[0]));
                } else {
                    reject(new Error('No JSON output from Python'));
                }
            } catch (e) {
                reject(new Error(`Parse error: ${e.message}`));
            }
        });
    });
}

// =============================================================================
// INICIO DEL SERVIDOR
// =============================================================================

ensureDataFiles();

app.listen(PORT, () => {
    console.log(`
╔══════════════════════════════════════════════════════════════════╗
║     🍽️  SISTEMA CBR DE MENÚS GASTRONÓMICOS  🍽️                    ║
║══════════════════════════════════════════════════════════════════║
║  Servidor activo en: http://localhost:${PORT}                      ║
║  API Endpoints:                                                  ║
║    POST /api/users          - Crear/actualizar usuario           ║
║    POST /api/cbr/search     - Ejecutar búsqueda CBR              ║
║    POST /api/cbr/evaluate   - Evaluar menú                       ║
║    GET  /api/sessions/:id   - Historial de sesiones              ║
╚══════════════════════════════════════════════════════════════════╝
    `);
});
