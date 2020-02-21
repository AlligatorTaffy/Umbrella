from tkinter import *


root = Tk()
root.title('S.U.N. Shade Sysytem')

screen = Frame(master = root, width = 680, height = 400, bg = 'white')
screen.pack()

windSpeedDisplayLabel = Label(root, text = 'Wind Speed (MPH):', height = 1, width = 17, bg = 'white')
windSpeedDisplayLabel.place(relx = 0, rely = 0)

windSpeedDisplayTextbox = Text(root, height = 1, width = 5)
windSpeedDisplayTextbox.place(relx = 0.18, rely = 0)

logo = Label(root, text = 'S.U.N. Shade System', height = 1, width = 18, bg = 'white', fg = 'red', font = 'arial')
logo.place(relx = 0.38, rely = 0)

emgStopAlertIcon = PhotoImage(file = "assets/stopsign.gif")
icon1 = Label(root, compound = CENTER, image = emgStopAlertIcon).place(relx = 0.8, rely = 0)

callAlertIcon = PhotoImage(file = "assets/callalert.gif")
icon2 = Label(root, compound = CENTER, image = callAlertIcon).place(relx = 0.933, rely = 0)

#create buttons
openAllButton = Button(root, text = 'Open All', bg = 'green', fg = 'black')
openAllButton.place(relx = 0.3, rely = 0.35, anchor = "c")

closeAllButton = Button(root, text = 'Close All', bg = 'red', fg = 'white')
closeAllButton.place(relx = 0.69, rely = 0.35, anchor = "c")

#add a grid for Open dropdown list
mainframe1 = Frame(root)
mainframe1.grid(column = 0, row = 0, sticky = (N, W, E, S))
mainframe1.columnconfigure(0, weight = 1)
mainframe1.rowconfigure(0, weight = 1)
mainframe1.place(relx = 0, rely = 0.6)

#add a grid for Close dropdown list
mainframe2 = Frame(root)
mainframe2.grid(column = 0, row = 0, sticky = (N, W, E, S))
mainframe2.columnconfigure(0, weight = 1)
mainframe2.rowconfigure(0, weight = 1)
mainframe2.place(relx = 0.3, rely = 0.6)

#add a grid for Reset dropdown list
mainframe3 = Frame(root)
mainframe3.grid(column = 0, row = 0, sticky = (N, W, E, S))
mainframe3.columnconfigure(0, weight = 1)
mainframe3.rowconfigure(0, weight = 1)
mainframe3.place(relx = 0.6, rely = 0.6)

#create tkinter variables
tkvar1 = StringVar(root)
tkvar2 = StringVar(root)
tkvar3 = StringVar(root)

#Dictionary with options (Open)
choices1 = ['Umbrella 1', 'Umbrella 2', 'Umbrella 3']
popupMenu1 = OptionMenu(mainframe1, tkvar1, * choices1)
Label(mainframe1, text = 'Open').grid(row = 1, column = 1)
popupMenu1.grid(row = 2, column = 1)
tkvar1.set('') #set the default option

#Dictionary with options (Close)
choices2 = ['Umbrella 1', 'Umbrella 2', 'Umbrella 3']
popupMenu2 = OptionMenu(mainframe2, tkvar2, * choices2)
Label(mainframe2, text = 'Close').grid(row = 1, column = 1)
popupMenu2.grid(row = 2, column = 1)
tkvar2.set('') #set the default option

#Dictionary with options (Reset)
choices3 = ['Umbrella 1', 'Umbrella 2', 'Umbrella 3']
popupMenu3 = OptionMenu(mainframe3, tkvar3, * choices3)
Label(mainframe3, text = 'Reset').grid(row = 1, column = 1)
popupMenu3.grid(row = 2, column = 1)
tkvar3.set('') #set the default option

listbox = Listbox(root)
listbox.place(relx = 0.8, rely = 0.6, height = 80)
listbox.insert(END, "Power")
for item in ["Umbrella 1: %", "Umbrella 2: %", "Umbrella 3: %"]:
    listbox.insert(END, item)

#on change drowdown value
#def change_dropdown(* args):
    #print(tkvar.get())

#link function to change dropdown
#tkvar.trace('w', change_dropdown)

root.mainloop()
