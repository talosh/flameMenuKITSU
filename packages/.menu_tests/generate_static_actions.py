for i in range(1, 1000):
    text = '{\n' + ' '*4 + '"name": "Menu Item ' + str(i).zfill(3) + '",\n'
    text += ' '*4 + '"order": ' + str(i) + ',\n'
    text += ' '*4 + '"execute": menu_' + str(i).zfill(3) + ',\n'
    text += '},'
    print (text)