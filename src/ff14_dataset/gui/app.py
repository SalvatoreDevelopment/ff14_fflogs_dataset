from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ff14_dataset.config import load_settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FF14 Dataset Builder")
        self.resize(1100, 720)
        self.settings = load_settings()
        self._init_ui()

    def _init_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self._tab_fetch_grouped(), "Raccolta")
        tabs.addTab(self._tab_process(), "Processa")
        tabs.addTab(self._tab_features(), "Features")
        tabs.addTab(self._tab_preview(), "Anteprima")
        tabs.addTab(self._tab_settings(), "Impostazioni")
        self.setCentralWidget(tabs)

    def _tab_fetch_grouped(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)

        # Sezione: Selezione boss
        sel_group = QGroupBox("Selezione boss")
        sel_form = QFormLayout(sel_group)

        self.fight_type_combo = QComboBox()
        self.fight_type_combo.addItems([
            "Raid (Savage)",
            "Raid (Ultimate)",
            "Trial (Extreme)",
            "Tutti",
        ])
        self.fight_type_combo.currentIndexChanged.connect(self._on_load_bosses)
        sel_form.addRow(QLabel("Tipo fight"), self.fight_type_combo)

        self.tier_combo = QComboBox()
        self.tier_combo.setPlaceholderText("Seleziona un tier…")
        self.tier_combo.currentIndexChanged.connect(self._populate_bosses_for_selected_tier)
        sel_form.addRow(QLabel("Tier"), self.tier_combo)

        self.boss_combo = QComboBox()
        self.boss_combo.setEditable(True)
        self.boss_combo.setPlaceholderText("Seleziona un boss…")
        sel_form.addRow(QLabel("Boss"), self.boss_combo)

        # Sezione: Filtri
        filt_group = QGroupBox("Filtri")
        filt_form = QFormLayout(filt_group)

        self.job_combo = QComboBox()
        self.job_combo.addItems([
            "PLD","WAR","DRK","GNB",
            "WHM","SCH","AST","SGE",
            "MNK","DRG","NIN","SAM","RPR",
            "BRD","MCH","DNC",
            "BLM","SMN","RDM",
            "VPR","PCT",
        ])
        self.job_combo.setCurrentText("SAM")
        filt_form.addRow(QLabel("Job"), self.job_combo)

        self.patch_combo = QComboBox()
        self.patch_combo.setEditable(True)
        for p in [
            self.settings.app.game_patch,
            "7.30","7.31","7.32","7.33","7.34","7.35",
            "7.3x",
        ]:
            if self.patch_combo.findText(p) == -1:
                self.patch_combo.addItem(p)
        self.patch_combo.setCurrentText(self.settings.app.game_patch)
        filt_form.addRow(QLabel("Patch"), self.patch_combo)

        perc_row = QHBoxLayout()
        perc_row.addWidget(QLabel("Percentile minimo"))
        self.perc_spin = QSpinBox()
        self.perc_spin.setRange(0, 100)
        self.perc_spin.setValue(self.settings.ingestion.quality_filters.min_percentile)
        perc_row.addWidget(self.perc_spin)
        perc_row.addSpacing(12)
        self.kills_only = QCheckBox("Solo kill")
        self.kills_only.setChecked(self.settings.ingestion.quality_filters.kills_only)
        perc_row.addWidget(self.kills_only)
        perc_row.addStretch()
        filt_form.addRow(perc_row)

        # Sezione: Limiti rete
        lim_group = QGroupBox("Limiti rete")
        lim_form = QFormLayout(lim_group)
        self.conc_spin = QSpinBox()
        self.conc_spin.setRange(1, 16)
        self.conc_spin.setValue(self.settings.ingestion.concurrency)
        self.conc_spin.setToolTip("Numero massimo di richieste HTTP parallele a FF Logs (non è il numero di fight in parallelo). Più alto = più veloce, ma attenzione ai rate limit.")
        lim_form.addRow(QLabel("Richieste parallele"), self.conc_spin)

        self.sleep_spin = QSpinBox()
        self.sleep_spin.setRange(0, 5000)
        self.sleep_spin.setValue(self.settings.ingestion.sleep_ms)
        self.sleep_spin.setToolTip("Pausa tra richieste per rispettare i rate limit (millisecondi)")
        lim_form.addRow(QLabel("Sleep (ms)"), self.sleep_spin)

        # Barra azioni
        actions = QHBoxLayout()
        self.run_fetch_btn = QPushButton("Avvia raccolta (skeleton)")
        self.run_fetch_btn.clicked.connect(self._on_run_fetch)
        actions.addWidget(self.run_fetch_btn)
        actions.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("color: gray;")
        actions.addWidget(self.loading_label)

        # Log
        self.fetch_log = QTextEdit()
        self.fetch_log.setReadOnly(True)

        # Compose
        root.addWidget(sel_group)
        root.addWidget(filt_group)
        root.addWidget(lim_group)
        root.addLayout(actions)
        root.addWidget(self.fetch_log)
        return w

    def _tab_fetch(self) -> QWidget:
        w = QWidget()
        layout = QGridLayout(w)

        # Fight type and Boss selectors
        layout.addWidget(QLabel("Tipo fight"), 0, 0)
        self.fight_type_combo = QComboBox()
        self.fight_type_combo.addItems([
            "Raid (Savage)",
            "Raid (Ultimate)",
            "Trial (Extreme)",
            "Tutti",
        ])
        self.fight_type_combo.currentIndexChanged.connect(self._on_load_bosses)
        layout.addWidget(self.fight_type_combo, 0, 1)

        self.boss_combo = QComboBox()
        self.boss_combo.setEditable(True)
        self.boss_combo.setPlaceholderText("Seleziona un boss…")
        layout.addWidget(self.boss_combo, 0, 3)

        # Tier selector (riempito dopo il fetch dei zones)
        layout.addWidget(QLabel("Tier"), 1, 0)
        self.tier_combo = QComboBox()
        self.tier_combo.setPlaceholderText("Seleziona un tier…")
        self.tier_combo.currentIndexChanged.connect(self._populate_bosses_for_selected_tier)
        layout.addWidget(self.tier_combo, 1, 1)

        layout.addWidget(QLabel("Job"), 1, 2)
        self.job_combo = QComboBox()
        self.job_combo.addItems([
            "PLD","WAR","DRK","GNB",
            "WHM","SCH","AST","SGE",
            "MNK","DRG","NIN","SAM","RPR",
            "BRD","MCH","DNC",
            "BLM","SMN","RDM",
            "VPR","PCT",
        ])
        self.job_combo.setCurrentText("SAM")
        layout.addWidget(self.job_combo, 1, 3)

        layout.addWidget(QLabel("Patch"), 2, 0)
        self.patch_combo = QComboBox()
        self.patch_combo.setEditable(True)
        # Common 7.3x options; default from config
        for p in [
            self.settings.app.game_patch,
            "7.30","7.31","7.32","7.33","7.34","7.35",
            "7.3x",
        ]:
            if self.patch_combo.findText(p) == -1:
                self.patch_combo.addItem(p)
        self.patch_combo.setCurrentText(self.settings.app.game_patch)
        layout.addWidget(self.patch_combo, 2, 1)

        layout.addWidget(QLabel("Percentile minimo"), 2, 2)
        self.perc_spin = QSpinBox()
        self.perc_spin.setRange(0, 100)
        self.perc_spin.setValue(self.settings.ingestion.quality_filters.min_percentile)
        layout.addWidget(self.perc_spin, 2, 3)

        self.kills_only = QCheckBox("Solo kill")
        self.kills_only.setChecked(self.settings.ingestion.quality_filters.kills_only)
        layout.addWidget(self.kills_only, 3, 0)

        layout.addWidget(QLabel("Concorrenza"), 3, 1)
        self.conc_spin = QSpinBox()
        self.conc_spin.setRange(1, 16)
        self.conc_spin.setValue(self.settings.ingestion.concurrency)
        self.conc_spin.setToolTip("Numero massimo di richieste HTTP parallele a FF Logs (più alto = più veloce, ma attenzione ai rate limit)")
        layout.addWidget(self.conc_spin, 3, 2)

        layout.addWidget(QLabel("Sleep (ms)"), 3, 3)
        self.sleep_spin = QSpinBox()
        self.sleep_spin.setRange(0, 5000)
        self.sleep_spin.setValue(self.settings.ingestion.sleep_ms)
        self.sleep_spin.setToolTip("Pausa tra richieste per rispettare i rate limit (millisecondi)")
        layout.addWidget(self.sleep_spin, 3, 4)

        self.run_fetch_btn = QPushButton("Avvia raccolta (skeleton)")
        self.run_fetch_btn.clicked.connect(self._on_run_fetch)
        layout.addWidget(self.run_fetch_btn, 4, 0, 1, 2)

        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("color: gray;")
        layout.addWidget(self.loading_label, 4, 2, 1, 3)

        self.fetch_log = QTextEdit()
        self.fetch_log.setReadOnly(True)
        layout.addWidget(self.fetch_log, 5, 0, 1, 5)

        return w

    def _tab_process(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Processa raw → staging (skeleton)"))
        layout.addWidget(QPushButton("Esegui normalizzazione (TODO)"))
        return w

    def _tab_features(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Costruisci features e labels (skeleton)"))
        layout.addWidget(QPushButton("Calcola features (TODO)"))
        return w

    def _tab_preview(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Anteprima tabelle DuckDB (TODO)"))
        return w

    def _tab_settings(self) -> QWidget:
        w = QWidget()
        layout = QGridLayout(w)
        layout.addWidget(QLabel("Cartella dati"), 0, 0)
        self.data_path_edit = QLineEdit(str(self.settings.paths.data_root))
        layout.addWidget(self.data_path_edit, 0, 1)
        browse = QPushButton("Sfoglia…")
        layout.addWidget(browse, 0, 2)
        browse.clicked.connect(self._browse_data_dir)

        self.exploratory_toggle = QCheckBox("Modalità esplorativa (disattiva filtri ML)")
        self.exploratory_toggle.setChecked(self.settings.app.exploratory_mode)
        layout.addWidget(self.exploratory_toggle, 1, 0, 1, 3)
        return w

    def _browse_data_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Scegli cartella dati", str(self.settings.paths.data_root))
        if path:
            self.data_path_edit.setText(path)

    def _on_run_fetch(self):
        # Skeleton: just echo parameters; ingestion wiring comes later
        boss_text = self.boss_combo.currentText().strip()
        tier_text = self.tier_combo.currentText().strip()
        job = self.job_combo.currentText().strip() or "SAM"
        patch = self.patch_combo.currentText().strip() or self.settings.app.game_patch
        perc = self.perc_spin.value()
        kills = self.kills_only.isChecked()
        conc = self.conc_spin.value()
        sleep_ms = self.sleep_spin.value()
        self.fetch_log.append(f"Filtri → Tier: {tier_text}, Boss: {boss_text}, Job: {job}, Patch: {patch}, >=Percentile: {perc}, Kills: {kills}")
        self.fetch_log.append(f"Limiti → Richieste parallele: {conc}, Sleep: {sleep_ms} ms")
        self.fetch_log.append("Esecuzione raccolta: TODO (wiring a FFLogsClient/pipeline)")

    def _on_load_bosses(self):
        # Lazy import to avoid GUI startup cost
        import os
        import asyncio
        from ff14_dataset.ingestion.fflogs_client import FFLogsClient

        client_id = os.getenv("FFLOGS_CLIENT_ID")
        client_secret = os.getenv("FFLOGS_CLIENT_SECRET")
        if not client_id or not client_secret:
            self.fetch_log.append("Errore: FFLOGS_CLIENT_ID/SECRET non impostati in .env")
            return

        async def load():
            client = FFLogsClient(client_id, client_secret, concurrency=self.conc_spin.value(), sleep_ms=self.sleep_spin.value())
            try:
                data = await client.list_zones()
            finally:
                await client.close()
            return data

        try:
            self._set_loading(True, "Caricamento tier/boss da FF Logs…")
            data = asyncio.run(load())
        except Exception as e:
            self.fetch_log.append(f"Errore caricando boss: {e}")
            return
        finally:
            self._set_loading(False)

        zones = data.get("worldData", {}).get("zones", [])
        sel = self.fight_type_combo.currentText()

        def matches(zone: dict) -> bool:
            # Some zones expose difficulty in `difficulties`, others encode it in the name
            # and some (like Ultimate) only indicate it in the encounter names.
            diffs = {d.get("name", "").lower() for d in zone.get("difficulties", [])}
            zname = (zone.get("name") or "").lower()

            def has_encounter_keyword(keyword: str) -> bool:
                for e in zone.get("encounters", []) or []:
                    en = (e.get("name") or "").lower()
                    if keyword in en:
                        return True
                return False

            if sel.startswith("Raid (Savage)"):
                return ("savage" in diffs) or ("savage" in zname) or has_encounter_keyword("savage")
            if sel.startswith("Raid (Ultimate)"):
                # Known abbreviations: UCOB, UWU, TEA, DSR, TOP, FRU
                if ("ultimate" in diffs) or ("ultimate" in zname) or has_encounter_keyword("ultimate"):
                    return True
                # Fallback: check known ultimate names in encounters
                ultimate_names = [
                    "unending coil of bahamut",
                    "weapon's refrain",
                    "epic of alexander",
                    "dragonsong's reprise",
                    "omega protocol",
                    "futures rewritten",
                ]
                for e in zone.get("encounters", []) or []:
                    en = (e.get("name") or "").lower()
                    if any(k in en for k in ultimate_names):
                        return True
                return False
            if sel.startswith("Trial (Extreme)"):
                # Trials often encode Extreme in the name rather than difficulties
                return ("extreme" in diffs) or ("extreme" in zname) or has_encounter_keyword("extreme")
            return True

        # Modalità speciale per Ultimate: raggruppa per i 6 ultimate noti
        if sel.startswith("Raid (Ultimate)"):
            self._mode = "ultimate"
            def canon_ultimate(enc_name: str) -> tuple[str, str] | None:
                n = (enc_name or "").lower()
                mapping = {
                    "UCOB": ["unending coil of bahamut", "ucob"],
                    "UWU": ["weapon's refrain", "uwu"],
                    "TEA": ["epic of alexander", "tea"],
                    "DSR": ["dragonsong's reprise", "dsr"],
                    "TOP": ["omega protocol", "top"],
                    "FRU": ["futures rewritten", "fru"],
                }
                for code, keys in mapping.items():
                    if any(k in n for k in keys) or ("(ultimate)" in n and any(k.split()[0] in n for k in keys)):
                        # Display name: preferisci la forma breve codice + nome
                        full_name = {
                            "UCOB": "The Unending Coil of Bahamut (Ultimate)",
                            "UWU": "The Weapon's Refrain (Ultimate)",
                            "TEA": "The Epic of Alexander (Ultimate)",
                            "DSR": "Dragonsong's Reprise (Ultimate)",
                            "TOP": "The Omega Protocol (Ultimate)",
                            "FRU": "Futures Rewritten (Ultimate)",
                        }[code]
                        return code, full_name
                return None

            ult_map = {}
            for z in zones:
                if not matches(z):
                    continue
                for e in z.get("encounters", []) or []:
                    res = canon_ultimate(e.get("name", ""))
                    if not res:
                        continue
                    code, disp = res
                    # Salva la prima occorrenza per ciascun ultimate
                    if code not in ult_map:
                        ult_map[code] = {
                            "display": disp,
                            "encounter_id": int(e.get("id")),
                            "zone_id": int(z.get("id")),
                        }

            order = ["UCOB", "UWU", "TEA", "DSR", "TOP", "FRU"]
            self._ultimate_map = {k: ult_map[k] for k in order if k in ult_map}

            self.tier_combo.blockSignals(True)
            self.tier_combo.clear()
            for code in self._ultimate_map.keys():
                self.tier_combo.addItem(self._ultimate_map[code]["display"], userData=code)
            self.tier_combo.blockSignals(False)

            self._populate_bosses_for_selected_tier()
            self.fetch_log.append(f"Caricati {len(self._ultimate_map)} ultimate.")
            return

        # Modalità normale (Savage/Extreme/Tutti): filtra per zone (tier)
        self._mode = "normal"
        filtered_zones = [z for z in zones if matches(z)]
        self._zones_by_id = {int(z.get("id")): z for z in filtered_zones}

        # Popola il combo dei tier con i nomi delle zone
        self.tier_combo.blockSignals(True)
        self.tier_combo.clear()
        for z in filtered_zones:
            self.tier_combo.addItem(z.get("name", f"Zone {z.get('id')}") or "", userData=int(z.get("id")))
        self.tier_combo.blockSignals(False)

        # Aggiorna boss in base al tier selezionato
        self._populate_bosses_for_selected_tier()
        self.fetch_log.append(f"Caricati {len(filtered_zones)} tier e boss per '{sel}'.")

    def _populate_bosses_for_selected_tier(self):
        if getattr(self, "_mode", "normal") == "ultimate":
            # In ultimate mode, boss list is 1:1 with the selected ultimate
            self.boss_combo.clear()
            code = self.tier_combo.currentData()
            if not code or not hasattr(self, "_ultimate_map"):
                return
            info = self._ultimate_map.get(code)
            if not info:
                return
            self.boss_combo.addItem(info["display"], userData=info["encounter_id"])
            return

        if not hasattr(self, "_zones_by_id"):
            return
        idx = self.tier_combo.currentIndex()
        if idx < 0:
            return
        tier_id = self.tier_combo.currentData()
        z = self._zones_by_id.get(int(tier_id)) if tier_id is not None else None
        self.boss_combo.clear()
        if not z:
            return
        encs = z.get("encounters", [])
        for e in encs:
            self.boss_combo.addItem(e.get("name", str(e.get("id"))) or "", userData=int(e.get("id")))

    # Carica tier/boss al primo avvio in base al default selezionato
    def showEvent(self, event):
        super().showEvent(event)
        try:
            if not hasattr(self, "_zones_by_id"):
                self._on_load_bosses()
        except Exception:
            pass

    def _set_loading(self, flag: bool, msg: str = ""):
        if flag:
            self.loading_label.setText(msg)
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            self.loading_label.setText("")
            QApplication.restoreOverrideCursor()
        # Enable/disable relevant widgets during load
        for w in [
            self.fight_type_combo,
            self.tier_combo,
            self.boss_combo,
            self.job_combo,
            self.patch_combo,
            self.conc_spin,
            self.sleep_spin,
            self.run_fetch_btn,
        ]:
            try:
                w.setEnabled(not flag)
            except Exception:
                pass


def main():
    app = QApplication()
    w = MainWindow()
    w.show()
    app.exec()
