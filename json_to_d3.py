"""
Convertisseur de données Sonalyze vers format D3.js
Utilise vos fonctions json_utils.py existantes
"""

import json
from sonalyse_advisor.json_utils import (
    load_json,
    json_extract_info,
    get_average_rating,
    get_noise_type_by_hour,
    get_noise_type_percentage_hourly,
    get_noise_type_percentage_daily,
    
)

def convert_to_d3_format(json_filename="data/dps_analysis_pi3_exemple.json"):
    """
    Convertit les données JSON Sonalyze en format D3.js
    
    Returns:
        dict: Données formatées pour D3.js avec:
            - timeline: données horaires
            - radar: pourcentages de bruits
            - heatmap: matrice jour x heure (si plusieurs jours)
    """
    
    print(f"📁 Chargement de {json_filename}...")
    
    # Charger données avec votre fonction
    data = load_json(json_filename)
    print(f"✅ {len(data)} mesures chargées")
    
    # Extraire infos avec vos fonctions
    (
        extracted_rating,
        extracted_dominant_noise,
        extracted_average_median,
        extracted_min_max_peak,
        extracted_background_noise,
    ) = json_extract_info(data)
    
    # Calculer stats
    average_rating = get_average_rating(extracted_rating)
    noise_percentage = get_noise_type_percentage_daily(extracted_dominant_noise)
    noise_by_hour = get_noise_type_by_hour(extracted_dominant_noise)
    noise_percentage_hourly = get_noise_type_percentage_hourly(noise_by_hour)
    
    print(f"📊 Note calculée: {average_rating}")
    print(f"🔊 Types de bruits: {len(noise_percentage)}")
    
    # FORMAT 1: Timeline (évolution par heure)
    timeline_data = []
    
    # Agréger par heure
    db_by_hour = {}
    for item in extracted_average_median:
        timestamp = item['timestamp']
        # Parser l'heure depuis timestamp (format: "YYYY-MM-DD HH:MM:SS")
        try:
            hour = int(timestamp.split(' ')[1].split(':')[0])
        except:
            continue
        
        avg_db = item['average_dB']
        
        if hour not in db_by_hour:
            db_by_hour[hour] = {'values': [], 'mins': [], 'maxs': []}
        
        db_by_hour[hour]['values'].append(avg_db)
    
    # Calculer min/max pour chaque heure
    for item in extracted_min_max_peak:
        timestamp = item['timestamp']
        try:
            hour = int(timestamp.split(' ')[1].split(':')[0])
        except:
            continue
        
        if hour in db_by_hour:
            db_by_hour[hour]['mins'].append(item['min_dB'])
            db_by_hour[hour]['maxs'].append(item['max_dB'])
    
    # Construire timeline
    for hour in sorted(db_by_hour.keys()):
        values = db_by_hour[hour]['values']
        mins = db_by_hour[hour]['mins']
        maxs = db_by_hour[hour]['maxs']
        
        timeline_data.append({
            'hour': hour,
            'value': round(sum(values) / len(values), 1) if values else 0,
            'min': round(min(mins), 1) if mins else 0,
            'max': round(max(maxs), 1) if maxs else 0
        })
    
    print(f"📈 Timeline: {len(timeline_data)} points horaires")
    
    # FORMAT 2: Radar (pourcentages de bruits)
    radar_data = []
    for noise_type, percentage in noise_percentage.items():
        radar_data.append({
            'category': noise_type.replace('_', ' ').title(),
            'value': round(percentage, 1)
        })
    
    print(f"🎵 Radar: {len(radar_data)} catégories")
    
    # FORMAT 3: Heatmap (jour x heure)
    # Note: nécessite plusieurs jours de données
    heatmap_data = []
    
    # Extraire jour et heure de chaque mesure
    day_hour_db = {}
    for item in extracted_average_median:
        timestamp = item['timestamp']
        try:
            date_part = timestamp.split(' ')[0]
            hour = int(timestamp.split(' ')[1].split(':')[0])
            avg_db = item['average_dB']
            
            # Utiliser date comme "jour"
            if date_part not in day_hour_db:
                day_hour_db[date_part] = {}
            
            if hour not in day_hour_db[date_part]:
                day_hour_db[date_part][hour] = []
            
            day_hour_db[date_part][hour].append(avg_db)
        except:
            continue
    
    # Convertir en format heatmap
    day_names = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    for day_idx, (date, hours_data) in enumerate(day_hour_db.items()):
        day_name = day_names[day_idx % 7]
        for hour, values in hours_data.items():
            heatmap_data.append({
                'day': day_name,
                'dayIndex': day_idx % 7,
                'hour': hour,
                'value': round(sum(values) / len(values), 1) if values else 0
            })
    
    print(f"🗓️ Heatmap: {len(heatmap_data)} cellules")
    
    # FORMAT COMPLET
    d3_format = {
        'timeline': timeline_data,
        'radar': radar_data,
        'heatmap': heatmap_data,
        'metadata': {
            'grade': average_rating,
            'total_measurements': len(data),
            'hours_covered': len(timeline_data),
            'noise_types': len(radar_data)
        }
    }
    
    return d3_format


def save_d3_json(d3_data, output_file="d3_data.json"):
    """Sauvegarde les données au format D3.js"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(d3_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Données D3.js sauvegardées dans: {output_file}")


def print_summary(d3_data):
    """Affiche un résumé des données converties"""
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES DONNÉES D3.js")
    print("="*60)
    
    meta = d3_data['metadata']
    print(f"\n🎯 Note globale: {meta['grade']}")
    print(f"📏 Mesures totales: {meta['total_measurements']}")
    print(f"⏰ Heures couvertes: {meta['hours_covered']}")
    print(f"🔊 Types de bruits: {meta['noise_types']}")
    
    print(f"\n📈 Timeline: {len(d3_data['timeline'])} points")
    if d3_data['timeline']:
        print("   Exemple:")
        for item in d3_data['timeline'][:3]:
            print(f"   - {item['hour']}h: {item['value']} dB (min: {item['min']}, max: {item['max']})")
    
    print(f"\n🎵 Radar: {len(d3_data['radar'])} catégories")
    if d3_data['radar']:
        print("   Répartition:")
        for item in sorted(d3_data['radar'], key=lambda x: x['value'], reverse=True):
            print(f"   - {item['category']}: {item['value']}%")
    
    print(f"\n🗓️ Heatmap: {len(d3_data['heatmap'])} cellules")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print("\n🔊 CONVERTISSEUR SONALYZE → D3.js")
    print("="*60)
    
    # Convertir
    d3_data = convert_to_d3_format()
    
    # Afficher résumé
    print_summary(d3_data)
    
    # Sauvegarder
    save_d3_json(d3_data)
    
    print("\n💡 COMMENT UTILISER:")
    print("1. Le fichier 'd3_data.json' contient vos données au format D3.js")
    print("2. Copiez le contenu dans le HTML standalone")
    print("3. Ou utilisez-le directement dans Streamlit avec:")
    print("   import json")
    print("   with open('d3_data.json') as f:")
    print("       d3_data = json.load(f)")
    print("\n✅ Conversion terminée!")