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
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp, sp
from kivy.uix.scrollview import ScrollView
from collections import defaultdict
import random
import string
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from kivy.clock import Clock
import icon_matcher
from threading import Thread
from contextlib import closing





Window.minimum_width, Window.minimum_height = (800, 600)
Window.maximum_width, Window.maximum_height = (800, 600)


Config.set('input', 'mouse', 'mouse,multitouch_on_demand') 

# MDApp
class Essentials(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user_id = None # ID that will be used to link the user's information on every screen.
        self.greeting_name = "" # Variable used to generate personalized names based on the user's ID and name.
    
    
    # Creating the database and adding each screen to the ScreenManager.
    def build(self):        
        self.create_db() 

        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(LoadingScreen(name="loading_screen"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(SignupScreen(name="signup"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(HobbyScreen(name="hobby"))
        sm.add_widget(DeleteHobbyScreen(name="delete_hobby"))
        sm.add_widget(HobbiesListScreen(name="hobbies_list"))
        sm.add_widget(StatsScreen(name="stats_screen"))
        sm.add_widget(ForgotPasswordScreen(name="forgot_pass_screen"))
        sm.add_widget(CodeScreen(name="code_screen"))
        sm.add_widget(ChangingPassScreen(name="changing_password"))
        return sm
    
    # Method responsible for creating the database.
    def create_db(self):
        with sqlite3.connect("data/essentials_db.db") as conn:
            with closing(conn.cursor()) as cursor:        
                cursor.execute("""
                            CREATE TABLE if not exists users(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            fullname TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            birthday DATE NOT NULL,
                            password_hash TEXT NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME,
                            recovery_code TEXT)
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
                return self.root    
    
    # Methods responsible for creating and displaying all pop-ups used on screens.
    def show_popup(self, message, title="Hey!"):        
        popup = Popup(
            title=title,
            title_font = "fonts/jersey_25.ttf",
            title_size = "20sp",
            title_color = (0.5, 0.8, 0.5, 1),
            title_align = "center",
            separator_color = (0, 0, 0, 0),
            content=Label(
                text=message,
                font_name="fonts/jersey_25.ttf",
                font_size="16sp",  
                halign="center", valign="middle"
            ),
            size_hint=(None, None),
            size=(665, 150),
            auto_dismiss=True
        )
        popup.open()    

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
        progress = 0.0
        updated_at = datetime.now(ZoneInfo("America/Chicago")).date()
        user_id = self.current_user_id

        if not hobby or not unit_measure or not goal:
            self.show_popup("Please, fill in all the fields.", title="Oops!")
            return
        
                
        try:
            conn = sqlite3.connect("data/essentials_db.db")
            cursor = conn.cursor()
            cursor.execute("""SELECT unit_measure, hobby_name, goal FROM hobbies WHERE user_id = ? AND hobby_name = ?  """, (user_id, hobby))
            existing = cursor.fetchone()

            if existing:
                if existing[0] != unit_measure or existing[1] == hobby:
                    self.show_popup("This hobby already exists!", title="Oops!")
                    hobby_screen.clear_fields_hobby()
                
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO hobbies (user_id, hobby_name, unit_measure, goal, progress, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, hobby, unit_measure, goal, progress, updated_at))
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
                cursor.execute("DELETE FROM statistic WHERE user_id = ? AND hobby_name = ?", (user_id, hobby_to_delete))
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
            

class LoadingScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_model_in_background(), 0.01)

        Clock.schedule_once(lambda dt: self.on_model_loaded(), 5)

        
    def on_model_loaded(self):
        MDApp.get_running_app().root.current = "login"

    def load_model_in_background(self):
        def _load():
            try:
                icon_matcher.load_model()
            except Exception as e:
                print("Model loading failed:", e)
                    

        Thread(target=_load).start()

        
        
    
class LoginScreen(Screen):
    # Method responsible for clearing all input fields on the LoginScreen.
    def clear_fields_login(self):
        self.ids.username_field.text = ""
        self.ids.password_field.text = ""


    def login_authentification(self):
        access = MDApp.get_running_app()
        login = self.ids.username_field.text.strip()
        password = self.ids.password_field.text.strip()
        hashed_pw = sha256(password.encode()).hexdigest()
        with sqlite3.connect("data/essentials_db.db") as conn:
            with closing(conn.cursor()) as cursor:
                cursor = conn.cursor()
                cursor.execute("SELECT id, fullname, email, password_hash FROM users WHERE email = ? AND  password_hash = ?", (login, hashed_pw))
                user = cursor.fetchone()
        
        if user:            
            access.current_user_id = user[0]
            access.greeting_name = user[1]
            access.root.current = "home"            
            hobby_screen = access.root.get_screen("hobby")
            hobbies_list_screen = access.root.get_screen("hobbies_list")
            hobbies_list_screen.ids.greetings.text = f"{access.current_day()}"          
            hobby_screen.ids.greetings.text = f"Have fun, make mistakes, and keep going. \nThat’s how you grow {access.greeting_name}!"            
            self.clear_fields_login()
        else:
            if not login or not password:
                access.show_popup("Hey don’t forget to enter your email and password.", title = "Wow!")

            else:
                access.show_popup("Sorry, password or e-mail invalid.", title = "Try again!")

class SignupScreen(Screen):    
    # Method responsible for clearing all input fields on the SignupScreen. 
    def clear_fields_signup(self):
        self.ids.user_fullname.text = ""
        self.ids.user_email.text = ""
        self.ids.user_password.text = ""
        self.ids.user_password_confirm.text = ""
        self.ids.user_birthday.text = ""

    # Method responsible for creating a user's account. 
    def create_account(self):
        access = MDApp.get_running_app()  # Gets access to the MDApp instance
        # Capturing user's input.       
        fullname = self.ids.user_fullname.text.strip().title()
        email = self.ids.user_email.text.strip().lower()
        password = self.ids.user_password.text.strip()
        confirm_password = self.ids.user_password_confirm.text.strip()
        birthday = self.ids.user_birthday.text.strip()

        # Checking if any required field is missing to prevent invalid database entries. 
        if not fullname or not email or not password or not confirm_password or not birthday:
            access.show_popup("All fields are required!", title = "Wow!")
            return

        # Checking if passwords match. 
        if password != confirm_password:
            access.show_popup("Passwords do not match!", title = "Wow!")
            return

        # Hashing the password to improve security and ensure it’s not stored in plain text. 
        password_hash = sha256(password.encode()).hexdigest() 

        # Inserting the user's information into the database. 
        try:
            with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO users (fullname, email, birthday, password_hash)
                        VALUES (?, ?, ?, ?)
                    """, (fullname, email, birthday, password_hash))
                    conn.commit()
            access.show_popup("Account created successfully!", title="Heck yes!")
            access.root.current = "login" # Redirecting to the LoginScreen. 
            self.clear_fields_signup()  # Clearing the fields to prepare for the next user 
            

        except sqlite3.IntegrityError as e: 
            # Handles duplicate email error. Each email must be unique in the database 
            print(e)
            self.clear_fields_signup()
            access.show_popup("This email already exists!", title="Oops!") 

        except sqlite3.OperationalError as e: 
            # Handles database operation issues or timeouts, useful for informing the user it's temporary. 
            print(e)
            self.clear_fields_signup()
            access.show_popup("Database is busy, please try again.", title = "STAY HARD!")
         

class HomeScreen(Screen):
    def on_enter(self):
        access = MDApp.get_running_app()
        storage_updating = access.root.get_screen("hobbies_list")     
        storage_updating.storage_hobby()

    def greetings(self):
        access = MDApp.get_running_app()
        self.ids.greetings.text = f"Welcome back, {access.greeting_name}!" 
        

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

        

        


    def showing_list(self):
        acess = MDApp.get_running_app()         
        base_layout = self.ids.base  
        user_id = acess.current_user_id
        widgets_to_remove = []
        
               
        
        with sqlite3.connect("data/essentials_db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hobby_name, unit_measure, goal, progress FROM hobbies WHERE user_id = ?", (user_id,))
            hobbies_list = cursor.fetchall()
       
        
        for child in base_layout.children:           
            if isinstance(child, MDSwiper):
                widgets_to_remove.append(child)              

        if not hobbies_list:
            self.no_hobbies_label = Label(                
                text="Sorry, you haven't added any hobbies yet.",
                halign="center",
                valign="top",
                size_hint=(.8, None),
                pos_hint={"top": 0.6, "center_x": 0.5},            
                font_name="fonts/jersey_25.ttf",            
                color=(0, 0, 0, 1),
                font_size=sp(20),            
            )
            base_layout.add_widget(self.no_hobbies_label)
        else:
            if self.no_hobbies_label is not None and self.no_hobbies_label in base_layout.children:
                    base_layout.remove_widget(self.no_hobbies_label)                    
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
                    size_hint=(0.45 , 0.9),
                    pos_hint={"center_x": 0.5, "center_y": 0.47},
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
                    font_name="fonts/jersey_25.ttf",            
                    color=(0, 0, 0, 1),
                    font_size=sp(20),           
                )            
                
                percentage_field = Label(
                    text= f"{(100*progress)/goal:.2f}%",
                    size_hint = (0.1, None),
                    pos_hint={"center_y": 0.5, "center_x": 0.85},
                    color = (0, 0, 0, 1),
                    font_size = sp(15),
                    font_name="fonts/jersey_25.ttf"
                )
                
                label_1 = Label(
                    text = f"{progress}/{goal} {unit_measure}",                
                    halign="center",               
                    size_hint=(0.8, None),
                    pos_hint={"center_y": 0.4, "center_x": 0.5},            
                    font_name="fonts/jersey_25.ttf",            
                    color=(0, 0, 0, 1),
                    font_size=sp(15)           
                )

                progress_bar = MDProgressBar(                
                    size_hint = (0.45, None),
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
                    font_name="fonts/jersey_25.ttf",
                    theme_text_color= "Custom",
                    line_color_focus= (0.5, 0.8, 0.5, 1),
                    line_color_normal= (0.5, 0.8, 0.5, 1),
                    cursor_color= (0.5, 0.8, 0.5, 1),
                    text_color_focus= (0, 0, 0, 1),                                             
                )
                progress_capture.bind(text=lambda instance, value: acess.limit_field_length(instance, value, 7))
                
                
                hobby_icon = icon_matcher.match_user_input(hobby)           
                    
                bg_image = MDIconButton(
                    icon = hobby_icon,                
                    pos_hint={"center_x": 0.5, "center_y": 0.75},
                    icon_size = sp(40)                    
                )
                

                submit_progress = MDFlatButton(
                    text = "ADD YOUR PROGRESS!",               
                    size_hint = (0.4, None),
                    font_name="fonts/jersey_25.ttf",               
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
        
        
                

        for widget in widgets_to_remove:
            try:
                base_layout.remove_widget(widget)                               
            except Exception:
                print("Error to remove the swiper")                
        
        try:
            base_layout.add_widget(swiper)
            
        except Exception:
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
                            cursor.execute("""INSERT OR IGNORE INTO statistic (user_id, hobby_name, unit_measure, goal, progress, updated_at)
                                        SELECT user_id, hobby_name, unit_measure, goal, progress, updated_at FROM hobbies
                                        WHERE user_id = ? AND updated_at = ?
                                        """, (user_id, updated_at)
                                        )
                            cursor.execute("""
                                UPDATE hobbies
                                SET progress = ?
                                WHERE user_id = ? AND hobby_name = ?
                            """, (reset_progress, user_id, hobby_name))
                conn.commit()
            except Exception:                
                acess.show_popup("Something went wrong. Try again.", title="Oops!")

class StatsScreen(Screen):   

    def update_table_height(self, table, min_table_height):
        table.height = max(table.minimum_height, min_table_height)

    # Creating stats table    
    def creating_table(self):
        data = []             
        acess = MDApp.get_running_app()
        user_id = acess.current_user_id
        scroll = ScrollView(
            pos_hint = {"center_x": 0.5, "center_y": 0.40},
            size_hint = (0.9, 0.75)            
        )               

        min_table_height = dp(420)

        #Creating gridlayout
        table = MDGridLayout(
            cols = 7,
            spacing = 10,
            padding = 10,
            md_bg_color = (0.5, 0.8, 0.5, 0.2),
            radius = [30],
            size_hint_y = None,           
        )
        
        table.bind(minimum_height= lambda instance, value:self.update_table_height(table, min_table_height))

        stats_base = acess.root.get_screen("stats_screen").ids.stats_base #Getting acess to MDFloatLayout in .kv
        stats_base.add_widget(scroll) #Adding scrollview to the acess
        scroll.add_widget(table) #Adding MDGridLayout to scrollview

        #Adding headers to MDGridLayout
        headers = ("HOBBY", "UNIT MEASURE", "GOAL", "TOTAL", "DAYS", "SUCCESS DAYS", "AVERAGE PER DAY")
        for header in headers:
            table.add_widget(Label(
                text= header,
                size_hint_y = None,
                halign = "center",
                valign = "middle",
                height = 50,
                bold = True,
                font_name="fonts/jersey_25.ttf",            
                color=(0, 0, 0, 1),
                font_size= sp(15),
                text_size = (None, None)
            ))    

        try:
            #Pulling information from stats db
            with sqlite3.connect("data/essentials_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT hobby_name, unit_measure, goal, progress FROM statistic WHERE user_id = ?", (user_id,))
                raw_data = cursor.fetchall()

            if raw_data:
                for entry in raw_data:
                    success_days = 0
                    if entry[3] >= entry[2]:
                        success_days = 1
                    data.append([*entry, success_days])

                hobby_summary = defaultdict(lambda: [0.0, 0.0, 0, 0, 0.0])

                for item in data:
                    name_key = (item[0], item[1])
                    hobby_summary[name_key][0] = item[2]  
                    hobby_summary[name_key][1] += item[3]
                    hobby_summary[name_key][2] += 1   
                    hobby_summary[name_key][3] += item[4]  
                    hobby_summary[name_key][4] = round((hobby_summary[name_key][1]/ hobby_summary[name_key][2]), 2)

                calculated_table = [[name, unit, goal, round(total_progress, 2), days, days_success, avg_day] for (name, unit), (goal, total_progress, days, days_success, avg_day) in hobby_summary.items()]

                for user_info in calculated_table:
                    for cell in user_info:
                        table.add_widget(Label(
                            text= str(cell),
                            size_hint_y = None,
                            halign = "center",
                            valign = "middle",
                            height = 40,                    
                            font_name="fonts/jersey_25.ttf",            
                            color=(0, 0, 0, 1),
                            font_size=sp(15),
                            text_size = (None, None)
                        ))            
        except Exception as e:
            print("ERROR!", e)
            


    def cleaning_table(self):        
        statistic_base = self.ids.stats_base
        try:        
            for child in statistic_base.children[:]:           
                if isinstance(child, ScrollView):
                    statistic_base.remove_widget(child)
        except Exception as e:
            print("ERROR!", e)
            return

class ForgotPasswordScreen(Screen):
    def checking_email(self):
        acess = MDApp.get_running_app()
        acess_forgot_screen = acess.root.get_screen("forgot_pass_screen")
        email = acess_forgot_screen.ids.forgot_pass_user_mail.text.strip().lower()
        

        if email == "":
            return acess.show_popup("Please type your email before submit it!", title="Hey")
        
        try:
            with sqlite3.connect("data/essentials_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT email FROM users WHERE email = ?""", (email,))
                email_exist = cursor.fetchone()

            if email_exist:
                code_screen = acess.root.get_screen("code_screen")
                changing_pass = acess.root.get_screen("changing_password")
                time_now = datetime.now().date().isoformat()
                code_screen.user_email = email
                changing_pass.user_email = email
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

                with sqlite3.connect("data/essentials_db.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("""UPDATE users SET recovery_code =?, updated_at =? WHERE email = ?""", (code, time_now, email))
                    conn.commit()
                
                
                
                load_dotenv()                
                username = os.getenv("SMTP_USERNAME")
                password = os.getenv("SMTP_PASSWORD")
                
                
                sender_email = "no-reply@essentials.local"
                receiver_email = email
                

                message = MIMEText(f"Don't worry, we've got you! Here is your recovery code: {code}.\n Don't waste any more time—get back to tracking your hobbies!")
                message["Subject"] = "Recovery Account!"
                message["From"] = sender_email
                message["To"] = receiver_email

                with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
                    server.starttls()
                    server.login(username, password)
                    server.sendmail(sender_email, receiver_email, message.as_string())                 

                acess.root.current = "code_screen"
                
                acess_forgot_screen.ids.forgot_pass_user_mail.text = ""
            else:
                acess.show_popup("Sorry the email you typed doesn't exist.", title="Wow!")

        except Exception as e:
            acess_forgot_screen.ids.forgot_pass_user_mail.text = ""
            print(f"Error during email checking: {e}")
            acess.show_popup("Something went wrong. Try again.", title="Oops!")

class CodeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs) 
        self.attempts_code = 0
        

    def validating_code(self):        
        email = getattr(self, "user_email", None)
        acess = MDApp.get_running_app()        
        code = self.ids.code_mailed.text
        

        if not email:
            acess.show_popup("No email found. Please retry.", title="Error")
            return
            
        if code == "":
            return acess.show_popup("Please enter the code you received before submitting it!", title="Hey")
        
            
        try:
            with sqlite3.connect("data/essentials_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT recovery_code FROM users WHERE email=?""", (email,))
                row = cursor.fetchone()

            if row is None:
                acess.show_popup("No recovery code found. Please try again.", title="Error")
                return
            
                       
            code_from_db = row[0]
            if code == code_from_db:                
                acess.root.current = "changing_password"
                self.ids.code_mailed.text = ""
            else:
                self.attempts_code += 1
                if self.attempts_code >= 3:
                     acess.show_popup("Too many incorrect tries. Please request a new code.", title="Locked Out")
                     self.ids.code_mailed.text = ""
                     self.attempts_code = 0
                     acess.root.current = "forgot_pass_screen"                     
                else:
                    self.ids.code_mailed.text = ""
                    acess.show_popup("Sorry, the code you typed is wrong. Please double-check your email.", title="Oops!")

        except Exception as e:           
            acess.show_popup(f"Something went wrong: {str(e)}", title="Oops!")




class ChangingPassScreen(Screen):
    def double_checkingpass(self):
        access = MDApp.get_running_app()
        email = getattr(self, "user_email", None)       
        if self.ids.recovery_pass.text == "" or self.ids.recovery_pass_confirm.text == "":            
            return access.show_popup("All fields are required!", title="Hey!")
        elif self.ids.recovery_pass.text != self.ids.recovery_pass_confirm.text:
            return access.show_popup("Passwords do not match!", title="Wow!")
        else:
            password = self.ids.recovery_pass_confirm.text
            password_hash_confirm = sha256(password.encode()).hexdigest()
            with sqlite3.connect("data/essentials_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""UPDATE users SET password_hash = ? WHERE email = ?""", (password_hash_confirm, email))
                conn.commit()

            access.root.current = "login"
            return access.show_popup("Password changed successfully!", title="Heck Yeah!")

                    

        

Essentials().run()  

