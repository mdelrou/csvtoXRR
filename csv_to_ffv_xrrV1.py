import csv
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

def format_date(date_str):
    """Convertit les dates au format YYYY-MM-DD requis par le XSD[cite: 9]."""
    if not date_str: return ""
    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ""

def map_gender(g):
    """Mappe le genre selon les énumérations : male, female, non_binary[cite: 5]."""
    g = str(g).lower()
    if 'm' in g: return "male"
    if 'f' in g: return "female"
    return ""

def run_conversion():
    # Saisie du fichier en entrée
    input_filename = input("Entrez le nom du fichier CSV (ex: COUPE DE L AMITIE.csv) : ").strip()
    
    if not os.path.exists(input_filename):
        print(f"Erreur : Le fichier '{input_filename}' est introuvable.")
        return

    # Génération automatique du nom de sortie
    output_filename = os.path.splitext(input_filename)[0] + ".XRR"

    # Racine conforme au XSD [cite: 22]
    root = ET.Element("SailingXRR", {
        "Version": "1.0",
        "Type": "Inscriptions",
        "Date": datetime.now().strftime("%Y-%m-%d")
    })

    persons_data = []
    boats_data = []
    teams_data = []

    try:
        with open(input_filename, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';') # Utilisation du point-virgule 
            
            for i, row in enumerate(reader, 1):
                # ID Unique pour le bateau [cite: 11]
                boat_id = f"B_{row.get('Sail Number', i)}".replace(" ", "_")
                
                # --- 1. PERSONNES (Skipper + Équipiers) ---
                current_team_crews = []

                # Skipper (Position 'S') [cite: 6]
                skip_id = f"P_S_{i}"
                persons_data.append({
                    "PersonID": skip_id,
                    "IFPersonID": row.get('Skipper ISAF', ''),
                    "FamilyName": row.get('Skipper LastName', 'Inconnu'),
                    "GivenName": row.get('Skipper FirstName', 'Inconnu'),
                    "NOC": row.get('Skipper Country', 'FRA'), # Requis [cite: 8]
                    "Gender": map_gender(row.get('Skipper Gender', '')),
                    "BirthDate": format_date(row.get('Skipper Date of Birth', '')),
                    "ClubName": row.get('Skipper Club', '')
                })
                current_team_crews.append({"id": skip_id, "pos": "S"})

                # Crew 1 (Position 'C') [cite: 15]
                if row.get('Crew1 Lastname'):
                    c1_id = f"P_C1_{i}"
                    persons_data.append({
                        "PersonID": c1_id,
                        "IFPersonID": row.get('Crew1 WS ID', ''),
                        "FamilyName": row.get('Crew1 Lastname', ''),
                        "GivenName": row.get('Crew1 Firstname', ''),
                        "NOC": row.get('Skipper Country', 'FRA'),
                        "Gender": map_gender(row.get('Crew1 Gender', '')),
                        "ClubName": row.get('Crew1 Club', '')
                    })
                    current_team_crews.append({"id": c1_id, "pos": "C"})

                # --- 2. BATEAU ---
                boats_data.append({
                    "BoatID": boat_id,
                    "BoatName": row.get('Boat Name', 'Sans Nom'), # Requis [cite: 11]
                    "SailNumber": row.get('Sail Number', str(i)), # Requis [cite: 11]
                    "BowNumber": row.get('Bow Number', ''),
                    "BoatModel": row.get('Class', '')
                })

                # --- 3. TEAM ---
                teams_data.append({
                    "BoatID": boat_id,
                    "NOC": row.get('Represented Country', 'FRA'),
                    "Crews": current_team_crews
                })

        # --- ASSEMBLAGE XML SELON ORDRE DU XSD [cite: 22] ---
        
        # Balises Person [cite: 7, 8, 9]
        for p in persons_data:
            p_elem = ET.SubElement(root, "Person")
            for k, v in p.items():
                if v: p_elem.set(k, str(v))

        # Balises Boat [cite: 11, 12]
        for b in boats_data:
            b_elem = ET.SubElement(root, "Boat")
            for k, v in b.items():
                if v: b_elem.set(k, str(v))

        # Balise Event et ses Teams [cite: 19, 21]
        event_elem = ET.SubElement(root, "Event", {"CoID": "COMP2026", "EpID": "1"})
        for t in teams_data:
            t_elem = ET.SubElement(event_elem, "Team", {
                "BoatID": t["BoatID"],
                "NOC": t["NOC"]
            })
            for c in t["Crews"]:
                # Balise Crew enfant de Team [cite: 14, 16]
                ET.SubElement(t_elem, "Crew", {
                    "PersonID": c["id"],
                    "Position": c["pos"]
                })

        # Enregistrement avec mise en forme
        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        
        print(f"\nTerminé ! Fichier généré : {output_filename}")

    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    run_conversion()