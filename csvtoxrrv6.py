import csv
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog

# Configuration du thème
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class XRRConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Convertisseur FFVoile CSV vers XRR")
        self.geometry("600x400")

        # Configuration du layout
        self.grid_columnconfigure(0, weight=1)

        # 1. Message d'affichage (Statut/Erreur)
        self.status_label = ctk.CTkLabel(self, text="Sélectionnez un fichier pour commencer", 
                                        font=("Segoe UI", 14, "bold"), wraplength=500)
        self.status_label.grid(row=0, column=0, pady=(30, 20), padx=20)

        # 2. Zone de sélection de fichier
        self.file_path = ""
        self.btn_browse = ctk.CTkButton(self, text="📁 Parcourir les fichiers...", 
                                       command=self.browse_file, height=40)
        self.btn_browse.grid(row=1, column=0, pady=10)

        self.file_display_label = ctk.CTkLabel(self, text="Aucun fichier sélectionné", 
                                              font=("Segoe UI", 11), text_color="gray")
        self.file_display_label.grid(row=2, column=0, pady=(0, 20))

        # 3. Bouton Convertir (Inactif au départ)
        self.btn_convert = ctk.CTkButton(self, text="🚀 Lancer la conversion", 
                                        command=self.process_conversion, 
                                        state="disabled", fg_color="#1f538d")
        self.btn_convert.grid(row=3, column=0, pady=10)

        # 4. Bouton Fermer
        self.btn_close = ctk.CTkButton(self, text="Fermer l'application", 
                                      fg_color="#d32f2f", hover_color="#b71c1c", 
                                      command=self.quit)
        self.btn_close.grid(row=4, column=0, pady=(20, 20))

    def browse_file(self):
        # Ouvre l'explorateur Windows
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier CSV des inscriptions",
            filetypes=(("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*"))
        )
        if filename:
            self.file_path = filename
            self.file_display_label.configure(text=os.path.basename(filename), text_color="white")
            self.btn_convert.configure(state="normal")
            self.update_status("Fichier chargé. Prêt pour la conversion.")

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
        if not self.file_path:
            return

        output_file = os.path.splitext(self.file_path)[0] + ".XRR"

        try:
            data_rows = []
            success_load = False
            # Gestion de l'encodage pour éviter l'erreur 0x84
            for enc in ['utf-8-sig', 'cp1252', 'latin-1']:
                try:
                    with open(self.file_path, mode='r', encoding=enc) as f:
                        reader = csv.DictReader(f, delimiter=';')
                        data_rows = list(reader)
                        success_load = True
                        break
                except: continue

            if not success_load:
                self.update_status("Erreur : Impossible de lire l'encodage du fichier.", "#ff5252")
                return

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
                    "SailNumber": sail_num,
                    "BoatModel": row.get('Class', '')
                })
                
                # Team (Lien Skipper -> Bateau)
                all_teams.append({"BoatID": boat_id, "NOC": country, "CrewID": skip_id})

            # Génération du XML
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

            self.update_status(f"Fichier créé avec succès !\n{os.path.basename(output_file)}", "#4caf50")

        except Exception as e:
            self.update_status(f"Erreur technique : {str(e)}", "#ff5252")

if __name__ == "__main__":
    app = XRRConverterApp()
    app.mainloop()