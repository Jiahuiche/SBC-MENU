/**
 * MAISON CBR - Cliente JavaScript
 * ================================
 * Sistema de Menús Gastronómicos con CBR
 */

// Estado de la aplicación
const state = {
    sessionId: null,
    currentCaseId: null,
    currentMenu: null,
    currentResult: null,
    currentPreferences: null
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    state.sessionId = generateSessionId();
    
    setupFormListeners();
    setupResultsListeners();
    setupStarRating();
}

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// ============================================================================
// FORM LISTENERS
// ============================================================================

function setupFormListeners() {
    const form = document.getElementById('preferencesForm');
    
    // Submit form
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSearch();
    });
    
    // Mostrar opciones de boda cuando se selecciona
    const eventRadios = document.querySelectorAll('input[name="event_type"]');
    eventRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            const weddingOptions = document.getElementById('weddingOptions');
            if (radio.value === 'wedding' && radio.checked) {
                weddingOptions.classList.remove('hidden');
            } else if (radio.checked) {
                weddingOptions.classList.add('hidden');
            }
        });
    });
}

function getFormPreferences() {
    const form = document.getElementById('preferencesForm');
    const formData = new FormData(form);
    
    const preferences = {};
    
    // Tipo de evento
    const eventType = formData.get('event_type');
    if (eventType) preferences.event_type = eventType;
    
    // Cultura
    const culture = formData.get('culture');
    if (culture) preferences.culture = culture;
    
    // Temporada
    const season = formData.get('season');
    if (season) preferences.season = season;
    
    // Restricciones (múltiples checkboxes)
    const restrictions = formData.getAll('restrictions');
    if (restrictions.length > 0) preferences.restrictions = restrictions;
    
    // Precio
    preferences.min_price = parseInt(formData.get('min_price')) || 20;
    preferences.max_price = parseInt(formData.get('max_price')) || 80;
    
    // Opciones de boda
    if (eventType === 'wedding') {
        preferences.quiere_tarta = formData.get('quiere_tarta') === 'true';
        preferences.max_people = parseInt(formData.get('max_people')) || 100;
    }
    
    return preferences;
}

// ============================================================================
// API: BÚSQUEDA CBR
// ============================================================================

