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
    
    
    # Creates the database and adding each screen to the ScreenManager.
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
    
    # Create all the tables.
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
    
    # Creates and displays pop-up dialogs used throughout the app's screens.
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

    # Establish a character limit on a text field.    
    def limit_field_length(self, instance, value, max_lenth = 10):
        if len(value) > max_lenth:
            instance.text = value[:max_lenth]

    
    # Gets the current date and formatting it for display on the HobbiesListScreen.
    def current_day(self):
        today = datetime.now(ZoneInfo("America/Chicago"))
        today_day = today.day
        today_month = today.strftime("%B")
        today_year = today.year
        return (f"{today_month} {today_day}, {today_year}")    
    
           

class LoadingScreen(Screen):
    # Initiate model loading in the background when the screen opens,
    # and scheduling a transition to the LoginScreen after 5 seconds.
    def on_enter(self):
        self.load_model_in_background()
        # Clock.schedule_once(lambda dt: self.on_model_loaded(), 5)

    # Switch the current screen to the LoginScreen.
    def on_model_loaded(self):
        MDApp.get_running_app().root.current = "login"

    # This method loads the icon recognition model in the background to avoid blocking the main UI thread.
    def load_model_in_background(self):
        def _load():
            try:
                icon_matcher.load_model() # Loading the machine learning model
                Clock.schedule_once(lambda dt: self.on_model_loaded())
            except Exception as e:
                print("Model loading failed:", e) # Logs error if model loading fails
                    

        Thread(target=_load).start() # Starts the thread to run _load() in the background

        
        
    
class LoginScreen(Screen):
    # Clears all input fields on the LoginScreen.
    def clear_fields_login(self):
        self.ids.username_field.text = ""
        self.ids.password_field.text = ""

    # Check user authentication.
    def login_authentication(self):
        access = MDApp.get_running_app()
        
        # Capturing user's input.
        login = self.ids.username_field.text.strip()
        password = self.ids.password_field.text.strip()
        hashed_pw = sha256(password.encode()).hexdigest()

        # Open the database and compare credentials.
        with sqlite3.connect("data/essentials_db.db") as conn:
            with closing(conn.cursor()) as cursor:                
                cursor.execute("SELECT id, fullname, email, password_hash FROM users WHERE email = ? AND  password_hash = ?", (login, hashed_pw))
                user = cursor.fetchone()
        
        # If user exists, assign the user ID globally so other screens can access it.
        if user:            
            access.current_user_id = user[0]
            access.greeting_name = user[1] # Stores the user's full name for greetings.
            access.root.current = "home"                   
            self.clear_fields_login()
        else:
            # If either field is empty, notify the user.
            if not login or not password: 
                access.show_popup("Hey don’t forget to enter your email and password.", title = "Wow!")

            else:
                # If the credentials are invalid.
                access.show_popup("Sorry, password or e-mail invalid.", title = "Try again!") # In case either of them were wrong.

class SignupScreen(Screen):    
    # Clears all input fields on the SignupScreen. 
    def clear_fields_signup(self):
        self.ids.user_fullname.text = ""
        self.ids.user_email.text = ""
        self.ids.user_password.text = ""
        self.ids.user_password_confirm.text = ""
        self.ids.user_birthday.text = ""

    # Create user's account. 
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
    # Method that runs as soon as the HomeScreen is entered.
    # It calls a method from HobbiesListScreen to update the list of hobbies modified the day before,
    # and resets each hobby's progress to zero.
    def on_enter(self):
        access = MDApp.get_running_app()
        storage_updating = access.root.get_screen("hobbies_list")     
        storage_updating.storage_hobby()

    # Greets the user by name on the HomeScreen.
    def greetings_homescreen(self):
        access = MDApp.get_running_app()
        self.ids.greetings.text = f"Welcome back, {access.greeting_name}!" 
        

