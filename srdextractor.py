# ======================================================================
# Author: Tobias Meisel (meisto)
# Creation Date: Fri 17 Feb 2023 01:30:52 AM CET
# Description: -
# ======================================================================
import json
import os
import re

import easyocr

if __name__ == "__main__":
    image = "test.jpg"
    lang = "en"

    reader = easyocr.Reader(['en'])
    result = reader.readtext('test.jpg')

    for i, c in enumerate(result):
        if c[2] > 0.95: continue

        print("[DOUBT]", end=" ")
        if i > 0: print("...", result[i-1][1][-30:], end=" ")
        print("|>", c[1], "<|", end=" ")
        if i < len(result) - 1: print(result[i+1][1][:30], "...")

    ## Monster entries in the SRD have the following layout:
    # Please note that this is a structural not a logical partition

    ## Block 1: all entries are always present and in this order
    # Creature Name
    # Creature Type and alignment
    # Armor Class
    # Hit Points
    # Speed
    # A block of stats in table form (6 columns, 2 rows)

    ## Block 2: any number of these entries are present but the order is preserved
    # Saving Throws
    # Skills
    # Damage Resistances
    # Damage Immunities
    # Condition Immunities
    # ...

    ## Block 3: all entries are always present and in this order
    # Senses
    # Languages
    # Challenge

    ## Block 4: Special Traits - This whole block is optional and has one or more entries.
    ## Block Actions - This block is present in all creature descriptions
    ## Block Reactions - This block is present in some creature descriptions
    ## Block Legendary Actions - This block is present in a limited number of creatures.
    ## Block Short description - sometimes present

    
    # Find creature line
    block1_regex = re.compile(
        r'(?P<name>[a-zA-Z ]+)\s*\n\s*' +
        r'(?P<creature_type>((Tiny)|(Small)|(Medium)|(Large)|(Huge)|(Gargantuan))\s+([ a-zA-Z]+)(\s*\(.*\))?)\s*,?\s*' + 
        r'(?P<alignment>((((lawful)|(neutral)|(chaotic))\s*((good)|(neutral)|(evil)))|(neutral)|(unaligned)|(any (non-good )?alignment)))\s*\n\s*' + 
        r'(?P<armor_class>Armor\s+Class\s*[0-9]+\s*[a-zA-z,\(\)\n]*)\s*\n\s*' +
        r'(?P<hit_points>Hit\s+Points\s+[0-9]+\s*\(.*\))\s*\n\s*' +
        r'(?P<speed>Speed\s*[0-9]+\s*ft\s*\.,?(\s*[a-zA-Z]+\s*[0-9]+\s*ft\s*\.\s*(\(.*\))?,?)*)\s*\n?' + 
        r'(?P<stat_block>STR\nDEX\nCON\nINT\nWIS\nCHA\n([1-9][0-9]*\s*\((-|\+)[0-9]+\)\n){6,6})'
    )

    block3_regex = re.compile(
        r'(?P<senses>Senses(\s*[ a-zA-Z]+[0-9]+(\s*ft\.)?,?\s*\n\s*)+)' + 
        r'(?P<languages>Languages(\s*[ a-zA-Z]+\s*\(.*\),?)+)\s*\n\s*' + 
        r'(?P<challenge>Challenge\s*[0-9]+\s*\n?\s*(\(?.*XP\s*\)?))\s*\n'
    )

    block5_regex = re.compile(
        r'Actions\n' + 
        r'(?P<actions>[a-zA-Z]+(\.|:)((.*)\s*\n\s*)+)'
    )

    block6_regex = re.compile(
        r'Reactions\n' + 
        r'(?P<reactions>[a-zA-Z]+(\.|:)((.*)\s*\n\s*)+)'
    )

    # Merge and clean input
    con = map(lambda a: a[1], result)
    con = "\n".join(con).replace("_", ".")

    # Print out what has been read for regex debugging
    print(repr(con))


    # Introduce default values
    name            = "NONAME"
    creature_type   = "NOTYPE"
    alignment       = "NOALIGN"
    armor_class     = "NOARMOR"
    hit_points      = "NOHIT"
    speed           = "NOSPEED"
    stats           = ["-", "-", "-", "-", "-", "-"]
    properties      = []
    senses          = "NOSENS"
    languages       = "NOLANGUAGE"
    challenge       = "NOCHALLENGE"
    special_traits  = []
    actions         = []
    reactions       = []

    a = block1_regex.search(con)
    if a != None:
        d = a.groupdict()
        name            = d["name"]
        creature_type   = d["creature_type"]
        alignment       = d["alignment"]
        armor_class     = re.sub(r"Armor Class\s*", "", d["armor_class"], 1)
        hit_points      = re.sub(r"Hit Points\s*", "", d["hit_points"], 1)
        speed           = re.sub(r"Speed\s*", "", d["speed"], 1)
        stats           = d["stat_block"].strip().split("\n")[6:]


    b = block3_regex.search(con)
    if b != None:
        d = b.groupdict()
        
        senses      = re.sub(r"Senses\s*", "", d["senses"], 1)
        languages   = re.sub(r"Languages\s*", "", d["languages"], 1)
        challenge   = re.sub(r"Challenge\s*", "", d["challenge"], 1)


    c = block5_regex.search(con)
    if c != None:
        ac = c.groupdict()["actions"].split("\n")

        isHeader_regex = re.compile(r"^[a-zA-Z]+(\.|:).+$")

        for i,x in enumerate(ac):
            if isHeader_regex.match(x) != None:
                actions.append(x)
            else:

                # This should not happen but could be due to a acr problem
                if i == 0: actions.append("")

                actions[-1] += " " + x


    d = block6_regex.search(con)
    if d != None:
        ac = d.groupdict()["reactions"].split("\n")

        isHeader_regex = re.compile(r"^[a-zA-Z]+(\.|:).+$")

        for i,x in enumerate(ac):
            if isHeader_regex.match(x) != None:
                reactions.append(x)
            else:

                # This should not happen but could be due to a acr problem
                if i == 0: reactions.append("")

                reactions[-1] += " " + x
        

    file_content = {   
        "name": name,
        "creature_type": creature_type,
        "alignment": alignment,
        "armor_class": armor_class,
        "hit_points": hit_points,
        "speed": speed,
        "stats": stats,
        "properties": properties,
        "senses": senses,
        "languages": languages,
        "challenge": challenge,
        "special_traits": special_traits,
        "actions": actions,
        "reactions": reactions,
    }

    # Generate File name
    file_name = re.sub(r'\s+', "_", file_content["name"].lower()) 
    file_name = file_name + ".json"

    # Write object to file
    file_path = os.path.join(os.getcwd(), "data", "creatures", file_name)
    with open(file_path, mode='w') as f:
        json.dump(file_content, f, indent="\t")
