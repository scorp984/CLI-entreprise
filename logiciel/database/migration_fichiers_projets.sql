CREATE TABLE IF NOT EXISTS fichiers_projets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projet_id INT NOT NULL,
    employe_id INT NOT NULL,
    etape VARCHAR(32) NOT NULL,
    nom_original VARCHAR(255) NOT NULL,
    nom_stockage VARCHAR(64) NOT NULL UNIQUE,
    type_mime VARCHAR(127) NOT NULL,
    taille BIGINT UNSIGNED NOT NULL,
    ajoute_le TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    supprime_le TIMESTAMP NULL DEFAULT NULL,
    KEY idx_fichiers_projets_projet (projet_id, supprime_le, ajoute_le),
    KEY idx_fichiers_projets_employe (employe_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;