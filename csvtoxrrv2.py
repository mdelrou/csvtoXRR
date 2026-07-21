import csv
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

def format_date(date_str):
    if not date_str: return ""
    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ""

def map_gender(g):
    g = str(g).lower()
    if 'm' in g: return "male"
    if 'f' in g: return "female"
    return ""

def run_conversion():
    input_filename = input("Entrez le nom du fichier CSV : ").strip()
    
    if not os.path.exists(input_filename):
        print(f"Erreur : Le fichier '{input_filename}' est introuvable.")
        return

    output_filename = os.path.splitext(input_filename)[0] + ".XRR"

    # Racine conforme au XSD
    root = ET.Element("SailingXRR", {
        "Version": "1.0",
        "Type": "Inscriptions",
        "Date": datetime.now().strftime("%Y-%m-%d")
    })

    all_persons = []
    all_boats = []
    all_teams = []

    try:
        with open(input_filename, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for i, row in enumerate(reader, 1):
                # Pays par défaut (NOC est requis par le XSD)
                country = row.get('Skipper Country') or row.get('Sail Number Country') or "FRA"
                boat_id = f"B_{row.get('Sail Number', i)}".replace(" ", "_")
                
                team_crews = []

                # --- 1. COLLECTE SKIPPER ---
                skip_id = f"P_S_{i}"
                all_persons.append({
                    "PersonID": skip_id,
                    "IFPersonID": row.get('Skipper ISAF', ''),
                    "FamilyName": row.get('Skipper LastName', 'Inconnu'),
                    "GivenName": row.get('Skipper FirstName', 'Inconnu'),
                    "NOC": country,
                    "Gender": map_gender(row.get('Skipper Gender', '')),
                    "BirthDate": format_date(row.get('Skipper Date of Birth', '')),
                    "FFVLicenseNumber": row.get('Skipper National ID', ''),
                    "ClubName": row.get('Skipper Club', '')
                })
                team_crews.append({"id": skip_id, "pos": "S"})

                # --- 2. COLLECTE CREW 1 ---
                if row.get('Crew1 Lastname'):
                    c1_id = f"P_C1_{i}"
                    all_persons.append({
                        "PersonID": c1_id,
                        "IFPersonID": row.get('Crew1 WS ID', ''),
                        "FamilyName": row.get('Crew1 Lastname', ''),
                        "GivenName": row.get('Crew1 Firstname', ''),
                        "NOC": country,
                        "Gender": map_gender(row.get('Crew1 Gender', '')),
                        "FFVLicenseNumber": row.get('Crew1NationalID', ''),
                        "ClubName": row.get('Crew1 Club', '')
                    })
                    team_crews.append({"id": c1_id, "pos": "C"})

                # --- 3. COLLECTE BATEAU ---
                all_boats.append({
                    "BoatID": boat_id,
                    "BoatName": row.get('Boat Name') or f"Boat_{row.get('Sail Number')}",
                    "SailNumber": row.get('Sail Number', str(i)),
                    "BowNumber": row.get('Bow Number', ''),
                    "BoatModel": row.get('Class', '')
                })

                # --- 4. PREPARATION TEAM ---
                all_teams.append({
                    "BoatID": boat_id,
                    "NOC": country,
                    "Crews": team_crews
                })

        # --- CONSTRUCTION DU XML : L'ORDRE SUIVANT EST OBLIGATOIRE ---
        
        # 1. Toutes les balises Person d'abord
        for p in all_persons:
            p_elem = ET.SubElement(root, "Person")
            for k, v in p.items():
                if v: p_elem.set(k, str(v))

        # 2. Toutes les balises Boat ensuite
        for b in all_boats:
            b_elem = ET.SubElement(root, "Boat")
            for k, v in b.items():
                if v: b_elem.set(k, str(v))

        # 3. L'unique balise Event à la fin
        event_elem = ET.SubElement(root, "Event", {"CoID": "COMP2026", "EpID": "1"})
        for t in all_teams:
            t_elem = ET.SubElement(event_elem, "Team", {"BoatID": t["BoatID"], "NOC": t["NOC"]})
            for c in t["Crews"]:
                ET.SubElement(t_elem, "Crew", {"PersonID": c["id"], "Position": c["pos"]})

        # Sauvegarde
        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        
        print(f"\nFichier XML validé et généré : {output_filename}")

    except Exception as e:
        print(f"Erreur technique : {e}")

if __name__ == "__main__":
    run_conversion()