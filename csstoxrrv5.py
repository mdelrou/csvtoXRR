import csv
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import customtkinter as ctk

# Configuration de l'apparence Windows 11
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class XRRConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Convertisseur CSV vers XRR - FFVoile")
        self.geometry("500x350")

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)

        # 1. Message d'affichage (Statut/Erreur)
        self.status_label = ctk.CTkLabel(self, text="En attente d'un fichier...", font=("Segoe UI", 13))
        self.status_label.grid(row=0, column=0, pady=(20, 10), padx=20)

        # 2. Champ de saisie
        self.label_input = ctk.CTkLabel(self, text="Nom du fichier (sans extension) :")
        self.label_input.grid(row=1, column=0, pady=(10, 0))

        self.entry_filename = ctk.CTkEntry(self, width=300, placeholder_text="ex: cpa2026")
        self.entry_filename.grid(row=2, column=0, pady=10)

        # 3. Bouton Convertir
        self.btn_convert = ctk.CTkButton(self, text="Lancer la conversion", command=self.process_conversion)
        self.btn_convert.grid(row=3, column=0, pady=20)

        # 4. Bouton Fermer (Rouge)
        self.btn_close = ctk.CTkButton(self, text="Fermer", fg_color="#d32f2f", hover_color="#b71c1c", command=self.quit)
        self.btn_close.grid(row=4, column=0, pady=(10, 20))

    def update_status(self, message, color="white"):
        self.status_label.configure(text=message, text_color=color)

    def format_date(self, date_str):
        if not date_str or len(str(date_str)) < 5: return ""
        date_part = str(date_str).split(' ')[0]
        for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
            try: return datetime.strptime(date_part.strip(), fmt).strftime('%Y-%m-%d')
            except ValueError: continue
        return ""

    def process_conversion(self):
        raw_name = self.entry_filename.get().strip()
        if not raw_name:
            self.update_status("Erreur : Veuillez saisir un nom.", "#ff5252")
            return

        input_file = raw_name + ".csv"
        output_file = raw_name + ".XRR"

        if not os.path.exists(input_file):
            self.update_status(f"Fichier '{input_file}' introuvable.", "#ff5252")
            return

        # Logique de conversion
        try:
            data_rows = []
            success_load = False
            for enc in ['utf-8-sig', 'cp1252', 'latin-1']:
                try:
                    with open(input_file, mode='r', encoding=enc) as f:
                        reader = csv.DictReader(f, delimiter=';')
                        data_rows = list(reader)
                        success_load = True
                        break
                except: continue

            if not success_load:
                self.update_status("Erreur d'encodage du fichier.", "#ff5252")
                return

            # Création structure XML
            all_persons, all_boats, all_teams = [], [], []

            for i, row in enumerate(data_rows, 1):
                country = row.get('Skipper Country') or row.get('Sail Number Country') or "FRA"
                sail_num = str(row.get('Sail Number', i)).replace(" ", "")
                boat_id = f"B_{sail_num}_{i}"
                
                # Skipper
                skip_id = f"P_S_{i}"
                all_persons.append({
                    "PersonID": skip_id,
                    "FamilyName": (row.get('Skipper LastName') or "Inconnu").upper(),
                    "GivenName": row.get('Skipper FirstName') or "Inconnu",
                    "NOC": country,
                    "FFVLicenseNumber": row.get('Skipper National ID', ''),
                    "BirthDate": self.format_date(row.get('Skipper Date of Birth', ''))
                })
                
                # Bateau
                all_boats.append({
                    "BoatID": boat_id,
                    "BoatName": row.get('Boat Name') or f"BATEAU {sail_num}",
                    "SailNumber": sail_num
                })
                
                # Team (Lien)
                all_teams.append({"BoatID": boat_id, "NOC": country, "CrewID": skip_id})

            # Assemblage XML
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
                ET.SubElement(t_el, "Crew", {"PersonID": t["CrewID"], "Position": "S"})

            xml_str = ET.tostring(root, encoding='utf-8')
            pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
            with open(output_file, "w", encoding="utf-8") as out:
                out.write(pretty_xml)

            self.update_status(f"Succès ! Fichier '{output_file}' créé.", "#4caf50")

        except Exception as e:
            self.update_status(f"Erreur : {str(e)}", "#ff5252")

    
if __name__ == "__main__":
    app = XRRConverterApp()
    app.mainloop()