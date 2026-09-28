ALTER TABLE taches
    ADD COLUMN employe_id INT NULL AFTER projet_id;

CREATE INDEX idx_taches_employe ON taches (employe_id);