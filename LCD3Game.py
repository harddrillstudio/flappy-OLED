import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import RPi.GPIO as GPIO
import time
import random

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

font = ImageFont.load_default()

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

#================= GPIO BUTTONS ========================

# setup game vars
buttonOkay = 16

# setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# setup buttons
GPIO.setup(buttonOkay,  GPIO.IN, pull_up_down=GPIO.PUD_UP)

#================= END BUTTONS ========================

def getHighScore(filename):
    f = open(filename, "r")
    highscore = int(f.read())
    f.close()
    return highscore

def saveHighScore(filename, score):
    highscore = getHighScore(filename)
    if (score > highscore):
        f = open(filename, "w")
        f.write(str(score))
        f.close()

class Wall:
    sizeX = 5
    sizeY = 25

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __init__(self):
        self.x = areaX[1]
        self.y = random.randint(areaY[0], areaY[1] - self.sizeY)

    def getBody(self):
        body = [self.x, self.y, self.x + self.sizeX, self.y + self.sizeY]
        return body


class Player:
    size = 5
    g = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def getBody(self):
        body = [self.x, self.y, self.x + self.size, self.y + self.size]
        return body

    def checkBounds(self):
        if (self.y < areaY[0]):
            self.y = areaY[0]
        if (self.y > areaY[1]-self.size):
            self.y = areaY[1]-self.size

    def move(self):
        self.g = self.g + 0.2
        self.y = self.y + self.g

    def moveDown(self):
        self.g = self.g + 0.2

    def moveUp(self):
        self.g = -3

def getClosestWall(xPos):
    closest = Wall()
    closest.x = 100
    for w in walls:
        if (w.x < closest.x):
            closest = w
    return closest



areaX = [0, 127]
areaY = [0, 53]

player = Player(64, 10)
wall = Wall()

walls = [wall]

okayClick = False

timeOutEndMenu = 4
alive = True
score = 0
AIswitch = False

def checkOkayButton():
    global buttonOkay
    global okayClick

    if not GPIO.input(buttonOkay):
        okayClick = True
    else:
        okayClick = False

def intersect(player, wall):
    # if player on left or right of wall, then it's ok
    if (player.getBody()[2] < wall.x or player.x > wall.getBody()[2]):
        return False
    else: # if player is on X pos of wall, THEN
        # if player below wall, then ok
        if (player.y >= wall.y and player.getBody()[3] <= wall.getBody()[3]):
            return False
        else:
            return True


wallClock = 0
scoreClock = 0
score = 0
targetY = 30

while(alive):
    while(alive):

        #================= UPDATE LOGIC ========================

        # Spawn walls
        if (wallClock > 45 and len(walls) < 3):
            walls.append(Wall())
            wallClock = 0

        # increase score
        if (scoreClock >= 10):
            scoreClock = 0
            score = score + 1

        scoreClock = scoreClock + 1
        wallClock = wallClock + 1

        # handle button
        checkOkayButton()

        # AI
        if (AIswitch):
            for w in walls:
                if (w.x == player.x + 30):
                    targetY = w.y

            try:
                if (player.y > targetY + 15):
                    okayClick = True
            except:
                print("No walls")

        if (okayClick):
            player.moveUp()
        else:
            player.moveDown()

        # move player
        player.move()
        player.checkBounds()


        # move walls
        for w in walls:
            w.x = w.x - 1

        # delete walls
        for w in walls:
            if (w.x < 0 - Wall.sizeX):
                walls.remove(w)
                walls.append(Wall())


        # collision
        for w in walls:
            if (intersect(player, w)):
                alive = False

        #================= RENDER LCD ==========================

        # UI
        draw.line((areaX[0], areaY[1], areaX[1], areaY[1]), fill=255)

        draw.rectangle(player.getBody(), outline=255, fill=1)
        for w in walls:
            draw.rectangle((w.x, -1, w.x+w.sizeX, w.y), outline=255, fill=0)
            draw.rectangle((w.x, w.y+w.sizeY, w.x+w.sizeX, 64), outline=255, fill=0)

        draw.text((20, 54), str(score), font=font, fill=255)

    	# Display image
        disp.image(image)
        disp.display()
        # Clear image
        draw.rectangle((0,0,width,height), outline=0, fill=0)

        #================= END ==========================

    for i in range(timeOutEndMenu):
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((5, 0), 'Hold jump to restart', font=font, fill=255)
        draw.text((60, 53), "DECIDE!!! " + str(timeOutEndMenu-i), font=font, fill=255)

        # Draw scores
        draw.text((30, 10), 'Your score:', font=font, fill=255)
        draw.text((30, 20), str(score), font=font, fill=255)
        saveHighScore("highscoreOLED2.txt", score)
        highscore = getHighScore("highscoreOLED2.txt")
        draw.text((30, 30), 'Highest score:', font=font, fill=255)
        draw.text((30, 40), str(highscore), font=font, fill=255)

        disp.image(image)
        disp.display()

        time.sleep(1)

    checkOkayButton()
    if (okayClick):
        alive = True
        # reset game
        walls.clear()
        score = 0

    else:

        # Draw scores
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((30, 10), 'Your score:', font=font, fill=255)
        draw.text((30, 20), str(score), font=font, fill=255)
        saveHighScore("highscoreOLED2.txt", score)
        highscore = getHighScore("highscoreOLED2.txt")
        draw.text((30, 30), 'Highest score:', font=font, fill=255)
        draw.text((30, 40), str(highscore), font=font, fill=255)

        disp.image(image)
        disp.display()
