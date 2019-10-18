from curses import textpad
import threading
import random
import pickle
import curses
import time
import sys
import os


# Let op: Curses gebruikt Y,X inplaats van X,Y.


DELAY = 500
snake_display_symbol = 'o'
quit_game = False
possible_powerups = {"speed":{"kind":"speed","symbol":'+',"duration":5,"color":3, "description":"Increases the snake's speed by 5."},
                "slowness":{"kind":"slowness","symbol":'-',"duration":5,"color":3, "description":"Decreases the snake's speed by 5."},
                "reverse":{"kind":"reverse","symbol":'R',"duration":5,"color":2, "description":"Reverses the snake's controls."},
                "score1":{"kind":"score1","symbol":'1',"duration":0,"color":1, "description":"Increases the snake's score by 1."},
                "score2":{"kind":"score2","symbol":'2',"duration":0,"color":1, "description":"Increases the snake's score by 2."},
                "score5":{"kind":"score5","symbol":'5',"duration":0,"color":1, "description":"Increases the snake's score by 5"},
                "random":{"kind":"random", "description": "Chooses a random powerup from the above."}}
possible_settings = {"Positive Color":1,"Negative Color":2,"Neutral Color":3,"Selection Color":4}
possible_controls = {"Up":"Up-Arrow","Down":"Down-Arrow","Left":"Left-Arrow","Right":"Right-Arrow","Back":"ESC"}

class SavedData:
    def __init__(self, highscore, selection_color, positive_color, negative_color, neutral_color, standard_game_height, standard_game_width, standard_powerup_amount):
        self.highscore = highscore
        self.selection_color = selection_color
        self.positive_color = positive_color
        self.negative_color = negative_color
        self.neutral_color = neutral_color
        self.standard_game_height = standard_game_height
        self.standard_game_width = standard_game_width
        self.standard_powerup_amount = standard_powerup_amount


# Check if the game already has some saved data.
if os.path.isfile("saveddata.data"):
    file = open("saveddata.data", "rb")
    object = pickle.load(file)
    file.close()
    highscore = object.highscore
    selection_color = object.selection_color
    positive_color = object.positive_color
    negative_color = object.negative_color
    neutral_color = object.neutral_color
    standard_game_height = object.standard_game_height
    standard_game_width = object.standard_game_width
    standard_powerup_amount = object.standard_powerup_amount
else:
    highscore = 0
    selection_color = curses.COLOR_YELLOW
    positive_color = curses.COLOR_GREEN
    negative_color = curses.COLOR_RED
    neutral_color = curses.COLOR_BLUE
    standard_game_height = 20
    standard_game_width = 50
    standard_powerup_amount = 5


# Gets user input
def curses_input(window, height, width, y, x, question):
    window.addstr(y,x-int(len(question)/2), question)
    new_window = curses.newwin(height, width, y+5, x)
    txtbox = curses.textpad.Textbox(new_window)
    curses.textpad.rectangle(screen, y+5 - 1, x - 1, y+5 + height, x + width)
    screen.refresh()
    return txtbox.edit()


# Saves the data to a file.
def save_data():
    saveddata = SavedData(highscore,selection_color,positive_color,negative_color,neutral_color,standard_game_height,standard_game_width,standard_powerup_amount)
    file = open("saveddata.data","wb")
    pickle.dump(saveddata,file)
    file.close()


class Snake:
    def __init__(self):
        self.positions = [[10,10]]
        self.length = 5
        self._direction = [0,1]
        self.is_alive = False
        self.speed = 10  # The delay will be 1/speed
        self.reversed_controls = False
        threading.Thread(target=self.__loop).start()

    def __loop(self):
        while not quit_game:
            if self.is_alive:
                new_position = [self.positions[-1][0]+self._direction[0],self.positions[-1][1]+self._direction[1]]

                self.positions.append(new_position)
                if len(self.positions) > self.length:
                    self.positions.pop(0)

            time.sleep(1/self.speed)

    # I used this way for changing directions so I could apply the 'reverse' powerup.
    def set_direction(self, direction):
        if self.reversed_controls:
            self._direction = [-direction[0],-direction[1]]
        else:
            self._direction = direction

    def wait_duration(self, duration, action):
        time.sleep(duration)
        action()

    def apply_powerup(self, powerup):
        # THERE HAS TO BE A BETTER WAY OF DOING THIS... From within the PowerUp Definition, But how???

        if powerup.kind == "speed":
            self.speed += 5

            def action():
                self.speed -= 5

            threading.Thread(target=self.wait_duration, args=(powerup.duration, action,)).start()
            powerup.reset()
        elif powerup.kind == "slowness":
            self.speed -= 5

            def action():
                self.speed += 5

            threading.Thread(target=self.wait_duration, args=(powerup.duration, action,)).start()
            powerup.reset()
        elif powerup.kind == "reverse":
            self.reversed_controls = True

            def action():
                self.reversed_controls = False

            threading.Thread(target=self.wait_duration, args=(powerup.duration, action,)).start()
            powerup.reset()

        elif powerup.kind in ["score1", "score2", "score5"]:
            self.length+=int(powerup.kind[-1])
            powerup.reset()

    def reset(self):
        new_self = Snake()
        self.__dict__.update(new_self.__dict__)


