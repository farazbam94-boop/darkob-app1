import sys
import json
import os
import webbrowser
import requests
import mimetypes
from openai import OpenAI
from woocommerce import API

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
    QHBoxLayout, QComboBox, QSpinBox, QFileDialog, QMessageBox, QGroupBox, 
    QScrollArea, QListWidget, QListWidgetItem, QAbstractItemView, QTabWidget, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QStackedWidget,
    QDialog, QFormLayout, QTextEdit
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# تنظیم پروکسی
os.environ['NO_PROXY'] = 'zibaastyle.ir,localhost,127.0.0.1'

CONFIG_FILE = "config.json"
WP_USERNAME = "hoseinbarghi1370"
WP_APP_PASSWORD = "7PKi xdEE Tq2N X3OV MnX8 o1iO"

FANTASY_STYLE = """
    QWidget {
        background-color: #F1F5F9;
        color: #0F172A;
        font-family: 'IRANSans', 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
        font-size: 16px;
    }
    QTabWidget::pane {
        border: none;
        border-radius: 16px;
        background-color: #FFFFFF;
        padding: 8px;
    }
    QTabBar::tab {
        font-size: 15px;
        font-weight: bold;
        padding: 12px 20px;
        margin-left: 6px;
        border-radius: 12px;
        color: white;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3B82F6, stop:1 #1D4ED8);
    }
    QTabBar::tab:selected {
        border: 3px solid #0F172A;
    }
    QLineEdit, QSpinBox, QComboBox, QTextEdit {
        border: 2px solid #CBD5E1;
        border-radius: 12px;
        padding: 10px;
        background-color: #FFFFFF;
        color: #0F172A;
        font-size: 16px;
        font-weight: bold;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
        border: 3px solid #4F46E5;
        background-color: #F8FAFC;
    }
    QListWidget {
        border: 2px solid #94A3B8;
        border-radius: 12px;
        background-color: #FFFFFF;
        padding: 6px;
        font-size: 15px;
    }
    QListWidget::item {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        margin: 3px;
        padding: 8px 14px;
        font-weight: bold;
        color: #334155;
    }
    QListWidget::item:selected {
        background-color: #4F46E5;
        color: #FFFFFF;
        border: 2px solid #3730A3;
    }
    QGroupBox {
        font-size: 18px;
        font-weight: bold;
        border-radius: 16px;
        margin-top: 15px;
        padding: 20px;
    }
    QGroupBox#box_info { border: 3px solid #818CF8; background-color: #EEF2FF; color: #3730A3; }
    QGroupBox#box_price { border: 3px solid #34D399; background-color: #ECFDF5; color: #065F46; }
    QGroupBox#box_cat { border: 3px solid #FBBF24; background-color: #FFFBEB; color: #92400E; }
    QGroupBox#box_attr { border: 3px solid #F472B6; background-color: #FDF2F8; color: #9D174D; }
    QGroupBox#box_ai { border: 3px solid #A78BFA; background-color: #F5F3FF; color: #5B21B6; }
    QPushButton {
        font-size: 16px;
        font-weight: bold;
        border-radius: 12px;
        padding: 10px 20px;
        border: none;
        color: white;
    }
    QTableWidget {
        background-color: #FFFFFF;
        border: 2px solid #CBD5E1;
        border-radius: 12px;
        font-size: 15px;
    }
    QHeaderView::section {
        background-color: #4338CA;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        padding: 12px;
    }
"""

