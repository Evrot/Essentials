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
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.core.window import Window
from kivymd.uix.button import MDFlatButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.fitimage import FitImage
import pytz

from kivy.animation import Animation
from random import randint



Window.set_icon("images/icon_window.png")
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
                    goal REAL,                    
                    progress REAL,
                    updated_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, hobby_name)
                            )
                        """)
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS statistic (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    hobby_name TEXT NOT NULL,
                    unit_measure TEXT,
                    goal REAL,
                    progress REAL,
                    updated_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,                    
                    created_date TEXT GENERATED ALWAYS AS (date(created_at)) VIRTUAL,
                    UNIQUE(user_id, hobby_name, created_date)
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
        fullname = signup_screen.ids.user_fullname.text.strip().title()
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
        goal = hobby_screen.ids.user_hobby_goal.text.strip()
        user_id = self.current_user_id

        if not hobby or not unit_measure or not goal:
            self.show_popup("Please, fill in all the fields.", title="Oops!")
            return
        
                
        try:
            conn = sqlite3.connect("data/essentials_db.db", timeout = 5)
            cursor = conn.cursor()
            cursor.execute("""SELECT unit_measure, hobby_name, goal FROM hobbies WHERE user_id = ? AND hobby_name = ?  """, (user_id, hobby))
            existing = cursor.fetchone()

            if existing:
                if existing[0] != unit_measure or existing[1] == hobby:
                    self.show_popup("This hobby already exists!", title="Oops!")
                    hobby_screen.clear_fields_hobby()
                
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO hobbies (user_id, hobby_name, unit_measure, goal)
                    VALUES (?, ?, ?, ?)
                """, (user_id, hobby, unit_measure, goal))

                conn.commit()
                conn.close()

                self.show_popup(f"{hobby} added successfully!", title="Nice!")
                hobby_screen.ids.user_hobby.text = ""
                hobby_screen.ids.user_measure_hobby.text = ""
                hobby_screen.ids.user_hobby_goal.text = ""
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
    def on_enter(self):
        acess = MDApp.get_running_app()
        storage_updating = acess.root.get_screen("hobbies_list")     
        storage_updating.storage_hobby() 
        

class HobbyScreen(Screen):
    def clear_fields_hobby(self):
        self.ids.user_hobby.text = ""
        self.ids.user_measure_hobby.text = ""
        self.ids.user_hobby_goal.text = ""

class DeleteHobbyScreen(Screen):
    def clear_fields_delete(self):
        self.ids.hobby_to_delete.text = ""

class HobbiesListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)        
        self.no_hobbies_label = None
        self.progress_capture = None
        self.progress = 0

    def progress_updating(self, hobby_name, progress_capture, label_1, progress_bar, goal, unit_measure, percentage):
        acess = MDApp.get_running_app()        
        user_id = acess.current_user_id
        text = progress_capture.text.strip()
        time_now = datetime.now(ZoneInfo("America/Chicago")).date()
        if text == "":
            return acess.show_popup("Don't forget to type in your progress first!", title="It's all good!") 
        
        try:
            with sqlite3.connect("data/essentials_db.db") as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT progress
                    FROM hobbies
                    WHERE user_id = ? AND hobby_name = ?
                """, (user_id, hobby_name))
                result = cursor.fetchone()                    
                hobby_progress = result[0]

            if hobby_progress:
                hobby_progress += float(text)
                self.progress = hobby_progress                    
            else:
                self.progress = float(text)  
           
                
        except ValueError:                
            print("ERROR! Wrong value.")
            return
                    
        
        try:
            with sqlite3.connect("data/essentials_db.db") as conn:
                cursor = conn.cursor()                   
                cursor.execute("""
                    UPDATE hobbies
                    SET progress = ?, updated_at = ?
                    WHERE user_id = ? AND hobby_name = ?
                """, (self.progress, time_now, user_id, hobby_name))
                conn.commit()
        except Exception as e:
            print("ERROR! Wrong value.", e)
            return

        
        label_1.text = f"{self.progress:.2f}/{goal} {unit_measure}"
        percentage.text = f"{(100*self.progress)/goal:.2f}%"
        progress_bar.value = min((self.progress / goal) * 100, 100)

        
        progress_capture.text = ""

        if self.progress >= goal:
            self.show_star_celebration()

        


    def showing_list(self):
        acess = MDApp.get_running_app()              
        hobbies_list_screen = acess.root.get_screen("hobbies_list")       
        base_layout = hobbies_list_screen.ids.base  
        user_id = acess.current_user_id
        
               

        with sqlite3.connect("data/essentials_db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hobby_name, unit_measure, goal, progress FROM hobbies WHERE user_id = ?", (user_id,))
            hobbies_list = cursor.fetchall()
       
        widgets_to_remove = []
        for child in base_layout.children:           
            if isinstance(child, MDSwiper):
                widgets_to_remove.append(child)                

        for son in base_layout.children:
            if son == self.no_hobbies_label and hobbies_list:
                widgets_to_remove.append(son)
                

        for widget in widgets_to_remove:
            try:
                base_layout.remove_widget(widget)                
            except Exception as e:
                print(f"Error to remove the swiper")        

        if not hobbies_list:
            self.no_hobbies_label = Label(                
                text="Sorry, you haven't added any hobbies yet.",
                halign="center",
                valign="top",
                size_hint=(.8, None),
                pos_hint={"top": 0.6, "center_x": 0.5},            
                font_name="fonts/pixelify_bold.ttf",            
                color=(0, 0, 0, 1),
                font_size=25,            
            )
            base_layout.add_widget(self.no_hobbies_label)
            return

        
        swiper = MDSwiper(
            size_hint=(0.9, 0.6),
            pos_hint={"center_x": 0.5, "center_y": 0.40})        

        
        for i in hobbies_list:
            hobby = i[0]
            unit_measure = i[1]
            goal = i[2]
            progress = i[3]
            if progress == None:
                progress = 0
                      
            
            swiper_item = MDSwiperItem()
            float_layout = MDFloatLayout()
            card_layout = MDFloatLayout()

            card = MDCard(
                size_hint=(None, None),
                size=(Window.width * 0.4, Window.height * 0.55),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                md_bg_color=(0.902, 0.941, 0.941, 1),
                radius=[30],
                elevation=2,
                shadow_color=(0.5, 0.8, 0.5, 1)
            )
            
            label = Label(
                text=hobby,
                halign="center",                
                size_hint=(.8, None),
                pos_hint={"center_y": 0.6, "center_x": 0.5},            
                font_name="fonts/pixelify_bold.ttf",            
                color=(0, 0, 0, 1),
                font_size=30,           
            )            
            
            percentage_field = Label(
                text= f"{(100*progress)/goal:.2f}%",
                size_hint = (0.1, None),
                pos_hint={"center_y": 0.5, "center_x": 0.9},
                color = (0, 0, 0, 1),
                font_size = 23,
                font_name="fonts/pixelify_bold.ttf"
            )

            label_1 = Label(
                text = f"{progress}/{goal} {unit_measure}",                
                halign="center",               
                size_hint=(0.8, None),
                pos_hint={"center_y": 0.4, "center_x": 0.5},            
                font_name="fonts/pixelify_bold.ttf",            
                color=(0, 0, 0, 1),
                font_size=25           
            )

            progress_bar = MDProgressBar(                
                size_hint = (0.6, None),
                pos_hint = {"center_x": 0.5, "center_y": 0.5},                
                max = 100,
                height = 20,
                radius = [10],
                color = (0.5, 0.8, 0.5, 1),
                value = min((progress / goal) * 100, 100)                
            )
           

            progress_capture = MDTextField(                
                size_hint = (None, None),
                input_filter = "float",
                size = (115, 50),
                pos_hint = {"center_y": 0.25, "center_x": 0.5},
                font_size = 22,                                               
                font_name="fonts/pixelify_bold.ttf",
                theme_text_color= "Custom",
                line_color_focus= (0.5, 0.8, 0.5, 1),
                line_color_normal= (0.5, 0.8, 0.5, 1),
                cursor_color= (0.5, 0.8, 0.5, 1),
                text_color_focus= (0, 0, 0, 1),                                             
            )
            progress_capture.bind(text=lambda instance, value: acess.limit_field_length(instance, value, 7))
            
            bg_image = FitImage(
                source="images/essentials_logo_3.png",
                size_hint=(None, None),
                size=(200, 200),
                pos_hint={"center_x": 0.5, "center_y": 0.85},
                radius=[40],  
            )
            

            submit_progress = MDFlatButton(
                text = "Add your progress!",               
                size_hint = (0.4, None),
                font_name="fonts/pixelify_bold.ttf",               
                pos_hint= {"center_x": 0.5, "center_y": 0.10},
                md_bg_color= (0.5, 0.8, 0.5, 1),
                theme_text_color= "Custom",
                text_color= (1, 1, 1, 1),
                on_press=lambda instance, h=hobby, pc=progress_capture, l=label_1, pb=progress_bar, g=goal, u=unit_measure, p=percentage_field: 
            self.progress_updating(h, pc, l, pb, g, u, p),                
            )
            
            card_layout.add_widget(bg_image)
            card_layout.add_widget(submit_progress)
            card_layout.add_widget(progress_capture)
            card_layout.add_widget(percentage_field)                     
            card_layout.add_widget(progress_bar)
            card_layout.add_widget(label_1)            
            card_layout.add_widget(label)
            card.add_widget(card_layout)                                   
            float_layout.add_widget(card)            
            swiper_item.add_widget(float_layout)            
            swiper.add_widget(swiper_item)        
        
        try:
            base_layout.add_widget(swiper)
            
        except Exception as e:
            print("Error!")

    def storage_hobby(self):                
        acess = MDApp.get_running_app()
        user_id = acess.current_user_id        
        time_now = datetime.now(ZoneInfo("America/Chicago")).date()
        reset_progress = 0


        with sqlite3.connect("data/essentials_db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT updated_at, hobby_name FROM hobbies WHERE user_id =?""", (user_id,))
            hobby_storage = cursor.fetchall()

            try:
                for updated_at, hobby_name in hobby_storage:
                    conversion_datetime = datetime.strptime(updated_at,"%Y-%m-%d").date()
                    
                            
                    if conversion_datetime != time_now:                    
                            cursor.execute("""INSERT OR IGNORE INTO statistic (user_id, hobby_name, unit_measure, goal, progress, updated_at, created_at)
                                        SELECT user_id, hobby_name, unit_measure, goal, progress, updated_at, created_at FROM hobbies
                                        WHERE user_id = ? AND updated_at = ?
                                        """, (user_id, updated_at)
                                        )
                            cursor.execute("""
                                UPDATE hobbies
                                SET progress = ?
                                WHERE user_id = ? AND hobby_name = ?
                            """, (reset_progress, user_id, hobby_name))
                conn.commit()
            except Exception as e:
                print("That's fine!")
        

Essentials().run()  