class MenuOption:
    def __init__(self, name, fr, to):
        self.name = name
        self.fr = fr
        self.to = to


class Navigation:
    def __init__(self,window, own_snake):
        main_menu = [MenuOption("Singleplayer","Main","Options"),
                     MenuOption("Settings","Main","Settings"),
                     MenuOption("Info", "Main", "Info"),
                     MenuOption("Exit","Main","EXIT")]

       

        options_menu = [MenuOption("Start","Options","Play"),
                     MenuOption("Game Width","Options","change.Game Width"),
                     MenuOption("Game Height","Options","change.Game Height"),
                     MenuOption("Powerup Amount", "Options", "change.Powerup Amount"),
                     MenuOption("Back", "Options", "Main")]

        settings_menu = [MenuOption("Back","Settings","Main")]
        [settings_menu.insert(0,MenuOption(name,"Settings","set."+name)) for name in possible_settings.keys()]

        self.menus = {"Main":main_menu,"Settings":settings_menu,"Options":options_menu}
        self.own_snake = own_snake
        self.current_menu = "Main"
        self.current_selection_index = 0
        self.window = window
        self.display_current_menu()
        self.__loop()

    def display_current_menu(self):
        global standard_game_width, standard_game_height, standard_powerup_amount
        # Check if the game should exit:
        if self.current_menu == "EXIT":
            global quit_game
            quit_game = True
        elif self.current_menu == "Play":
            # Create and start the match+input loop
            self.in_match = True
            threading.Thread(target=self.__ingame_input_loop).start()
            Match(self.window, standard_game_height, standard_game_width, standard_powerup_amount ,[self.own_snake])
            # When you get here, the match is over
            self.in_match = False  # This will stop the input loop.
            self.own_snake.reset()
            self.current_menu = "Main"
            self.display_current_menu()
        else:
            self.window.clear()
            h, w = self.window.getmaxyx()
            self.window.addstr(2, int(w / 2 - len(self.current_menu) / 2), self.current_menu)

            if self.current_menu == "Info":
                line_number = 6
                x = int(w / 2 - w / 4)

                self.window.addstr(5, int(w / 2 - len("Controls") / 2), "Controls")
                for action, control_key in possible_controls.items():
                    self.window.addstr(line_number, x, action+": "+control_key)
                    line_number += 1

                self.window.addstr(line_number, int(w / 2 - len("Powerups") / 2), "Powerups")

                for powerup in possible_powerups.values():
                    # Don't display 'random' as a powerup
                    if powerup.get("kind") == "random":
                        continue
                    for name, attribute in powerup.items():

                        try:
                            if name == "kind":
                                line_number += 1  # Extra new line
                                self.window.attron(curses.color_pair(powerup.get("color")))
                                self.window.addstr(line_number, x, str(attribute))
                                self.window.attroff(curses.color_pair(powerup.get("color")))
                                line_number += 1
                            elif name == "duration" and attribute == 0:
                                continue
                            elif not name == "color":
                                self.window.addstr(line_number, x, name+": "+str(attribute))
                                line_number += 1
                        except:
                            # It doesn't fit in the window.
                            # Disable the color in case it didn't fit the window after attron.
                            self.window.attroff(curses.color_pair(powerup.get("color")))
                            pass
            elif self.current_menu.startswith("set."):
                option = self.current_menu.replace("set.","")
                variable_name = option.lower().replace(" ","_")
                line_number = 6
                x = int(w/2)
                color = None
                while not color in range(0,256):
                    try:
                        color = int(curses_input(self.window, 1, 4, line_number, x, option+ " - Enter the number of a color from the 256 color palette."))
                    except:
                        # Input wasn't a number
                        pass

                # THERE HAS TO BE A BETTER WAY OF DOING THIS. with exec() or something
                global selection_color, positive_color, negative_color, neutral_color
                if variable_name == "selection_color":
                    selection_color = color
                elif variable_name == "positive_color":
                    positive_color = color
                elif variable_name == "negative_color":
                    negative_color = color
                elif variable_name == "neutral_color":
                    neutral_color = color

                color_number = possible_settings.get(option)
                curses.init_pair(color_number, color, curses.COLOR_BLACK)
                self.window.attron(curses.color_pair(color_number))
                string = option+" Changed to "+ str(color)
                self.window.addstr(line_number+3, int(x-len(string)/2), string)
                self.window.attroff(curses.color_pair(color_number))
                self.window.refresh()
                time.sleep(2)
                self.current_menu = "Settings"
                self.display_current_menu()

            elif self.current_menu.startswith("change."):
                option = self.current_menu.replace("change.", "")
                line_number = 6
                x = int(w / 2)
                game_width = -1
                game_height = -1
                powerup_amount = -1
                if option == "Game Width":
                    while not game_width in range(10,w-5):
                        try:
                            game_width = int(curses_input(self.window, 1, 5, line_number, x,option + " - Enter a game width that fits your screen."))
                        except:
                            # Input wasn't a number
                            pass
                    standard_game_width = game_width
                elif option == "Game Height":
                    while not game_height in range(10,h-5):
                        try:
                            game_height = int(curses_input(self.window, 1, 5, line_number, x,option + " - Enter a game height that fits your screen."))
                        except:
                            # Input wasn't a number
                            pass
                    standard_game_height = game_height
                elif option == "Powerup Amount":
                    while not powerup_amount in range(0,81):
                        try:
                            powerup_amount = int(curses_input(self.window, 1, 5, line_number, x,option + " - Enter the amount of powerups you want (0-80)"))
                        except:
                            # Input wasn't a number
                            pass
                    standard_powerup_amount = powerup_amount
                string = option + " Changed!"
                self.window.addstr(line_number + 3, int(x - len(string) / 2), string)
                self.window.refresh()
                time.sleep(2)
                self.current_menu = "Options"
                self.display_current_menu()

            else:
                snake_text = "SNAKE SNAKE SNAKE SNAKE SNAKE SNAKE"
                x = int(w / 2 - len(snake_text) / 2)
                y = int(h / 2 - int(len(self.menus[self.current_menu]) / 2)-7)
                self.window.addstr(y, x, snake_text)

                # Display every menu option
                for i,menu_option in enumerate(self.menus[self.current_menu]):
                    x = int(w / 2 - len(menu_option.name) / 2)
                    y = int(h / 2 - int(len(self.menus[self.current_menu])/2) + i)
                    if i == self.current_selection_index:
                        self.window.attron(curses.color_pair(4))
                    self.window.addstr(y, x, menu_option.name)
                    self.window.attroff(curses.color_pair(4))

            self.window.refresh()

    def __ingame_input_loop(self):
        while not quit_game:
            if not self.in_match:
                break

            key = self.window.getch()

            if key == curses.KEY_UP:
                self.own_snake.set_direction([-1, 0])
            elif key == curses.KEY_DOWN:
                self.own_snake.set_direction([1, 0])
            elif key == curses.KEY_LEFT:
                self.own_snake.set_direction([0, -1])
            elif key == curses.KEY_RIGHT:
                self.own_snake.set_direction([0, 1])
            elif key == 27:  # 27 = ESC or ALT
                break

    def __loop(self):
        while not quit_game:

            key = self.window.getch()

            # Check if you pressed a key that has a functionality,
            # otherwise it would be refreshing the current menu for no reason.
            if key in [curses.KEY_UP,curses.KEY_DOWN,curses.KEY_ENTER,27,10,13]:  # 27 = ESC or ALT [10,13] = Enter
                if key == curses.KEY_UP and self.current_selection_index > 0:
                    self.current_selection_index -= 1
                elif key == curses.KEY_DOWN:
                    try:
                        if self.current_selection_index < len(self.menus[self.current_menu])-1:
                            self.current_selection_index += 1
                    except:
                        # Some menu's aren't in 'self.menus' so trying to subscript them wil cause an error.
                        pass
                elif key in [10,13]:            # [10,13] = Enter
                    self.current_menu = self.menus[self.current_menu][self.current_selection_index].to
                    self.current_selection_index = 0
                elif key == 27:                 # 27 = ESC or ALT
                    if self.current_menu == "Main":
                        break
                    else:
                        self.current_menu = "Main"

                self.display_current_menu()


