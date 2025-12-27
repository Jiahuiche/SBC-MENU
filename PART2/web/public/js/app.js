/**
 * Sistema CBR de Menús - JavaScript Cliente
 * ==========================================
 * Maneja la lógica de UI, llamadas a API y flujo del usuario
 */

// Estado de la aplicación
const state = {
    userId: localStorage.getItem('cbr_user_id') || generateUserId(),
    sessionId: null,
    searchCount: 0,
    currentMenuId: null,
    currentResult: null
};

// Guardar userId en localStorage
localStorage.setItem('cbr_user_id', state.userId);

// Generar ID de usuario único
function generateUserId() {
    return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Generar ID de sesión
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// =============================================================================
// INICIALIZACIÓN
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    // Iniciar nueva sesión
    state.sessionId = generateSessionId();
    updateSessionDisplay();
    
    // Event listeners
    setupFormListeners();
    setupEvaluationListeners();
    setupPriceSlider();
}

// =============================================================================
// UI: SESSION TRACKER
// =============================================================================

function updateSessionDisplay() {
    document.getElementById('sessionId').textContent = state.sessionId.slice(0, 12) + '...';
    
    const countEl = document.getElementById('searchCount');
    if (state.searchCount > 0) {
        countEl.textContent = `(Búsqueda #${state.searchCount})`;
    } else {
        countEl.textContent = '';
    }
}

// =============================================================================
// FORM: PREFERENCIAS
// =============================================================================

function setupFormListeners() {
    const form = document.getElementById('preferencesForm');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSearch();
    });
}

function setupPriceSlider() {
    const slider = document.getElementById('maxPrice');
    const output = document.getElementById('priceOutput');
    
    slider.addEventListener('input', () => {
        output.textContent = slider.value + '€';
    });
}

function getFormPreferences() {
    const form = document.getElementById('preferencesForm');
    const formData = new FormData(form);
    
    const preferences = {};
    
    // Cultura
    const cultura = formData.get('cultura');
    if (cultura) preferences.cultura = cultura;
    
    // Estilo
    const estilo = formData.get('estilo_cocina');
    if (estilo) preferences.estilo_cocina = estilo;
    
    // Temporada
    const season = formData.get('season');
    if (season) preferences.season = season;
    
    // Restricciones dietéticas (checkboxes)
    preferences.is_vegan = formData.get('is_vegan') === 'true';
    preferences.is_vegetarian = formData.get('is_vegetarian') === 'true';
    preferences.is_gluten_free = formData.get('is_gluten_free') === 'true';
    preferences.is_dairy_free = formData.get('is_dairy_free') === 'true';
    preferences.is_kosher = formData.get('is_kosher') === 'true';
    preferences.is_halal = formData.get('is_halal') === 'true';
    
    // Precio
    preferences.max_price = parseInt(formData.get('max_price'));
    
    return preferences;
}

// =============================================================================
// API: BÚSQUEDA CBR
// =============================================================================

async function handleSearch() {
    const preferences = getFormPreferences();
    
    // Validar que hay al menos una preferencia
    if (!preferences.cultura && !preferences.estilo_cocina && !preferences.season) {
        alert('Por favor, selecciona al menos una cultura, estilo o temporada.');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/cbr/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: state.userId,
                sessionId: state.sessionId,
                preferences
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.searchCount = data.searchNumber;
            state.currentResult = data.result;
            state.currentMenuId = data.result.menu?.menu_id;
            
            updateSessionDisplay();
            displayResults(data.result);
            showPanel('results');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error en búsqueda:', error);
        alert('Error de conexión. Por favor, intenta de nuevo.');
    } finally {
        showLoading(false);
    }
}

// =============================================================================
// UI: MOSTRAR RESULTADOS
// =============================================================================