async function handleSearch() {
    const preferences = getFormPreferences();
    
    // Validar
    if (!preferences.event_type && !preferences.culture && !preferences.season) {
        alert('Por favor, seleccione al menos un tipo de evento, cultura o temporada.');
        return;
    }
    
    state.currentPreferences = preferences;
    showLoading(true);
    
    try {
        const response = await fetch('/api/cbr/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionId: state.sessionId,
                preferences
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.currentCaseId = data.case_id;
            state.currentResult = data;
            state.currentMenu = data.menu;
            
            displayResults(data);
            showPanel('results');
        } else {
            alert('Error: ' + (data.error || 'No se encontraron menús'));
        }
        
    } catch (error) {
        console.error('Error en búsqueda:', error);
        alert('Error de conexión. Por favor, intente de nuevo.');
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// MOSTRAR RESULTADOS
// ============================================================================

function displayResults(data) {
    // Score
    document.querySelector('.score-value').textContent = data.score.toFixed(2);
    
    // Menu info tags
    const menu = data.menu;
    document.getElementById('menuCulture').textContent = `🌍 ${capitalizeFirst(menu.culture)}`;
    document.getElementById('menuSeason').textContent = `🍂 ${translateSeason(menu.season)}`;
    document.getElementById('menuPrice').textContent = `💰 ${menu.price_per_serving?.toFixed(2) || '--'}€/persona`;
    
    // Courses
    const coursesContainer = document.getElementById('coursesContainer');
    coursesContainer.innerHTML = '';
    
    const courseLabels = {
        starter: 'Entrante',
        main: 'Principal',
        dessert: 'Postre'
    };
    
    for (const [key, course] of Object.entries(menu.courses || {})) {
        const card = document.createElement('div');
        card.className = 'course-card';
        
        card.innerHTML = `
            <span class="course-type">${courseLabels[key] || key}</span>
            <h4 class="course-title">${course.title || 'Sin título'}</h4>
            <div class="course-ingredients">
                ${(course.ingredients || []).slice(0, 12).map(ing => 
                    `<span class="ingredient-tag">${ing}</span>`
                ).join('')}
            </div>
            <span class="course-price">${course.price?.toFixed(2) || '--'}€</span>
        `;
        
        coursesContainer.appendChild(card);
    }
    
    // Adaptations
    displayAdaptations(data.adaptation);
    
    // Validation
    displayValidation(data.validation);
    
    // Reset evaluation
    resetStarRating();
}

function displayAdaptations(adaptation) {
    const section = document.getElementById('adaptationsSection');
    const list = document.getElementById('adaptationsList');
    const summary = document.getElementById('adaptationsSummary');
    const culturePending = document.getElementById('culturePendingInfo');
    
    if (!adaptation || (!adaptation.substitutions || adaptation.substitutions.length === 0) && !adaptation.adapted) {
        section.classList.add('hidden');
        return;
    }
    
    section.classList.remove('hidden');
    list.innerHTML = '';
    
    // Resumen de adaptaciones
    let summaryText = '';
    if (adaptation.restrictions_adapted && adaptation.restrictions_adapted.length > 0) {
        summaryText += `Restricciones adaptadas: ${adaptation.restrictions_adapted.join(', ')}. `;
    }
    if (adaptation.culture_adapted) {
        summaryText += `Cultura adaptada: ${adaptation.culture_adapted}. `;
    }
    summaryText += `Total de cambios: ${adaptation.total_changes}.`;
    summary.textContent = summaryText;
    
    // Renderizar cada sustitución con trazabilidad
    adaptation.substitutions.forEach(sub => {
        const item = document.createElement('div');
        item.className = 'adaptation-item';
        
        // Header con curso y acción
        let headerHTML = `
            <div class="adaptation-header">
                <span class="adaptation-course">${translateCourse(sub.course)}</span>
                <span class="adaptation-action ${sub.action}">${translateAction(sub.action)}</span>
            </div>
        `;
        
        // Cambio principal
        let changeHTML = '<div class="adaptation-change">';
        if (sub.action === 'removed') {
            changeHTML += `
                <span class="original">${sub.original}</span>
                <span class="arrow">→</span>
                <span class="removed">ELIMINADO</span>
            `;
        } else if (sub.action === 'added') {
            changeHTML += `
                <span class="arrow">+</span>
                <span class="substitute">${sub.substitute}</span>
            `;
        } else if (sub.action === 'kept') {
            changeHTML += `
                <span class="original">${sub.original}</span>
                <span class="arrow">→</span>
                <span style="color: var(--warning);">MANTENIDO</span>
            `;
        } else {
            changeHTML += `
                <span class="original">${sub.original || '?'}</span>
                <span class="arrow">→</span>
                <span class="substitute">${sub.substitute || '?'}</span>
            `;
        }
        changeHTML += '</div>';
        
        // Razones/justificaciones
        let reasonsHTML = '';
        if (sub.reason && sub.reason.length > 0) {
            reasonsHTML = '<div class="adaptation-reasons">';
            sub.reason.forEach(r => {
                reasonsHTML += `<div class="reason">${r}</div>`;
            });
            reasonsHTML += '</div>';
        }
        
        // Traza de búsqueda
        let traceHTML = '';
        if (sub.search_attempts && sub.search_attempts.length > 0) {
            traceHTML = `<div class="adaptation-trace">Búsqueda: ${sub.search_attempts.join(' → ')}`;
            if (sub.candidates_found > 0) {
                traceHTML += ` (${sub.candidates_found} candidatos evaluados)`;
            }
            traceHTML += '</div>';
        }
        
        // Nota o warning
        let noteHTML = '';
        if (sub.warning) {
            noteHTML = `<div class="adaptation-warning">⚠️ ${sub.warning}</div>`;
        } else if (sub.note) {
            noteHTML = `<div class="adaptation-trace">ℹ️ ${sub.note}</div>`;
        }
        
        item.innerHTML = headerHTML + changeHTML + reasonsHTML + traceHTML + noteHTML;
        list.appendChild(item);
    });
    
    // Mostrar información de cultura pendiente
    if (adaptation.culture_pending && adaptation.culture_pending_count > 0) {
        culturePending.classList.remove('hidden');
        
        document.getElementById('pendingNote').textContent = 
            adaptation.adaptation_note || 
            `Quedan ${adaptation.culture_pending_count} ingredientes por adaptar culturalmente. ` +
            `Puede solicitar más ajustes usando el panel de abajo.`;
        
        const pendingContainer = document.getElementById('pendingIngredients');
        pendingContainer.innerHTML = '';
        
        if (adaptation.culture_pending_ingredients && adaptation.culture_pending_ingredients.length > 0) {
            adaptation.culture_pending_ingredients.slice(0, 8).forEach(ing => {
                const span = document.createElement('span');
                span.className = 'pending-ingredient';
                span.textContent = ing;
                pendingContainer.appendChild(span);
            });
            
            if (adaptation.culture_pending_ingredients.length > 8) {
                const more = document.createElement('span');
                more.className = 'pending-ingredient';
                more.textContent = `+${adaptation.culture_pending_ingredients.length - 8} más`;
                pendingContainer.appendChild(more);
            }
        }
    } else {
        culturePending.classList.add('hidden');
    }
}

function translateCourse(course) {
    const translations = {
        'starter': 'Entrante',
        'main': 'Principal',
        'dessert': 'Postre'
    };
    return translations[course] || course;
}

function translateAction(action) {
    const translations = {
        'substituted': 'Sustituido',
        'removed': 'Eliminado',
        'added': 'Añadido',
        'kept': 'Mantenido'
    };
    return translations[action] || action;
}

function displayValidation(validation) {
    const section = document.getElementById('validationSection');
    const icon = document.getElementById('validationIcon');
    const text = document.getElementById('validationText');
    const details = document.getElementById('validationDetails');
    
    if (validation.is_valid) {
        section.className = 'validation-section valid';
        icon.textContent = '✓';
        text.textContent = `Menú validado · Performance: ${validation.performance}%`;
        details.innerHTML = '';
    } else {
        section.className = 'validation-section invalid';
        icon.textContent = '⚠';
        text.textContent = `${validation.violations} violaciones encontradas`;
        
        if (validation.violation_details && validation.violation_details.length > 0) {
            details.innerHTML = validation.violation_details.map(v => 
                `<div>• ${v.ingredient || v}: ${v.reason || 'violación detectada'}</div>`
            ).join('');
        }
    }
}

// ============================================================================
// AJUSTE CULTURAL
// ============================================================================

function setupResultsListeners() {
    // Botón añadir cultura
    document.getElementById('btnAddCulture').addEventListener('click', async () => {
        const culture = document.getElementById('adjustCulture').value;
        if (!culture) {
            alert('Por favor, seleccione una cultura.');
            return;
        }
        await handleCultureAdjust('add', culture);
    });
    
    // Botón quitar cultura
    document.getElementById('btnRemoveCulture').addEventListener('click', async () => {
        const culture = document.getElementById('adjustCulture').value;
        if (!culture) {
            alert('Por favor, seleccione una cultura.');
            return;
        }
        await handleCultureAdjust('remove', culture);
    });
    
    // Nueva búsqueda
    document.getElementById('btnNewSearch').addEventListener('click', () => {
        showPanel('preferences');
        resetForm();
    });
    
    // Enviar evaluación
    document.getElementById('btnSubmitRating').addEventListener('click', handleEvaluation);
}

async function handleCultureAdjust(action, culture) {
    showLoading(true);
    
    try {
        const response = await fetch('/api/cbr/adjust', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_id: state.currentCaseId,
                culture_adjustment: action,
                culture_adjustment_target: culture,
                restrictions: state.currentPreferences?.restrictions || []
            })
        });
        
        const data = await response.json();
        const messageDiv = document.getElementById('adjustMessage');
        
        if (data.success && data.adjusted) {
            messageDiv.className = 'adjust-message success';
            messageDiv.textContent = data.message;
            messageDiv.classList.remove('hidden');
            
            // Actualizar menú mostrado
            if (data.menu) {
                state.currentMenu = data.menu;
                // Actualizar visualización de cursos
                updateCoursesDisplay(data.menu);
            }
        } else {
            messageDiv.className = 'adjust-message error';
            messageDiv.textContent = data.message || data.error || 'No se pudo realizar el ajuste';
            messageDiv.classList.remove('hidden');
        }
        
    } catch (error) {
        console.error('Error en ajuste:', error);
        alert('Error de conexión.');
    } finally {
        showLoading(false);
    }
}

