ALTER TABLE comptes
    ADD COLUMN employe_id INT NULL,
    ADD UNIQUE KEY uq_comptes_employe_id (employe_id);

CREATE TABLE fiches_techniques_developpeurs (
    employe_id INT NOT NULL PRIMARY KEY,
    competences TEXT NOT NULL,
    disponibilite VARCHAR(255) NOT NULL,
    experience_avant_embauche DECIMAL(6, 2) NOT NULL,
    modifie_le TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;

-- Les comptes développeur déjà existants doivent être associés manuellement
-- à leur ligne employé vérifiée avant d'utiliser la fiche :
-- UPDATE comptes SET employe_id = <id_employe> WHERE id = <id_compte> AND role = 'developpeur';