class EditProductDialog(QDialog):
    def __init__(self, parent, product_info):
        super().__init__(parent)
        self.product_info = product_info
        self.parent_app = parent
        self.setWindowTitle(f"✏️ ویرایش جامع محصول: {product_info.get('name', '')}")
        self.setFixedWidth(750)
        self.setFixedHeight(850)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.main_img_path = None
        self.gallery_img_paths = []
        self.cached_ai_result = {
            "full_description": product_info.get('description', ''),
            "short_description": product_info.get('short_description', ''),
            "tags": [t.get('name') for t in product_info.get('tags', [])]
        }

        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout()

        # ----------------- بخش ۰: تولید محتوا با هوش مصنوعی -----------------
        box_ai = QGroupBox("🤖 تولید و ویرایش محتوا با هوش مصنوعی")
        box_ai.setObjectName("box_ai")
        v_ai = QVBoxLayout()
        v_ai.addWidget(QLabel("تغییرات یا پرامپت جدید برای هوش مصنوعی:"))
        self.ai_prompt_input = QTextEdit()
        self.ai_prompt_input.setFixedHeight(70)
        self.ai_prompt_input.setPlaceholderText(product_info.get('name', ''))
        v_ai.addWidget(self.ai_prompt_input)

        btn_generate_ai = QPushButton("✨ بازنویسی هوشمند عنوان، توضیحات و سئو")
        btn_generate_ai.setStyleSheet("background: #7C3AED;")
        btn_generate_ai.clicked.connect(self.trigger_ai_generation)
        v_ai.addWidget(btn_generate_ai)
        box_ai.setLayout(v_ai)
        form_layout.addWidget(box_ai)

        # ----------------- بخش ۱: اطلاعات پایه -----------------
        box_info = QGroupBox("📌 اطلاعات اصلی محصول")
        box_info.setObjectName("box_info")
        v_info = QVBoxLayout()
        v_info.addWidget(QLabel("📦 عنوان محصول:"))
        self.title_input = QLineEdit(product_info.get('name', ''))
        v_info.addWidget(self.title_input)

        v_info.addWidget(QLabel("🔢 شناسه کالا (SKU):"))
        self.sku_input = QLineEdit(product_info.get('sku', ''))
        v_info.addWidget(self.sku_input)
        box_info.setLayout(v_info)
        form_layout.addWidget(box_info)

        # ----------------- بخش ۲: قیمت و تخفیف و موجودی -----------------
        box_price = QGroupBox("💰 قیمت‌گذاری، تخفیف و موجودی")
        box_price.setObjectName("box_price")
        h_price = QHBoxLayout()
        
        v_p = QVBoxLayout()
        v_p.addWidget(QLabel("قیمت اصلی (تومان):"))
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 100000000)
        self.price_input.setSingleStep(5000)
        try:
            self.price_input.setValue(int(float(product_info.get('regular_price', 0))))
        except:
            self.price_input.setValue(0)
        v_p.addWidget(self.price_input)

        v_d = QVBoxLayout()
        v_d.addWidget(QLabel("درصد تخفیف:"))
        self.discount_input = QSpinBox()
        self.discount_input.setRange(0, 99)
        self.discount_input.setSuffix(" %")
        v_d.addWidget(self.discount_input)

        v_s = QVBoxLayout()
        v_s.addWidget(QLabel("موجودی هر تنوع:"))
        self.stock_input = QSpinBox()
        self.stock_input.setRange(1, 1000)
        self.stock_input.setValue(1)
        v_s.addWidget(self.stock_input)

        h_price.addLayout(v_p)
        h_price.addLayout(v_d)
        h_price.addLayout(v_s)
        box_price.setLayout(h_price)
        form_layout.addWidget(box_price)

        # ----------------- بخش ۳: دسته‌بندی‌ها -----------------
        box_cat = QGroupBox("📂 انتخاب دسته‌بندی‌ها (چند انتخابی)")
        box_cat.setObjectName("box_cat")
        cat_layout = QVBoxLayout()
        self.cat_list_widget = QListWidget()
        self.cat_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.cat_list_widget.setFixedHeight(110)
        
        current_cats = [cat.get('name') for cat in product_info.get('categories', [])]
        for cat_name in self.parent_app.categories.keys():
            item = QListWidgetItem(cat_name)
            self.cat_list_widget.addItem(item)
            if cat_name in current_cats:
                item.setSelected(True)
                
        cat_layout.addWidget(self.cat_list_widget)
        box_cat.setLayout(cat_layout)
        form_layout.addWidget(box_cat)

        # ----------------- بخش ۴: ویژگی‌ها (رنگ و سایز) -----------------
        box_attr = QGroupBox("🎨 ویژگی‌های محصول (رنگ و سایز)")
        box_attr.setObjectName("box_attr")
        attr_layout = QVBoxLayout()

        attr_layout.addWidget(QLabel("🎨 رنگ‌ها:"))
        self.colors_list_widget = QListWidget()
        self.colors_list_widget.setViewMode(QListWidget.IconMode)
        self.colors_list_widget.setResizeMode(QListWidget.Adjust)
        self.colors_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.colors_list_widget.setFixedHeight(90)
        
        # استخراج رنگ‌های فعلی محصول
        existing_colors = []
        for attr in product_info.get('attributes', []):
            if "color" in attr.get("slug", "").lower() or "رنگ" in attr.get("name", ""):
                existing_colors = attr.get("options", [])

        for c_name in self.parent_app.colors_dict.keys():
            item = QListWidgetItem(c_name)
            self.colors_list_widget.addItem(item)
            if c_name in existing_colors:
                item.setSelected(True)
        attr_layout.addWidget(self.colors_list_widget)

        attr_layout.addWidget(QLabel("📐 سایزها:"))
        self.sizes_list_widget = QListWidget()
        self.sizes_list_widget.setViewMode(QListWidget.IconMode)
        self.sizes_list_widget.setResizeMode(QListWidget.Adjust)
        self.sizes_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.sizes_list_widget.setFixedHeight(80)

        existing_sizes = []
        for attr in product_info.get('attributes', []):
            if "size" in attr.get("slug", "").lower() or "سایز" in attr.get("name", ""):
                existing_sizes = attr.get("options", [])

        for s_name in self.parent_app.sizes_dict.keys():
            item = QListWidgetItem(s_name)
            self.sizes_list_widget.addItem(item)
            if s_name in existing_sizes:
                item.setSelected(True)
        attr_layout.addWidget(self.sizes_list_widget)
        box_attr.setLayout(attr_layout)
        form_layout.addWidget(box_attr)

        # ----------------- بخش ۵: تصاویر -----------------
        box_img = QGroupBox("📸 مدیریت تصاویر و آلبوم گالری")
        box_img.setObjectName("box_img")
        img_layout = QVBoxLayout()
        
        h_main_img = QHBoxLayout()
        self.btn_select_img = QPushButton("🖼️ تغییر تصویر اصلی")
        self.btn_select_img.setStyleSheet("background: #0284C7;")
        self.btn_select_img.clicked.connect(self.select_main_image)
        
        self.lbl_main_img = QLabel("تصویر فعلی روی سایت برقرار است")
        self.lbl_main_img.setStyleSheet("color: #059669; font-weight: bold;")
        h_main_img.addWidget(self.btn_select_img)
        h_main_img.addWidget(self.lbl_main_img)
        img_layout.addLayout(h_main_img)

        self.btn_select_gallery = QPushButton("📚 افزودن عکس‌های جدید به گالری...")
        self.btn_select_gallery.setStyleSheet("background: #0369A1;")
        self.btn_select_gallery.clicked.connect(self.select_gallery_images)
        img_layout.addWidget(self.btn_select_gallery)

        self.gallery_list_widget = QListWidget()
        self.gallery_list_widget.setFixedHeight(90)
        img_layout.addWidget(self.gallery_list_widget)
        box_img.setLayout(img_layout)
        form_layout.addWidget(box_img)

        scroll_widget.setLayout(form_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # دکمه‌های ثبت و انصراف
        btn_box = QHBoxLayout()
        self.btn_save = QPushButton("💾 ذخیره تغییرات کلی در سایت")
        self.btn_save.setStyleSheet("background: #10B981; padding: 14px;")
        self.btn_save.clicked.connect(self.accept)

        btn_cancel = QPushButton("انصراف")
        btn_cancel.setStyleSheet("background: #64748B; padding: 14px;")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(self.btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

        self.setLayout(layout)

    def trigger_ai_generation(self):
        prompt_text = self.ai_prompt_input.toPlainText().strip()
        if not prompt_text:
            prompt_text = self.title_input.text().strip()
        
        try:
            system_prompt = "تو یک متخصص ارشد سئو و کپی‌رایتینگ پوشاک هستی. خروجی باید صرفاً یک JSON معتبر شامل کلیدهای full_description, short_description, meta_title, meta_description, tags باشد."
            res = self.parent_app.client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"اطلاعات محصول برای بازنویسی: {prompt_text}"}
                ], 
                response_format={"type": "json_object"}, 
                timeout=45
            )
            data = json.loads(res.choices[0].message.content)
            if data and "full_description" in data:
                self.cached_ai_result = data
                if data.get("meta_title"):
                    self.title_input.setText(data.get("meta_title"))
                QMessageBox.information(self, "موفق", "محتوای محصول با موفقیت توسط هوش مصنوعی بازنویسی شد!")
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در تولید محتوا توسط هوش مصنوعی: {e}")

    def select_main_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب تصویر اصلی جدید", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.main_img_path = file_path
            self.lbl_main_img.setText(os.path.basename(file_path))
            self.lbl_main_img.setStyleSheet("color: #2563EB; font-weight: bold;")

    def select_gallery_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "انتخاب عکس‌های گالری", "", "Images (*.png *.jpg *.jpeg)")
        if file_paths:
            for path in file_paths:
                if path not in self.gallery_img_paths:
                    self.gallery_img_paths.append(path)
                    self.gallery_list_widget.addItem(os.path.basename(path))

    def get_data(self):
        selected_cats = [item.text() for item in self.cat_list_widget.selectedItems()]
        selected_colors = [item.text() for item in self.colors_list_widget.selectedItems()]
        selected_sizes = [item.text() for item in self.sizes_list_widget.selectedItems()]
        
        return {
            "title": self.title_input.text().strip(),
            "sku": self.sku_input.text().strip(),
            "price": self.price_input.value(),
            "discount": self.discount_input.value(),
            "stock": self.stock_input.value(),
            "selected_cats": selected_cats,
            "selected_colors": selected_colors,
            "selected_sizes": selected_sizes,
            "main_img_path": self.main_img_path,
            "gallery_img_paths": self.gallery_img_paths,
            "ai_data": self.cached_ai_result
        }