class Match:
    def __init__(self, window, height, width, powerup_amount ,snakes):
        self.window = window
        self.height = height
        self.width = width
        self.snakes = snakes
        self.own_snake = snakes[0]
        self.game_over = False
        self.powerups = [PowerUp(possible_powerups.get("random"), [height-1,width-1]) for _ in range(powerup_amount)]

        # Make sure the snakes are alive:
        for snake in snakes:
            snake.is_alive = True
        self.display_match()
        self.__display_loop()

    def display_match(self):
        self.window.clear()

        h, w = self.window.getmaxyx()

        left_border = int(w / 2 - self.width / 2)
        right_border = int(w / 2 + self.width / 2)
        top_border = int(h / 2 - self.height / 2)
        bottom_border = int(h / 2 + self.height / 2)
        topleft = [top_border,left_border]
        bottomright = [bottom_border, right_border]

        textpad.rectangle(self.window, topleft[0], topleft[1], bottomright[0], bottomright[1])

        living_snakes = False
        # Draw the Score and Highscore
        score = self.own_snake.length - 5
        global highscore
        if score > highscore:
            highscore = score
        score_text = "Score: "+str(score)
        highscore_text = "HighScore: "+ str(highscore)
        self.window.attron(curses.color_pair(1))
        self.window.addstr(top_border, left_border+1, score_text)
        self.window.addstr(top_border, right_border-len(highscore_text), highscore_text)
        self.window.attroff(curses.color_pair(1))


        # Draw The PowerUps
        for powerup in self.powerups:
            self.window.attron(curses.color_pair(powerup.color))
            self.window.addstr(top_border + powerup.position[0], left_border + powerup.position[1], powerup.symbol)
            self.window.attroff(curses.color_pair(powerup.color))

        all_snake_positions = []

        for snake in self.snakes:
            for pos in snake.positions:
                all_snake_positions.append(pos)

        # Draw The Snakes
        for snake in self.snakes:

            # Check if the snake is in a powerup
            for powerup in self.powerups:
                if powerup.position in snake.positions:
                    snake.apply_powerup(powerup)

            # Kill the snake if it's head is inside another snake.
            if all_snake_positions.count(snake.positions[-1]) >= 2:
                snake.is_alive = False

            for pos in snake.positions:

                # Kill the snake when it's out of the window.
                if pos[0] <= 0 or pos[0] >= self.height:
                    snake.is_alive = False
                elif pos[1] <=0 or pos[1] >= self.width:
                    snake.is_alive = False

                self.window.addstr(top_border+pos[0],left_border+pos[1],snake_display_symbol)

            if snake.is_alive:
                living_snakes = True

        # Stop the game if all snakes are dead.
        if not living_snakes:
            self.game_over = True
            game_over_message = "GAME OVER!"
            winner_message = "YOU DIED WITH A SCORE OF "+str(score)
            h, w = self.window.getmaxyx()
            x = int(w / 2 - len(game_over_message) / 2)
            y = int(h / 2)
            self.window.attron(curses.color_pair(2))
            self.window.addstr(y, x, game_over_message)
            self.window.attroff(curses.color_pair(2))
            self.window.refresh()
            time.sleep(1)
            x = int(w / 2 - len(winner_message) / 2)
            y = int(h / 2+1)
            self.window.attron(curses.color_pair(1))
            self.window.addstr(y,x, winner_message)
            self.window.attroff(curses.color_pair(1))
            self.window.refresh()
            time.sleep(2)

        self.window.refresh()

    def __display_loop(self):
        while not quit_game:

            if self.game_over:
                break
            self.display_match()