function displayResults(result) {
    if (!result.success) {
        alert('No se encontraron menús: ' + result.error);
        return;
    }
    
    const menu = result.menu;
    
    // Similitud
    document.querySelector('.similarity-value').textContent = result.similarity;
    
    // Nombre del menú
    document.getElementById('menuName').textContent = menu.menu_name || 'Menú Recomendado';
    
    // Tags del menú
    const tagsContainer = document.getElementById('menuTags');
    tagsContainer.innerHTML = '';
    
    const tags = [
        { icon: '🌍', text: menu.culture },
        { icon: '👨‍🍳', text: menu.style },
        { icon: '🍂', text: translateSeason(menu.season) },
        { icon: '🍷', text: menu.wine_pairing }
    ];
    
    tags.forEach(tag => {
        if (tag.text && tag.text !== 'N/A') {
            const span = document.createElement('span');
            span.className = 'menu-tag';
            span.textContent = `${tag.icon} ${tag.text}`;
            tagsContainer.appendChild(span);
        }
    });
    
    // Certificaciones
    const certs = menu.certifications;
    if (certs) {
        if (certs.is_vegan) addTag(tagsContainer, '🌱 Vegano');
        if (certs.is_vegetarian && !certs.is_vegan) addTag(tagsContainer, '🥬 Vegetariano');
        if (certs.is_gluten_free) addTag(tagsContainer, '🌾 Sin Gluten');
        if (certs.is_dairy_free) addTag(tagsContainer, '🥛 Sin Lácteos');
        if (certs.is_kosher) addTag(tagsContainer, '✡️ Kosher');
        if (certs.is_halal) addTag(tagsContainer, '☪️ Halal');
    }
    
    // Cursos
    const coursesContainer = document.getElementById('coursesContainer');
    coursesContainer.innerHTML = '';
    
    const courseNames = {
        starter: { name: 'Entrante', icon: '🥗' },
        main: { name: 'Principal', icon: '🍖' },
        dessert: { name: 'Postre', icon: '🍰' }
    };
    
    for (const [key, course] of Object.entries(menu.courses || {})) {
        const info = courseNames[key] || { name: key, icon: '🍽️' };
        const card = createCourseCard(key, info, course);
        coursesContainer.appendChild(card);
    }
    
    // Adaptaciones
    displayAdaptations(result.adaptations);
    
    // Validación
    displayValidation(result.validation);
    
    // Totales
    document.getElementById('totalPrice').textContent = `${menu.total_price?.toFixed(2) || '--'}€`;
    document.getElementById('totalTime').textContent = `${menu.avg_time || '--'} min`;
    
    // Mostrar panel de evaluación
    document.getElementById('evaluationPanel').classList.remove('hidden');
    resetEvaluationForm();
}

function addTag(container, text) {
    const span = document.createElement('span');
    span.className = 'menu-tag';
    span.textContent = text;
    container.appendChild(span);
}

function createCourseCard(key, info, course) {
    const card = document.createElement('div');
    card.className = `course-card ${key} fade-in`;
    
    card.innerHTML = `
        <div class="course-header">
            <span class="course-type">${info.icon} ${info.name}</span>
            <span class="course-price">${course.price?.toFixed(2) || '--'}€</span>
        </div>
        <div class="course-title">${course.title || 'Sin título'}</div>
        <div class="course-ingredients">
            ${(course.ingredients || []).map(ing => 
                `<span class="ingredient-tag">${ing}</span>`
            ).join('')}
        </div>
    `;
    
    return card;
}

function displayAdaptations(adaptations) {
    const section = document.getElementById('adaptationsSection');
    const list = document.getElementById('adaptationsList');
    
    if (!adaptations || adaptations.total_changes === 0) {
        section.classList.add('hidden');
        return;
    }
    
    section.classList.remove('hidden');
    list.innerHTML = '';
    
    // Mostrar sustituciones
    (adaptations.substitutions || []).slice(0, 8).forEach(sub => {
        const item = document.createElement('div');
        item.className = 'adaptation-item';
        
        const typeName = getAdaptationTypeName(sub.type);
        
        item.innerHTML = `
            <span class="adaptation-type ${sub.type}">${typeName}</span>
            <span class="adaptation-change">
                <strong>${sub.original}</strong>
                <span class="adaptation-arrow">→</span>
                <strong>${sub.substitute}</strong>
            </span>
        `;
        list.appendChild(item);
    });
    
    // Mostrar cambios de proceso
    (adaptations.process_changes || []).slice(0, 4).forEach(proc => {
        const item = document.createElement('div');
        item.className = 'adaptation-item';
        
        item.innerHTML = `
            <span class="adaptation-type style">PROCESO</span>
            <span class="adaptation-change">
                <strong>${proc.original_method}</strong>
                <span class="adaptation-arrow">→</span>
                <strong>${proc.new_method}</strong>
            </span>
        `;
        list.appendChild(item);
    });
}

function displayValidation(validation) {
    const section = document.getElementById('validationSection');
    
    if (!validation) {
        section.classList.add('hidden');
        return;
    }
    
    section.classList.remove('hidden');
    section.className = `validation-section ${validation.is_valid ? 'valid' : 'invalid'}`;
    
    const icon = validation.is_valid ? '✅' : '⚠️';
    const message = validation.is_valid ? 'Menú validado correctamente' : 'Menú con advertencias';
    
    let detailsHTML = '';
    
    if (validation.critical_issues?.length > 0) {
        detailsHTML += validation.critical_issues.map(issue => `<div>${issue}</div>`).join('');
    }
    
    if (validation.warnings?.length > 0) {
        detailsHTML += validation.warnings.map(warn => `<div>${warn}</div>`).join('');
    }
    
    section.innerHTML = `
        <span class="validation-icon">${icon}</span>
        <span class="validation-message">${message}</span>
        ${detailsHTML ? `<div class="validation-details">${detailsHTML}</div>` : ''}
    `;
}