function updateCoursesDisplay(menu) {
    const coursesContainer = document.getElementById('coursesContainer');
    coursesContainer.innerHTML = '';
    
    const courseLabels = {
        starter: 'Entrante',
        main: 'Principal',
        dessert: 'Postre'
    };
    
    for (const [key, course] of Object.entries(menu.courses || {})) {
        const card = document.createElement('div');
        card.className = 'course-card';
        
        card.innerHTML = `
            <span class="course-type">${courseLabels[key] || key}</span>
            <h4 class="course-title">${course.title || 'Sin título'}</h4>
            <div class="course-ingredients">
                ${(course.ingredients || []).slice(0, 12).map(ing => 
                    `<span class="ingredient-tag">${ing}</span>`
                ).join('')}
            </div>
            <span class="course-price">${course.price_per_serving?.toFixed(2) || '--'}€</span>
        `;
        
        coursesContainer.appendChild(card);
    }
}

// ============================================================================
// EVALUACIÓN (RETAIN)
// ============================================================================

function setupStarRating() {
    const stars = document.querySelectorAll('#starRating .star');
    
    stars.forEach((star, index) => {
        star.addEventListener('click', () => {
            const value = parseInt(star.dataset.value);
            document.getElementById('ratingValue').value = value;
            
            stars.forEach((s, i) => {
                s.classList.toggle('active', i < value);
            });
            
            document.getElementById('btnSubmitRating').disabled = false;
        });
        
        star.addEventListener('mouseenter', () => {
            stars.forEach((s, i) => {
                s.classList.toggle('hovered', i <= index);
            });
        });
        
        star.addEventListener('mouseleave', () => {
            stars.forEach(s => s.classList.remove('hovered'));
        });
    });
}

