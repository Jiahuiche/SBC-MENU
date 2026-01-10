import sys
def prompt_number(prompt, minimum):
    """Solicita un número al usuario con validación."""
    while True:
        try:
            value = float(input(f"    {prompt}"))
            if value >= minimum:
                return value
            else:
                print(f"    ⚠️  Por favor, ingrese un valor ≥ {minimum}\n")
        except ValueError:
            print(f"    ⚠️  Por favor, ingrese un valor numérico válido\n")

def get_user_restrictions(first_input=None):
    """Recopila las preferencias del usuario para el menú."""
    
    print("\n" + "="*70)
    print("SISTEMA DE MENÚS GASTRONÓMICOS")
    print("="*70 + "\n")
    
    # Tipo de evento
    print("Tipo de Evento")
    print("  - wedding  : Boda")
    print("  - congress : Evento corporativo")
    print("  - family   : Reunión familiar")
    if first_input:
        event_type = first_input
    else:
        event_type = input("\nIngrese el tipo de evento: ").strip().lower()

    # Tarta especial (solo para bodas y eventos familiares)
    quiere_tarta = False
    if event_type in ['wedding', 'family']:
        cake_response = input("\n¿Desea incluir una tarta especial? (yes/no): ").strip().lower()
        quiere_tarta = (cake_response == 'yes')
    
    # Número de personas
    print("\nNúmero de Invitados")
    max_people = int(prompt_number("Cantidad máxima de personas (≥1): ", 1))
    
    # Temporada
    print("\nEstación del Año")
    print("  - spring : Primavera")
    print("  - summer : Verano")
    print("  - autumn : Otoño")
    print("  - winter : Invierno")
    print("  - any    : Cualquier temporada")
    season = input("\nEstación preferida: ").strip().lower()
    if not season or season == 'any':
        season = 'any-season'

    # Gastronomia cultural
    print("\nGastronomía Cultural")
    print("  - Italian  : Italiana")
    print("  - Chinese  : China")
    print("  - Japanese  : Japonesa")
    print("  - Korean  : Coreana")
    print("  - Latin American  : Latinoamericana")
    print("  - South Asian  : Sudasiática")
    print("  - Mediterranean : Mediterránea")
    print("  - French/Western European : Francesa/Europa Occidental")
    print("  - Middle Eastern/North African : Oriente Medio/Norteafricana")
    print("  - East Asian : Este Asiática (General)")
    print("  - American : Estadounidense")
    cuisine = input("\nCocina preferida: ").strip().lower()
    
    # Restricciones dietéticas
    print("\nRestricciones Dietéticas")
    print("Opciones: gluten-free, vegetarian, vegan, dairy-free, kosher,")
    print("          halal, shellfish-free, soy-free, nut-free")
    print("\nIngrese una restricción por línea. Presione Enter para finalizar.\n")
    
    restrictions = []
    while True:
        entry = input("  → ").strip().lower()
        if not entry or entry == 'exit':
            break
        if entry not in restrictions:
            restrictions.append(entry)
    
    # Presupuesto
    print("\nPresupuesto por Persona")
    min_price = prompt_number("Precio mínimo por persona (€, ≥0): ", 0)
    max_price = prompt_number("Precio máximo por persona (€, ≥mínimo): ", min_price)
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PREFERENCIAS")
    print("="*70)
    print(f"  • Tipo de evento     : {event_type}")
    print(f"  • Número de personas : {max_people}")
    print(f"  • Temporada          : {season}")
    print(f"  • Gastronomía        : {cuisine}")
    print(f"  • Presupuesto        : {min_price}€ - {max_price}€ por persona")
    print(f"  • Tarta especial     : {'Sí' if quiere_tarta else 'No'}")
    print(f"  • Restricciones      : {', '.join(restrictions) if restrictions else 'Ninguna'}")
    print("="*70 + "\n")
    
    return {
        'event_type': event_type,
        'max_people': max_people,
        'season': season,
        'cuisine': cuisine,
        'restrictions': restrictions,
        'min_price': min_price,
        'max_price': max_price,
        'quiere_tarta': quiere_tarta
    }

if __name__ == "__main__":
    # Detectamos si la entrada es un archivo redirigido (ej. python script.py < test.txt)
    is_redirected = not sys.stdin.isatty()

    try:
        if is_redirected:
            # MODO TEST: Bucle para procesar múltiples casos en el archivo
            while True:
                linea = sys.stdin.readline()
                if not linea: break # Fin del archivo
                
                linea = linea.strip()
                # Saltamos líneas vacías, comentarios o separadores como ---
                if not linea or linea.startswith(('-', '#')):
                    print(linea)
                    continue
                
                # Ejecutamos la función pasando la línea como el tipo de evento
                user_data = get_user_restrictions(first_input=linea.lower())
        else:
            # MODO MANUAL: Funciona como siempre
            user_data = get_user_restrictions()
            print("Datos recopilados exitosamente!")

    except (EOFError, KeyboardInterrupt):
        print("\n[INFO] Finalización del programa.")