class HobbyScreen(Screen):
    # Clears all input fields on the HobbyScreen.
    def clear_fields_hobby(self):
        self.ids.user_hobby.text = ""
        self.ids.user_measure_hobby.text = ""
        self.ids.user_hobby_goal.text = ""

    # Greets the user by name on the HobbyScreen.
    def greetings_hobbyscreen(self):
        access = MDApp.get_running_app()
        self.ids.greetings.text = f"Have fun, make mistakes, and keep going. \nThat’s how you grow {access.greeting_name}!"

    # Creates a new hobby entry based on the user input.
    def create_hobby(self):
        access = MDApp.get_running_app()            
        hobby = self.ids.user_hobby.text.strip().title()
        unit_measure = self.ids.user_measure_hobby.text.strip().title()
        goal = self.ids.user_hobby_goal.text.strip()
        progress = 0.0
        updated_at = datetime.now(ZoneInfo("America/Chicago")).date()
        user_id = access.current_user_id

        # Check if any required field is empty to prevent invalid database entries.
        if not hobby or not unit_measure or not goal:
            access.show_popup("Please, fill in all the fields.", title="Oops!")
            return
        
        # Try block to ensure the app continues running even if something goes wrong.       
        try:
            # Check the database to confirm the hobby does not already exist.
            with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor:                    
                    cursor.execute("""SELECT unit_measure, hobby_name, goal FROM hobbies WHERE user_id = ? AND hobby_name = ?  """, (user_id, hobby))
                    existing = cursor.fetchone()

                    # If the hobby exists, notify the user and clear the fields.
                    if existing:
                        if existing[0] != unit_measure or existing[1] == hobby:
                            access.show_popup("This hobby already exists!", title="Oops!")
                            self.clear_fields_hobby()

                    # If the hobby does not exist, insert it into the hobbies table.    
                    else:
                        cursor.execute("""
                            INSERT OR IGNORE INTO hobbies (user_id, hobby_name, unit_measure, goal, progress, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (user_id, hobby, unit_measure, goal, progress, updated_at))
                        conn.commit() # Commit the changes to the database.          

                        access.show_popup(f"{hobby} added successfully!", title="Nice!")
                        self.clear_fields_hobby() # Clear the input fields.
                        access.root.current = "home" # Redirect to HomeScreen.

        except sqlite3.IntegrityError: 
            # Catch and handle any unexpected insertion errors.
            self.show_popup("This hobby already exists!", title="Oops!")


class DeleteHobbyScreen(Screen):
    # Clear the input field on the DeleteHobbyScreen
    def clear_fields_delete(self):
        self.ids.hobby_to_delete.text = ""

    # Deletes a hobby from both the hobbies and statistic tables in the database.
    def delete_hobby(self):
        access = MDApp.get_running_app()        
        hobby_to_delete = self.ids.hobby_to_delete.text.strip().title()
        user_id = access.current_user_id

        # Prevent submission if the field is empty.
        if not hobby_to_delete:
            access.show_popup("Please enter the hobby you would like to delete", title = "Oops!")
            return 

        with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor:
                    # Check if the hobby exists for the current user.                    
                    cursor.execute("SELECT user_id, hobby_name FROM hobbies WHERE user_id = ? and hobby_name = ?", (user_id, hobby_to_delete))
                    hobby_check = cursor.fetchone()                            

                    
                    if hobby_check:
                        try: 
                            # Delete hobby from both hobbies and statistic tables.  
                            cursor.execute("DELETE FROM hobbies WHERE user_id = ? and hobby_name = ?", (user_id, hobby_to_delete))
                            cursor.execute("DELETE FROM statistic WHERE user_id = ? AND hobby_name = ?", (user_id, hobby_to_delete))
                            conn.commit()                                
                            access.show_popup(f"{hobby_to_delete} was successfully deleted!", title="Done")          
                            self.clear_fields_delete() 
                            access.root.current = "home" # Redirect to HomeScreen
                            
                        except sqlite3.IntegrityError:
                            access.show_popup("Please enter the hobby you would like to delete appropriately.", title = "Oops!")                
                       
                    else:
                        # Hobby not found in the user's list.
                        access.show_popup(f"{hobby_to_delete} is not in the hobbies list.", title="Oops!")
                        self.clear_fields_delete()

class HobbiesListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Class-level variables for easier access within methods.    
        self.no_hobbies_label = None
        self.progress_capture = None
        self.progress = 0    
    
    # Display the exact day, month, and year in the format returned by current_day().
    def greetings_hobbieslistscreen(self):
        access = MDApp.get_running_app()
        self.ids.greetings.text = f"{access.current_day()}" 
    
    # Remove the "no hobbies" message if it exists and hobbies are present.
    def cleaning_no_hobbieslabel(self):
        base_layout = self.ids.base
        if self.no_hobbies_label is not None and self.no_hobbies_label in base_layout.children:
                    base_layout.remove_widget(self.no_hobbies_label)

    # Update the hobby's progress in the database after each user input.
    def progress_updating(self, hobby_name, progress_capture, label_1, progress_bar, goal, unit_measure, percentage):
        access = MDApp.get_running_app()                
        user_id = access.current_user_id
        text = progress_capture.text.strip()
        time_now = datetime.now(ZoneInfo("America/Chicago")).date()
        if text == "":
            # Make sure progress is entered before updating the database.
            return access.show_popup("Don't forget to type in your progress first!", title="It's all good!") 
        
        try:
            # Retrieve the current progress from the database.
            with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("""
                        SELECT progress
                        FROM hobbies
                        WHERE user_id = ? AND hobby_name = ?
                    """, (user_id, hobby_name))
                    result = cursor.fetchone()                    
                    hobby_progress = result[0]

             # If progress exists, add the new entry to it; otherwise, use the entered value.
            if hobby_progress:
                hobby_progress += float(text)
                self.progress = hobby_progress                    
            else:                
                self.progress = float(text)  
           
                
        except ValueError:                
            print("ERROR! Wrong value.")
            return
                    
        
        try:
            # Update the database with the new progress and the timestamp.
            with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor:                   
                    cursor.execute("""
                        UPDATE hobbies
                        SET progress = ?, updated_at = ?
                        WHERE user_id = ? AND hobby_name = ?
                    """, (self.progress, time_now, user_id, hobby_name))
                    conn.commit()
        except Exception as e:
            print("ERROR! Wrong value.", e)
            return

        # Update the UI labels and progress bar live.
        label_1.text = f"{self.progress:.2f}/{goal} {unit_measure}"
        percentage.text = f"{(100*self.progress)/goal:.2f}%"
        progress_bar.value = min((self.progress / goal) * 100, 100)

        # Clear the input field.
        progress_capture.text = ""

        

        

    # Build the hobby list page: Swiper, cards, and card contents.
    def showing_list(self):
        access = MDApp.get_running_app()         
        base_layout = self.ids.base  # MDFloatLayout from the .kv file.
        user_id = access.current_user_id
        widgets_to_remove = []  # Track widgets to remove (old swiper/cards).     
        
               
        # Retrieve hobbies from the database.
        with sqlite3.connect("data/essentials_db.db") as conn:
            with closing(conn.cursor()) as cursor:                
                cursor.execute("SELECT hobby_name, unit_measure, goal, progress FROM hobbies WHERE user_id = ?", (user_id,))
                hobbies_list = cursor.fetchall()
       
         # Mark old swipers for removal.
        for child in base_layout.children:           
            if isinstance(child, MDSwiper):
                widgets_to_remove.append(child)              

        # If no hobbies exist, show a message.
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
            # Remove "no hobbies" label if hobbies exist.
            if self.no_hobbies_label is not None and self.no_hobbies_label in base_layout.children:
                    base_layout.remove_widget(self.no_hobbies_label)

            # Create a swiper for horizontal scrolling.                  
            swiper = MDSwiper(
            size_hint=(0.9, 0.6),
            pos_hint={"center_x": 0.5, "center_y": 0.40})        

            # Create a card for each hobby.
            for hobby, unit_measure, goal, progress in hobbies_list:
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
                progress_capture.bind(text=lambda instance, value: access.limit_field_length(instance, value, 7))
                
                
                
                hobby_icon = lambda: icon_matcher.match_user_input(hobby)                
                bg_image = MDIconButton(
                    icon = hobby_icon(),                
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
                    # Pass values to update method.
                    on_press=lambda instance, h=hobby, pc=progress_capture, l=label_1, pb=progress_bar, g=goal, u=unit_measure, p=percentage_field: 
                self.progress_updating(h, pc, l, pb, g, u, p),                
                )
                
                # Add widgets to layouts.
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
        
        
                
        # Remove old widgets.
        for widget in widgets_to_remove:
            try:
                base_layout.remove_widget(widget)                               
            except Exception:
                print("Error to remove the swiper")                
        
        try:
            # Add new swiper.
            base_layout.add_widget(swiper)
            
        except Exception:
            print("Error!")

    # Store hobbies in the statistics table.
    def storage_hobby(self):                
        access = MDApp.get_running_app()
        user_id = access.current_user_id        
        time_now = datetime.now(ZoneInfo("America/Chicago")).date()
        reset_progress = 0

        # Get hobby update info.
        with sqlite3.connect("data/essentials_db.db") as conn:            
            with closing(conn.cursor()) as cursor:
                cursor.execute("""SELECT updated_at, hobby_name FROM hobbies WHERE user_id =?""", (user_id,))
                hobby_storage = cursor.fetchall()

                try:
                    for updated_at, hobby_name in hobby_storage:
                        conversion_datetime = datetime.strptime(updated_at,"%Y-%m-%d").date() 
                        
                        # If last update date is different from today, save it to statistics and reset progress.       
                        if conversion_datetime != time_now:                    
                                cursor.execute("""INSERT OR IGNORE INTO statistic (user_id, hobby_name, unit_measure, goal, progress, updated_at)
                                            SELECT user_id, hobby_name, unit_measure, goal, progress, updated_at FROM hobbies
                                            WHERE user_id = ? AND updated_at = ?
                                            """, (user_id, updated_at)
                                            )
                                # Updates the progress to zero, so the user can continue tracking their progress on a fresh day.
                                cursor.execute("""
                                    UPDATE hobbies
                                    SET progress = ?
                                    WHERE user_id = ? AND hobby_name = ?
                                """, (reset_progress, user_id, hobby_name))
                    conn.commit()
                except Exception:                
                    access.show_popup("Something went wrong. Try again.", title="Oops!")

class StatsScreen(Screen):
    # Update the table's height and enforce a minimum height.
    def update_table_height(self, table, min_table_height):
        table.height = max(table.minimum_height, min_table_height)

    # Create the stats table.    
    def creating_table(self):
        data = []             
        access = MDApp.get_running_app()
        user_id = access.current_user_id
        scroll = ScrollView(
            pos_hint = {"center_x": 0.5, "center_y": 0.40},
            size_hint = (0.9, 0.75)            
        )               

        min_table_height = dp(420)

        # Create the grid layout that will hold table rows.
        table = MDGridLayout(
            cols = 7,
            spacing = 10,
            padding = 10,
            md_bg_color = (0.5, 0.8, 0.5, 0.2),
            radius = [30],
            size_hint_y = None,           
        )
        
        table.bind(minimum_height= lambda instance, value:self.update_table_height(table, min_table_height))

        stats_base = access.root.get_screen("stats_screen").ids.stats_base 
        stats_base.add_widget(scroll)
        scroll.add_widget(table) 

        # Add headers to the MDGridLayout.
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
            # Retrieve records from the stats database for the current user.
            with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("SELECT hobby_name, unit_measure, goal, progress FROM statistic WHERE user_id = ?", (user_id,))
                    raw_data = cursor.fetchall()

            if raw_data:
                # Build a data list and compute whether each row counts as a "success day".
                for entry in raw_data:
                    success_days = 0
                    if entry[3] >= entry[2]:
                        success_days = 1
                    data.append([*entry, success_days])

                # Aggregate stats by hobby (keyed by (hobby_name, unit_measure)).
                hobby_summary = defaultdict(lambda: [0.0, 0.0, 0, 0, 0.0])

                for item in data:
                    name_key = (item[0], item[1])
                    hobby_summary[name_key][0] = item[2]  
                    hobby_summary[name_key][1] += item[3]
                    hobby_summary[name_key][2] += 1   
                    hobby_summary[name_key][3] += item[4]  
                    hobby_summary[name_key][4] = round((hobby_summary[name_key][1]/ hobby_summary[name_key][2]), 2)

                calculated_table = [[name, unit, goal, round(total_progress, 2), days, days_success, avg_day] for (name, unit), (goal, total_progress, days, days_success, avg_day) in hobby_summary.items()]

                # Populate the grid layout with the calculated rows.
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
            

    # Remove the table (remove the ScrollView that contains it).
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
    # Check if the typed email exists in the database.
    def checking_email(self):
        access = MDApp.get_running_app()
        access_forgot_screen = access.root.get_screen("forgot_pass_screen")
        email = access_forgot_screen.ids.forgot_pass_user_mail.text.strip().lower()
        
        # Handle empty email submission.
        if email == "":
            return access.show_popup("Please type your email before submit it!", title="Hey")
        
        try:
            # Connect to the database and check if email exists.
            with sqlite3.connect("data/essentials_db.db") as conn:
                    with closing(conn.cursor()) as cursor:                               
                        cursor.execute("""SELECT email FROM users WHERE email = ?""", (email,))
                        email_exist = cursor.fetchone()

            if email_exist:
                # Get screens to share email info and prepare for code verification.
                code_screen = access.root.get_screen("code_screen") 
                changing_pass = access.root.get_screen("changing_password") 
                time_now = datetime.now().date().isoformat()
                code_screen.user_email = email # Pass email to CodeScreen.
                changing_pass.user_email = email # Pass email to ChangingPassScreen.

                # Generate a random 6-character recovery code (letters and digits).
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) 

                # Update the database with the recovery code and timestamp.
                with sqlite3.connect("data/essentials_db.db") as conn:
                    with closing(conn.cursor()) as cursor: 
                        cursor.execute("""UPDATE users SET recovery_code =?, updated_at =? WHERE email = ?""", (code, time_now, email))
                        conn.commit()
                
                
                 # Load SMTP credentials from environment variables.
                load_dotenv()                
                username = os.getenv("SMTP_USERNAME")
                password = os.getenv("SMTP_PASSWORD")
                
                 # Prepare email details.
                sender_email = "no-reply@essentials.local"
                receiver_email = email # Receiver is the user.
                
                # Compose the recovery email message.
                message = MIMEText(f"Don't worry, we've got you! Here is your recovery code: {code}.\n Don't waste any more time—get back to tracking your hobbies!")
                message["Subject"] = "Recovery Account!"
                message["From"] = sender_email
                message["To"] = receiver_email

                # Connect to SMTP server and send the email.
                with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
                    server.starttls()
                    server.login(username, password)
                    server.sendmail(sender_email, receiver_email, message.as_string())                 

                # Redirect to CodeScreen.
                access.root.current = "code_screen"
                
                # Clear the input field.
                access_forgot_screen.ids.forgot_pass_user_mail.text = ""
            else:
                # Email not found in database.
                access.show_popup("Sorry the email you typed doesn't exist.", title="Wow!")

        except Exception as e:
            # Handle any errors during the process.
            access_forgot_screen.ids.forgot_pass_user_mail.text = ""
            print(f"Error during email checking: {e}")
            access.show_popup("Something went wrong. Try again.", title="Oops!")

class CodeScreen(Screen):
    # Initialize a variable to track the number of code entry attempts.
    def __init__(self, **kwargs):
        super().__init__(**kwargs) 
        self.attempts_code = 0
        
    # Validate the entered recovery code against the one stored in the database.
    def validating_code(self):        
        email = getattr(self, "user_email", None)
        access = MDApp.get_running_app()        
        code = self.ids.code_mailed.text
        
        # Handle missing email (possible transition bug).
        if not email:
            access.show_popup("No email found. Please retry.", title="Error")
            return
        
        # Handle empty code submissions.    
        if code == "":
            return access.show_popup("Please enter the code you received before submitting it!", title="Hey")
        
            
        try:
            # Retrieve the stored recovery code for the user from the database.
            with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor: 
                    cursor.execute("""SELECT recovery_code FROM users WHERE email=?""", (email,))
                    row = cursor.fetchone()

            if row is None:
                access.show_popup("No recovery code found. Please try again.", title="Error")
                return
            
                       
            code_from_db = row[0]
            
           # Check if the entered code matches the stored code.
            if code == code_from_db:
                # If correct, navigate to the password changing screen and clear input.                
                access.root.current = "changing_password"
                self.ids.code_mailed.text = ""
            else:
               # If incorrect, increment attempt counter and handle lockout after 3 tries.
                self.attempts_code += 1
                if self.attempts_code >= 3:
                     access.show_popup("Too many incorrect tries. Please request a new code.", title="Locked Out")
                     self.ids.code_mailed.text = ""
                     self.attempts_code = 0
                     access.root.current = "forgot_pass_screen"                     
                else:
                    self.ids.code_mailed.text = ""
                    access.show_popup("Sorry, the code you typed is wrong. Please double-check your email.", title="Oops!")

        # Handle unexpected exceptions during validation.
        except Exception as e:           
            access.show_popup(f"Something went wrong: {str(e)}", title="Oops!")




class ChangingPassScreen(Screen):
    # Verify if the two entered passwords match and update the user's password in the database.
    def double_checkingpass(self):
        access = MDApp.get_running_app()
        email = getattr(self, "user_email", None)

        # Handle missing email (possible transition bug).
        if not email:
            access.show_popup("No email found. Please retry.", title="Error")
            return

        # Handle empty passwords submissions.       
        if self.ids.recovery_pass.text == "" or self.ids.recovery_pass_confirm.text == "":            
            return access.show_popup("All fields are required!", title="Hey!")
        
        # Check if both passwords match.
        elif self.ids.recovery_pass.text != self.ids.recovery_pass_confirm.text:
            return access.show_popup("Passwords do not match!", title="Wow!")
        else:
            # If passwords match, hash and update the new password in the database.
            password = self.ids.recovery_pass_confirm.text
            password_hash_confirm = sha256(password.encode()).hexdigest()
            with sqlite3.connect("data/essentials_db.db") as conn:
                with closing(conn.cursor()) as cursor:
                    cursor = conn.cursor()
                    cursor.execute("""UPDATE users SET password_hash = ? WHERE email = ?""", (password_hash_confirm, email))
                    conn.commit()

           # Redirect user to the login screen and show success message.
            access.root.current = "login"
            return access.show_popup("Password changed successfully!", title="Heck Yeah!")

                    

        

Essentials().run()  

