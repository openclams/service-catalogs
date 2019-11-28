import glob, os
import json
import urllib
import textwrap
# in Konsole: pip install Pillow
from PIL import Image, ImageDraw, ImageFont, ImageOps

def createImage(text, filename):

    selected_font='arial.ttf'
    font_size=42

    font = ImageFont.truetype(selected_font, font_size)

    #create black rectangle with rounded edges
    imgback = round_rectangle((266, 266), 40, 'black')

    #create smaller white rectangle with rounded edges
    imgfront = round_rectangle((252, 252), 40, 'white')

    #combine both with an 7 to 7 offset
    imgback.paste(imgfront, (7, 7), imgfront)

    draw = ImageDraw.Draw(imgback)

    # add text
    margin = offset = 20
    for line in textwrap.wrap(text, width=9):
        draw.text((margin, offset), line, font=font, fill="#aa0000")
        offset += font.getsize(line)[1]


    imgback.save("scripts/"+filename+'.png')


def round_corner(radius, fill):
    """Draw a round corner"""
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
    return corner

def round_rectangle(size, radius, fill):
    """Draw a rounded rectangle"""
    width, height = size
    rectangle = Image.new('RGBA', size, fill)
    corner = round_corner(radius, fill)
    rectangle.paste(corner, (0, 0))
    rectangle.paste(corner.rotate(90), (0, height - radius)) # Rotate the corner and paste it
    rectangle.paste(corner.rotate(180), (width - radius, height - radius))
    rectangle.paste(corner.rotate(270), (width - radius, 0))
    return rectangle


os.chdir("../")

# read files and create images
for file in glob.glob("*.json"):
    print("Reading:" + file)
    jsonfile = json.load(open(file))

    for jsonobj in jsonfile:
        createImage(jsonobj['name'],jsonobj['id'])
