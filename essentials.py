print("Welcome to Essentials!  \nStay on top of your favorite hobbies.")


hobbies_list = {}

security = 0

while security < 3:
    login = input("Login: ")
    password = int(input("Password: "))
    if login == 'evrot' and password == 102030:
        print("Hi, are you ready to track your hobbies? Shall we?")
        while True:
                print("\n Select one of the options:")            
                print("1. Add a new hobby.")
                print("2. Take a a look on your hobbie's list.")
                print("3. Delete a hobby.")
                print("4. Set a goal for your hobby.")
                print("5. Exit.")
                try:
                    option_capture = int(input("Enter the number of your choice: "))

                    if option_capture == 1:
                        hobby = input("Please type your hobby: ").lower()
                        hobbies_list[hobby] = None
                        print(f"{hobby.capitalize()} added to your list!")
                        print(hobbies_list)

                    elif option_capture == 2:
                        if len(hobbies_list) == 0:
                            print("You don't have any hobbies at the moment")
                        else:
                            print("Here is your hobbie's list!")
                            for key, value in hobbies_list.items():
                                if value:                                                                                         
                                    print(f"Hobby: {key.capitalize()} | Goal: {value} {unit_measure}")
                                else:
                                    print(f"Hobby: {key.capitalize()} | Goal: It has not been defined yet.")                                 
                        
                            

                    elif option_capture == 3:
                        element_remove = input("Please type the hobby you would like to remove: ").lower()
                        if element_remove in hobbies_list:
                            hobbies_list.pop(element_remove)
                            print(f"{element_remove.capitalize()} removed from your list!")
                        else:
                            print("Sorry, the hobby typed is not in the list.")

                            

                    elif option_capture == 4:
                        edit_option = input('What hobby would you like to set a goal for? ').lower()
                        if edit_option in hobbies_list:
                            unit_measure = input("Insert the unit measure for your hobby: ")
                            hobby_goal = float(input(f"Insert the goal in {unit_measure} for {edit_option} today: "))                        
                            hobbies_list[edit_option] = hobby_goal                            
                        else:
                            print("Sorry, hobby not in the list.")
                
                    
                    elif option_capture == 5:
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