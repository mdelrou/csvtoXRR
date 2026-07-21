# Changelog - Format XRR inscriptions

## [2.0.0] - 15/09/2025

- Uniformisation du fichier pour le temps compensé et le temps réel
- Possibilité d'avoir un unique fichier pour plusieurs épreuves d'une même compétition


### Ajouté

- Ajout de trois attributs (optionnels) à la balise `<Team>`
  - EpID : Id de l'épreuve sur laquelle l'équipage est inscrit.
  - EpBoatCode : Code bateau (issu du dictionnaire FFVoile) de l'épreuve sur lequel l'équipage est inscrit. Privilégiez l'EpId (à l'EpBoatCode) si vous en avez connaissance.
  - Remarks : Remarques pour préciser une information utile au moment de l'import des inscrits

### Supprimé
#### Temps compensé
- Suppression de l'attribut `BoatHandicapType` de la balise `<Boat>` 
  ```
  <xs:simpleType name="handicapType">
        <xs:restriction base="xs:string">
            <xs:enumeration value="CIM"/>
            <xs:enumeration value="INC"/>
            <xs:enumeration value="IND"/>
            <xs:enumeration value="INQ"/>
            <xs:enumeration value="INVL"/>
            <xs:enumeration value="IRC"/>
            <xs:enumeration value="JCH"/>
            <xs:enumeration value="M2K"/>
            <xs:enumeration value="ORC"/>
            <xs:enumeration value="OSIR"/> <!-- OSIRIS -->
        </xs:restriction>
    </xs:simpleType>
  ```