function resetStarRating() {
    document.getElementById('ratingValue').value = '0';
    document.querySelectorAll('#starRating .star').forEach(s => {
        s.classList.remove('active', 'hovered');
    });
    document.getElementById('btnSubmitRating').disabled = true;
}

async function handleEvaluation() {
    const rating = parseInt(document.getElementById('ratingValue').value);
    
    if (rating === 0) {
        alert('Por favor, seleccione una puntuación.');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/cbr/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                menu: state.currentMenu,
                original_input: state.currentPreferences,
                adaptation_steps: state.currentResult?.adaptation?.substitutions || [],
                revision: {
                    performance: (state.currentResult?.validation?.performance || 80) / 100,
                    violations: state.currentResult?.validation?.violation_details || []
                },
                user_feedback: rating
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let message = `¡Gracias por su evaluación!\n\nUtilidad calculada: ${(data.usefulness * 100).toFixed(1)}%`;
            if (data.case_saved) {
                message += '\n\nEste caso ha sido guardado en nuestra base de conocimiento.';
            }
            alert(message);
            
            if (confirm('¿Desea buscar otro menú?')) {
                showPanel('preferences');
                resetForm();
            }
        } else {
            alert('Error al guardar evaluación: ' + data.error);
        }
        
    } catch (error) {
        console.error('Error en evaluación:', error);
        alert('Error de conexión.');
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// UTILIDADES
// ============================================================================

function showPanel(panelName) {
    document.getElementById('preferencesPanel').classList.toggle('hidden', panelName !== 'preferences');
    document.getElementById('resultsPanel').classList.toggle('hidden', panelName !== 'results');
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLoading(show) {
    document.getElementById('loadingOverlay').classList.toggle('hidden', !show);
}

function resetForm() {
    document.getElementById('preferencesForm').reset();
    document.getElementById('weddingOptions').classList.add('hidden');
    document.getElementById('adjustMessage').classList.add('hidden');
    resetStarRating();
}

function capitalizeFirst(str) {
    if (!str) return 'N/A';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function translateSeason(season) {
    const translations = {
        'spring': 'Primavera',
        'summer': 'Verano',
        'fall': 'Otoño',
        'winter': 'Invierno',
        'any': 'Cualquier temporada'
    };
    return translations[season?.toLowerCase()] || season || 'N/A';
}
