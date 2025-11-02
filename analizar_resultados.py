#!/usr/bin/env python3
"""
Analizador de salida de CLIPS
Lee un archivo .txt con la salida completa y genera análisis
"""

import re
import json
from pathlib import Path
from collections import defaultdict

class CLIPSOutputParser:
    def __init__(self, output_file):
        self.output_file = Path(output_file)
        with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
            self.content = f.read()
        
        self.experiments = []
        self.parse_experiments()
    
    def parse_experiments(self):
        """Divide la salida en experimentos individuales"""
        # Buscar todos los experimentos
        pattern = r'EXPERIMENTO (\d+): ([^\n]+)'
        matches = re.finditer(pattern, self.content)
        
        positions = []
        for match in matches:
            positions.append({
                'num': match.group(1),
                'name': match.group(2).strip(),
                'start': match.start()
            })
        
        # Extraer contenido de cada experimento
        for i, pos in enumerate(positions):
            start = pos['start']
            end = positions[i+1]['start'] if i+1 < len(positions) else len(self.content)
            
            exp_content = self.content[start:end]
            experiment = self.parse_single_experiment(exp_content, pos['num'], pos['name'])
            self.experiments.append(experiment)
    
    def parse_single_experiment(self, content, num, name):
        """Analiza un experimento individual"""
        exp = {
            'num': num,
            'name': name,
            'config': {},
            'candidates': {},
            'menus': {},
            'perfect_match': False,
            'errors': []
        }
        
        # Extraer configuración
        event_match = re.search(r'Event type.*?:\s*(\w+)', content)
        if event_match:
            exp['config']['event_type'] = event_match.group(1)
        
        cake_match = re.search(r'cake\?.*?:\s*(\w+)', content, re.IGNORECASE)
        if cake_match:
            exp['config']['cake'] = cake_match.group(1).lower() == 'yes'
        
        people_match = re.search(r'people.*?:\s*(\d+)', content)
        if people_match:
            exp['config']['max_people'] = int(people_match.group(1))
        
        season_match = re.search(r'Season.*?:\s*(\S+)', content)
        if season_match:
            exp['config']['season'] = season_match.group(1)
        
        # Extraer restricciones
        restrictions = re.findall(r'>\s*(gluten-free|vegetarian|vegan|dairy-free|kosher|halal|shellfish-free|soy-free|nut-free)', content)
        exp['config']['restrictions'] = restrictions
        
        # Extraer precios
        min_price_match = re.search(r'Minimum price.*?:\s*(\d+)', content)
        max_price_match = re.search(r'Maximum price.*?:\s*(\d+)', content)
        if min_price_match and max_price_match:
            exp['config']['min_price'] = int(min_price_match.group(1))
            exp['config']['max_price'] = int(max_price_match.group(1))
        
        # Extraer candidatos
        total_match = re.search(r'TOTAL de candidatos:\s*(\d+)', content)
        if total_match:
            exp['candidates']['total'] = int(total_match.group(1))
        
        # Candidatos por restricción
        for i in range(5):
            pattern = f'Recetas con {i} restriccion.*?:\\s*(\\d+)'
            match = re.search(pattern, content)
            if match:
                exp['candidates'][f'rest_{i}'] = int(match.group(1))
        
        # Extraer límites de precio
        limits_match = re.search(r'Final:\s*([\d.]+)\s*-\s*([\d.]+)', content)
        if limits_match:
            exp['limits'] = {
                'min': float(limits_match.group(1)),
                'max': float(limits_match.group(2))
            }
        
        # Detectar menús creados
        exp['menus']['barato'] = 'MENÚ BARATO CREADO' in content
        exp['menus']['medio'] = 'MENÚ MEDIO CREADO' in content
        exp['menus']['caro'] = 'MENÚ CARO CREADO' in content
        
        # Extraer precios de menús
        barato_match = re.search(r'MENÚ BARATO CREADO:\s*([\d.]+)', content)
        medio_match = re.search(r'MENÚ MEDIO CREADO:\s*([\d.]+)', content)
        caro_match = re.search(r'MENÚ CARO CREADO:\s*([\d.]+)', content)
        
        if barato_match:
            exp['menus']['barato_price'] = float(barato_match.group(1))
        if medio_match:
            exp['menus']['medio_price'] = float(medio_match.group(1))
        if caro_match:
            exp['menus']['caro_price'] = float(caro_match.group(1))
        
        # Detectar aperitivos
        aperitivos_match = re.search(r'(\d+) aperitivos seleccionados', content)
        if aperitivos_match:
            exp['aperitivos'] = int(aperitivos_match.group(1))
        else:
            exp['aperitivos'] = 0
        
        # Detectar tarta
        exp['cake_included'] = 'PLUS: Tarta' in content
        
        # Detectar modo relajado
        exp['fallback'] = 'versión relajada' in content or 'modo relajado' in content.lower()
        
        # Detectar perfect match
        exp['perfect_match'] = 'Se encontraron platos que satisfacen todas' in content
        
        # Detectar errores
        if 'ERROR' in content:
            exp['errors'].append('ERROR encontrado')
        if 'No se pudo crear' in content:
            exp['errors'].append('No se pudo crear menú')
        
        return exp
    
    def generate_summary_table(self):
        """Genera tabla resumen en formato texto"""
        lines = []
        lines.append("=" * 120)
        lines.append("TABLA RESUMEN DE EXPERIMENTOS")
        lines.append("=" * 120)
        
        header = f"{'#':<4} {'Nombre':<40} {'Event':<10} {'Rest':<5} {'Cand':<6} {'B':<3} {'M':<3} {'C':<3} {'PM':<3} {'FB':<3}"
        lines.append(header)
        lines.append("-" * 120)
        
        for exp in self.experiments:
            num_rest = len(exp['config'].get('restrictions', []))
            cand = exp['candidates'].get('total', 0)
            event = exp['config'].get('event_type', '?')[:8]
            
            b = '✓' if exp['menus'].get('barato', False) else '✗'
            m = '✓' if exp['menus'].get('medio', False) else '✗'
            c = '✓' if exp['menus'].get('caro', False) else '✗'
            pm = '✓' if exp.get('perfect_match', False) else '✗'
            fb = '✓' if exp.get('fallback', False) else '✗'
            
            name = exp['name'][:38]
            
            line = f"{exp['num']:<4} {name:<40} {event:<10} {num_rest:<5} {cand:<6} {b:<3} {m:<3} {c:<3} {pm:<3} {fb:<3}"
            lines.append(line)
        
        lines.append("=" * 120)
        lines.append("\nLeyenda:")
        lines.append("  B/M/C: Menú Barato/Medio/Caro creado")
        lines.append("  PM: Perfect Match")
        lines.append("  FB: Fallback activado")
        lines.append("  Rest: Número de restricciones")
        lines.append("  Cand: Candidatos totales")
        
        return "\n".join(lines)
    
    def generate_statistics(self):
        """Genera estadísticas globales"""
        stats = {
            'total_experiments': len(self.experiments),
            'menus_created': {
                'barato': 0,
                'medio': 0,
                'caro': 0
            },
            'perfect_matches': 0,
            'fallbacks': 0,
            'by_event_type': defaultdict(lambda: {'total': 0, 'success': 0}),
            'by_restrictions': defaultdict(lambda: {'total': 0, 'success': 0}),
            'avg_candidates': 0,
            'errors': 0
        }
        
        total_cand = 0
        
        for exp in self.experiments:
            # Contar menús creados
            if exp['menus'].get('barato'):
                stats['menus_created']['barato'] += 1
            if exp['menus'].get('medio'):
                stats['menus_created']['medio'] += 1
            if exp['menus'].get('caro'):
                stats['menus_created']['caro'] += 1
            
            # Perfect matches y fallbacks
            if exp.get('perfect_match'):
                stats['perfect_matches'] += 1
            if exp.get('fallback'):
                stats['fallbacks'] += 1
            
            # Por tipo de evento
            event = exp['config'].get('event_type', 'unknown')
            stats['by_event_type'][event]['total'] += 1
            if all(exp['menus'].get(m, False) for m in ['barato', 'medio', 'caro']):
                stats['by_event_type'][event]['success'] += 1
            
            # Por número de restricciones
            num_rest = len(exp['config'].get('restrictions', []))
            stats['by_restrictions'][num_rest]['total'] += 1
            if all(exp['menus'].get(m, False) for m in ['barato', 'medio', 'caro']):
                stats['by_restrictions'][num_rest]['success'] += 1
            
            # Candidatos
            cand = exp['candidates'].get('total', 0)
            total_cand += cand
            
            # Errores
            if exp.get('errors'):
                stats['errors'] += 1
        
        stats['avg_candidates'] = total_cand / len(self.experiments) if self.experiments else 0
        
        return stats
    
    def generate_report(self):
        """Genera reporte completo"""
        lines = []
        
        lines.append("=" * 80)
        lines.append("REPORTE DE ANÁLISIS DE EXPERIMENTOS CLIPS")
        lines.append("=" * 80)
        lines.append(f"\nArchivo analizado: {self.output_file.name}")
        lines.append(f"Total de experimentos: {len(self.experiments)}\n")
        
        # Estadísticas globales
        stats = self.generate_statistics()
        
        lines.append("\n" + "=" * 80)
        lines.append("ESTADÍSTICAS GLOBALES")
        lines.append("=" * 80)
        
        total = stats['total_experiments']
        
        lines.append(f"\nMenús Creados:")
        lines.append(f"  Barato: {stats['menus_created']['barato']}/{total} ({stats['menus_created']['barato']/total*100:.1f}%)")
        lines.append(f"  Medio:  {stats['menus_created']['medio']}/{total} ({stats['menus_created']['medio']/total*100:.1f}%)")
        lines.append(f"  Caro:   {stats['menus_created']['caro']}/{total} ({stats['menus_created']['caro']/total*100:.1f}%)")
        
        lines.append(f"\nPerfect Matches: {stats['perfect_matches']}/{total} ({stats['perfect_matches']/total*100:.1f}%)")
        lines.append(f"Fallback Activado: {stats['fallbacks']}/{total} ({stats['fallbacks']/total*100:.1f}%)")
        lines.append(f"Candidatos Promedio: {stats['avg_candidates']:.1f}")
        lines.append(f"Experimentos con Errores: {stats['errors']}/{total}")
        
        # Por tipo de evento
        lines.append("\n" + "=" * 80)
        lines.append("RESULTADOS POR TIPO DE EVENTO")
        lines.append("=" * 80)
        for event, data in sorted(stats['by_event_type'].items()):
            rate = data['success']/data['total']*100 if data['total'] > 0 else 0
            lines.append(f"\n{event.upper()}:")
            lines.append(f"  Total: {data['total']}")
            lines.append(f"  Éxito completo: {data['success']}/{data['total']} ({rate:.1f}%)")
        
        # Por número de restricciones
        lines.append("\n" + "=" * 80)
        lines.append("RESULTADOS POR NÚMERO DE RESTRICCIONES")
        lines.append("=" * 80)
        for num_rest in sorted(stats['by_restrictions'].keys()):
            data = stats['by_restrictions'][num_rest]
            rate = data['success']/data['total']*100 if data['total'] > 0 else 0
            lines.append(f"\n{num_rest} restricciones:")
            lines.append(f"  Total: {data['total']}")
            lines.append(f"  Éxito completo: {data['success']}/{data['total']} ({rate:.1f}%)")
        
        # Tabla resumen
        lines.append("\n\n")
        lines.append(self.generate_summary_table())
        
        # Detalles de experimentos fallidos
        failed = [e for e in self.experiments if not all(e['menus'].get(m, False) for m in ['barato', 'medio', 'caro'])]
        if failed:
            lines.append("\n\n" + "=" * 80)
            lines.append("EXPERIMENTOS CON FALLOS")
            lines.append("=" * 80)
            for exp in failed:
                lines.append(f"\nExperimento {exp['num']}: {exp['name']}")
                lines.append(f"  Config: {exp['config']}")
                lines.append(f"  Menús: Barato={exp['menus'].get('barato', False)}, Medio={exp['menus'].get('medio', False)}, Caro={exp['menus'].get('caro', False)}")
                if exp.get('errors'):
                    lines.append(f"  Errores: {exp['errors']}")
        
        # Casos de éxito destacados
        success = [e for e in self.experiments if all(e['menus'].get(m, False) for m in ['barato', 'medio', 'caro']) and len(e['config'].get('restrictions', [])) >= 3]
        if success:
            lines.append("\n\n" + "=" * 80)
            lines.append("CASOS DE ÉXITO DESTACADOS (3+ restricciones)")
            lines.append("=" * 80)
            for exp in success:
                lines.append(f"\nExperimento {exp['num']}: {exp['name']}")
                lines.append(f"  Restricciones: {exp['config'].get('restrictions', [])}")
                lines.append(f"  Candidatos: {exp['candidates'].get('total', 0)}")
                lines.append(f"  Precios: Barato={exp['menus'].get('barato_price', '?'):.2f}€, Medio={exp['menus'].get('medio_price', '?'):.2f}€, Caro={exp['menus'].get('caro_price', '?'):.2f}€")
        
        return "\n".join(lines)
    
    def save_json(self, output_file):
        """Guarda datos en JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.experiments, f, indent=2, ensure_ascii=False)
    
    def save_csv(self, output_file):
        """Guarda datos en CSV"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Num', 'Nombre', 'Event_Type', 'Cake', 'Max_People', 'Season',
                'Num_Restrictions', 'Min_Price', 'Max_Price', 'Total_Candidates',
                'Rest_0', 'Rest_1', 'Rest_2', 'Rest_3', 'Rest_4',
                'Menu_Barato', 'Menu_Medio', 'Menu_Caro',
                'Price_Barato', 'Price_Medio', 'Price_Caro',
                'Perfect_Match', 'Fallback', 'Aperitivos', 'Cake_Included', 'Errors'
            ])
            
            # Data
            for exp in self.experiments:
                writer.writerow([
                    exp['num'],
                    exp['name'],
                    exp['config'].get('event_type', ''),
                    exp['config'].get('cake', ''),
                    exp['config'].get('max_people', ''),
                    exp['config'].get('season', ''),
                    len(exp['config'].get('restrictions', [])),
                    exp['config'].get('min_price', ''),
                    exp['config'].get('max_price', ''),
                    exp['candidates'].get('total', 0),
                    exp['candidates'].get('rest_0', 0),
                    exp['candidates'].get('rest_1', 0),
                    exp['candidates'].get('rest_2', 0),
                    exp['candidates'].get('rest_3', 0),
                    exp['candidates'].get('rest_4', 0),
                    'SI' if exp['menus'].get('barato', False) else 'NO',
                    'SI' if exp['menus'].get('medio', False) else 'NO',
                    'SI' if exp['menus'].get('caro', False) else 'NO',
                    exp['menus'].get('barato_price', ''),
                    exp['menus'].get('medio_price', ''),
                    exp['menus'].get('caro_price', ''),
                    'SI' if exp.get('perfect_match', False) else 'NO',
                    'SI' if exp.get('fallback', False) else 'NO',
                    exp.get('aperitivos', 0),
                    'SI' if exp.get('cake_included', False) else 'NO',
                    len(exp.get('errors', []))
                ])


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python parse_output.py <archivo_salida.txt>")
        print("\nEjemplo:")
        print("  python parse_output.py salida_clips.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"Error: Archivo no encontrado: {input_file}")
        sys.exit(1)
    
    print("=" * 80)
    print("ANALIZANDO SALIDA DE CLIPS")
    print("=" * 80)
    print(f"Archivo: {input_file}\n")
    
    parser = CLIPSOutputParser(input_file)
    
    print(f"✓ Encontrados {len(parser.experiments)} experimentos\n")
    
    # Generar reporte de texto
    report = parser.generate_report()
    
    output_base = Path(input_file).stem
    
    # Guardar reporte
    report_file = f"{output_base}_REPORTE.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Reporte generado: {report_file}")
    
    # Guardar JSON
    json_file = f"{output_base}_datos.json"
    parser.save_json(json_file)
    print(f"✓ Datos JSON generados: {json_file}")
    
    # Guardar CSV
    csv_file = f"{output_base}_datos.csv"
    parser.save_csv(csv_file)
    print(f"✓ Datos CSV generados: {csv_file}")
    
    print("\n" + "=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)
    
    # Mostrar resumen en pantalla
    print("\n" + report)


if __name__ == "__main__":
    main()