CREATE TABLE IF NOT EXISTS projet_developpeurs (
    projet_id INT NOT NULL,
    employe_id INT NOT NULL,
    PRIMARY KEY (projet_id, employe_id),
    KEY idx_projet_developpeurs_employe (employe_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO projet_developpeurs (projet_id, employe_id)
SELECT id, employe_id FROM projets;