class PowerUp:
    def __init__(self, dict, pos_max):
        self.max_y = pos_max[0]
        self.max_x = pos_max[1]
        self.position = [random.randint(1, self.max_y),random.randint(1,self.max_x)]
        self.used = False

        for k,v in dict.items():
            setattr(self, k, v)

        if self.kind == "random":
            new_self = PowerUp(random.choice(list(possible_powerups.values())),pos_max)
            self.__dict__.update(new_self.__dict__)

    def reset(self):
        new_self = PowerUp(random.choice(list(possible_powerups.values())),[self.max_y,self.max_x])
        self.__dict__.update(new_self.__dict__)


if __name__ == '__main__':

    screen = curses.initscr()
    curses.start_color()
    curses.init_pair(1, positive_color, curses.COLOR_BLACK)
    curses.init_pair(2, negative_color, curses.COLOR_BLACK)
    curses.init_pair(3, neutral_color, curses.COLOR_BLACK)
    curses.init_pair(4, selection_color, curses.COLOR_BLACK)
    curses.beep()
    curses.beep()
    screen.timeout(DELAY)
    screen.keypad(1)
    curses.noecho()
    curses.curs_set(0)
    screen.border(0)
    curses.curs_set(0)

    try:
        own_snake = Snake()
        navigator = Navigation(screen, own_snake)
        save_data()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(str(e)+ str(exc_type)+ str(fname)+ str(exc_tb.tb_lineno))
    curses.endwin()

