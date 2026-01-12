/**
 * Servidor Express para Sistema CBR de Menús Gastronómicos
 * =========================================================
 * APIs actualizadas para el sistema CBR modular
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

// Rutas a bases de datos
const DATA_DIR = path.join(__dirname, 'data');
const SESSIONS_FILE = path.join(DATA_DIR, 'sessions.json');

// Asegurar que existen los archivos de datos
function ensureDataFiles() {
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(SESSIONS_FILE)) {
        fs.writeFileSync(SESSIONS_FILE, JSON.stringify({ sessions: {} }, null, 2));
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
// API: CBR - BÚSQUEDA
// =============================================================================

app.post('/api/cbr/search', async (req, res) => {
    try {
        const { sessionId, preferences } = req.body;
        const currentSessionId = sessionId || uuidv4();
        
        console.log('🔍 Búsqueda CBR recibida:', preferences);
        
        // Ejecutar CBR via Python
        const result = await runCBRPython('search', preferences);
        
        // Guardar sesión
        const sessions = readJSON(SESSIONS_FILE);
        if (!sessions.sessions[currentSessionId]) {
            sessions.sessions[currentSessionId] = {
                created: new Date().toISOString(),
                searches: []
            };
        }
        
        sessions.sessions[currentSessionId].searches.push({
            timestamp: new Date().toISOString(),
            preferences,
            result: {
                case_id: result.case_id,
                score: result.score,
                success: result.success
            }
        });
        
        writeJSON(SESSIONS_FILE, sessions);
        
        res.json({
            success: true,
            sessionId: currentSessionId,
            ...result
        });
        
    } catch (error) {
        console.error('❌ Error en CBR search:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// =============================================================================
// API: CBR - AJUSTE CULTURAL (SEGUNDA RONDA)
// =============================================================================

app.post('/api/cbr/adjust', async (req, res) => {
    try {
        const { case_id, culture_adjustment, culture_adjustment_target, restrictions } = req.body;
        
        console.log('🔧 Ajuste cultural:', { case_id, culture_adjustment, culture_adjustment_target });
        
        const result = await runCBRPython('adjust', {
            case_id,
            culture_adjustment,
            culture_adjustment_target,
            restrictions
        });
        
        res.json(result);
        
    } catch (error) {
        console.error('❌ Error en ajuste cultural:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// =============================================================================
// API: CBR - EVALUACIÓN Y RETAIN
// =============================================================================

app.post('/api/cbr/evaluate', async (req, res) => {
    try {
        const { menu, original_input, adaptation_steps, revision, user_feedback } = req.body;
        
        console.log('⭐ Evaluación recibida:', { user_feedback });
        
        const result = await runCBRPython('retain', {
            menu,
            original_input,
            adaptation_steps,
            revision,
            user_feedback
        });
        
        res.json(result);
        
    } catch (error) {
        console.error('❌ Error en evaluación:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// =============================================================================
// PUENTE PYTHON - CBR
// =============================================================================

function runCBRPython(action, data) {
    return new Promise((resolve, reject) => {
        const pythonScript = path.join(__dirname, 'cbr_bridge.py');
        
        const inputData = JSON.stringify({
            action,
            preferences: action === 'search' || action === 'adjust' ? data : undefined,
            data: action === 'retain' ? data : undefined
        });
        
        console.log('🐍 Ejecutando Python con:', action);
        
        const python = spawn('python', [pythonScript, inputData], {
            cwd: __dirname
        });
        
        let stdout = '';
        let stderr = '';
        
        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        python.stderr.on('data', (data) => {
            stderr += data.toString();
            console.log('Python stderr:', data.toString());
        });
        
        python.on('close', (code) => {
            if (code !== 0) {
                console.error('Python exited with code:', code);
                console.error('Stderr:', stderr);
                reject(new Error(`Python error: ${stderr || 'Unknown error'}`));
                return;
            }
            
            try {
                // Buscar JSON en la salida
                const jsonMatch = stdout.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    const result = JSON.parse(jsonMatch[0]);
                    resolve(result);
                } else {
                    reject(new Error('No JSON output from Python'));
                }
            } catch (e) {
                console.error('Parse error:', e.message);
                console.error('Stdout was:', stdout);
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
║                                                                  ║
║      ◆  MAISON CBR - Sistema de Menús Gastronómicos  ◆          ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Servidor activo en: http://localhost:${PORT}                      ║
║                                                                  ║
║  API Endpoints:                                                  ║
║    POST /api/cbr/search    - Búsqueda CBR                        ║
║    POST /api/cbr/adjust    - Ajuste cultural (2ª ronda)          ║
║    POST /api/cbr/evaluate  - Evaluar y guardar caso              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    `);
});
