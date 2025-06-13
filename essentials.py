print("Welcome to Essentials!  \nStay on top of your favorite hobbies.")


hobbies_list = {}

security = 0

while security < 3:
    login = input("Login: ")
    password = int(input("Password: "))
    progress = 0
    percentage_progress = 0
    if login == 'evrot' and password == 102030:
        print("\nHi, are you ready to track your hobbies? Shall we?")
        while True:
                print("\n Select one of the options:")            
                print("1. Add a new hobby.")
                print("2. Take a a look on your hobbie's list.")
                print("3. Delete a hobby.")
                print("4. Set a goal for your hobby.")
                print("5. To update your progress toward your hobby goal.")
                print("6. Exit.")
                try:
                    option_capture = int(input("\nEnter the number of your choice: "))

                    if option_capture == 1:
                        hobby = input("\nPlease type your hobby: ").lower()
                        hobbies_list[hobby] = None
                        print(f"\n{hobby.capitalize()} added to your list!")
                        
                    elif option_capture == 2:
                        if len(hobbies_list) == 0:
                            print("You don't have any hobbies at the moment")
                        else:
                            print("Here is your hobbie's list!")
                            for key, value in hobbies_list.items():
                                if value:
                                    if progress:                                                                                                                       
                                        print(f"Hobby: {key.capitalize()} | Goal: {value} {unit_measure} | Progress: {progress} {unit_measure} {percentage_progress}% of your goal!")
                                    else:
                                        print(f"Hobby: {key.capitalize()} | Goal: {value} {unit_measure} | Progress: It has not been defined yet.")
                                else:
                                    print(f"Hobby: {key.capitalize()} | Goal: It has not been defined yet. | Progress: It has not been defined yet.")                                 
                        
                            

                    elif option_capture == 3:
                        element_remove = input("Please type the hobby you would like to remove: ").lower()
                        if element_remove in hobbies_list:
                            hobbies_list.pop(element_remove)
                            print(f"\n{element_remove.capitalize()} removed from your list!")
                        else:
                            print("\nSorry, the hobby typed is not in the list.")

                            

                    elif option_capture == 4:
                        edit_option = input("What hobby would you like to set a goal for? ").lower()
                        if edit_option in hobbies_list:
                            unit_measure = input("Insert the unit measure for your hobby: ")
                            hobby_goal = round(float(input(f"Insert the goal in {unit_measure} for {edit_option} today: ")), 2)                        
                            hobbies_list[edit_option] = hobby_goal
                            print(f"\nAll set! You can start working on your {edit_option} to achieve your today's {hobby_goal} {unit_measure}!")                            
                        else:
                            print("\nSorry, hobby not in the list.")
                
                    
                    elif option_capture == 5:
                        update_progress = input("What hobby would you like to update your progress? ").lower()
                        if update_progress in hobbies_list:
                            progress = round(float(input("Please type your progress: ")), 2)
                            print("\nYou are unstoppable! You're getting closer to your goal—stay relentless in your pursuit!")                                                   
                        else:
                            print("\nSorry, hobby not in the list.")

                    
                    elif option_capture == 6:
                        print("See you next time!")
                        break

                    else:
                        print("Invalid option, try again.")
                except ValueError:
                    print("Please select one of the available options.")
        break

    else:
        print("Sorry, user name or password invalid.")
        security += 1

if security == 3:
    print("Too many failed attempts. Access denied.")