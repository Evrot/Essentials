from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
import sqlite3
from hashlib import sha256
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.config import Config
from datetime import datetime
from zoneinfo import ZoneInfo
from kivymd.uix.card import MDCard
from kivymd.uix.swiper import MDSwiper, MDSwiperItem
from kivymd.uix.label import MDLabel
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.core.window import Window






Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


class Essentials(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user_id = None
        self.greeting_name = ""

    def build(self):        
        self.create_user_table()

        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(SignupScreen(name="signup"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(HobbyScreen(name="hobby"))
        sm.add_widget(DeleteHobbyScreen(name="delete_hobby"))
        sm.add_widget(HobbiesListScreen(name="hobbies_list"))
        return sm
    
    def create_user_table(self):
        conn = sqlite3.connect("data/essentials_db.db")
        cursor = conn.cursor()
        cursor.execute("""
                    CREATE TABLE if not exists users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fullname TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    birthday DATE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME)
                       """)
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hobbies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    hobby_name TEXT NOT NULL,
                    unit_measure TEXT,                    
                    measure REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, hobby_name)
                            )
                        """)
        conn.commit()
        conn.close()
        return self.root    

    def show_popup(self, message, title="Hey!"):        
        popup = Popup(
            title=title,
            title_font = "fonts/pixelify_bold.ttf",
            title_size = "20sp",
            title_color = (0.5, 0.8, 0.5, 1),
            title_align = "center",
            separator_color = (0, 0, 0, 0),
            content=Label(
                text=message,
                font_name="fonts/pixelify_bold.ttf",
                font_size="16sp",  
                halign="center", valign="middle"
            ),
            size_hint=(None, None),
            size=(665, 150),
            auto_dismiss=True
        )
        popup.open()
           
        
    def create_account(self):
        signup_screen = self.root.get_screen("signup")
        fullname = signup_screen.ids.user_fullname.text.strip()
        email = signup_screen.ids.user_email.text.strip().lower()
        password = signup_screen.ids.user_password.text.strip()
        confirm_password = signup_screen.ids.user_password_confirm.text.strip()
        birthday = signup_screen.ids.user_birthday.text.strip()

        if not fullname or not email or not password or not confirm_password or not birthday:
            self.show_popup("All fields are required!", title = "Wow!")
            return

        if password != confirm_password:
            self.show_popup("Passwords do not match!", title = "Wow!")
            return

        password_hash = sha256(password.encode()).hexdigest() 

        try:
            conn = sqlite3.connect("data/essentials_db.db", timeout = 5)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (fullname, email, birthday, password_hash)
                VALUES (?, ?, ?, ?)
            """, (fullname, email, birthday, password_hash))
            conn.commit()
            self.show_popup("Account created successfully!", title="Heck yes!")
            self.root.current = "login"
            signup_screen.clear_fields_signup()   
            

        except sqlite3.IntegrityError as e:
            self.show_popup("This email already exists!", title="Oops!")

        except sqlite3.OperationalError as e:
            self.show_popup("Database is busy, please try again.", title = "STAY HARD!")
            
            

        finally:
            cursor.close()
            conn.close()
    
    def login_authentification(self):
        login_screen = self.root.get_screen("login")
        login = login_screen.ids.username_field.text.strip()
        password = login_screen.ids.password_field.text.strip()
        hashed_pw = sha256(password.encode()).hexdigest()
        conn = sqlite3.connect("data/essentials_db.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, fullname, email, password_hash FROM users WHERE email = ? AND  password_hash = ?", (login, hashed_pw))
        user = cursor.fetchone()
        
        if user:            
            self.current_user_id = user[0]
            self.greeting_name = user[1]
            self.root.current = "home"
            home_screnn = self.root.get_screen("home")
            hobby_screen = self.root.get_screen("hobby")
            hobbies_list_screen = self.root.get_screen("hobbies_list")
            hobbies_list_screen.ids.greetings.text = f"{self.current_day()}"          
            hobby_screen.ids.greetings.text = f"Have fun, make mistakes, and keep going. \nThat’s how you grow {self.greeting_name}!"
            home_screnn.ids.greetings.text = f"Welcome back, {self.greeting_name}!"
            login_screen.clear_fields_login()
        else:
            if not login or not password:
                self.show_popup("Hey don’t forget to enter your email and password.", title = "Wow!")

            else:
                self.show_popup("Sorry, password or e-mail invalid.", title = "Try again!")

    def limit_field_length(self, instance, value, max_lenth = 10):
        if len(value) > max_lenth:
            instance.text = value[:max_lenth]

    def current_day(self):
        today = datetime.now(ZoneInfo("America/Chicago"))
        today_day = today.day
        today_month = today.strftime("%B")
        today_year = today.year
        return (f"{today_month} {today_day}, {today_year}")
    
    def create_hobby(self):
        hobby_screen = self.root.get_screen("hobby")     
        hobby = hobby_screen.ids.user_hobby.text.strip().title()
        unit_measure = hobby_screen.ids.user_measure_hobby.text.strip().title()
        user_id = self.current_user_id

        if not hobby or not unit_measure:
            self.show_popup("Please enter a hobby name or its unit measures.", title="Oops!")
            return
        
                
        try:
            conn = sqlite3.connect("data/essentials_db.db", timeout = 5)
            cursor = conn.cursor()
            cursor.execute("""SELECT unit_measure, hobby_name FROM hobbies WHERE user_id = ? AND hobby_name = ? """, (user_id, hobby))
            existing = cursor.fetchone()

            if existing:
                if existing[0] != unit_measure or existing[1] == hobby:
                    self.show_popup("This hobby already exists!", title="Oops!")
                    hobby_screen.clear_fields_hobby()
                
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO hobbies (user_id, hobby_name, unit_measure)
                    VALUES (?, ?, ?)
                """, (user_id, hobby, unit_measure))

                conn.commit()
                conn.close()

                self.show_popup(f"{hobby} added successfully!", title="Nice!")
                hobby_screen.ids.user_hobby.text = ""
                hobby_screen.ids.user_measure_hobby.text = ""
                self.root.current = "home"

        except sqlite3.IntegrityError:
            self.show_popup("This hobby already exists!", title="Oops!")

    def delete_hobby(self):
        delete_screen = self.root.get_screen("delete_hobby")
        hobby_to_delete = delete_screen.ids.hobby_to_delete.text.strip().title()
        user_id = self.current_user_id
        conn = sqlite3.connect("data/essentials_db.db", timeout= 5)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, hobby_name FROM hobbies WHERE user_id = ? and hobby_name = ?", (user_id, hobby_to_delete))
        hobby_check = cursor.fetchone()
        

        if hobby_check:
            try:   
                cursor.execute("DELETE FROM hobbies WHERE user_id = ? and hobby_name = ?", (user_id, hobby_to_delete))
                conn.commit()
                acess_hobby_screen = self.root.get_screen("hobbies_list")                
                self.show_popup(f"{hobby_to_delete} was successfully deleted!")                
                delete_screen.clear_fields_delete()
                self.root.current = "home"

            except sqlite3.IntegrityError:
                self.show_popup("Please enter the hobby you would like to delete appropriately.", title = "Oops!")
            
            finally:
                conn.close()

        else:
            if not hobby_to_delete:
                self.show_popup("Please enter the hobby you would like to delete", title = "Oops!")
            else:
                self.show_popup(f"{hobby_to_delete} is not in the hobbies list.")
                delete_screen.clear_fields_delete()
            


        
    
class LoginScreen(Screen):
    def clear_fields_login(self):
        self.ids.username_field.text = ""
        self.ids.password_field.text = ""

class SignupScreen(Screen):
    def clear_fields_signup(self):
        self.ids.user_fullname.text = ""
        self.ids.user_email.text = ""
        self.ids.user_password.text = ""
        self.ids.user_password_confirm.text = ""
        self.ids.user_birthday.text = ""

class HomeScreen(Screen):
    pass

class HobbyScreen(Screen):
    def clear_fields_hobby(self):
        self.ids.user_hobby.text = ""
        self.ids.user_measure_hobby.text = ""

class DeleteHobbyScreen(Screen):
    def clear_fields_delete(self):
        self.ids.hobby_to_delete.text = ""

class HobbiesListScreen(Screen):
    def on_enter(self):
        self.showing_list()

    def showing_list(self):
        acess = MDApp.get_running_app()
        hobbies_list_screen = acess.root.get_screen("hobbies_list")
        base_layout = hobbies_list_screen.ids.base  
        user_id = acess.current_user_id        

        with sqlite3.connect("data/essentials_db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hobby_name FROM hobbies WHERE user_id = ?", (user_id,))
            hobbies_list = cursor.fetchall()
       
        widgets_to_remove = []
        for child in base_layout.children:           
            if isinstance(child, MDSwiper):
                widgets_to_remove.append(child)                

        for widget in widgets_to_remove:
            try:
                base_layout.remove_widget(widget)                
            except Exception as e:
                print(f"Error to remove the swiper")        

        if not hobbies_list:
            label = Label(
                text="Sorry, you haven't added any hobbies yet.",
                halign="center",
                valign="top",
                size_hint=(.8, None),
                pos_hint={"top": 0.6, "center_x": 0.5},            
                font_name="fonts/pixelify_bold.ttf",            
                color=(0, 0, 0, 1),
                font_size=20,            
            )
            base_layout.add_widget(label)
            return

        
        swiper = MDSwiper(
            size_hint=(0.9, 0.6),
            pos_hint={"center_x": 0.5, "center_y": 0.40})        

        
        for i in hobbies_list:
            hobby = i[0]            
            
            swiper_item = MDSwiperItem()
            float_layout = MDFloatLayout()

            card = MDCard(
                size_hint=(None, None),
                size=(Window.width * 0.4, Window.height * 0.5),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                md_bg_color="black",
                radius=[30],
                elevation=2,
                shadow_color=(0.5, 0.8, 0.5, 1)
            )
            
            label = Label(
                text=hobby,
                halign="center",
                valign="top",
                size_hint=(.8, None),
                pos_hint={"top": 1, "center_x": 0.5},            
                font_name="fonts/pixelify_bold.ttf",            
                color=(1, 1, 1, 1),
                font_size=25,            
            )

            card.add_widget(label)
            float_layout.add_widget(card)            
            swiper_item.add_widget(float_layout)            
            swiper.add_widget(swiper_item)        
        
        try:
            base_layout.add_widget(swiper)
            
        except Exception as e:
            print(f"Error!")       
        
        

Essentials().run()  