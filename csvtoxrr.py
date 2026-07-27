import csv
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class XRRConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FFVoile XRR - Version Stable")
        self.geometry("600x600")
        self.grid_columnconfigure(0, weight=1)

        # 1. Statut
        self.status_label = ctk.CTkLabel(self, text="Prêt pour l'import Score", font=("Segoe UI", 16, "bold"))
        self.status_label.grid(row=0, column=0, pady=20)

        # 2. Fichier
        self.file_path = ""
        self.btn_browse = ctk.CTkButton(self, text="📁 Choisir le fichier CSV", command=self.browse_file)
        self.btn_browse.grid(row=1, column=0, pady=5)

        self.file_display_label = ctk.CTkLabel(self, text="Aucun fichier sélectionné", font=("Segoe UI", 11), text_color="gray")
        self.file_display_label.grid(row=2, column=0, pady=(0, 20))

        # 3. Paramètres CoID / EpID
        self.frame_ids = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_ids.grid(row=3, column=0, pady=10)
        
        self.entry_coid = ctk.CTkEntry(self.frame_ids, width=80, justify="center")
        self.entry_coid.insert(0, "0")
        self.entry_coid.grid(row=1, column=0, padx=10)
        ctk.CTkLabel(self.frame_ids, text="CoID").grid(row=0, column=0)

        self.entry_epid = ctk.CTkEntry(self.frame_ids, width=80, justify="center")
        self.entry_epid.insert(0, "1")
        self.entry_epid.grid(row=1, column=1, padx=10)
        ctk.CTkLabel(self.frame_ids, text="EpID").grid(row=0, column=1)

        # 4. Bouton Action
        self.btn_convert = ctk.CTkButton(self, text="🚀 Générer le fichier XRR", command=self.process_conversion, state="disabled", height=45)
        self.btn_convert.grid(row=4, column=0, pady=20)

        # 5. Bouton Quitter (Rétabli et bien visible)
        self.btn_quit = ctk.CTkButton(self, text="Quitter l'application", fg_color="#d32f2f", hover_color="#b71c1c", command=self.destroy)
        self.btn_quit.grid(row=5, column=0, pady=20)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=(("CSV", "*.csv"), ("Tous", "*.*")))
        if filename:
            self.file_path = filename
            self.file_display_label.configure(text=os.path.basename(filename), text_color="#3a86ff")
            self.btn_convert.configure(state="normal")

    def clean_val(self, val, default="INCONNU"):
        """Assure qu'une valeur n'est jamais vide pour le XML."""
        s = str(val).strip()
        return s if s else default

    def format_date(self, date_str):
        if not date_str or len(str(date_str)) < 5: return ""
        date_part = str(date_str).split(' ')[0]
        for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
            try: return datetime.strptime(date_part.strip(), fmt).strftime('%Y-%m-%d')
            except ValueError: continue
        return ""

    def process_conversion(self):
        if not self.file_path: return
        coid, epid = self.entry_coid.get(), self.entry_epid.get()
        output_file = os.path.splitext(self.file_path)[0] + ".XRR"

        try:
            with open(self.file_path, mode='r', encoding='latin-1') as f:
                reader = csv.DictReader(f, delimiter=';')
                data_rows = [r for r in reader if r.get('Sail Number')]

            all_persons, all_boats, all_teams = [], [], []

            for i, row in enumerate(data_rows, 1):
                raw_sail = self.clean_val(row.get('Sail Number'), str(i))
                clean_sail = "".join(filter(str.isalnum, raw_sail))
                boat_id = f"B_{clean_sail}_{i}"
                country = self.clean_val(row.get('Skipper Country'), "FRA")
                
                crew_links = []

                # --- SKIPPER ---
                sid = f"P_S_{i}"
                all_persons.append({
                    "PersonID": sid,
                    "FamilyName": self.clean_val(row.get('Skipper LastName'), f"SKIPPER {clean_sail}").upper(),
                    "GivenName": self.clean_val(row.get('Skipper FirstName'), "Inconnu"),
                    "NOC": country,
                    "FFVLicenseNumber": row.get('Skipper National ID', ''),
                    "BirthDate": self.format_date(row.get('Skipper Date of Birth', ''))
                })
                crew_links.append((sid, "S"))

                # --- CREW 1 ---
                c1_fname = row.get('Crew1 Firstname', '').strip()
                c1_lname = row.get('Crew1 Lastname', '').strip()
                if c1_fname or c1_lname:
                    c1id = f"P_C1_{i}"
                    all_persons.append({
                        "PersonID": c1id,
                        "FamilyName": self.clean_val(c1_lname, "INCONNU").upper(),
                        "GivenName": self.clean_val(c1_fname, "Equipier"),
                        "NOC": country,
                        "FFVLicenseNumber": row.get('Crew1NationalID', '')
                    })
                    crew_links.append((c1id, "C"))

                # --- REMAINING CREW ---
                rem = row.get('Remaining Crew', '')
                if rem:
                    members = [m.strip() for m in re.split(r'[,;]', str(rem)) if m.strip()]
                    for idx, m_name in enumerate(members):
                        if "@" in m_name or len(m_name) < 2: continue
                        rcid = f"P_RC_{i}_{idx}"
                        # Split basique Prénom Nom
                        parts = m_name.split()
                        fn = parts[0] if len(parts) > 0 else "Equipier"
                        ln = " ".join(parts[1:]) if len(parts) > 1 else "INCONNU"
                        all_persons.append({
                            "PersonID": rcid, "FamilyName": ln.upper(), "GivenName": fn, "NOC": country
                        })
                        crew_links.append((rcid, "C"))

                # --- BATEAU ---
                all_boats.append({
                    "BoatID": boat_id,
                    "SailNumber": raw_sail,
                    "BoatName": self.clean_val(row.get('Boat Name'), f"BATEAU {raw_sail}"),
                    "BoatModel": self.clean_val(row.get('Class'), "Dragon")
                })
                all_teams.append({"BoatID": boat_id, "NOC": country, "Links": crew_links})

            # XML
            root = ET.Element("SailingXRR", {"Version": "1.0", "Type": "Inscriptions", "Date": datetime.now().strftime("%Y-%m-%d")})
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
                for pid, pos in t["Links"]:
                    ET.SubElement(t_el, "Crew", {"PersonID": pid, "Position": pos})

            xml_str = ET.tostring(root, encoding='utf-8')
            pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
            with open(output_file, "w", encoding="utf-8") as out:
                out.write(pretty_xml)
            
            self.status_label.configure(text=f"✅ {len(all_teams)} Bateaux importés !", text_color="#4caf50")

        except Exception as e:
            self.status_label.configure(text=f"❌ Erreur : {str(e)}", text_color="#ff5252")

if __name__ == "__main__":
    app = XRRConverterApp()
    app.mainloop()