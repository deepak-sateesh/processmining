import xml.etree.ElementTree as ET
Nodes=["Change Version - Machine 22 (4)", "Deburring - Manual (9)", "Final Inspection Q.C. (534)"]
Nodes=set(Nodes)
mytree = ET.parse('Backloop.svg')
myroot = mytree.getroot()
Edges=[("Change Version - Machine 22 (4)", "Deburring - Manual (9)"),("Deburring - Manual (9)", "Final Inspection Q.C. (534)")]
Edges=set(Edges)

NodesDict={}
for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
    for gg in g.findall('{http://www.w3.org/2000/svg}g'):
        if (gg.get('class') == 'node'):
            n = gg.find('{http://www.w3.org/2000/svg}text').text
            if (n in Nodes):
                # chAttrb = gg.find('{http://www.w3.org/2000/svg}polygon').attrib
                # print((chAttrb.keys())[0])
                NodesDict[n] = gg.find('{http://www.w3.org/2000/svg}title').text
                gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')

print(NodesDict[x] for x in NodesDict.keys())
for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
    for gg in g.findall('{http://www.w3.org/2000/svg}g'):
        if (gg.get('class') == 'edge'):
            for (s, d) in Edges:

                title = gg.find('{http://www.w3.org/2000/svg}title').text
                t= [title.split('->')]

                if(NodesDict[s]==t[0][0] and NodesDict[d]==t[0][1]):
                    print((s,NodesDict[s], t[0][0], d,NodesDict[d], t[0][1], gg.find('{http://www.w3.org/2000/svg}title').text ))
                    gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')
                    gg.find('{http://www.w3.org/2000/svg}polygon').set('stroke', '#800000')

mytree.write('output.svg')
'''Node = g.find('text').text
    Edge = g.get('cl')
    print(Text, rank)
print("Fin")'''
'''
<breakfast_menu>
    <food>
        <name itemid="11">Belgian Waffles</name>
        <price>5.95</price>
        <description>Two of our famous Belgian Waffles
with plenty of real maple syrup</description>
        <calories>650</calories>
    </food>
    <food>
        <name itemid="21">Strawberry Belgian Waffles</name>
        <price>7.95</price>
        <description>Light Belgian waffles covered
with strawberries and whipped cream</description>
        <calories>900</calories>
    </food>
    <food>
        <name itemid="31">Berry-Berry Belgian Waffles</name>
        <price>8.95</price>
        <description>Light Belgian waffles covered with
an assortment of fresh berries and whipped cream</description>
        <calories>900</calories>
    </food>
    <food>
        <name itemid="41">French Toast</name>
        <price>4.50</price>
        <description>Thick slices made from our
homemade sourdough bread</description>
        <calories>600</calories>
    </food>
</breakfast_menu>

# iterating through the price values.
for prices in myroot.iter('price'):
    # updates the price value
    prices.text = str(float(prices.text) + 10)
    # creates a new attribute
    prices.set('newprices', 'yes')

# creating a new tag under the parent.
# myroot[0] here is the first food tag.
ET.SubElement(myroot[0], 'tasty')
for temp in myroot.iter('tasty'):
    # giving the value as Yes.
    temp.text = str('YES')

# deleting attributes in the xml.
# by using pop as attrib returns dictionary.
# removes the itemid attribute in the name tag of
# the second food tag.
myroot[1][0].attrib.pop('itemid')

# Removing the tag completely we use remove function.
# completely removes the third food tag.
myroot.remove(myroot[2])

mytree.write('output.xml')'''