import csv
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

def format_date(date_str):
    if not date_str or len(str(date_str)) < 5: return ""
    date_part = str(date_str).split(' ')[0]
    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_part.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ""

def map_gender(g):
    g = str(g).lower()
    if 'm' in g: return "male"
    if 'f' in g: return "female"
    return ""

def run_conversion():
    # 1. SAISIE DU FICHIER
    input_filename = input("Nom du fichier CSV (ex: cpa2026.csv) : ").strip()
    if not os.path.exists(input_filename):
        print(f"Erreur : '{input_filename}' introuvable.")
        return

    output_filename = os.path.splitext(input_filename)[0] + ".XRR"

    # 2. LECTURE AVEC DETECTION D'ENCODAGE (Gestion erreur 0x84)
    data_rows = []
    success_load = False
    for enc in ['utf-8-sig', 'cp1252', 'latin-1']:
        try:
            with open(input_filename, mode='r', encoding=enc) as f:
                reader = csv.DictReader(f, delimiter=';')
                data_rows = list(reader)
                success_load = True
                break
        except (UnicodeDecodeError, Exception):
            continue

    if not success_load:
        print("Erreur critique : impossible de lire le fichier (problème d'encodage).")
        return

    all_persons = []
    all_boats = []
    all_teams = []

    # 3. TRAITEMENT DES LIGNES
    for i, row in enumerate(data_rows, 1):
        country = row.get('Skipper Country') or row.get('Sail Number Country') or "FRA"
        sail_num = str(row.get('Sail Number', i)).replace(" ", "")
        boat_id = f"B_{sail_num}_{i}"
        
        team_crews = []

        # SKIPPER
        skip_id = f"P_S_{i}"
        all_persons.append({
            "PersonID": skip_id,
            "FamilyName": (row.get('Skipper LastName') or "Inconnu").upper(),
            "GivenName": row.get('Skipper FirstName') or "Inconnu",
            "NOC": country,
            "Gender": map_gender(row.get('Skipper Gender', '')),
            "FFVLicenseNumber": row.get('Skipper National ID', ''),
            "BirthDate": format_date(row.get('Skipper Date of Birth', ''))
        })
        team_crews.append({"id": skip_id, "pos": "S"})

        # EQUIPER 1
        if row.get('Crew1 Lastname'):
            c1_id = f"P_C1_{i}"
            all_persons.append({
                "PersonID": c1_id,
                "FamilyName": row.get('Crew1 Lastname', '').upper(),
                "GivenName": row.get('Crew1 Firstname', ''),
                "NOC": country,
                "FFVLicenseNumber": row.get('Crew1NationalID', ''),
                "Gender": map_gender(row.get('Crew1 Gender', ''))
            })
            team_crews.append({"id": c1_id, "pos": "C"})

        # BATEAU
        all_boats.append({
            "BoatID": boat_id,
            "BoatName": row.get('Boat Name') or f"BATEAU {sail_num}",
            "SailNumber": sail_num,
            "BoatModel": row.get('Class', '')
        })

        # TEAM
        all_teams.append({
            "BoatID": boat_id,
            "NOC": country,
            "Crews": team_crews
        })

    # 4. GÉNÉRATION XML (Structure fixe CoID=0, EpID=1)
    root = ET.Element("SailingXRR", {"Version": "1.0", "Type": "Inscriptions", "Date": datetime.now().strftime("%Y-%m-%d")})

    for p in all_persons:
        p_el = ET.SubElement(root, "Person")
        for k, v in p.items():
            if v: p_el.set(k, str(v))

    for b in all_boats:
        b_el = ET.SubElement(root, "Boat")
        for k, v in b.items():
            if v: b_el.set(k, str(v))

    event_el = ET.SubElement(root, "Event", {"CoID": "0", "EpID": "1"})
    for t in all_teams:
        t_el = ET.SubElement(event_el, "Team", {"BoatID": t["BoatID"], "NOC": t["NOC"]})
        for c in t["Crews"]:
            ET.SubElement(t_el, "Crew", {"PersonID": c["id"], "Position": c["pos"]})

    # Sauvegarde
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    with open(output_filename, "w", encoding="utf-8") as out:
        out.write(pretty_xml)
    
    print(f"\nConversion terminée. Fichier créé : {output_filename}")

if __name__ == "__main__":
    run_conversion()