class AIContentWorker(QThread):
    finished_signal = pyqtSignal(dict)

    def __init__(self, app_instance, raw_info):
        super().__init__()
        self.app = app_instance
        self.raw_info = raw_info

    def run(self):
        try:
            system_prompt = "تو یک متخصص ارشد سئو و کپی‌رایتینگ پوشاک هستی. خروجی باید صرفاً یک JSON معتبر شامل کلیدهای full_description, short_description, meta_title, meta_description, tags باشد."
            user_prompt = f"اطلاعات اولیه محصول برای تولید محتوا: {self.raw_info}"
            
            res = self.app.client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ], 
                response_format={"type": "json_object"}, 
                timeout=45
            )
            data = json.loads(res.choices[0].message.content)
            self.finished_signal.emit(data)
        except Exception:
            self.finished_signal.emit({})

class SubmitProductWorker(QThread):
    finished_signal = pyqtSignal(bool, str, dict)

    def __init__(self, app_instance, product_data, is_update=False, product_id=None, existing_images=None):
        super().__init__()
        self.app = app_instance
        self.data = product_data
        self.is_update = is_update
        self.product_id = product_id
        self.existing_images = existing_images or []

    def run(self):
        try:
            title = self.data['title']
            sku = self.data['sku']
            selected_cats = self.data['selected_cats']
            selected_colors = self.data['selected_colors']
            selected_sizes = self.data['selected_sizes']
            price = self.data['price']
            discount = self.data['discount']
            stock = self.data['stock']
            main_img_path = self.data['main_img_path']
            gallery_img_paths = self.data['gallery_img_paths']
            ai_data = self.data['ai_data']

            sale_price = int(price * (1 - (discount / 100))) if discount > 0 else None
            alt_text = f"خرید آنلاین {title} با کیفیت عالی - برند زیبا استایل"
            uploaded_images = list(self.existing_images)

            if main_img_path:
                m_id = self.app.upload_image(main_img_path, alt_text)
                if m_id: 
                    # اگر تصویر جدیدی به عنوان اصلی آپلود شد، قرارگیری در ابتدای لیست
                    uploaded_images.insert(0, {"id": m_id})

            for idx, g_path in enumerate(gallery_img_paths, 1):
                g_id = self.app.upload_image(g_path, f"{alt_text} - نمای شماره {idx}")
                if g_id: 
                    uploaded_images.append({"id": g_id})

            cat_payload = [{"id": int(self.app.categories[c])} for c in selected_cats if c in self.app.categories]
            woo_attributes = [
                {"id": self.app.target_attr["color"]["id"] or 0, "name": "رنگ", "slug": f"pa_{self.app.target_attr['color']['slug']}", "visible": True, "variation": True, "options": selected_colors},
                {"id": self.app.target_attr["size"]["id"] or 0, "name": "اندازه", "slug": f"pa_{self.app.target_attr['size']['slug']}", "visible": True, "variation": True, "options": selected_sizes}
            ]

            tags_data = [{"name": tag} for tag in ai_data.get("tags", [])] if isinstance(ai_data.get("tags"), list) else []

            meta_data = []
            if ai_data.get("meta_title"):
                meta_data.append({"key": "_yoast_wpseo_title", "value": ai_data.get("meta_title")})
            if ai_data.get("meta_description"):
                meta_data.append({"key": "_yoast_wpseo_metadesc", "value": ai_data.get("meta_description")})

            prod_payload = {
                "name": title,
                "type": "variable",
                "sku": sku,
                "description": ai_data.get("full_description", title),
                "short_description": ai_data.get("short_description", title),
                "categories": cat_payload,
                "tags": tags_data,
                "attributes": woo_attributes,
                "images": uploaded_images,
                "meta_data": meta_data,
                "status": "publish"
            }

            if self.is_update and self.product_id:
                prod_res = self.app.wcapi.put(f"products/{self.product_id}", prod_payload).json()
                p_id = self.product_id
                # حذف تنوع‌های قبلی برای ساخت مجدد بر اساس رنگ/سایز جدید
                try:
                    old_vars = self.app.wcapi.get(f"products/{p_id}/variations", params={"per_page": 100}).json()
                    if isinstance(old_vars, list):
                        var_ids_to_del = [{"id": v["id"]} for v in old_vars]
                        self.app.wcapi.post(f"products/{p_id}/variations/batch", {"delete": var_ids_to_del})
                except:
                    pass
            else:
                prod_res = self.app.wcapi.post("products", prod_payload).json()
                p_id = prod_res["id"]

            p_link = prod_res.get("permalink", f"{self.app.site_url}/?p={p_id}")

            variations_data = []
            for c in selected_colors:
                for s in selected_sizes:
                    var_item = {
                        "regular_price": str(price),
                        "manage_stock": True,
                        "stock_quantity": int(stock),
                        "attributes": [
                            {"id": self.app.target_attr["color"]["id"], "option": c},
                            {"id": self.app.target_attr["size"]["id"], "option": s}
                        ]
                    }
                    if sale_price and sale_price < price:
                        var_item["sale_price"] = str(sale_price)
                    variations_data.append(var_item)

            try:
                self.app.wcapi.post(f"products/{p_id}/variations/batch", {"create": variations_data})
            except Exception:
                for v in variations_data:
                    try:
                        self.app.wcapi.post(f"products/{p_id}/variations", v)
                    except Exception:
                        pass

            result_info = {
                "id": p_id, "title": title, "sku": sku, "price": price,
                "discount": discount, "sale_price": sale_price if sale_price else price, "link": p_link
            }

            action_msg = f"🎉 محصول «{title}» با موفقیت به‌روزرسانی شد!" if self.is_update else f"🎉 محصول «{title}» با موفقیت ثبت شد!"
            self.finished_signal.emit(True, action_msg, result_info)
        except Exception as e:
            self.finished_signal.emit(False, str(e), {})

