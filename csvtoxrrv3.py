# Version V3 inclut la demande  de CoID et EpID à l'utilisateur       
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
    # 1. PARAMÈTRES D'ENTRÉE
    input_filename = input("Nom du fichier CSV (ex: COUPE.csv) : ").strip()
    if not os.path.exists(input_filename):
        print("Fichier introuvable.")
        return

    coid = input("Entrez le N° de Concours (CoID) : ").strip() or "0"
    epid = input("Entrez le N° d'épreuve (EpID) : ").strip() or "1"

    output_filename = os.path.splitext(input_filename)[0] + ".XRR"

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
                country = row.get('Skipper Country') or row.get('Sail Number Country') or "FRA"
                # Création d'un ID de bateau propre (sans espaces)
                b_num = row.get('Sail Number', str(i)).replace(" ", "")
                boat_id = f"B_{b_num}"
                
                team_crews = []

                # --- A. LE SKIPPER ---
                skip_id = f"P_S_{i}"
                all_persons.append({
                    "PersonID": skip_id,
                    "FamilyName": row.get('Skipper LastName', 'Inconnu').upper(),
                    "GivenName": row.get('Skipper FirstName', 'Inconnu'),
                    "NOC": country,
                    "Gender": map_gender(row.get('Skipper Gender', '')),
                    "FFVLicenseNumber": row.get('Skipper National ID', ''),
                    "BirthDate": format_date(row.get('Skipper Date of Birth', ''))
                })
                team_crews.append({"id": skip_id, "pos": "S"})

                # --- B. LES ÉQUIPIERS (Dynamique Crew 1 à 5) ---
                for c_idx in range(1, 6):
                    fname = row.get(f'Crew{c_idx} Firstname')
                    lname = row.get(f'Crew{c_idx} Lastname')
                    if fname or lname:
                        c_id = f"P_C{c_idx}_{i}"
                        all_persons.append({
                            "PersonID": c_id,
                            "FamilyName": (lname or "Inconnu").upper(),
                            "GivenName": fname or "Inconnu",
                            "NOC": country,
                            "FFVLicenseNumber": row.get(f'Crew{c_idx}NationalID', ''),
                            "Gender": map_gender(row.get(f'Crew{c_idx} Gender', ''))
                        })
                        team_crews.append({"id": c_id, "pos": "C"})

                # --- C. LE BATEAU ---
                all_boats.append({
                    "BoatID": boat_id,
                    "BoatName": row.get('Boat Name') or f"BATEAU {b_num}",
                    "SailNumber": b_num,
                    "BoatModel": row.get('Class', '')
                })

                # --- D. LE TEAM ---
                all_teams.append({
                    "BoatID": boat_id,
                    "NOC": country,
                    "Crews": team_crews
                })

        # --- CONSTRUCTION FINALE (ORDRE XSD) ---
        for p in all_persons:
            p_el = ET.SubElement(root, "Person")
            for k, v in p.items():
                if v: p_el.set(k, str(v))

        for b in all_boats:
            b_el = ET.SubElement(root, "Boat")
            for k, v in b.items():
                if v: b_el.set(k, str(v))

        event_el = ET.SubElement(root, "Event", {"CoID": coid, "EpID": epid})
        for t in all_teams:
            t_el = ET.SubElement(event_el, "Team", {"BoatID": t["BoatID"], "NOC": t["NOC"]})
            for c in t["Crews"]:
                ET.SubElement(t_el, "Crew", {"PersonID": c["id"], "Position": c["pos"]})

        # Export XML
        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        
        print(f"\nFichier prêt pour import : {output_filename}")
        print(f"Note : Utilisez CoID={coid} et EpID={epid} dans votre logiciel de régate.")

    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    run_conversion()