for i in range(1, 1000):
    text = 'def menu_' + str(i).zfill(3) + '(selection):\n' + ' '*4 + 'message("Menu Item ' + str(i).zfill(3) + '")\n'
    print (text)