class DarkoobApp(QWidget):
    def __init__(self):
        super().__init__()
        self.wcapi = None
        self.site_url = "https://zibaastyle.ir"
        self.categories = {}
        self.colors_dict = {}
        self.sizes_dict = {}
        self.target_attr = {"color": {"id": None, "slug": "color"}, "size": {"id": None, "slug": "size"}}
        self.main_img_path = None
        self.gallery_img_paths = []
        self.all_products_cache = []

        self.client = OpenAI(
            api_key="aa-LluxF9mVwfz0RYVL0WBsQZhKutJXMIZJMJokYmcweJhjp3py", 
            base_url="https://api.avalai.ir/v1" 
        )

        self.initUI()
        self.load_config()

    def initUI(self):
        self.setWindowTitle("🦅 ربات دارکوب - زیبا استایل")
        self.resize(1000, 950)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(FANTASY_STYLE)

        self.stacked_widget = QStackedWidget()

        self.page_welcome = QWidget()
        self.page_login = QWidget()
        self.page_main = QWidget()

        self.setup_welcome_page()
        self.setup_login_page()
        self.setup_main_page()

        self.stacked_widget.addWidget(self.page_welcome)
        self.stacked_widget.addWidget(self.page_login)
        self.stacked_widget.addWidget(self.page_main)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

    def setup_welcome_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        card = QFrame()
        card.setFixedWidth(650)
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 28px; border: 4px solid #4F46E5; padding: 50px;")
        card_layout = QVBoxLayout()
        card_layout.setAlignment(Qt.AlignCenter)

        lbl_logo = QLabel("🦅")
        lbl_logo.setFont(QFont("Segoe UI", 85))
        lbl_logo.setAlignment(Qt.AlignCenter)

        lbl_title = QLabel("ربات هوشمند دارکوب")
        lbl_title.setFont(QFont("IRANSans", 26, QFont.Bold))
        lbl_title.setStyleSheet("color: #3730A3; margin-top: 15px;")
        lbl_title.setAlignment(Qt.AlignCenter)

        lbl_subtitle = QLabel("مدیریت، ساخت و انتشار اتوماتیک محصولات زیبا استایل")
        lbl_subtitle.setFont(QFont("IRANSans", 16))
        lbl_subtitle.setStyleSheet("color: #475569; margin-bottom: 35px; margin-top: 10px;")
        lbl_subtitle.setAlignment(Qt.AlignCenter)

        btn_start = QPushButton("ورود به برنامه 🚀")
        btn_start.setFont(QFont("IRANSans", 18, QFont.Bold))
        btn_start.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #7C3AED); padding: 18px 60px; border-radius: 16px;")
        btn_start.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        card_layout.addWidget(lbl_logo)
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_subtitle)
        card_layout.addWidget(btn_start)
        card.setLayout(card_layout)
        layout.addWidget(card)
        self.page_welcome.setLayout(layout)

    def setup_login_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        card = QFrame()
        card.setFixedWidth(550)
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 24px; border: 2px solid #CBD5E1; padding: 40px;")
        card_layout = QVBoxLayout()

        lbl_login_title = QLabel("🔑 احراز هویت اتصال")
        lbl_login_title.setFont(QFont("IRANSans", 22, QFont.Bold))
        lbl_login_title.setStyleSheet("color: #0F172A; margin-bottom: 25px;")
        lbl_login_title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(lbl_login_title)

        card_layout.addWidget(QLabel("کلید مصرف‌کننده (Consumer Key):"))
        self.ck_input = QLineEdit()
        self.ck_input.setPlaceholderText("ck_...")
        self.ck_input.setEchoMode(QLineEdit.Password)
        card_layout.addWidget(self.ck_input)

        card_layout.addSpacing(10)
        card_layout.addWidget(QLabel("رمز مصرف‌کننده (Consumer Secret):"))
        self.cs_input = QLineEdit()
        self.cs_input.setPlaceholderText("cs_...")
        self.cs_input.setEchoMode(QLineEdit.Password)
        card_layout.addWidget(self.cs_input)

        card_layout.addSpacing(25)
        btn_connect = QPushButton("⚡ اتصال و ذخیره کلیدها")
        btn_connect.setFont(QFont("IRANSans", 16, QFont.Bold))
        btn_connect.setStyleSheet("background: #10B981; padding: 16px; border-radius: 14px;")
        btn_connect.clicked.connect(self.connect_to_wc)
        card_layout.addWidget(btn_connect)

        card.setLayout(card_layout)
        layout.addWidget(card)
        self.page_login.setLayout(layout)

    def setup_main_page(self):
        layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        lbl_connected = QLabel("🟢 متصل به zibaastyle.ir")
        lbl_connected.setStyleSheet("color: #059669; font-weight: bold; font-size: 16px;")
        
        btn_logout = QPushButton("🔓 خروج / تغییر کلیدها")
        btn_logout.setStyleSheet("background: #EF4444; font-size: 13px; padding: 8px 16px;")
        btn_logout.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        top_bar.addWidget(lbl_connected)
        top_bar.addStretch()
        top_bar.addWidget(btn_logout)
        layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        
        self.tab_new_project = QWidget()
        self.setup_new_project_tab()
        self.tabs.addTab(self.tab_new_project, "✨ ثبت محصول جدید")

        self.tab_products = QWidget()
        self.setup_products_tab()
        self.tabs.addTab(self.tab_products, "📋 محصولات سایت (مدیریت و اصلاح)")

        layout.addWidget(self.tabs)
        self.page_main.setLayout(layout)

    def setup_new_project_tab(self):
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout()

        # ----------------- بخش صفر: هوش مصنوعی -----------------
        box_ai = QGroupBox("🤖 تولید خودکار محتوا با هوش مصنوعی")
        box_ai.setObjectName("box_ai")
        v_ai = QVBoxLayout()
        v_ai.addWidget(QLabel("اطلاعات خام محصول را بنویسید (مثلاً: پیراهن مردانه لینن اسپرت رنگ آبی و سفید با دوخت عالی):"))
        self.ai_prompt_input = QTextEdit()
        self.ai_prompt_input.setFixedHeight(70)
        v_ai.addWidget(self.ai_prompt_input)

        btn_generate_ai = QPushButton("✨ تولید هوشمند عنوان، توضیحات و سئو")
        btn_generate_ai.setStyleSheet("background: #7C3AED;")
        btn_generate_ai.clicked.connect(self.trigger_ai_generation)
        v_ai.addWidget(btn_generate_ai)
        box_ai.setLayout(v_ai)
        form_layout.addWidget(box_ai)

        # ----------------- بخش ۱: اطلاعات پایه -----------------
        box_info = QGroupBox("📌 اطلاعات اصلی محصول")
        box_info.setObjectName("box_info")
        v_info = QVBoxLayout()
        v_info.addWidget(QLabel("📦 عنوان محصول:"))
        self.title_input = QLineEdit()
        v_info.addWidget(self.title_input)

        v_info.addWidget(QLabel("🔢 شناسه کالا (SKU):"))
        self.sku_input = QLineEdit()
        v_info.addWidget(self.sku_input)
        box_info.setLayout(v_info)
        form_layout.addWidget(box_info)

        # ----------------- بخش ۲: قیمت و تخفیف -----------------
        box_price = QGroupBox("💰 قیمت‌گذاری، تخفیف و موجودی")
        box_price.setObjectName("box_price")
        h_price = QHBoxLayout()
        
        v_p = QVBoxLayout()
        v_p.addWidget(QLabel("قیمت اصلی (تومان):"))
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 100000000)
        self.price_input.setSingleStep(5000)
        v_p.addWidget(self.price_input)

        v_d = QVBoxLayout()
        v_d.addWidget(QLabel("درصد تخفیف:"))
        self.discount_input = QSpinBox()
        self.discount_input.setRange(0, 99)
        self.discount_input.setSuffix(" %")
        v_d.addWidget(self.discount_input)

        v_s = QVBoxLayout()
        v_s.addWidget(QLabel("موجودی هر تنوع:"))
        self.stock_input = QSpinBox()
        self.stock_input.setRange(1, 1000)
        self.stock_input.setValue(1)
        v_s.addWidget(self.stock_input)

        h_price.addLayout(v_p)
        h_price.addLayout(v_d)
        h_price.addLayout(v_s)
        box_price.setLayout(h_price)
        form_layout.addWidget(box_price)

        # ----------------- بخش ۳: دسته‌بندی‌ها -----------------
        box_cat = QGroupBox("📂 انتخاب دسته‌بندی‌ها (چند انتخابی)")
        box_cat.setObjectName("box_cat")
        cat_layout = QVBoxLayout()
        self.cat_list_widget = QListWidget()
        self.cat_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.cat_list_widget.setFixedHeight(110)
        cat_layout.addWidget(self.cat_list_widget)

        h_cat_controls = QHBoxLayout()
        btn_open_wp_cat = QPushButton("➕ ساخت دسته در سایت")
        btn_open_wp_cat.setStyleSheet("background: #D97706;")
        btn_open_wp_cat.clicked.connect(lambda: webbrowser.open(f"{self.site_url}/wp-admin/edit-tags.php?taxonomy=product_cat&post_type=product"))
        
        btn_refresh_cat = QPushButton("🔄 به‌روزرسانی دسته‌ها")
        btn_refresh_cat.setStyleSheet("background: #F59E0B;")
        btn_refresh_cat.clicked.connect(self.fetch_categories)
        
        h_cat_controls.addWidget(btn_open_wp_cat)
        h_cat_controls.addWidget(btn_refresh_cat)
        cat_layout.addLayout(h_cat_controls)
        box_cat.setLayout(cat_layout)
        form_layout.addWidget(box_cat)

        # ----------------- بخش ۴: ویژگی‌ها -----------------
        box_attr = QGroupBox("🎨 ویژگی‌های محصول (رنگ و سایز)")
        box_attr.setObjectName("box_attr")
        attr_layout = QVBoxLayout()

        h_color_header = QHBoxLayout()
        h_color_header.addWidget(QLabel("🎨 رنگ‌ها:"))
        h_color_header.addStretch()
        btn_open_wp_color = QPushButton("➕ افزودن رنگ")
        btn_open_wp_color.setStyleSheet("background: #DB2777; font-size: 13px; padding: 6px 12px;")
        btn_open_wp_color.clicked.connect(self.open_wp_color_page)
        h_color_header.addWidget(btn_open_wp_color)
        attr_layout.addLayout(h_color_header)

        self.colors_list_widget = QListWidget()
        self.colors_list_widget.setViewMode(QListWidget.IconMode)
        self.colors_list_widget.setResizeMode(QListWidget.Adjust)
        self.colors_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.colors_list_widget.setFixedHeight(100)
        attr_layout.addWidget(self.colors_list_widget)

        h_size_header = QHBoxLayout()
        h_size_header.addWidget(QLabel("📐 سایزها:"))
        h_size_header.addStretch()
        btn_open_wp_size = QPushButton("➕ افزودن سایز")
        btn_open_wp_size.setStyleSheet("background: #BE185D; font-size: 13px; padding: 6px 12px;")
        btn_open_wp_size.clicked.connect(self.open_wp_size_page)
        h_size_header.addWidget(btn_open_wp_size)
        attr_layout.addLayout(h_size_header)

        self.sizes_list_widget = QListWidget()
        self.sizes_list_widget.setViewMode(QListWidget.IconMode)
        self.sizes_list_widget.setResizeMode(QListWidget.Adjust)
        self.sizes_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.sizes_list_widget.setFixedHeight(90)
        attr_layout.addWidget(self.sizes_list_widget)

        btn_refresh_attr = QPushButton("🔄 به‌روزرسانی رنگ‌ها و سایزها")
        btn_refresh_attr.setStyleSheet("background: #EC4899; margin-top: 5px;")
        btn_refresh_attr.clicked.connect(self.fetch_attributes)
        attr_layout.addWidget(btn_refresh_attr)
        box_attr.setLayout(attr_layout)
        form_layout.addWidget(box_attr)

        # ----------------- بخش ۵: تصاویر -----------------
        box_img = QGroupBox("📸 مدیریت تصاویر و آلبوم گالری")
        box_img.setObjectName("box_img")
        img_layout = QVBoxLayout()
        
        h_main_img = QHBoxLayout()
        self.btn_select_img = QPushButton("🖼️ انتخاب تصویر اصلی")
        self.btn_select_img.setStyleSheet("background: #0284C7;")
        self.btn_select_img.clicked.connect(self.select_main_image)
        
        self.lbl_main_img = QLabel("تصویری انتخاب نشده")
        self.lbl_main_img.setStyleSheet("color: #64748B; font-weight: bold;")
        
        self.btn_remove_main_img = QPushButton("❌")
        self.btn_remove_main_img.setFixedWidth(40)
        self.btn_remove_main_img.setStyleSheet("background: #EF4444;")
        self.btn_remove_main_img.clicked.connect(self.remove_main_image)
        self.btn_remove_main_img.hide()

        h_main_img.addWidget(self.btn_select_img)
        h_main_img.addWidget(self.lbl_main_img)
        h_main_img.addWidget(self.btn_remove_main_img)
        img_layout.addLayout(h_main_img)

        self.btn_select_gallery = QPushButton("📚 افزودن عکس‌های گالری...")
        self.btn_select_gallery.setStyleSheet("background: #0369A1;")
        self.btn_select_gallery.clicked.connect(self.select_gallery_images)
        img_layout.addWidget(self.btn_select_gallery)

        self.gallery_list_widget = QListWidget()
        self.gallery_list_widget.setFixedHeight(100)
        img_layout.addWidget(self.gallery_list_widget)
        box_img.setLayout(img_layout)
        form_layout.addWidget(box_img)

        self.btn_submit = QPushButton("🚀 ثبت و انتشار هوشمند محصول")
        self.btn_submit.setFont(QFont("IRANSans", 18, QFont.Bold))
        self.btn_submit.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669); padding: 16px; border-radius: 14px; margin-top: 10px;")
        self.btn_submit.clicked.connect(self.submit_product)
        form_layout.addWidget(self.btn_submit)

        scroll_widget.setLayout(form_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        self.tab_new_project.setLayout(layout)

    def setup_products_tab(self):
        layout = QVBoxLayout()

        search_box = QHBoxLayout()
        search_box.addWidget(QLabel("🔍 جستجوی سریع محصولات:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("عنوان یا SKU محصول...")
        self.search_input.textChanged.connect(self.filter_products_table)
        search_box.addWidget(self.search_input)

        btn_refresh_products = QPushButton("🔄 به‌روزرسانی لیست محصولات سایت")
        btn_refresh_products.setStyleSheet("background: #3B82F6;")
        btn_refresh_products.clicked.connect(self.fetch_all_products)
        search_box.addWidget(btn_refresh_products)
        layout.addLayout(search_box)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["ID", "عنوان محصول", "شناسه (SKU)", "قیمت اصلی", "لینک سایت", "عملیات اصلاح"])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.products_table)

        self.tab_products.setLayout(layout)

    def trigger_ai_generation(self):
        prompt_text = self.ai_prompt_input.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "خطا", "لطفاً ابتدا توضیحات و مشخصات اولیه محصول را در کادر بالا بنویسید.")
            return
        
        self.ai_worker = AIContentWorker(self, prompt_text)
        self.ai_worker.finished_signal.connect(self.on_ai_content_received)
        self.ai_worker.start()
        QMessageBox.information(self, "در حال پردازش", "هوش مصنوعی در حال تولید محتواست، لطفاً چند لحظه صبر کنید...")

    def on_ai_content_received(self, data):
        if data and "full_description" in data:
            self.title_input.setText(data.get("meta_title", ""))
            self.cached_ai_result = data
            QMessageBox.information(self, "موفق", "محتوای محصول با موفقیت توسط هوش مصنوعی تولید شد!")
        else:
            QMessageBox.warning(self, "خطا", "خطا در تولید محتوا توسط هوش مصنوعی.")

    def fetch_all_products(self):
        if not self.wcapi: return
        try:
            res = self.wcapi.get("products", params={"per_page": 50}).json()
            if isinstance(res, list):
                self.all_products_cache = res
                self.populate_products_table(res)
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در دریافت لیست محصولات: {e}")

    def populate_products_table(self, products):
        self.products_table.setRowCount(len(products))
        for row, prod in enumerate(products):
            p_id = str(prod.get("id", ""))
            title = prod.get("name", "")
            sku = prod.get("sku", "")
            price = str(prod.get("regular_price") or prod.get("price", ""))
            link = prod.get("permalink", "")

            self.products_table.setItem(row, 0, QTableWidgetItem(p_id))
            self.products_table.setItem(row, 1, QTableWidgetItem(title))
            self.products_table.setItem(row, 2, QTableWidgetItem(sku))
            self.products_table.setItem(row, 3, QTableWidgetItem(price))
            
            link_item = QTableWidgetItem(link)
            self.products_table.setItem(row, 4, link_item)

            btn_edit = QPushButton("✏️ ویرایش جامع همه بخش‌ها")
            btn_edit.setStyleSheet("background: #10B981; padding: 5px;")
            btn_edit.clicked.connect(lambda checked, p=prod: self.open_edit_dialog(p))
            self.products_table.setCellWidget(row, 5, btn_edit)

    def filter_products_table(self, text):
        filtered = [
            p for p in self.all_products_cache 
            if text.lower() in p.get("name", "").lower() or text.lower() in p.get("sku", "").lower()
        ]
        self.populate_products_table(filtered)

    def open_edit_dialog(self, product):
        dialog = EditProductDialog(self, product)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            if not new_data['title'] or not new_data['sku']:
                QMessageBox.warning(self, "خطا", "عنوان و شناسه کالا (SKU) الزامی هستند.")
                return
            if not new_data['selected_cats']:
                QMessageBox.warning(self, "خطا", "انتخاب حداقل یک دسته‌بندی الزامی است.")
                return
            if not new_data['selected_colors'] or not new_data['selected_sizes']:
                QMessageBox.warning(self, "خطا", "انتخاب حداقل یک رنگ و یک سایز الزامی است.")
                return

            existing_images = product.get("images", [])
            self.worker = SubmitProductWorker(self, new_data, is_update=True, product_id=product.get("id"), existing_images=existing_images)
            self.worker.finished_signal.connect(self.on_submit_finished)
            self.worker.start()
            QMessageBox.information(self, "در حال به‌روزرسانی", "تغییرات در حال ارسال به سایت است، لطفاً چند لحظه صبر کنید...")

    def select_main_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب تصویر اصلی", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.main_img_path = file_path
            self.lbl_main_img.setText(os.path.basename(file_path))
            self.lbl_main_img.setStyleSheet("color: #059669; font-weight: bold;")
            self.btn_remove_main_img.show()

    def remove_main_image(self):
        self.main_img_path = None
        self.lbl_main_img.setText("تصویری انتخاب نشده")
        self.lbl_main_img.setStyleSheet("color: #64748B;")
        self.btn_remove_main_img.hide()

    def select_gallery_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "انتخاب عکس‌های گالری", "", "Images (*.png *.jpg *.jpeg)")
        if file_paths:
            for path in file_paths:
                if path not in self.gallery_img_paths:
                    self.gallery_img_paths.append(path)
                    self.add_gallery_item_widget(path)

    def add_gallery_item_widget(self, file_path):
        item = QListWidgetItem(self.gallery_list_widget)
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        lbl_name = QLabel(os.path.basename(file_path))
        btn_del = QPushButton("❌")
        btn_del.setFixedWidth(35)
        btn_del.setStyleSheet("background: #EF4444; padding: 4px;")
        btn_del.clicked.connect(lambda: self.remove_gallery_image(file_path, item))
        layout.addWidget(lbl_name)
        layout.addStretch()
        layout.addWidget(btn_del)
        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())
        self.gallery_list_widget.setItemWidget(item, widget)

    def remove_gallery_image(self, file_path, item):
        if file_path in self.gallery_img_paths:
            self.gallery_img_paths.remove(file_path)
        row = self.gallery_list_widget.row(item)
        self.gallery_list_widget.takeItem(row)

    def save_config(self, ck, cs):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"ck": ck, "cs": cs}, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.ck_input.setText(data.get("ck", ""))
                    self.cs_input.setText(data.get("cs", ""))
            except Exception:
                pass

    def connect_to_wc(self):
        ck = self.ck_input.text().strip()
        cs = self.cs_input.text().strip()
        if not ck or not cs:
            QMessageBox.warning(self, "خطا", "لطفاً کلیدهای CK و CS را وارد کنید.")
            return

        try:
            self.wcapi = API(url=self.site_url, consumer_key=ck, consumer_secret=cs, version="wc/v3", timeout=60)
            self.fetch_categories()
            self.fetch_attributes()
            self.fetch_all_products()
            self.save_config(ck, cs)
            self.stacked_widget.setCurrentIndex(2)
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در اتصال: {e}")

    def fetch_categories(self):
        if not self.wcapi: return
        try:
            cat_res = self.wcapi.get("products/categories", params={"per_page": 100}).json()
            self.categories = {cat["name"]: cat["id"] for cat in cat_res if isinstance(cat, dict) and "name" in cat}
            self.cat_list_widget.clear()
            self.cat_list_widget.addItems(list(self.categories.keys()))
        except Exception as e:
            pass

    def fetch_attributes(self):
        if not self.wcapi: return
        try:
            attr_res = self.wcapi.get("products/attributes").json()
            if isinstance(attr_res, list):
                for attr in attr_res:
                    if "color" in attr.get("slug", "").lower() or "رنگ" in attr.get("name", ""):
                        self.target_attr["color"]["id"] = attr["id"]
                        self.target_attr["color"]["slug"] = attr["slug"].replace("pa_", "")
                        c_res = self.wcapi.get(f"products/attributes/{attr['id']}/terms", params={"per_page": 100}).json()
                        if isinstance(c_res, list):
                            self.colors_dict = {c["name"]: c["id"] for c in c_res if "name" in c}
                            self.colors_list_widget.clear()
                            self.colors_list_widget.addItems(list(self.colors_dict.keys()))
                    elif "size" in attr.get("slug", "").lower() or "سایز" in attr.get("name", ""):
                        self.target_attr["size"]["id"] = attr["id"]
                        self.target_attr["size"]["slug"] = attr["slug"].replace("pa_", "")
                        s_res = self.wcapi.get(f"products/attributes/{attr['id']}/terms", params={"per_page": 100}).json()
                        if isinstance(s_res, list):
                            self.sizes_dict = {s["name"]: s["id"] for s in s_res if "name" in s}
                            self.sizes_list_widget.clear()
                            self.sizes_list_widget.addItems(list(self.sizes_dict.keys()))
        except Exception as e:
            pass

    def open_wp_color_page(self):
        if self.target_attr["color"]["slug"]:
            webbrowser.open(f"{self.site_url}/wp-admin/edit-tags.php?taxonomy=pa_{self.target_attr['color']['slug']}&post_type=product")
        else:
            webbrowser.open(f"{self.site_url}/wp-admin/edit.php?post_type=product")

    def open_wp_size_page(self):
        if self.target_attr["size"]["slug"]:
            webbrowser.open(f"{self.site_url}/wp-admin/edit-tags.php?taxonomy=pa_{self.target_attr['size']['slug']}&post_type=product")
        else:
            webbrowser.open(f"{self.site_url}/wp-admin/edit.php?post_type=product")

    def upload_image(self, file_path, alt_text):
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type: mime_type = "image/jpeg"
            file_name = os.path.basename(file_path)
            
            with open(file_path, "rb") as f:
                img_bytes = f.read()

            headers = {
                "Content-Disposition": f"attachment; filename={file_name}",
                "Content-Type": mime_type
            }

            response = requests.post(
                f"{self.site_url}/wp-json/wp/v2/media",
                headers=headers,
                data=img_bytes,
                auth=(WP_USERNAME, WP_APP_PASSWORD),
                timeout=45
            )
            
            if response.status_code in [200, 201]:
                return response.json().get("id")
        except Exception:
            pass
        return None

    def submit_product(self):
        title = self.title_input.text().strip()
        sku = self.sku_input.text().strip()
        price = self.price_input.value()
        discount = self.discount_input.value()
        stock = self.stock_input.value()

        selected_cats = [item.text() for item in self.cat_list_widget.selectedItems()]
        selected_colors = [item.text() for item in self.colors_list_widget.selectedItems()]
        selected_sizes = [item.text() for item in self.sizes_list_widget.selectedItems()]

        if not title or not sku:
            QMessageBox.warning(self, "خطا", "عنوان و شناسه کالا (SKU) الزامی هستند.")
            return
        if price <= 0:
            QMessageBox.warning(self, "خطا", "لطفاً قیمت معتبری برای محصول وارد کنید.")
            return
        if not selected_cats:
            QMessageBox.warning(self, "خطا", "لطفاً حداقل یک دسته‌بندی انتخاب کنید.")
            return
        if not selected_colors or not selected_sizes:
            QMessageBox.warning(self, "خطا", "انتخاب حداقل یک رنگ و یک سایز الزامی است.")
            return

        ai_data = getattr(self, "cached_ai_result", {
            "full_description": title,
            "short_description": title,
            "tags": []
        })

        product_data = {
            "title": title, "sku": sku, "price": price, "discount": discount,
            "stock": stock, "selected_cats": selected_cats, "selected_colors": selected_colors,
            "selected_sizes": selected_sizes, "main_img_path": self.main_img_path,
            "gallery_img_paths": self.gallery_img_paths, "ai_data": ai_data
        }

        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("⏳ در حال ارسال اطلاعات به ووکامرس...")

        self.worker = SubmitProductWorker(self, product_data, is_update=False)
        self.worker.finished_signal.connect(self.on_submit_finished)
        self.worker.start()

    def on_submit_finished(self, success, message, info):
        self.btn_submit.setEnabled(True)
        self.btn_submit.setText("🚀 ثبت و انتشار هوشمند محصول")
        if success:
            QMessageBox.information(self, "موفقیت", message)
            self.fetch_all_products()
        else:
            QMessageBox.critical(self, "خطا", f"خطا در ثبت یا به‌روزرسانی محصول: {message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DarkoobApp()
    window.show()
    sys.exit(app.exec_())
