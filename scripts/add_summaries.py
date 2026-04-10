#!/usr/bin/env python3
import json

# Load existing timeline
with open('hobbit_realistic_timeline.json') as f:
    timeline = json.load(f)

# Chapter summaries for canonical events
summaries = {
    'The Unexpected Party Begins': 'In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, but a hobbit-hole, and that means comfort. It had a perfectly round door like a porthole, painted green, with a shiny yellow brass knob in the exact middle.',
    'Thorin and Company Arrive': 'The bell rang and the door opened to reveal Thorin Oakenshield, a proud dwarf with a blue beard. Soon more dwarves arrived - Dwalin, Balin, Kili, Fili, Dori, Nori, Ori, Oin, Gloin, Bifur, Bofur, and Bombur - until Bilbo\'s hobbit-hole was quite crowded.',
    'The Company Departs': 'The morning came all too quickly for Bilbo Baggins. Despite his initial reluctance and his missing handkerchief, he found himself running to join Thorin and Company on their adventure, without so much as a pocket-handkerchief.',
    'The Trolls': 'Camped in the Trollshaws, the company\'s ponies were stolen by three trolls: Tom, Bert, and William. Bilbo tried to steal a wallet from one troll but was caught. The trolls argued until dawn, when Gandalf\'s trickery turned them to stone.',
    'Discovery of Sting and Orcrist': 'In the trolls\' cave, the company discovered elven blades: Glamdring for Gandalf, Orcrist for Thorin, and a small knife that Bilbo decided would make an excellent letter-opener, not knowing it was an ancient elven blade.',
    'Arrival at Rivendell': 'Elrond welcomed the travelers to the Last Homely House. He examined their swords and map, revealing the moon-letters that showed the secret door into the Lonely Mountain could be opened on Durin\'s Day.',
    'The Stone-giants': 'In the Misty Mountains, the company sheltered from a storm and witnessed stone-giants throwing boulders at each other. Fearing for their safety, they found a cave to rest in, not knowing it was a goblin entrance.',
    'Captured by Goblins': 'Goblins emerged from cracks in the cave and captured the company, taking them to their underground town. The Great Goblin threatened them, but Gandalf appeared and slew the Great Goblin, allowing the dwarves to flee.',
    'Riddles in the Dark': 'Falling in the dark, Bilbo found himself in an underground lake chamber with Gollum. They played a riddle-game: if Bilbo won, Gollum would show him the way out; if Gollum won, he would eat Bilbo. Bilbo won, but Gollum tried to kill him anyway.',
    'Reunion and Escape': 'Bilbo found his way out of the mountains using the Ring to become invisible. He reunited with the dwarves and Gandalf, though they were skeptical of his story. The company continued their journey eastward.',
    'Wargs and Eagles': 'The company was ambushed by Wargs - evil wolves - and forced to climb trees. Goblins arrived and set fires beneath them. Giant eagles rescued them and carried them to their eyrie, where the company was grateful but wary.',
    'The Eagles Eyrie': 'The Lord of the Eagles questioned the company and agreed to carry them safely beyond the borders of the Wilderland. They were set down on the Carrock, a great stone in the middle of a river.',
    'Gandalf Departs': 'Near the edge of Mirkwood, the company stayed with Beorn, a skin-changer who could take the form of a bear. After rest and supplies, Gandalf announced he must leave them to attend to other business, leaving the dwarves and Bilbo to enter Mirkwood alone.',
    'Spider Attack': 'In Mirkwood, Bombur fell into an enchanted sleep. Later, the dwarves were captured by giant spiders. Bilbo used his Ring and sword - now named Sting - to rescue them, fighting spiders and declaring "Attercop!"',
    'Captured by Elves': 'After escaping the spiders, the hungry dwarves were captured by Wood-elves and imprisoned in the Elvenking\'s halls. Bilbo, invisible, followed them and devised a plan for their escape.',
    'Barrel Escape': 'Bilbo discovered the water-gate and arranged for the dwarves to escape in barrels used for transporting wine to Lake-town. It was an uncomfortable journey for the dwarves, but they reached the Long Lake safely.',
    'Arrival at Lake-town': 'The company arrived at Lake-town (Esgaroth), where they were greeted with songs about the return of the King Under the Mountain. Thorin declared himself, and the Master of Lake-town provided them provisions and boats for their journey to the Mountain.',
    'The Desolation of Smaug': 'The company crossed the desolate lands around the Lonely Mountain, finding the ruins of Dale. They made camp at the secret door, but could not open it, waiting for Durin\'s Day.',
    'Secret Door Opens': 'On Durin\'s Day, the last light of the sun revealed the keyhole. Thorin used the key to open the secret door. Bilbo was sent down the tunnel to investigate, taking the Ring with him.',
    'First Contact with Smaug': 'Bilbo entered Smaug\'s lair and spoke with the dragon, using riddles and flattery. He discovered a bare patch on Smaug\'s left breast. Smaug grew suspicious and flew out to destroy Lake-town in revenge.',
    'Smaug Attacks Lake-town': 'Smaug descended upon Lake-town in a terrible rage. The thrush told Bard the Bowman of Smaug\'s weak spot. Bard shot a black arrow into the dragon\'s heart, and Smaug fell, destroying the town as he died.',
    'Smaug Slain': 'With Smaug dead, the company claimed the Lonely Mountain. Birds brought news of Smaug\'s fall. Thorin sent for Dain and his people, but the Elvenking and Bard came seeking a share of the treasure.',
    'Claiming the Mountain': 'Thorin grew proud and stubborn, refusing to share the treasure with Bard or the Elvenking. He called for Dain to come with armed dwarves, and walls were built across the entrance to the mountain.',
    'The Siege Begins': 'Bard and the Elvenking laid siege to the mountain. Bilbo tried to negotiate, offering the Arkenstone to Bard as a bargaining chip. Thorin was furious when he learned this and nearly threw Bilbo from the walls.',
    'The Battle of Five Armies': 'Dain arrived but then armies of goblins and Wargs attacked. Elves, Men, and Dwarves united against them. Thorin charged from the mountain with his companions but was mortally wounded. The Eagles arrived to turn the tide.',
    'Thorin\'s Death': 'Thorin lay dying on the battlefield. He reconciled with Bilbo, saying: "If more of us valued food and cheer and song above hoarded gold, it would be a merrier world." He died with his sword in his hand.',
    'Home Again': 'Bilbo returned home with Gandalf, two small chests of gold and silver, and his magic ring. He found his goods being auctioned off, as he was presumed dead. He bought back his own things and settled into his comfortable life, forever changed.'
}

# Add summaries to entries
for entry in timeline['entries']:
    title = entry.get('title', '')
    if title in summaries:
        entry['summary'] = summaries[title]
    else:
        entry['summary'] = title

with open('hobbit_realistic_timeline.json', 'w') as f:
    json.dump(timeline, f, indent=2)

print(f'Added summaries to {len(timeline["entries"])} timeline entries')
