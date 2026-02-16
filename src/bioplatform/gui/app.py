from __future__ import annotations

import sys
import webbrowser
from pathlib import Path
import re

from ..core.analysis_library import AnalysisLibrary
from ..core.data_cleaning import lof_outliers
from ..core.pipeline_engine import PythonRPipelineEngine
from ..core.preferences import PreferencesManager, UserPreferences
from ..core.r_integration import RIntegrationManager
from ..core.structure_integration import alphafold_prediction_url, detect_pymol
from ..core.workspace import WorkspaceManager
from ..llm.doe_assistant import DoEAssistant
from ..plugins.discovery import PluginIndexAggregator, PluginQuery
from ..plugins.manager import PluginRegistry
from ..plugins.microbiology_plugin import MicrobiologyPlugin
from ..plugins.runtime import LocalPluginRuntime
from ..plugins.toolkit_integrator import ToolSettingsManager, ToolkitIntegratorPlugin
from .color_tools import PaletteStore, pick_color
from .data_table import create_data_viewer_widget
from .themes import THEMES


def run(
    project: Path | None = None,
    data: Path | None = None,
    workflow: str | None = None,
    debug: bool = False,
) -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QAction, QColor, QKeySequence, QPainter, QPixmap, QShortcut
        from PySide6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QDialog,
            QDockWidget,
            QFileDialog,
            QFormLayout,
            QFrame,
            QHBoxLayout,
            QLabel,
            QInputDialog,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QPlainTextEdit,
            QMessageBox,
            QProgressBar,
            QProgressDialog,
            QPushButton,
            QSplashScreen,
            QSplitter,
            QToolBar,
            QVBoxLayout,
            QWidget,
        )
    except Exception:
        print("PySide6 is not installed. Install with: pip install '.[gui]'")
        return 1

    DataViewerWidget = create_data_viewer_widget()

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Bioinformatics Studio")
            self.setMinimumSize(1180, 760)
            self.setAcceptDrops(True)

            self.aggregator = PluginIndexAggregator()
            self.registry = PluginRegistry(Path("config/plugins.json"))
            self.runtime = LocalPluginRuntime(Path("plugins"), Path("config/plugins_enabled.json"))
            self.palette_store = PaletteStore()
            self.r_manager = RIntegrationManager(app_dir=Path.cwd())
            self.r_status = self.r_manager.detect_r()
            self.microbiology_plugin = MicrobiologyPlugin()
            self.toolkit_integrator = ToolkitIntegratorPlugin()
            self.tool_settings = ToolSettingsManager(Path("config/integrated_tools.json"))
            self.preferences_manager = PreferencesManager(Path("config/user_preferences.json"))
            self.preferences = self.preferences_manager.load()
            Path(self.preferences.project_root).mkdir(parents=True, exist_ok=True)
            Path(self.preferences.output_dir).mkdir(parents=True, exist_ok=True)
            self.workspace_manager = WorkspaceManager(Path(self.preferences.project_root))
            self.analysis_library = AnalysisLibrary()
            self.pipeline_engine = PythonRPipelineEngine(self.analysis_library)
            self.ai_assistant = self._build_ai_assistant()

            self._build_toolbar()
            self._build_shell()
            self._build_plugin_dock()
            self._build_progress_widgets()
            self._bind_shortcuts()

            self.statusBar().showMessage("Ready")

            if data:
                self._execute_with_progress("Loading startup data", lambda: self.data_viewer.load_file(data))
                self.statusBar().showMessage(f"Loaded data: {data}")
            if workflow:
                self.info_panel.addItem(f"Requested workflow: {workflow}")
            if debug:
                self.info_panel.addItem("Debug mode enabled")

        def _build_toolbar(self) -> None:
            toolbar = QToolBar("Main")
            toolbar.setMovable(False)
            self.addToolBar(toolbar)

            new_project_action = QAction("New Project", self)
            new_project_action.triggered.connect(self.create_new_project)
            toolbar.addAction(new_project_action)

            import_action = QAction("Import", self)
            import_action.triggered.connect(self._open_file_from_toolbar)
            toolbar.addAction(import_action)

            color_action = QAction("Color", self)
            color_action.triggered.connect(self.choose_color)
            toolbar.addAction(color_action)

            plugin_action = QAction("Plugins", self)
            plugin_action.triggered.connect(self.show_plugin_marketplace)
            toolbar.addAction(plugin_action)

            structure_action = QAction("Structure", self)
            structure_action.triggered.connect(self.open_structure_tools)
            toolbar.addAction(structure_action)

            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(self.open_toolkit_settings)
            toolbar.addAction(settings_action)

            analysis_lib_action = QAction("Analysis Library", self)
            analysis_lib_action.triggered.connect(self.open_analysis_library)
            toolbar.addAction(analysis_lib_action)

            pipeline_action = QAction("Pipelines", self)
            pipeline_action.triggered.connect(self.open_pipeline_runner)
            toolbar.addAction(pipeline_action)

            ai_action = QAction("AI Assistant", self)
            ai_action.triggered.connect(self.open_ai_assistant)
            toolbar.addAction(ai_action)

            toolbar.addSeparator()
            header = QLabel("Bioinformatics Studio")
            header.setObjectName("AppHeading")
            toolbar.addWidget(header)

        def _build_shell(self) -> None:
            shell = QWidget(self)
            shell_layout = QVBoxLayout(shell)
            shell_layout.setContentsMargins(10, 10, 10, 10)
            shell_layout.setSpacing(10)

            hero = QFrame()
            hero.setObjectName("Card")
            hero_layout = QHBoxLayout(hero)

            left = QVBoxLayout()
            title = QLabel("Research Workspace")
            title.setObjectName("SectionTitle")
            left.addWidget(title)
            default_project = project if project else Path(self.preferences.project_root)
            left.addWidget(QLabel(f"Project root: {default_project}"))
            left.addWidget(QLabel(f"Output dir: {self.preferences.output_dir}"))
            left.addWidget(QLabel(self.r_status.message))
            hero_layout.addLayout(left, 2)

            right = QHBoxLayout()
            self.global_search = QLineEdit()
            self.global_search.setPlaceholderText("Search commands, files, analyses (Ctrl+K)")
            self.global_search.setToolTip("Global quick search command bar.")
            right.addWidget(self.global_search)

            self.theme_combo = QComboBox()
            self.theme_combo.addItems(list(THEMES.keys()))
            self.theme_combo.currentTextChanged.connect(self.apply_theme)
            self.theme_combo.setToolTip("Instant theme switch.")
            right.addWidget(self.theme_combo)

            color_btn = QPushButton("Pick Color")
            color_btn.setToolTip("Open scientific color picker with alpha support.")
            color_btn.clicked.connect(self.choose_color)
            right.addWidget(color_btn)

            hero_layout.addLayout(right, 3)
            shell_layout.addWidget(hero)

            splitter = QSplitter(Qt.Horizontal)

            nav = QListWidget()
            nav.addItems([
                "📊 Data",
                "🔬 Analysis",
                "📈 Visualizations",
                "🧪 Microbiology",
                "🧬 Biophysics",
                "📦 Plugins",
                "⚙️ Settings",
            ])
            nav.setMaximumWidth(240)
            nav.currentTextChanged.connect(self._on_nav_change)
            nav.setCurrentRow(0)
            splitter.addWidget(nav)

            self.data_viewer = DataViewerWidget()
            self.data_viewer.selection_changed.connect(self._on_selection_count)
            splitter.addWidget(self.data_viewer)

            side = QFrame()
            side.setObjectName("Card")
            side_layout = QVBoxLayout(side)
            info_title = QLabel("Inspector")
            info_title.setObjectName("SectionTitle")
            side_layout.addWidget(info_title)

            self.info_panel = QListWidget()
            self.info_panel.addItem("Selection summary appears here.")
            side_layout.addWidget(self.info_panel)
            splitter.addWidget(side)
            splitter.setSizes([190, 900, 280])

            shell_layout.addWidget(splitter)
            self.setCentralWidget(shell)

        def _build_plugin_dock(self) -> None:
            plugin_dock = QDockWidget("Plugin Manager", self)
            plugin_widget = QWidget()
            plugin_layout = QVBoxLayout(plugin_widget)

            self.plugin_query = QLineEdit()
            self.plugin_query.setPlaceholderText("Search CRAN/Bioconductor or paste GitHub repo")
            self.plugin_query.setToolTip("Find bioinformatics plugins. GitHub fallback supported.")
            plugin_layout.addWidget(self.plugin_query)

            plugin_search_btn = QPushButton("Search Plugins")
            plugin_search_btn.clicked.connect(self.search_plugins)
            plugin_layout.addWidget(plugin_search_btn)

            self.plugin_results = QListWidget()
            self.plugin_results.itemDoubleClicked.connect(self.install_selected)
            plugin_layout.addWidget(self.plugin_results)

            plugin_dock.setWidget(plugin_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, plugin_dock)

        def _bind_shortcuts(self) -> None:
            QShortcut(QKeySequence("Ctrl+K"), self, activated=self.open_command_palette)
            QShortcut(QKeySequence("Ctrl+L"), self, activated=self._clear_info)

        def _build_progress_widgets(self) -> None:
            self.task_progress = QProgressBar(self)
            self.task_progress.setRange(0, 100)
            self.task_progress.setValue(0)
            self.task_progress.setFixedWidth(220)
            self.task_progress.setFormat("Idle")
            self.statusBar().addPermanentWidget(self.task_progress)

            self.loading_dialog = QProgressDialog("Loading...", None, 0, 0, self)
            self.loading_dialog.setWindowTitle("Please wait")
            self.loading_dialog.setWindowModality(Qt.WindowModal)
            self.loading_dialog.setCancelButton(None)
            self.loading_dialog.close()

        def _execute_with_progress(self, label: str, task) -> object:  # type: ignore[no-untyped-def]
            self.task_progress.setRange(0, 0)
            self.task_progress.setFormat(label)
            self.loading_dialog.setLabelText(f"{label}…")
            self.loading_dialog.show()
            QApplication.processEvents()
            try:
                return task()
            finally:
                self.loading_dialog.hide()
                self.task_progress.setRange(0, 100)
                self.task_progress.setValue(100)
                self.task_progress.setFormat(f"{label} complete")

        def open_command_palette(self) -> None:
            dlg = QDialog(self)
            dlg.setWindowTitle("Command Palette")
            layout = QVBoxLayout(dlg)
            search = QLineEdit()
            search.setPlaceholderText("Type a command...")
            layout.addWidget(search)
            lst = QListWidget()
            commands = [
                "Create New Project",
                "Import Data",
                "Open Plugin Marketplace",
                "Switch Theme",
                "Open Local FASTA",
                "Run QC Checks",
                "Run Microbiology Auto-Analysis",
                "Open AlphaFold entry",
                "Check PyMOL integration",
                "Open Analysis Library",
                "Open Pipeline Runner",
                "Open AI Assistant",
            ]
            for cmd in commands:
                lst.addItem(cmd)
            layout.addWidget(lst)

            def do_filter(txt: str) -> None:
                for i in range(lst.count()):
                    it = lst.item(i)
                    it.setHidden(txt.lower() not in it.text().lower())

            search.textChanged.connect(do_filter)
            search.setFocus()
            dlg.resize(420, 320)
            dlg.exec()

        def dragEnterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def dropEvent(self, event) -> None:  # type: ignore[no-untyped-def]
            urls = event.mimeData().urls()
            if not urls:
                return
            path = Path(urls[0].toLocalFile())
            self.intelligent_analysis_suggestion(path)


        def _on_nav_change(self, section: str) -> None:
            self.statusBar().showMessage(f"Section: {section}", 2000)
            if "Microbiology" in section:
                self.run_microbiology_auto_analysis()
            if "Settings" in section:
                self.open_toolkit_settings()

        def run_microbiology_auto_analysis(self) -> None:
            sample_payload = {"mode": "growth", "time_hours": [0, 2, 4, 6], "od600": [0.03, 0.05, 0.18, 0.42]}
            result = self._execute_with_progress(
                "Running microbiology analysis",
                lambda: self.microbiology_plugin.execute_logic(sample_payload),
            )
            self.info_panel.addItem(
                f"Microbiology μmax={result['mu_max']:.3f}, K={result['carrying_capacity']:.3f}, lag={result['lag_phase_hours']}h"
            )
            outliers = lof_outliers([0.03, 0.05, 0.18, 0.42])
            if outliers:
                self.info_panel.addItem(f"LOF outliers (indices): {outliers}")
            if result["flags"]:
                self.statusBar().showMessage(result["flags"][0], 5000)


        def open_structure_tools(self) -> None:
            status = detect_pymol()
            uid = "P69905"
            af_url = alphafold_prediction_url(uid)
            self.info_panel.addItem(status.message)
            self.info_panel.addItem(f"AlphaFold quick link: {af_url}")

            msg = QMessageBox(self)
            msg.setWindowTitle("Structure Tools")
            msg.setText(
                f"PyMOL: {'available' if status.available else 'not installed'}\n"
                f"AlphaFold entry prepared for {uid}."
            )
            open_btn = msg.addButton("Open AlphaFold", QMessageBox.AcceptRole)
            msg.addButton("Close", QMessageBox.RejectRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                webbrowser.open(af_url)

        def open_analysis_library(self) -> None:
            dlg = QDialog(self)
            dlg.setWindowTitle("Analysis Library (R + Python)")
            layout = QVBoxLayout(dlg)

            layout.addWidget(QLabel("Curated function catalog for bioinformatics/genomics/pharmacology/microbiology"))
            items = QListWidget()
            catalog = self.analysis_library.catalog()
            for item in catalog:
                items.addItem(f"{item.func_id} | {item.language} | {item.domain} | {item.title}")
            layout.addWidget(items)

            input_line = QLineEdit()
            input_line.setPlaceholderText("Numeric payload for Python functions (comma separated): e.g. 1,2,3")
            layout.addWidget(input_line)

            output = QPlainTextEdit()
            output.setReadOnly(True)
            layout.addWidget(output)

            run_btn = QPushButton("Run/Preview")

            def run_selected() -> None:
                row = items.currentRow()
                if row < 0:
                    output.setPlainText("Select a function from the catalog.")
                    return
                selected = catalog[row]
                if selected.language == "python":
                    try:
                        values = [float(x.strip()) for x in input_line.text().split(",") if x.strip()]
                    except Exception:
                        output.setPlainText("Invalid numeric payload.")
                        return
                    try:
                        result = self.analysis_library.execute_python(selected.func_id, values)
                        output.setPlainText(f"Python result: {result}")
                    except Exception as exc:
                        output.setPlainText(f"Execution error: {exc}")
                else:
                    try:
                        tpl = self.analysis_library.r_template(selected.func_id)
                        output.setPlainText(tpl)
                    except Exception as exc:
                        output.setPlainText(f"Template error: {exc}")

            run_btn.clicked.connect(run_selected)
            layout.addWidget(run_btn)
            dlg.resize(920, 620)
            dlg.exec()

        def open_pipeline_runner(self) -> None:
            dlg = QDialog(self)
            dlg.setWindowTitle("Python/R Pipeline Runner")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Pipeline: clean → stats → figure (editable export)"))

            input_line = QLineEdit()
            input_line.setPlaceholderText("Values (comma separated), e.g. 0.1,0.2,0.3,1.1")
            layout.addWidget(input_line)

            output = QPlainTextEdit()
            output.setReadOnly(True)
            layout.addWidget(output)

            run_btn = QPushButton("Run Pipeline")
            export_btn = QPushButton("Export Figure (PNG/SVG/PDF)")
            export_btn.setEnabled(False)
            r_template_btn = QPushButton("Show R Pipeline Template")

            state: dict[str, object] = {"result": None}

            def run_pipeline() -> None:
                try:
                    values = [float(x.strip()) for x in input_line.text().split(",") if x.strip()]
                except Exception:
                    output.setPlainText("Invalid numeric input.")
                    return
                result = self._execute_with_progress("Running pipeline", lambda: self.pipeline_engine.run_growth_pipeline(values))
                state["result"] = result
                export_btn.setEnabled(result.figure is not None)
                output.setPlainText(
                    "Pipeline complete\n"
                    f"Cleaned: {result.cleaned}\n"
                    f"Stats: {result.stats}\n"
                    f"Outliers: {result.outliers}\n"
                    f"Figure ready: {'yes' if result.figure is not None else 'no (matplotlib missing)'}"
                )

            def export_figure() -> None:
                result = state.get("result")
                if result is None:
                    output.setPlainText("Run pipeline first.")
                    return
                target, _ = QFileDialog.getSaveFileName(
                    self,
                    "Export pipeline figure",
                    str(Path(self.preferences.output_dir) / "pipeline_plot"),
                    "PNG file (*.png)",
                )
                if not target:
                    return
                exported = self.pipeline_engine.export_figure_high_quality(result.figure, Path(target).with_suffix(""))
                output.appendPlainText(f"Exported: {exported}")

            def show_r_template() -> None:
                output.setPlainText(self.pipeline_engine.r_pipeline_template())

            run_btn.clicked.connect(run_pipeline)
            export_btn.clicked.connect(export_figure)
            r_template_btn.clicked.connect(show_r_template)
            layout.addWidget(run_btn)
            layout.addWidget(export_btn)
            layout.addWidget(r_template_btn)

            dlg.resize(900, 620)
            dlg.exec()

        def _build_ai_assistant(self) -> DoEAssistant:
            provider = self.preferences.ai_provider if self.preferences.ai_provider in {"chatgpt", "gemini"} else "chatgpt"
            api_key = self.preferences.openai_api_key if provider == "chatgpt" else self.preferences.gemini_api_key
            return DoEAssistant(provider=provider, api_key=api_key or None)

        def _local_ai_suggestion(self, prompt: str) -> str:
            lower = prompt.lower()
            if "pipeline" in lower or "automate" in lower:
                return (
                    "Suggested process: 1) clean input values, 2) compute stats (mean/std), "
                    "3) detect outliers, 4) generate and export figure as SVG/PDF/600-DPI PNG."
                )
            if "microbio" in lower or "growth" in lower:
                return "Suggested process: run microbiology auto-analysis and inspect μmax, lag phase, and LOF outliers."
            if "sequence" in lower or "fasta" in lower:
                return "Suggested process: sanitize sequences, run QC checks, and open sequence viewer for curation."
            return "Provide a goal (pipeline, microbiology, sequence, or stats) for a concrete suggested workflow."

        def _extract_numeric_payload(self, text: str) -> list[float]:
            return [float(token) for token in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)]

        def open_ai_assistant(self) -> None:
            dlg = QDialog(self)
            dlg.setWindowTitle("AI Assistant (ChatGPT/Gemini)")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Ask for workflow suggestions or execute an automated process."))

            prompt_line = QLineEdit()
            prompt_line.setPlaceholderText("Prompt, e.g. 'Run pipeline on 0.12, 0.18, 0.35, 1.1'")
            layout.addWidget(prompt_line)

            output = QPlainTextEdit()
            output.setReadOnly(True)
            layout.addWidget(output)

            ask_btn = QPushButton("Get Suggestion")
            run_btn = QPushButton("Execute Process")
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(ask_btn)
            row_layout.addWidget(run_btn)
            layout.addWidget(row)

            def ask_ai() -> None:
                prompt = prompt_line.text().strip()
                if not prompt:
                    output.setPlainText("Enter a prompt first.")
                    return
                has_key = bool(self.ai_assistant.api_key)
                if has_key:
                    response = self._execute_with_progress("Querying AI assistant", lambda: self.ai_assistant.chat(prompt))
                    output.setPlainText(str(response))
                else:
                    output.setPlainText(
                        "API key not configured in Settings. Showing local workflow guidance:\n\n"
                        + self._local_ai_suggestion(prompt)
                    )

            def execute_process() -> None:
                prompt = prompt_line.text().strip()
                if not prompt:
                    output.setPlainText("Enter a prompt that includes a process request.")
                    return
                lower = prompt.lower()
                if "pipeline" in lower:
                    values = self._extract_numeric_payload(prompt)
                    if not values:
                        output.setPlainText("No numeric payload found. Example: 'run pipeline 0.1,0.2,0.3,1.0'")
                        return
                    result = self._execute_with_progress("Running pipeline", lambda: self.pipeline_engine.run_growth_pipeline(values))
                    output.setPlainText(
                        "Pipeline executed\n"
                        f"Cleaned: {result.cleaned}\n"
                        f"Stats: {result.stats}\n"
                        f"Outliers: {result.outliers}\n"
                        f"Figure ready: {'yes' if result.figure is not None else 'no'}"
                    )
                    self.info_panel.addItem("AI executed pipeline successfully.")
                    return
                if "microbio" in lower or "growth" in lower:
                    self.run_microbiology_auto_analysis()
                    output.setPlainText("Executed microbiology auto-analysis. See Inspector for details.")
                    self.info_panel.addItem("AI executed microbiology auto-analysis.")
                    return
                output.setPlainText(
                    "Supported executions: include 'pipeline' with numbers, or 'microbiology/growth' for auto-analysis."
                )

            ask_btn.clicked.connect(ask_ai)
            run_btn.clicked.connect(execute_process)
            dlg.resize(940, 640)
            dlg.exec()

        def create_new_project(self) -> None:
            project_id, ok = QInputDialog.getText(self, "New Project", "Project name:")
            if not ok:
                return
            project_id = project_id.strip()
            if not project_id:
                self.statusBar().showMessage("Project name is required", 2500)
                return

            paths = self._execute_with_progress(
                "Creating project",
                lambda: self.workspace_manager.create_project(project_id),
            )
            self.info_panel.addItem(f"Created project: {paths.root}")
            self.info_panel.addItem(f"Results folder: {paths.results}")
            self.statusBar().showMessage(f"Project '{project_id}' created", 3000)

        def open_toolkit_settings(self) -> None:
            settings = self.tool_settings.load()
            prefs = self.preferences_manager.load()
            dlg = QDialog(self)
            dlg.setWindowTitle("Integrated Toolkit Settings")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Enable/disable integrated open-source tools"))

            checkboxes: dict[str, QCheckBox] = {}
            for key in ["gseapy", "biopandas", "cobrapy", "statsmodels"]:
                cb = QCheckBox(key)
                cb.setChecked(bool(settings.get(key, True)))
                checkboxes[key] = cb
                layout.addWidget(cb)

            form = QFormLayout()
            project_root_edit = QLineEdit(prefs.project_root)
            output_dir_edit = QLineEdit(prefs.output_dir)
            provider_combo = QComboBox()
            provider_combo.addItems(["chatgpt", "gemini"])
            provider_combo.setCurrentText(prefs.ai_provider if prefs.ai_provider in {"chatgpt", "gemini"} else "chatgpt")
            openai_key_edit = QLineEdit(prefs.openai_api_key)
            openai_key_edit.setEchoMode(QLineEdit.Password)
            openai_key_edit.setPlaceholderText("OpenAI API key")
            gemini_key_edit = QLineEdit(prefs.gemini_api_key)
            gemini_key_edit.setEchoMode(QLineEdit.Password)
            gemini_key_edit.setPlaceholderText("Gemini API key")

            project_browse = QPushButton("Browse…")
            output_browse = QPushButton("Browse…")

            def pick_project_root() -> None:
                chosen = QFileDialog.getExistingDirectory(self, "Select project root", project_root_edit.text())
                if chosen:
                    project_root_edit.setText(chosen)

            def pick_output_dir() -> None:
                chosen = QFileDialog.getExistingDirectory(self, "Select output directory", output_dir_edit.text())
                if chosen:
                    output_dir_edit.setText(chosen)

            project_browse.clicked.connect(pick_project_root)
            output_browse.clicked.connect(pick_output_dir)

            project_row = QWidget()
            project_row_layout = QHBoxLayout(project_row)
            project_row_layout.setContentsMargins(0, 0, 0, 0)
            project_row_layout.addWidget(project_root_edit)
            project_row_layout.addWidget(project_browse)

            output_row = QWidget()
            output_row_layout = QHBoxLayout(output_row)
            output_row_layout.setContentsMargins(0, 0, 0, 0)
            output_row_layout.addWidget(output_dir_edit)
            output_row_layout.addWidget(output_browse)

            form.addRow("Project root", project_row)
            form.addRow("Output directory", output_row)
            form.addRow("AI provider", provider_combo)
            form.addRow("ChatGPT API key", openai_key_edit)
            form.addRow("Gemini API key", gemini_key_edit)
            layout.addLayout(form)

            save_btn = QPushButton("Save")

            def save() -> None:
                new_settings = {k: v.isChecked() for k, v in checkboxes.items()}
                self.tool_settings.save(new_settings)
                new_prefs = UserPreferences(
                    project_root=project_root_edit.text().strip() or "projects",
                    output_dir=output_dir_edit.text().strip() or "outputs",
                    ai_provider=provider_combo.currentText(),
                    openai_api_key=openai_key_edit.text().strip(),
                    gemini_api_key=gemini_key_edit.text().strip(),
                )
                self.preferences_manager.save(new_prefs)
                self.preferences = new_prefs
                self.ai_assistant = self._build_ai_assistant()
                Path(self.preferences.project_root).mkdir(parents=True, exist_ok=True)
                Path(self.preferences.output_dir).mkdir(parents=True, exist_ok=True)
                self.workspace_manager = WorkspaceManager(Path(self.preferences.project_root))
                self.statusBar().showMessage("Toolkit, path, and AI settings saved", 3000)
                dlg.accept()

            save_btn.clicked.connect(save)
            layout.addWidget(save_btn)
            dlg.exec()

        def intelligent_analysis_suggestion(self, path: Path) -> None:
            ext = path.suffix.lower()
            if ext in {".fasta", ".fa", ".fastq", ".fq"}:
                suggestion = "Sequence Viewer + ORF finder + GC profile"
            elif ext in {".vcf", ".bcf"}:
                suggestion = "Variant table + filtration + annotation"
            elif ext in {".pdb", ".cif"}:
                suggestion = "3D protein model + binding-site analysis"
            else:
                suggestion = "General import + data profiling"
            QMessageBox.information(
                self,
                "Intelligent Analysis",
                f"Detected file: {path.name}\nRecommended workflow: {suggestion}",
            )

        def show_plugin_marketplace(self) -> None:
            dlg = QDialog(self)
            dlg.setWindowTitle("Plugin Marketplace")
            layout = QVBoxLayout(dlg)
            label = QLabel("Enable/disable hot-swappable modules")
            layout.addWidget(label)
            items = QListWidget()
            plugins = self.runtime.list_plugins()
            for plugin in plugins:
                it = QListWidgetItem(f"{plugin.name} ({plugin.plugin_id}) - {plugin.description}")
                it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                it.setCheckState(Qt.CheckState.Checked if plugin.enabled else Qt.CheckState.Unchecked)
                items.addItem(it)
            layout.addWidget(items)

            def persist_states() -> None:
                for i, plugin in enumerate(plugins):
                    enabled = items.item(i).checkState() == Qt.CheckState.Checked
                    self.runtime.set_enabled(plugin.plugin_id, enabled)
                dlg.accept()

            save_btn = QPushButton("Save")
            save_btn.clicked.connect(persist_states)
            layout.addWidget(save_btn)
            dlg.resize(680, 420)
            dlg.exec()

        def _open_file_from_toolbar(self) -> None:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Import data",
                str(Path(self.preferences.project_root)),
                "Bio Files (*.csv *.tsv *.xlsx *.fasta *.fa *.fastq *.fq *.vcf *.pdb *.cif);;All Files (*.*)",
            )
            if not file_name:
                return
            path = Path(file_name)
            if path.suffix.lower() == ".csv":
                self._execute_with_progress("Importing data", lambda: self.data_viewer.load_file(path))
            else:
                self.intelligent_analysis_suggestion(path)

        def _clear_info(self) -> None:
            self.info_panel.clear()
            self.info_panel.addItem("Inspector cleared.")

        def apply_theme(self, name: str) -> None:
            theme = THEMES[name]
            QApplication.instance().setStyleSheet(theme.stylesheet)
            self.statusBar().showMessage(f"Theme: {name}", 2500)

        def choose_color(self) -> None:
            color = pick_color(self, self.palette_store)
            if color:
                self.info_panel.addItem(
                    f"Picked color: {color} | recent={', '.join(self.palette_store.recent[:4])}"
                )

        def _on_selection_count(self, count: int) -> None:
            self.info_panel.addItem(f"Selected rows: {count}")

        def search_plugins(self) -> None:
            query = self.plugin_query.text().strip()
            if not query:
                self.statusBar().showMessage("Enter a plugin query", 2500)
                return
            manifests = self._execute_with_progress(
                "Searching plugins",
                lambda: self.aggregator.search_all(PluginQuery(query, limit=25)),
            )
            self.plugin_results.clear()
            if not manifests and ("/" in query or query.startswith("http")):
                gh = self.aggregator.import_from_github(query)
                self.plugin_results.addItem(f"{gh.id} | {gh.description}")
                self.statusBar().showMessage("GitHub fallback entry created", 3000)
                return
            for item in manifests:
                self.plugin_results.addItem(f"{item.id} | {item.version} | {item.description}")
            self.statusBar().showMessage(f"Found {len(manifests)} plugin candidates", 3000)

        def install_selected(self, item) -> None:  # type: ignore[no-untyped-def]
            raw = item.text().split(" | ")[0]
            if raw.startswith("github:"):
                manifest = self.aggregator.import_from_github(raw.replace("github:", ""))
            else:
                QMessageBox.information(self, "Install", "MVP install currently supports GitHub fallback entries.")
                return
            self.registry.install_manifest(manifest)
            self.statusBar().showMessage(f"Installed {manifest.id}", 3500)

    app = QApplication(sys.argv)

    splash_pixmap = QPixmap(520, 280)
    splash_pixmap.fill(QColor("#efe7d8"))
    painter = QPainter(splash_pixmap)
    painter.setPen(QColor("#3a3128"))
    painter.drawText(40, 130, "Bioinformatics Studio")
    painter.setPen(QColor("#6f6251"))
    painter.drawText(40, 165, "Loading modules, plugins, and workspace…")
    painter.end()
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    splash.showMessage("Starting application…", Qt.AlignBottom | Qt.AlignLeft, QColor("#3a3128"))
    app.processEvents()

    win = MainWindow()
    win.resize(1440, 860)
    win.apply_theme("light")
    win.show()
    splash.finish(win)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