// =============================================================================
// EVALUACIÓN
// =============================================================================

function setupEvaluationListeners() {
    // Stars
    const stars = document.querySelectorAll('#starRating .star');
    stars.forEach(star => {
        star.addEventListener('click', () => {
            const value = parseInt(star.dataset.value);
            document.getElementById('ratingInput').value = value;
            
            stars.forEach((s, idx) => {
                s.classList.toggle('active', idx < value);
            });
        });
        
        star.addEventListener('mouseenter', () => {
            const value = parseInt(star.dataset.value);
            stars.forEach((s, idx) => {
                s.style.color = idx < value ? 'var(--primary-color)' : '';
            });
        });
    });
    
    document.getElementById('starRating').addEventListener('mouseleave', () => {
        const currentValue = parseInt(document.getElementById('ratingInput').value);
        const stars = document.querySelectorAll('#starRating .star');
        stars.forEach((s, idx) => {
            s.style.color = '';
        });
    });
    
    // Satisfaction buttons
    const satBtns = document.querySelectorAll('.sat-btn');
    satBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            satBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('satisfactionInput').value = btn.dataset.value;
        });
    });
    
    // Submit evaluation
    document.getElementById('evaluationForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleEvaluation();
    });
    
    // New search
    document.getElementById('newSearchBtn').addEventListener('click', () => {
        showPanel('preferences');
        resetEvaluationForm();
    });
}

function resetEvaluationForm() {
    document.getElementById('ratingInput').value = '0';
    document.getElementById('satisfactionInput').value = '';
    document.getElementById('commentsInput').value = '';
    
    document.querySelectorAll('#starRating .star').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.sat-btn').forEach(b => b.classList.remove('active'));
}

async function handleEvaluation() {
    const rating = parseInt(document.getElementById('ratingInput').value);
    const satisfaction = document.getElementById('satisfactionInput').value;
    const comments = document.getElementById('commentsInput').value;
    
    if (rating === 0) {
        alert('Por favor, selecciona una puntuación de estrellas.');
        return;
    }
    
    if (!satisfaction) {
        alert('Por favor, indica tu nivel de satisfacción.');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/cbr/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: state.userId,
                sessionId: state.sessionId,
                menuId: state.currentMenuId,
                rating,
                satisfaction,
                comments
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const message = `¡Gracias por tu evaluación!\n\nUtilidad del menú: ${data.menuUtility.toFixed(1)}/5\nTotal de evaluaciones: ${data.totalRatings}`;
            alert(message);
            
            // Si no está satisfecho, permitir nueva búsqueda
            if (satisfaction === 'insatisfecho' || satisfaction === 'neutral') {
                if (confirm('¿Deseas realizar una nueva búsqueda con preferencias diferentes?')) {
                    showPanel('preferences');
                }
            } else {
                // Satisfecho - ofrecer nueva sesión o terminar
                if (confirm('¿Deseas buscar otro menú?')) {
                    showPanel('preferences');
                }
            }
            
            resetEvaluationForm();
        } else {
            alert('Error al guardar evaluación: ' + data.error);
        }
    } catch (error) {
        console.error('Error en evaluación:', error);
        alert('Error de conexión. Por favor, intenta de nuevo.');
    } finally {
        showLoading(false);
    }
}

// =============================================================================
// UTILIDADES
// =============================================================================

function showPanel(panelName) {
    const panels = {
        preferences: document.getElementById('preferencesPanel'),
        results: document.getElementById('resultsPanel'),
        evaluation: document.getElementById('evaluationPanel')
    };
    
    // Ocultar todos primero
    Object.values(panels).forEach(p => p.classList.add('hidden'));
    
    // Mostrar los necesarios
    if (panelName === 'preferences') {
        panels.preferences.classList.remove('hidden');
        panels.results.classList.add('hidden');
        panels.evaluation.classList.add('hidden');
    } else if (panelName === 'results') {
        panels.preferences.classList.add('hidden');
        panels.results.classList.remove('hidden');
        panels.evaluation.classList.remove('hidden');
    }
    
    // Scroll al inicio
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.toggle('hidden', !show);
}

function translateSeason(season) {
    const translations = {
        'Spring': 'Primavera',
        'Summer': 'Verano',
        'Fall': 'Otoño',
        'Winter': 'Invierno'
    };
    return translations[season] || season;
}

function getAdaptationTypeName(type) {
    const names = {
        'cultural': 'CULTURAL',
        'dietary': 'DIETÉTICO',
        'seasonal': 'ESTACIONAL',
        'style': 'ESTILO'
    };
    return names[type] || type.toUpperCase();
}
