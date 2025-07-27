import sys
import json
import re
import string
import os
from pathlib import Path
import subprocess
import logging  # Ajouté pour les logs
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QListWidget,
    QSplitter, QLabel, QCheckBox, QMenuBar, QAction,
    QFileDialog, QWidgetAction, QMessageBox
)
from PyQt5.QtGui import QFont, QColor, QTextCursor, QTextCharFormat, QIcon
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtPrintSupport import QPrinter
from fuzzywuzzy import fuzz
import urllib.request  # Ajouté pour la vérification de mise à jour
import shutil


APP_VERSION = "1.0.2"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/RoK-studio2/homeopathy/main/homeopathy_version.txt"
GITHUB_EXE_URL = "https://github.com/RoK-studio2/homeopathy/releases/latest/download/App.exe"


# Journalisation discrète
hidden_log_dir = Path(__file__).parent / ".cache"
hidden_log_dir.mkdir(exist_ok=True)
hidden_log_path = hidden_log_dir / ".sysdata"
logging.basicConfig(
    filename=hidden_log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

class HomeopathyApp(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.results = []
        self.current_page = 0
        self.results_per_page = 20
        self.favorites = []
        self.fav_path = Path.home() / "Homeopathy" / "favorites.json"
        self.search_name = QCheckBox("По названию")
        self.search_symptoms = QCheckBox("По симптомам")
        self.load_favorites()
        self.initUI()
        self.check_for_updates()  # Vérification de mise à jour au démarrage
        self.icon_path = Path(__file__).parent / "app.ico"
        if self.icon_path.exists():
            self.setWindowIcon(QIcon(str(self.icon_path)))
        else:
            print(f"⚠️ Icône non trouvée : {self.icon_path}")

        logging.info("Application démarrée")

    def check_for_updates(self):
        update_url = "https://raw.githubusercontent.com/RoK-studio2/homeopathy/main/homeopathy_version.txt"

        try:
            with urllib.request.urlopen(update_url, timeout=5) as response:
                latest_version = response.read().decode("utf-8").strip()
            if latest_version != APP_VERSION:
                QMessageBox.information(
                    self,
                    "Обновление доступно",
                    f"Доступна новая версия приложения: {latest_version}\n"
                    "Пожалуйста, скачайте последнюю версию."
                )
                self.open_download_page()  # 👉 déplacé ici
        except Exception as e:
            print("Не удалось проверить обновление:", e)


    def open_download_page(self):
        import webbrowser
        # Remplace ce lien par l’URL exacte de ton fichier ou ta page GitHub
        download_url = "https://github.com/RoK-studio2/homeopathy/releases/latest"
        webbrowser.open(download_url)


    def initUI(self):
        self.setWindowTitle("Справочник гомеопатии")
        self.setFixedSize(1100, 700)
        font = QFont("Segoe UI", 15)  # Крупнее шрифт
        update_button = QPushButton("🔄 Vérifier les mises à jour", self)
        update_button.clicked.connect(self.check_for_updates)
        update_button.move(20, 50)  # Positionne-le où tu veux

        # Верхняя строка меню
        menubar = QMenuBar(self)

        # Меню Настройки (Параметры)
        settings_menu = menubar.addMenu("Настройки")
        # Ajout : cases à cocher pour les paramètres de recherche
        self.search_name.setChecked(True)
        self.search_symptoms.setChecked(True)
        self.search_name.setFont(font)
        self.search_symptoms.setFont(font)
        # Ajout dans le menu
        action_name = QWidgetAction(self)
        action_name.setDefaultWidget(self.search_name)
        action_symptoms = QWidgetAction(self)
        action_symptoms.setDefaultWidget(self.search_symptoms)
        settings_menu.addAction(action_name)
        settings_menu.addAction(action_symptoms)
        # Synchronisation avec le menu Отображение
        self.search_name.stateChanged.connect(lambda _: self.sync_display_menu())
        self.search_symptoms.stateChanged.connect(lambda _: self.sync_display_menu())

        # Меню Избранное
        fav_menu = menubar.addMenu("Избранное")
        fav_action = QAction("Открыть избранное", self)
        fav_action.triggered.connect(self.show_favorites_window)
        fav_menu.addAction(fav_action)

        # Меню Экспорт
        export_menu = menubar.addMenu("Экспорт")
        pdf_action = QAction("Экспорт в PDF", self)
        pdf_action.triggered.connect(self.export_pdf)
        export_menu.addAction(pdf_action)

        txt_action = QAction("Экспорт в TXT", self)
        txt_action.triggered.connect(self.export_txt)
        export_menu.addAction(txt_action)

        html_action = QAction("Экспорт в HTML", self)
        html_action.triggered.connect(self.export_html)
        export_menu.addAction(html_action)

        # Меню Отображение
        display_menu = menubar.addMenu("Отображение")
        self.name_action = QAction("По названию", self, checkable=True)
        self.name_action.setChecked(True)
        self.name_action.triggered.connect(lambda checked: self.set_search_name(checked))
        display_menu.addAction(self.name_action)
        self.symptoms_action = QAction("По симптомам", self, checkable=True)
        self.symptoms_action.setChecked(True)
        self.symptoms_action.triggered.connect(lambda checked: self.set_search_symptoms(checked))
        display_menu.addAction(self.symptoms_action)

        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        help_action = QAction("Показать справку", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        # Barre de recherche compacte
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setFont(font)
        self.search_input.setPlaceholderText("Введите название препарата или ключевое слово...")
        self.search_input.setFixedHeight(38)  # Plus grand
        self.search_input.setStyleSheet("border-radius: 6px; padding: 6px; font-size: 18px;")

        self.search_button = QPushButton("Поиск")
        self.search_button.setFont(font)
        self.search_button.setFixedHeight(38)
        self.search_button.setStyleSheet("border-radius: 6px; font-size: 18px; padding: 6px 18px;")

        self.clear_button = QPushButton("Очистить")
        self.clear_button.setFont(font)
        self.clear_button.setFixedHeight(38)
        self.clear_button.setStyleSheet("border-radius: 6px; font-size: 18px; padding: 6px 18px;")

        search_bar.addWidget(self.search_input, stretch=2)
        search_bar.addWidget(self.search_button)
        search_bar.addWidget(self.clear_button)

        # Résultats et détails
        splitter = QSplitter(Qt.Horizontal)
        self.result_list = QListWidget()
        self.result_list.setFont(font)
        self.result_list.setStyleSheet("border-radius: 6px; font-size: 18px;")
        splitter.addWidget(self.result_list)

        self.details_area = QTextEdit()
        self.details_area.setReadOnly(True)
        self.details_area.setFont(font)
        self.details_area.setStyleSheet("border-radius: 6px; font-size: 18px;")
        splitter.addWidget(self.details_area)
        splitter.setSizes([350, 750])

        # Label résultats
        self.results_count_label = QLabel("")
        self.results_count_label.setFont(font)
        self.results_count_label.setMaximumHeight(32)

        # Ajout du bouton "Добавить в избранное"
        self.add_fav_button = QPushButton("Добавить в избранное")
        self.add_fav_button.setFont(QFont("Segoe UI", 15))
        self.add_fav_button.setFixedHeight(38)
        self.add_fav_button.setStyleSheet("border-radius: 6px; font-size: 18px; padding: 6px 18px;")
        self.add_fav_button.clicked.connect(self.add_to_favorites)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setMenuBar(menubar)
        main_layout.addLayout(search_bar)
        main_layout.addWidget(self.results_count_label)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.add_fav_button)  # Ajout du bouton ici
        self.setLayout(main_layout)

        # Connexions
        self.search_button.clicked.connect(self.update_results)
        self.clear_button.clicked.connect(self.clear_search)
        self.result_list.itemClicked.connect(self.display_details)
        self.search_input.textChanged.connect(self.update_results)

        # Focus et raccourcis
        self.search_input.setFocus()
        self.search_button.setShortcut("Return")
        self.clear_button.setShortcut("Esc")

        # Style général compact
        self.setStyleSheet("""
            QWidget { background-color: #f4f8fb; color: #222; }
            QLineEdit, QListWidget, QTextEdit { background-color: #fff; color: #222; border-radius: 6px; border: 1px solid #dbe6ec; font-size: 18px; }
            QPushButton { background-color: #e0e0e0; color: #222; border-radius: 6px; border: 1px solid #c3d3e7; padding: 6px 18px; font-size: 18px; }
            QPushButton:hover { background-color: #f5f5f5; }
            QCheckBox { padding: 4px; font-size: 18px; }
            QMenuBar { background-color: #eaf3fb; color: #222; font-size: 18px; }
            QMenu { background-color: #fff; color: #222; border: 1px solid #c3d3e7; font-size: 18px; }
            QMenu::item:selected { background-color: #b0bec5; color: #222; }
        """)

    # Synchronisation des cases à cocher menu <-> параметры
    def set_search_name(self, checked):
        self.search_name.setChecked(checked)

    def set_search_symptoms(self, checked):
        self.search_symptoms.setChecked(checked)

    def sync_display_menu(self):
        self.name_action.setChecked(self.search_name.isChecked())
        self.symptoms_action.setChecked(self.search_symptoms.isChecked())
        self.update_results()

    def clear_search(self):
        self.search_input.clear()
        self.result_list.clear()
        self.details_area.clear()
        self.results_count_label.setText("")
        self.results = []

    def highlight_text(self, text, query_words):
        words = re.split(r'(\W+)', text)
        highlighted_words = []
        for w in words:
            clean_w = re.sub(r'<[^>]+>', '', w)
            # Точное совпадение
            if any(len(q) > 1 and clean_w.lower() == q.lower() for q in query_words):
                highlighted_words.append(f"<span style='background-color: yellow'>{w}</span>")
            # Похожее слово (>=70%) и длина слова > 1
            elif any(len(q) > 1 and len(clean_w) > 1 and fuzz.partial_ratio(q.lower(), clean_w.lower()) >= 70 for q in query_words):
                highlighted_words.append(f"<span style='background-color: #FFFF88'>{w}</span>")
            else:
                highlighted_words.append(w)
        return "".join(highlighted_words)

    def update_results(self):
        query = self.search_input.text().strip()
        logging.info(f"Recherche lancée : '{query}'")
        translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
        cleaned_query = query.translate(translator)
        query_words = [w.lower() for w in cleaned_query.split() if w]

        self.result_list.clear()
        self.details_area.clear()
        self.results = []
        self.results_count_label.setText("")

        if not query_words:
            logging.info("Recherche vide")
            self.results_count_label.setText("Пожалуйста, введите ключевое слово.")
            return

        SIMILARITY_THRESHOLD = 60  # plus tolérant

        scored_results = []

        for latin, info in self.data.items():
            scores = []
            found = False
            for word in query_words:
                if len(word) < 2:
                    continue
                if self.search_name.isChecked():
                    score_name = fuzz.WRatio(word, f"{latin} {info['russian']}".lower())
                    scores.append(score_name)
                    if word in f"{latin} {info['russian']}".lower():
                        found = True
                if self.search_symptoms.isChecked():
                    symptoms_text = " ".join(info.get('symptoms', [])).lower()
                    score_symptoms = fuzz.WRatio(word, symptoms_text)
                    scores.append(score_symptoms)
                    if word in symptoms_text:
                        found = True
            avg_score = sum(scores) / len(scores) if scores else 0
            if avg_score >= SIMILARITY_THRESHOLD or found:
                scored_results.append((avg_score, latin, info))

        if not scored_results:
            logging.info("Aucun résultat trouvé")
            self.result_list.addItem("Результаты не найдены.")
            self.results_count_label.setText("Нет результатов.")
            return
        else:
            logging.info(f"{len(scored_results)} résultats trouvés")

        scored_results.sort(key=lambda x: x[0], reverse=True)
        self.results_count_label.setText(f"Найдено результатов: {len(scored_results)}")
        self.current_page = 0
        self.scored_results = scored_results
        self.show_page()

    def show_page(self):
        self.result_list.clear()
        start = self.current_page * self.results_per_page
        end = start + self.results_per_page
        page_results = self.scored_results[start:end]
        self.results = []
        for score, latin, info in page_results:
            display_name = f"{info['russian']} ({latin})"
            self.result_list.addItem(display_name)
            self.results.append((latin, info))
        self.results_count_label.setText(f"Результаты {start+1}-{min(end, len(self.scored_results))} из {len(self.scored_results)}")
        # Добавить кнопки следующей/предыдущей страницы при необходимости

    def add_to_favorites(self):
        index = self.result_list.currentRow()
        if index >= 0 and index < len(self.results):
            latin, info = self.results[index]
            if not any(fav[0] == latin for fav in self.favorites):
                self.favorites.append((latin, info))
                self.save_favorites()
                logging.info(f"Ajouté aux favoris : {latin}")
                self.add_fav_button.setText("Добавлено!")
            else:
                logging.info(f"Déjà dans les favoris : {latin}")
                self.add_fav_button.setText("Уже в избранном")
        else:
            logging.info("Aucun médicament sélectionné pour favoris")
            self.add_fav_button.setText("Выберите препарат")

    def save_favorites(self):
        # Sauvegarde les favoris dans un fichier JSON
        try:
            favs = [
                {"latin": latin, "info": info}
                for latin, info in self.favorites
            ]
            self.fav_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fav_path, "w", encoding="utf-8") as f:
                json.dump(favs, f, ensure_ascii=False, indent=2)
            logging.info("Favoris sauvegardés")
        except Exception as e:
            logging.error(f"Erreur sauvegarde favoris : {e}")

    def load_favorites(self):
        # Charge les favoris depuis le fichier JSON
        try:
            if self.fav_path.exists():
                with open(self.fav_path, "r", encoding="utf-8") as f:
                    favs = json.load(f)
                self.favorites = [(fav["latin"], fav["info"]) for fav in favs]
                logging.info(f"{len(self.favorites)} favoris chargés")
            else:
                self.favorites = []
        except Exception as e:
            logging.error(f"Erreur chargement favoris : {e}")
            self.favorites = []

    def display_details(self, item):
        index = self.result_list.row(item)
        if index < 0 or index >= len(self.results):
            logging.info("Aucun médicament sélectionné pour détails")
            self.details_area.clear()
            self.add_fav_button.setText("Добавить в избранное")
            return

        latin, info = self.results[index]
        logging.info(f"Affichage détails : {latin}")
        query = self.search_input.text().strip()
        query_words = [w.lower() for w in query.split() if w]

        title = f"{info['russian']} ({latin})"
        symptoms = info.get('symptoms', [])

        highlighted_symptoms = [self.highlight_text(symptom, query_words) for symptom in symptoms]

        html = f"<h2>{self.highlight_text(title, query_words)}</h2><ul>"
        for s in highlighted_symptoms:
            html += f"<li>{s}</li>"
        html += "</ul>"

        self.details_area.setHtml(html)
        # Met à jour le texte du bouton selon l'état
        if any(fav[0] == latin for fav in self.favorites):
            self.add_fav_button.setText("Уже в избранном")
        else:
            self.add_fav_button.setText("Добавить в избранное")

    def get_export_path(self, ext, filter_str):
        settings = QSettings("HomeopathyApp", "Export")
        last_dir = settings.value("last_export_dir", str(Path.home()))
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", last_dir + f"/export.{ext}", filter_str)
        if file_path:
            settings.setValue("last_export_dir", str(Path(file_path).parent))
        return file_path

    def export_pdf(self):
        file_path = self.get_export_path("pdf", "PDF Files (*.pdf)")
        if not file_path:
            logging.info("Export PDF annulé")
            return
        html = self.details_area.toHtml()
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        from PyQt5.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
        confirm_win = QWidget()
        confirm_win.setWindowTitle("Экспорт PDF")
        layout = QVBoxLayout()
        label = QLabel(f"PDF успешно сохранён:\n{file_path}")
        layout.addWidget(label)
        confirm_win.setLayout(layout)
        confirm_win.resize(400, 120)
        confirm_win.show()
        self.confirm_win = confirm_win
        logging.info(f"Export PDF : {file_path}")

    def export_txt(self):
        file_path = self.get_export_path("txt", "Text Files (*.txt)")
        if not file_path:
            logging.info("Export TXT annulé")
            return
        text = self.details_area.toPlainText()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        confirm_win = QWidget()
        confirm_win.setWindowTitle("Экспорт TXT")
        layout = QVBoxLayout()
        label = QLabel(f"TXT успешно сохранён:\n{file_path}")
        layout.addWidget(label)
        confirm_win.setLayout(layout)
        confirm_win.resize(400, 120)
        confirm_win.show()
        self.confirm_win = confirm_win
        logging.info(f"Export TXT : {file_path}")

    def export_html(self):
        file_path = self.get_export_path("html", "HTML Files (*.html)")
        if not file_path:
            logging.info("Export HTML annulé")
            return
        html = self.details_area.toHtml()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        confirm_win = QWidget()
        confirm_win.setWindowTitle("Экспорт HTML")
        layout = QVBoxLayout()
        label = QLabel(f"HTML успешно сохранён:\n{file_path}")
        layout.addWidget(label)
        confirm_win.setLayout(layout)
        confirm_win.resize(400, 120)
        confirm_win.show()
        self.confirm_win = confirm_win
        logging.info(f"Export HTML : {file_path}")

    def show_help(self):
        logging.info("Affichage de la fenêtre d'aide")
        help_win = QWidget()
        help_win.setWindowTitle("Справка")
        if self.icon_path.exists():
            help_win.setWindowIcon(QIcon(str(self.icon_path)))
        layout = QVBoxLayout()
        label = QLabel(
            "<b>Руководство пользователя:</b><br><br>"
            "<b>1. Поиск препарата:</b><br>"
            "- Введите название препарата или симптом в поле поиска.<br>"
            "- Используйте галочки <b>По названию</b> и <b>По симптомам</b> в меню <b>Настройки</b> для выбора области поиска.<br>"
            "- Нажмите <b>Поиск</b> или клавишу Enter.<br><br>"
            "<b>2. Просмотр результатов:</b><br>"
            "- Кликните на препарат в списке для просмотра подробной информации и симптомов.<br><br>"
            "<b>3. Избранное:</b><br>"
            "- Добавьте препарат в избранное (функция доступна при расширении).<br>"
            "- Откройте меню <b>Избранное</b> для просмотра сохранённых препаратов.<br><br>"
            "<b>4. Экспорт:</b><br>"
            "- Используйте меню <b>Экспорт</b> для сохранения информации о препарате в PDF, TXT или HTML.<br><br>"
            "<b>5. Быстрые действия:</b><br>"
            "- <b>Enter</b> — начать поиск<br>"
            "- <b>Esc</b> — очистить поиск<br><br>"
            "<b>6. Советы:</b><br>"
            "- Можно искать как по русскому, так и по латинскому названию.<br>"
            "- Для более точного поиска используйте несколько ключевых слов.<br><br>"
            "<i>Разработано RoK-studio с помощью PyQt5.<br>Все данные используются только для ознакомительных целей.</i>"
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        help_win.setLayout(layout)
        help_win.resize(600, 400)
        help_win.show()
        self.help_win = help_win  # чтобы окно не закрывалось сразу

    def show_favorites_window(self):
        logging.info("Affichage de la fenêtre favoris")
        fav_win = QWidget()
        fav_win.setWindowTitle("Избранное")
        if self.icon_path.exists():
            fav_win.setWindowIcon(QIcon(str(self.icon_path)))
        layout = QVBoxLayout()
        fav_list = QListWidget()
        fav_list.setFont(QFont("Segoe UI", 14))
        for latin, info in self.favorites:
            fav_list.addItem(f"{info['russian']} ({latin})")
        fav_list.itemClicked.connect(lambda item: self.show_fav_details(item, fav_list))
        layout.addWidget(fav_list)
        fav_win.setLayout(layout)
        fav_win.resize(400, 600)
        fav_win.show()
        self.fav_win = fav_win

    def show_fav_details(self, item, fav_list):
        index = fav_list.row(item)
        if index < 0 or index >= len(self.favorites):
            logging.info("Aucun favori sélectionné pour détails")
            return
        latin, info = self.favorites[index]
        logging.info(f"Affichage détails favori : {latin}")
        details_win = QWidget()
        details_win.setWindowTitle(f"{info['russian']} ({latin})")
        if self.icon_path.exists():
            details_win.setWindowIcon(QIcon(str(self.icon_path)))
        layout = QVBoxLayout()
        symptoms = "<br>".join(info.get('symptoms', []))
        label = QLabel(f"<b>{info['russian']} ({latin})</b><br><br>{symptoms}")
        label.setWordWrap(True)
        layout.addWidget(label)
        details_win.setLayout(layout)
        details_win.resize(500, 400)
        details_win.show()
        self.details_win = details_win

def validate_data(data):
    # Проверка структуры данных
    seen = set()
    for latin, info in data.items():
        if not isinstance(info, dict) or 'russian' not in info or 'symptoms' not in info:
            raise ValueError(f"Некорректные данные для {latin}")
        key = (info['russian'], latin)
        if key in seen:
            print(f"Обнаружен дубликат: {key}")
        seen.add(key)
    logging.info("Validation des données terminée")

def load_data():
    # Utilise le dossier courant pour le JSON
    json_path = Path(__file__).parent / "homeopathy.json"
    if not json_path.exists():
        # Lancer le parsing uniquement si le fichier n'existe pas
        parcing_path = Path(__file__).parent / "Parcing.py"
        try:
            subprocess.run([sys.executable, str(parcing_path)], check=True)
        except Exception as e:
            print("Ошибка при запуске парсера:", e)
    if not json_path.exists():
        logging.warning(f"Fichier de données absent : {json_path}")
        raise FileNotFoundError(f"Файл данных не найден: {json_path}")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    logging.info("Chargement des données")
    return data


def auto_update():
    try:
        with urllib.request.urlopen(GITHUB_VERSION_URL, timeout=5) as response:
            latest_version = response.read().decode("utf-8").strip()
        if latest_version != APP_VERSION:
            exe_path = Path(sys.argv[0])
            new_exe_path = exe_path.with_suffix(".new.exe")
            # Télécharge la nouvelle version
            with urllib.request.urlopen(GITHUB_EXE_URL) as response, open(new_exe_path, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
            # Remplace l'exécutable courant
            os.replace(new_exe_path, exe_path)
            # Redémarre l'application
            os.execv(str(exe_path), sys.argv)
    except Exception as e:
        pass  # Silencieux pour l'utilisateur

if __name__ == "__main__":
    auto_update()
    data = load_data()
    validate_data(data)
    app = QApplication(sys.argv)
    # Créer et afficher la fenêtre
    window = HomeopathyApp(data)
    window.show()

    logging.info("Application principale lancée")
    sys.exit(app.exec_())